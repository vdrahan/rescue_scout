"""Builds camera sources from config and tracks the active one + a frame cache."""

from __future__ import annotations

import threading

import numpy as np

from ..config import Settings
from ..logging_conf import get_logger
from .base import CameraSource
from .mock_camera import MockCamera

log = get_logger(__name__)


class CameraManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._lock = threading.Lock()
        self._cache: np.ndarray | None = None
        self.degraded = False
        self._cameras = self._build()
        self._active_id = next(iter(self._cameras))

    # -- construction -------------------------------------------------------
    def _build(self) -> dict[str, CameraSource]:
        s = self._settings
        cams: dict[str, CameraSource] = {}
        force_mock = s.detection_mode == "mock"

        cams["detection"] = self._make(
            force_mock, "detection", "Detection Camera", s.rtsp_camera_1_url, None
        )
        cams["fpv"] = self._make(
            force_mock, "fpv", "FPV / Nav Camera", s.rtsp_camera_2_url, s.usb_camera_index
        )
        return cams

    def _make(self, force_mock: bool, cam_id: str, name: str,
              rtsp_url: str, usb_index: int | None) -> CameraSource:
        w, h = self._settings.frame_width, self._settings.frame_height
        has_rtsp = bool(rtsp_url)
        has_usb = usb_index is not None

        # No real source configured at all → synthetic feed.
        if not has_rtsp and not has_usb:
            return MockCamera(cam_id, name, w, h)
        # Camera source is decoupled from the detector: a configured RTSP URL
        # streams real video even when DETECTION_MODE=mock. USB is reserved for
        # real/auto modes so a laptop in mock mode never grabs a local webcam.
        if force_mock and not has_rtsp:
            return MockCamera(cam_id, name, w, h)
        try:
            from .rtsp_camera import RtspCamera, UsbCamera  # lazy cv2

            cam = RtspCamera(cam_id, name, rtsp_url) if has_rtsp \
                else UsbCamera(cam_id, name, usb_index)
            if cam.status == "error":
                self.degraded = True
                # In real mode, or whenever a real RTSP URL is configured, keep
                # the real source visible as error instead of pretending with mock.
                if self._settings.detection_mode == "real" or has_rtsp:
                    return cam
                raise RuntimeError("camera failed to open")
            return cam
        except Exception as exc:  # noqa: BLE001
            log.warning("Camera %s falling back to mock: %s", cam_id, exc)
            self.degraded = True
            return MockCamera(cam_id, name, w, h)

    # -- queries ------------------------------------------------------------
    def list(self) -> list[dict]:
        return [
            {**cam.info(), "active": cam.id == self._active_id}
            for cam in self._cameras.values()
        ]

    def has(self, cam_id: str) -> bool:
        return cam_id in self._cameras

    @property
    def active_id(self) -> str:
        return self._active_id

    def set_active(self, cam_id: str) -> bool:
        if cam_id not in self._cameras:
            return False
        with self._lock:
            self._active_id = cam_id
            self._cache = None
        return True

    def capture_active(self) -> np.ndarray | None:
        """Read a fresh frame from the active camera and refresh the cache.

        The background :class:`CameraReader` is the only caller, so one thread
        owns the underlying ``VideoCapture`` and the HTTP layer never blocks on a
        camera read nor races a second reader on the same capture.
        """
        cam = self._cameras[self._active_id]
        frame = cam.read()
        with self._lock:
            if frame is not None:
                self._cache = frame
            elif cam.status == "error":
                self._cache = None  # source errored — drop the stale frame
        return frame

    def read_active(self) -> np.ndarray | None:
        """Non-blocking: the latest cached frame (populated by the reader)."""
        return self.cached()

    def read_one(self, cam_id: str) -> np.ndarray | None:
        """Read a single frame from a specific camera (used for previews)."""
        cam = self._cameras.get(cam_id)
        return cam.read() if cam is not None else None

    def cached(self) -> np.ndarray | None:
        with self._lock:
            return self._cache

    def close_all(self) -> None:
        for cam in self._cameras.values():
            cam.close()
