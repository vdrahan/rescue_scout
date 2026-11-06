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
"""

from __future__ import annotations

import threading
import time

from ..config import Settings
from ..logging_conf import get_logger
from .manager import CameraManager

log = get_logger(__name__)

_IDLE_SLEEP = 0.1  # a camera in reconnect backoff returns at once; poll it gently


class CameraReader:
    def __init__(self, manager: CameraManager, settings: Settings):
        self._manager = manager
        self._interval = 1.0 / max(1.0, settings.camera_read_fps)
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
        while self._running.is_set():
            t0 = time.monotonic()
            frame = None
            try:
                frame = self._manager.capture_camera(cam_id)
            except Exception as exc:  # noqa: BLE001
                log.warning("Camera %s capture error: %s", cam_id, exc)
            # A live read blocks until the camera delivers its next frame, which
            # paces the loop; the sleep only matters for mock/failed cameras.
            wait = (self._interval if frame is not None else _IDLE_SLEEP) - (time.monotonic() - t0)
            if wait > 0:
                time.sleep(wait)
