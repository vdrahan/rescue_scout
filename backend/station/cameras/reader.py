"""Background camera reader: one capture thread per camera, newest frame only.

Every camera - active or standby - is read by its own thread, continuously, at the
rate the stream produces frames. Every other consumer (the detection loop and the
HTTP frame endpoint) only reads the per-camera cache via non-blocking methods.

Why one thread per camera: an RTSP source that is read more slowly than it produces
(the old 4 fps "standby" poll against a ~22 fps stream) queues the surplus inside the
capture and the socket buffer. Measured on the Pi that backlog was ~30 s of video, so
a camera switch - and the detector, which always reads the detection camera - got
footage from half a minute ago. Reading continuously and keeping only the newest frame
leaves nothing to queue. It also isolates cameras: a dead camera that blocks in its
reconnect attempt no longer stalls the healthy one.

Consuming a frame (decode) is cheap; converting it to RGB for the cache is not. The
camera on screen is converted every frame, any other camera only a few times a second -
enough that its cache is fresh the instant you switch to it, and the detection camera
often enough for the detector. Converting every frame of the camera nobody was
watching cost ~30% of a core and slowed detection from ~4 to ~2.5 fps.
"""

from __future__ import annotations

import threading
import time

from ..config import Settings
from ..logging_conf import get_logger
from .manager import CameraManager

log = get_logger(__name__)

_IDLE_SLEEP = 0.1  # a camera in reconnect backoff returns at once; poll it gently
_STANDBY_CONVERT_INTERVAL = 0.2  # a camera nobody is watching: ~5 converted frames/s


class CameraReader:
    def __init__(self, manager: CameraManager, settings: Settings):
        self._manager = manager
        self._interval = 1.0 / max(1.0, settings.camera_read_fps)
        # The detector needs ~target_fps frames/s from the detection camera, watched or not.
        self._inference_interval = min(
            _STANDBY_CONVERT_INTERVAL, 1.0 / (1.5 * max(1.0, settings.target_fps))
        )
        self._running = threading.Event()
        self._threads: list[threading.Thread] = []

    def _tick(self) -> bool:
        """Capture one frame from every camera; True if the active camera produced one."""
        active = self._manager.active_id
        active_ok = False
        for cam_id in self._manager.camera_ids():
            frame = self._manager.capture_camera(cam_id)
            if cam_id == active:
                active_ok = frame is not None
        return active_ok

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        self._threads = [
            threading.Thread(target=self._loop, args=(cam_id,), name=f"camera-reader-{cam_id}", daemon=True)
            for cam_id in self._manager.camera_ids()
        ]
        for thread in self._threads:
            thread.start()
        log.info("CameraReader started (%d cameras, up to %.0f fps each)",
                 len(self._threads), 1.0 / self._interval)

    def stop(self) -> None:
        self._running.clear()
        for thread in self._threads:
            thread.join(timeout=2.0)
        self._threads = []
        log.info("CameraReader stopped")

    def _loop(self, cam_id: str) -> None:
        is_inference = cam_id == self._manager.inference_source_id()
        standby_every = self._inference_interval if is_inference else _STANDBY_CONVERT_INTERVAL
        last_convert = 0.0
        while self._running.is_set():
            t0 = time.monotonic()
            alive = False
            try:
                if cam_id == self._manager.active_id or t0 - last_convert >= standby_every:
                    last_convert = t0
                    alive = self._manager.capture_camera(cam_id) is not None
                else:
                    alive = self._manager.advance_camera(cam_id)
            except Exception as exc:  # noqa: BLE001
                log.warning("Camera %s capture error: %s", cam_id, exc)
            # A live read blocks until the camera delivers its next frame, which
            # paces the loop; the sleep only matters for mock/failed cameras.
            wait = (self._interval if alive else _IDLE_SLEEP) - (time.monotonic() - t0)
            if wait > 0:
                time.sleep(wait)
