"""Background camera reader: single thread owns capture, others read the cache.

The reader is the only caller of ``CameraManager.capture_active()``.  Every
other consumer — the detection loop and the HTTP frame endpoint — reads the
cached latest frame via ``CameraManager.cached()`` / ``read_active()``,
so a slow or dropped RTSP source never blocks a request and two threads never
race on the same ``VideoCapture``.
"""

from __future__ import annotations

import threading
import time

from ..config import Settings
from ..logging_conf import get_logger
from .manager import CameraManager

log = get_logger(__name__)


class CameraReader:
    def __init__(self, manager: CameraManager, settings: Settings):
        self._manager = manager
        self._interval = 1.0 / max(1.0, settings.camera_read_fps)
        self._running = threading.Event()
        self._thread: threading.Thread | None = None

    def _tick(self) -> bool:
        """Capture one frame into the cache. Returns True if a frame was obtained."""
        frame = self._manager.capture_active()
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
