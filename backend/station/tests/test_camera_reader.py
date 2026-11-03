"""Background camera reader + non-blocking frame cache.

The reader thread is the single owner of camera capture (cv2). The HTTP frame
endpoint and the detection loop only ever read the cached latest frame, so a
slow/dropped RTSP source never blocks a request and two threads never touch the
same VideoCapture at once.
"""

from __future__ import annotations

import time

from station.cameras import rtsp_camera
from station.cameras.base import CameraSource
from station.cameras.manager import CameraManager
from station.cameras.reader import CameraReader
from station.config import Settings
from station.detection.registry import build_detector
from station.detection.service import DetectionService
from station.imaging import new_scene


def _mock_settings(**kw) -> Settings:
    base = dict(detection_mode="mock", hardware_mode="mock")
    base.update(kw)
    return Settings(**base)


def test_reader_tick_warms_cache_from_active_camera():
    mgr = CameraManager(_mock_settings())
    assert mgr.cached() is None

    reader = CameraReader(mgr, _mock_settings())
    assert reader._tick() is True
    assert mgr.cached() is not None


def test_read_active_returns_cache_without_capturing():
    """read_active() must be non-blocking: it returns the cached frame the reader
    produced, never a fresh (blocking) capture."""
    mgr = CameraManager(_mock_settings())
    reader = CameraReader(mgr, _mock_settings())
    reader._tick()

    cached = mgr.cached()
    assert cached is not None
    assert mgr.read_active() is cached  # same object → returned cache, not a new read


class _NoneCamera(CameraSource):
    def __init__(self):
        super().__init__("detection", "Detection Camera", "rtsp")
        self.status = "error"
        self.last_error = "stream stopped"

    def read(self):
        return None


def test_reader_survives_failed_read_and_keeps_last_frame():
    mgr = CameraManager(_mock_settings())
    reader = CameraReader(mgr, _mock_settings())
    reader._tick()
    last = mgr.cached()
    assert last is not None

    mgr._cameras[mgr.active_id] = _NoneCamera()
    assert reader._tick() is False
    # Keep the last good frame so the UI can show "Camera Reconnecting - Showing last frame".
    assert mgr.cached() is last


class _FakeCams:
    """Camera-manager stand-in that distinguishes cache reads from captures."""

    def __init__(self, frame):
        self._frame = frame
        self.cached_calls = 0
        self.read_active_calls = 0
        self.capture_calls = 0

    def cached(self):
        self.cached_calls += 1
        return self._frame

    def read_active(self):
        self.read_active_calls += 1
        return self._frame

    def capture_active(self):
        self.capture_calls += 1
        return self._frame


def test_frame_jpeg_serves_cache_not_a_fresh_capture_when_idle():
    settings = _mock_settings()
    bundle = build_detector(settings)
    cams = _FakeCams(new_scene(64, 48, "idle"))
    svc = DetectionService(settings, cams, object(), object(), bundle)

    data = svc.frame_jpeg()

    assert data[:2] == b"\xff\xd8"  # JPEG magic
    assert cams.cached_calls == 1
    assert cams.read_active_calls == 0  # idle endpoint must not trigger a capture
    assert cams.capture_calls == 0


def test_rtsp_ffmpeg_options_set_a_connection_timeout():
    assert "timeout" in rtsp_camera.RTSP_FFMPEG_OPTIONS


def test_reader_start_stop_runs_background_thread():
    mgr = CameraManager(_mock_settings(camera_read_fps=50.0))
    reader = CameraReader(mgr, _mock_settings(camera_read_fps=50.0))
    reader.start()
    try:
        time.sleep(0.1)
        assert mgr.cached() is not None
    finally:
        reader.stop()
