from __future__ import annotations

import sys
import time
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


class _BacklogCapture:
    """Capture whose first N grabs return instantly (frames already queued in the
    socket buffer, i.e. OLD video) and later grabs block until a live frame arrives."""

    def __init__(self, queued):
        self.queue = [f"old-{i}" for i in range(queued)]
        self.grabs = 0
        self.live = 0
        self.current = None
        self.released = False

    def isOpened(self):
        return True

    def set(self, *_):
        return True

    def grab(self):
        self.grabs += 1
        if self.queue:
            self.current = self.queue.pop(0)
        else:
            time.sleep(0.03)  # waits for the camera -> we have caught up
            self.live += 1
            self.current = f"live-{self.live}"
        return True

    def retrieve(self):
        marker = int(self.current.split("-")[1]) + (200 if self.current.startswith("live") else 0)
        return True, np.full((1, 1, 3), marker, dtype=np.uint8)

    def release(self):
        self.released = True


def _camera_with(monkeypatch, capture):
    fake_cv2 = types.SimpleNamespace(
        CAP_FFMPEG=1900, CAP_PROP_BUFFERSIZE=38, VideoCapture=lambda source, backend: capture
    )
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    return RtspCamera("fpv", "FPV", "rtsp://example/stream")


def test_rtsp_read_skips_a_real_backlog_to_the_live_frame(monkeypatch):
    """After a stall the capture holds seconds of queued (old) video. read() must
    jump to the live frame instead of replaying the queue frame by frame."""
    capture = _BacklogCapture(queued=60)
    camera = _camera_with(monkeypatch, capture)

    frames = [camera.read() for _ in range(8)]

    assert all(f is not None for f in frames)
    assert int(frames[-1][0, 0, 0]) >= 200, "still replaying queued video after 8 reads"
    assert capture.queue == [], "the backlog was not drained"


class _BurstyCapture:
    """Network jitter: frames normally arrive one per grab (grab waits), but every
    second frame arrives back to back with the previous one (grab returns at once)."""

    def __init__(self):
        self.n = 0
        self.current = 0

    def isOpened(self):
        return True

    def set(self, *_):
        return True

    def grab(self):
        self.n += 1
        if self.n % 2 == 1:
            time.sleep(0.03)  # waits for the camera
        self.current = self.n
        return True

    def retrieve(self):
        return True, np.full((1, 1, 3), self.current, dtype=np.uint8)

    def release(self):
        pass


def test_rtsp_read_does_not_drop_frames_on_ordinary_jitter(monkeypatch):
    """Two frames arriving back to back is normal on Wi-Fi, not a backlog. Treating
    the second one as 'old video' threw away a third of the frames (15 -> 10 fps)."""
    camera = _camera_with(monkeypatch, _BurstyCapture())

    got = [int(camera.read()[0, 0, 0]) for _ in range(20)]

    assert got == list(range(1, 21))


def test_empty_env_values_fall_back_to_defaults(monkeypatch):
    """`.env.example` leaves TARGET_FPS / IMG_SIZE empty so compose can supply Pi
    defaults; running the station directly must not crash on those blanks."""
    monkeypatch.setenv("TARGET_FPS", "")
    monkeypatch.setenv("IMG_SIZE", "")
    settings = Settings(_env_file=None)
    assert settings.target_fps > 0
    assert settings.img_size > 0


def test_tests_never_read_a_local_env_file(tmp_path, monkeypatch):
    """A developer's real `.env` (with camera URLs) must not leak into the tests."""
    (tmp_path / ".env").write_text("RTSP_CAMERA_1_URL=rtsp://user:secret@192.0.2.1/stream\n")
    monkeypatch.chdir(tmp_path)
    assert Settings().rtsp_camera_1_url == ""
