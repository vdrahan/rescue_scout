"""Background camera reader: single thread owns capture, others read the cache.

The reader is the only caller of ``CameraManager.capture_active()`` and
``CameraManager.capture_camera()``.  Every other consumer — the detection loop
and the HTTP frame endpoint — reads the per-camera cache via non-blocking methods.

Camera read priorities (per tick):
  1. Active camera        — always, at ``camera_read_fps`` (e.g. 15 fps).
  2. Detection camera     — always at ``_INFERENCE_BG_INTERVAL`` when it is NOT
                            active, so AI inference never starves while the user
                            watches the FPV feed.
  3. Other secondary cams — every ``_SECONDARY_INTERVAL`` seconds (4 fps) to
                            keep the buffer drained so switching back is instant.
"""

from __future__ import annotations

import threading
import time

from ..config import Settings
from ..logging_conf import get_logger
from .manager import CameraManager

log = get_logger(__name__)

_INFERENCE_BG_INTERVAL = 0.25   # 4 fps — keeps detection camera fresh in background
_SECONDARY_INTERVAL = 0.25      # 4 fps — keeps all standby cameras fresh to avoid stale frames on switch


class CameraReader:
    def __init__(self, manager: CameraManager, settings: Settings):
        self._manager = manager
        self._interval = 1.0 / max(1.0, settings.camera_read_fps)
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_inference_bg = 0.0
        self._last_secondary = 0.0

    def _tick(self) -> bool:
        """Capture one frame into the active camera cache, then service secondaries."""
        frame = self._manager.capture_active()

        now = time.monotonic()
        inference_id = self._manager.inference_source_id()

        for cam_id in self._manager.secondary_ids():
            if cam_id == inference_id:
                # Detection camera must stay fresh for background AI inference
                if now - self._last_inference_bg >= _INFERENCE_BG_INTERVAL:
                    try:
                        self._manager.capture_camera(cam_id)
                    except Exception as exc:  # noqa: BLE001
                        log.warning("BG inference camera %s error: %s", cam_id, exc)
                    self._last_inference_bg = now
            else:
                # Other standby cameras: drain buffer at 4 fps so switching back is instant
                if now - self._last_secondary >= _SECONDARY_INTERVAL:
                    try:
                        self._manager.capture_camera(cam_id)
                    except Exception as exc:  # noqa: BLE001
                        log.warning("Secondary camera %s error: %s", cam_id, exc)

        if now - self._last_secondary >= _SECONDARY_INTERVAL:
            self._last_secondary = now

        return frame is not None

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        self._thread = threading.Thread(target=self._loop, name="camera-reader", daemon=True)
        self._thread.start()
        log.info("CameraReader started (%.0f fps target)", 1.0 / self._interval)

    def stop(self) -> None:
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        log.info("CameraReader stopped")

    def _loop(self) -> None:
        while self._running.is_set():
            t0 = time.monotonic()
            try:
                self._tick()
            except Exception as exc:  # noqa: BLE001
                log.warning("CameraReader tick error: %s", exc)
            elapsed = time.monotonic() - t0
            remaining = self._interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
