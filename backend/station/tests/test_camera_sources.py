from __future__ import annotations

import sys
import types

import numpy as np

from station.cameras.manager import CameraManager
from station.cameras.rtsp_camera import RtspCamera
from station.config import Settings


class _FakeCapture:
    def __init__(self, source):
        self.source = source
        self.grabs = 0
        self.released = False

    def isOpened(self):
        return True

    def set(self, *_):
        return True

    def grab(self):
        self.grabs += 1
        return True

    def retrieve(self):
        calls = _FakeCv2.retrieve_calls
        _FakeCv2.retrieve_calls += 1
        if calls == 0:
            return False, None
        # BGR pixel that should become RGB [30, 20, 10].
        return True, np.array([[[10, 20, 30]]], dtype=np.uint8)

    def release(self):
        self.released = True


class _FakeCv2(types.SimpleNamespace):
    CAP_FFMPEG = 1900
    CAP_PROP_BUFFERSIZE = 38
    retrieve_calls = 0
    captures: list[_FakeCapture] = []

    @staticmethod
    def VideoCapture(source, backend):
        cap = _FakeCapture(source)
        _FakeCv2.captures.append(cap)
        return cap


class _ClosedCv2(types.SimpleNamespace):
    CAP_FFMPEG = 1900
    CAP_PROP_BUFFERSIZE = 38

    class VideoCapture:  # noqa: D106 - tiny cv2 test double
        def __init__(self, *_):
            pass

        def isOpened(self):
            return False

        def set(self, *_):
            return True


def test_rtsp_camera_reopens_after_read_failure(monkeypatch):
    _FakeCv2.retrieve_calls = 0
    _FakeCv2.captures = []
    monkeypatch.setitem(sys.modules, "cv2", _FakeCv2)
    # Production waits _RECONNECT_DELAY after a failed read before reopening; skip it here.
    monkeypatch.setattr("station.cameras.rtsp_camera._RECONNECT_DELAY", 0.0)

    camera = RtspCamera("detection", "Detection Camera", "rtsp://example/stream")

    first = camera.read()
    second = camera.read()

    assert first is None
    assert second.tolist() == [[[30, 20, 10]]]
    assert camera.status == "ok"
    assert len(_FakeCv2.captures) == 2
    assert _FakeCv2.captures[0].released is True


def test_configured_rtsp_camera_stays_real_when_initial_open_fails(monkeypatch):
    monkeypatch.setitem(sys.modules, "cv2", _ClosedCv2)
    settings = Settings(
        detection_mode="real",
        hardware_mode="mock",
        rtsp_camera_1_url="rtsp://example/stream",
        rtsp_camera_2_url="",
    )

    cameras = CameraManager(settings).list()
    detection = next(c for c in cameras if c["id"] == "detection")

    assert detection["type"] == "rtsp"
    assert detection["status"] == "error"


def test_rtsp_url_overrides_mock_detection_mode(monkeypatch):
    """A configured RTSP URL must stream real video even in mock detection mode.

    Camera source must not be coupled to the detector: DETECTION_MODE=mock with
    RTSP_CAMERA_1_URL set should run a real RTSP camera (with the mock detector).
    """
    _FakeCv2.retrieve_calls = 0
    _FakeCv2.captures = []
    monkeypatch.setitem(sys.modules, "cv2", _FakeCv2)
    settings = Settings(
        detection_mode="mock",
        hardware_mode="mock",
        rtsp_camera_1_url="rtsp://example/stream",
        rtsp_camera_2_url="",
    )

    cameras = CameraManager(settings).list()
    detection = next(c for c in cameras if c["id"] == "detection")

    assert detection["type"] == "rtsp"


def test_mock_mode_without_rtsp_stays_mock_and_skips_usb(monkeypatch):
    """No RTSP configured + mock mode → mock cameras, never a USB capture attempt."""
    def _boom(*_args, **_kw):
        raise AssertionError("USB/RTSP capture must not be opened in mock mode")

    fake_cv2 = types.SimpleNamespace(
        CAP_FFMPEG=1900, CAP_PROP_BUFFERSIZE=38, VideoCapture=_boom
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    settings = Settings(detection_mode="mock", hardware_mode="mock",
                        rtsp_camera_1_url="", rtsp_camera_2_url="")

    cameras = CameraManager(settings).list()

    assert all(c["type"] == "mock" for c in cameras)
