"""Builds camera sources from config and tracks the active one + a frame cache."""

from __future__ import annotations

import threading

import numpy as np

from ..config import Settings
from ..imaging import to_jpeg
from ..logging_conf import get_logger
from .base import CameraSource
from .mock_camera import MockCamera

log = get_logger(__name__)


class CameraManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._lock = threading.Lock()
        self._caches: dict[str, np.ndarray | None] = {}
        self._seq: dict[str, int] = {}            # bumped on every fresh frame
        self._jpeg_cache: dict[str, tuple] = {}   # cam_id -> (key, jpeg bytes)
        self.degraded = False
        self._cameras = self._build()
        self._active_id = next(iter(self._cameras))
        for cam_id in self._cameras:
            self._caches[cam_id] = None
            self._seq[cam_id] = 0

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

        if not has_rtsp and not has_usb:
            return MockCamera(cam_id, name, w, h)
        if force_mock and not has_rtsp:
            return MockCamera(cam_id, name, w, h)
        try:
            from .rtsp_camera import RtspCamera, UsbCamera  # lazy cv2

            cam = RtspCamera(cam_id, name, rtsp_url) if has_rtsp \
                else UsbCamera(cam_id, name, usb_index)
            if cam.status == "error":
                self.degraded = True
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

    def secondary_ids(self) -> list[str]:
        """IDs of all cameras that are not currently active."""
        active = self._active_id
        return [k for k in self._cameras if k != active]

    def inference_source_id(self) -> str:
        """Camera that always supplies frames for AI inference, regardless of active camera."""
        return "detection"

    def read_inference(self) -> np.ndarray | None:
        """Return the latest cached frame from the detection camera (non-blocking)."""
        with self._lock:
            return self._caches.get("detection")

    def set_active(self, cam_id: str) -> bool:
        if cam_id not in self._cameras:
            return False
        with self._lock:
            self._active_id = cam_id
            # Keep existing cache — don't blank the screen during the handover
        return True

    def capture_active(self) -> np.ndarray | None:
        """Read a fresh frame from the active camera and update its cache.

        The background CameraReader is the only caller.
        """
        return self._capture(self._active_id)

    def capture_camera(self, cam_id: str) -> np.ndarray | None:
        """Read a fresh frame from any camera and update its cache.

        Used by CameraReader to keep non-active cameras alive.
        """
        return self._capture(cam_id)

    def _capture(self, cam_id: str) -> np.ndarray | None:
        cam = self._cameras.get(cam_id)
        if cam is None:
            return None
        frame = cam.read()
        with self._lock:
            if frame is not None:
                self._caches[cam_id] = frame
                self._seq[cam_id] += 1
            # On error we intentionally keep the last good frame so the UI
            # shows a stale image while the camera reconnects rather than
            # flashing a placeholder "no signal" screen.
        return frame

    def read_active(self) -> np.ndarray | None:
        """Non-blocking: latest cached frame for the active camera."""
        return self.cached()

    def read_one(self, cam_id: str) -> np.ndarray | None:
        """Return the last cached frame for a camera — never blocks."""
        with self._lock:
            return self._caches.get(cam_id)

    def read_one_jpeg(self, cam_id: str, max_width: int | None = None,
                      quality: int = 80) -> bytes | None:
        """Encoded JPEG for the cached frame, memoised per frame so repeated polls
        (the FPV feed refreshes faster than the camera produces frames) never
        re-encode the same image — that redundant work was starving the reader."""
        with self._lock:
            frame = self._caches.get(cam_id)
            seq = self._seq.get(cam_id, 0)
            cached = self._jpeg_cache.get(cam_id)
        if frame is None:
            return None
        key = (seq, max_width, quality)
        if cached is not None and cached[0] == key:
            return cached[1]
        data = to_jpeg(frame, quality=quality, max_width=max_width)
        with self._lock:
            self._jpeg_cache[cam_id] = (key, data)
        return data

    def cached(self) -> np.ndarray | None:
        with self._lock:
            return self._caches.get(self._active_id)

    def close_all(self) -> None:
        for cam in self._cameras.values():
            cam.close()
