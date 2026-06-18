"""Detection worker: one background thread, one model, thread-safe latest state.

The FastAPI endpoints only ever read the shared snapshot, so heavy inference
never blocks the API loop. Frame-skip + target FPS keep the Raspberry Pi 5 from
saturating, and event writes to the data-api are debounced per class.
"""

from __future__ import annotations

import threading
import time
from collections import Counter, deque
from datetime import datetime

import numpy as np

from ..config import Settings
from ..imaging import placeholder, to_jpeg
from ..logging_conf import get_logger
from .registry import DetectorBundle

log = get_logger(__name__)


class DetectionService:
    def __init__(self, settings: Settings, camera_manager, hardware_manager,
                 sink, bundle: DetectorBundle):
        self._settings = settings
        self._cameras = camera_manager
        self._hw = hardware_manager
        self._sink = sink
        self._detector = bundle.detector
        self.mode = bundle.mode
        self.degraded = bundle.degraded
        self.note = bundle.note

        self._lock = threading.Lock()
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self._started_at: float | None = None

        # mutable config
        self._conf = settings.conf_threshold
        self._iou = settings.iou_threshold
        self._target_fps = settings.target_fps

        # shared latest state (guarded by _lock)
        self._frame: np.ndarray | None = None
        self._frame_seq = 0
        self._jpeg_cache: tuple[int, bytes] | None = None
        self._detections: list[dict] = []
        self._recent: deque[dict] = deque(maxlen=10)
        self._counts: Counter = Counter()
        self._fps = 0.0
        self._last_tick: float | None = None
        self._last_detection: dict | None = None
        self._debounce: dict[str, float] = {}
        self._last_gas_check = 0.0
        self._gas_was_dangerous = False  # tracks previous state for edge detection
        self._temp_was_high = False
        self._last_temp_check = 0.0

        # Start gas polling thread immediately (independent of detection)
        self._gas_stop = threading.Event()
        self._gas_thread = threading.Thread(target=self._gas_loop, name="gas-poll", daemon=True)
        self._gas_thread.start()

    # -- control ------------------------------------------------------------
    def start(self) -> bool:
        if self._running.is_set():
            return False
        self._running.set()
        self._started_at = time.time()
        self._thread = threading.Thread(target=self._loop, name="detection", daemon=True)
        self._thread.start()
        self._sink.record_event("detection_started", "INFO", f"mode={self.mode}")
        log.info("Detection started (mode=%s)", self.mode)
        return True

    def stop(self) -> bool:
        self._gas_stop.set()
        if not self._running.is_set():
            return False
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        self._hw.signal_detection(False)
        self._sink.record_event("detection_stopped", "INFO", "")
        log.info("Detection stopped")
        return True

    @property
    def active(self) -> bool:
        return self._running.is_set()

    # -- worker -------------------------------------------------------------
    def _loop(self) -> None:
        try:
            self._detector.warmup()
        except Exception as exc:  # noqa: BLE001
            log.warning("detector warmup failed: %s", exc)

        skip = max(0, self._settings.frame_skip)
        frame_no = 0
        while self._running.is_set():
            loop_start = time.time()
            frame = self._cameras.read_active()
            if frame is None:
                time.sleep(0.1)
                continue

            frame_no += 1
            if skip and frame_no % (skip + 1) != 0:
                continue

            try:
                result = self._detector.infer(frame, self._conf, self._iou)
            except Exception as exc:  # noqa: BLE001
                log.warning("inference failed: %s", exc)
                time.sleep(0.1)
                continue

            self._publish(result)
            self._emit_events(result)
            self._poll_gas()
            self._measure_fps()

            elapsed = time.time() - loop_start
            target = 1.0 / max(0.5, self._target_fps)
            if elapsed < target:
                time.sleep(target - elapsed)

    def _publish(self, result) -> None:
        with self._lock:
            self._frame = result.frame
            self._frame_seq += 1
            self._detections = [d.to_dict() for d in result.detections]
        self._hw.signal_detection(bool(result.detections))

    def _measure_fps(self) -> None:
        now = time.time()
        if self._last_tick is not None:
            dt = now - self._last_tick
            if dt > 0:
                inst = 1.0 / dt
                with self._lock:
                    # exponential moving average for a steady readout
                    self._fps = round(self._fps * 0.7 + inst * 0.3, 1)
        self._last_tick = now

    def _emit_events(self, result) -> None:
        now = time.time()
        debounce = self._settings.detection_debounce_seconds
        alerted = False
        for det in result.detections:
            last = self._debounce.get(det.class_name, 0.0)
            if now - last < debounce:
                continue
            self._debounce[det.class_name] = now
            entry = {
                "class_name": det.class_name,
                "confidence": int(det.confidence * 100),
                "time": datetime.now().strftime("%H:%M:%S"),
                "priority": det.priority,
            }
            with self._lock:
                self._recent.appendleft(entry)
                self._counts[det.class_name] += 1
                self._last_detection = entry
            self._sink.record_detection(det.class_name, det.confidence)
            self._hw.blink_rgb_module_red(3.0)
            self._hw.show_detection_on_lcd(det.class_name, entry["time"])
            if not alerted:
                self._hw.priority_alert(det.priority)
                alerted = True

    def _gas_loop(self) -> None:
        """Background thread: read MQ-2 every 2 s and temperature every 10 s."""
        while not self._gas_stop.is_set():
            self._gas_stop.wait(timeout=2.0)
            if self._gas_stop.is_set():
                break
            try:
                reading = self._hw.read_gas()
                if reading.get("ppm") is None:
                    continue
                self._sink.record_gas(reading["ppm"], reading["dangerous"])
                now_dangerous = reading["dangerous"]
                if now_dangerous and not self._gas_was_dangerous:
                    threading.Thread(
                        target=self._hw.gas_alert,
                        args=(reading["ppm"],),
                        name="gas-buzz",
                        daemon=True,
                    ).start()
                self._gas_was_dangerous = now_dangerous
            except Exception as exc:  # noqa: BLE001
                log.warning("gas poll error: %s", exc)

            # Temperature check every 10 s
            now = time.time()
            if now - self._last_temp_check < 5.0:
                continue
            self._last_temp_check = now
            try:
                climate = self._hw.read_climate()
                temp = climate.get("temperature")
                if temp is None:
                    continue
                now_high = float(temp) > 50.0
                self._sink.record_temperature(float(temp), now_high)
                if now_high and not self._temp_was_high:
                    threading.Thread(
                        target=self._hw.temp_alert,
                        args=(float(temp),),
                        name="temp-buzz",
                        daemon=True,
                    ).start()
                self._temp_was_high = now_high
            except Exception as exc:  # noqa: BLE001
                log.warning("temp poll error: %s", exc)

    def _poll_gas(self) -> None:
        pass  # gas polling moved to dedicated _gas_loop thread

    # -- queries ------------------------------------------------------------
    def get_config(self) -> dict:
        return {"conf_threshold": self._conf, "iou_threshold": self._iou,
                "target_fps": self._target_fps}

    def set_config(self, conf: float | None = None, target_fps: float | None = None) -> dict:
        if conf is not None:
            self._conf = max(0.0, min(1.0, conf))
        if target_fps is not None:
            self._target_fps = max(0.5, min(30.0, target_fps))
        return self.get_config()

    def latest(self) -> dict:
        with self._lock:
            return {
                "active": self.active,
                "mode": self.mode,
                "degraded": self.degraded,
                "fps": self._fps,
                "threshold": self._conf,
                "target_fps": self._target_fps,
                "counts": dict(self._counts),
                "detections": list(self._detections),
                "recent": list(self._recent),
                "last_detection": self._last_detection,
            }

    def uptime_seconds(self) -> float:
        return 0.0 if self._started_at is None else round(time.time() - self._started_at, 1)

    def frame_jpeg(self) -> bytes:
        # While running, serve the latest annotated frame (cached per sequence).
        if self.active:
            with self._lock:
                frame = self._frame
                seq = self._frame_seq
                cache = self._jpeg_cache
            if frame is not None:
                if cache is not None and cache[0] == seq:
                    return cache[1]
                data = to_jpeg(frame)
                with self._lock:
                    self._jpeg_cache = (seq, data)
                return data
        # Stopped (or no frame yet) — serve whatever the CameraReader last cached.
        preview = self._cameras.cached()
        if preview is not None:
            return to_jpeg(preview)
        return to_jpeg(placeholder(self._settings.frame_width,
                                   self._settings.frame_height, "no signal"))
