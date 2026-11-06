"""RTSP / USB camera sources backed by OpenCV (imported lazily).

Low-latency RTSP grabbing: reads normally return every frame as it arrives; if the
capture falls behind (a stall) it skips the queued old video and jumps to the live frame.
"""

from __future__ import annotations

import os
import time
from urllib.parse import urlsplit, urlunsplit

import numpy as np

from ..logging_conf import get_logger
from .base import CameraSource

log = get_logger(__name__)

# stimeout: TCP socket connection timeout (µs).
# rw_timeout: FFmpeg I/O read/write timeout (µs) — limits the OpenCV interrupt
#   callback window from the default 30 s to 5 s so dropped streams are detected
#   and reconnected much faster.
# flags;low_delay was removed — it causes avformat_find_stream_info to fail on
# some TP-Link firmware versions.
RTSP_FFMPEG_OPTIONS = (
    "rtsp_transport;tcp|stimeout;5000000|rw_timeout;5000000|max_delay;0|fflags;nobuffer"
)
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", RTSP_FFMPEG_OPTIONS)


def redact_url(url: str) -> str:
    """Hide the password in a camera URL before it reaches logs."""
    parts = urlsplit(url)
    if parts.password is None:
        return url
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    return urlunsplit(parts._replace(netloc=f"{parts.username}:***@{host}"))


_RECONNECT_DELAY = 1.0  # seconds between reconnect attempts after failure

# A grab that returns at once found its frame already queued; one that takes longer
# waited on the network for it. Two frames arriving back to back is ordinary Wi-Fi
# jitter, so a single fast grab must NOT drop anything (that cost a third of the frames:
# 15 -> 10 fps). A run of consecutive fast grabs means a real backlog of OLD video
# (after a stall): then read() skips ahead to the live frame.
# (cv2.CAP_PROP_BUFFERSIZE does nothing for the FFmpeg backend, so we do it ourselves.)
_CAUGHT_UP_S = 0.015  # a grab slower than this waited on the network for a new frame
_BACKLOG_AFTER = 4    # consecutive fast grabs that mean "frames are queued"
_MAX_DRAIN = 150      # per skip-ahead; a larger backlog is worked off over a few calls


class _CvCamera(CameraSource):
    def __init__(self, cam_id: str, name: str, kind: str, source):
        super().__init__(cam_id, name, kind)
        self._source = source
        self._cap = None
        self._next_open: float = 0.0  # monotonic timestamp; 0 = open immediately
        self._fast_grabs = 0          # consecutive grabs that did not wait on the network
        self._open()

    def _scrub(self, exc: Exception) -> str:
        # OpenCV/ffmpeg errors may embed the source URL; mask its password.
        src = str(self._source)
        return str(exc).replace(src, redact_url(src))

    def _open(self) -> None:
        self.close()
        try:
            import cv2  # noqa: WPS433 - real mode only

            cap = cv2.VideoCapture(self._source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not cap.isOpened():
                self.status = "error"
                self.last_error = "Camera could not be opened"
                self._next_open = time.monotonic() + _RECONNECT_DELAY
                log.warning("Camera %s could not open source %s", self.id, redact_url(str(self._source)))
                return
            self._cap = cap
            self._fast_grabs = 0
            self._next_open = 0.0
            self.status = "ok"
            self.last_error = ""
        except Exception as exc:  # noqa: BLE001
            self.status = "error"
            self.last_error = self._scrub(exc)
            self._next_open = time.monotonic() + _RECONNECT_DELAY
            log.warning("Camera %s init failed: %s", self.id, self.last_error)

    def read(self) -> np.ndarray | None:
        return self._read(convert=True)[1]

    def advance(self) -> bool:
        """Decode the next frame to keep the stream live, but skip the BGR->RGB
        conversion - the costly part, and wasted on a frame nobody will look at."""
        return self._read(convert=False)[0]

    def _read(self, convert: bool) -> tuple[bool, np.ndarray | None]:
        if self._cap is None:
            if time.monotonic() < self._next_open:
                return False, None  # backoff: avoid hammering the camera
            self._open()
            if self._cap is None:
                return False, None
        try:
            started = time.monotonic()
            grabbed = self._cap.grab()
            waited = time.monotonic() - started >= _CAUGHT_UP_S
            self._fast_grabs = 0 if waited else self._fast_grabs + 1
            if self._fast_grabs >= _BACKLOG_AFTER:
                # Behind: skip the queued old video, up to the frame the camera just sent.
                for _ in range(_MAX_DRAIN):
                    started = time.monotonic()
                    if not self._cap.grab() or time.monotonic() - started >= _CAUGHT_UP_S:
                        break
                self._fast_grabs = 0
            frame = None
            if grabbed and convert:
                grabbed, frame = self._cap.retrieve()
            if not grabbed:
                self.status = "error"
                self.last_error = "Camera stream stopped or frame could not be read"
                self._next_open = time.monotonic() + _RECONNECT_DELAY
                self.close()
                return False, None
            self.status = "ok"
            self.last_error = ""
            return True, (frame[..., ::-1].copy() if convert else None)  # BGR -> RGB
        except Exception as exc:  # noqa: BLE001
            self.status = "error"
            self.last_error = self._scrub(exc)
            self._next_open = time.monotonic() + _RECONNECT_DELAY
            self.close()
            log.warning("Camera %s read failed: %s", self.id, self.last_error)
            return False, None

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class RtspCamera(_CvCamera):
    def __init__(self, cam_id: str, name: str, url: str):
        super().__init__(cam_id, name, kind="rtsp", source=url)


class UsbCamera(_CvCamera):
    def __init__(self, cam_id: str, name: str, index: int):
        super().__init__(cam_id, name, kind="usb", source=index)
