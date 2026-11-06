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


class _CountingCamera(CameraSource):
    """Camera that returns a fresh tiny frame every read and counts the reads."""

    def __init__(self, cam_id):
        super().__init__(cam_id, cam_id, "rtsp")
        self.reads = 0

    def read(self):
        self.reads += 1
        time.sleep(0.005)
        return new_scene(16, 12, f"{self.id}-{self.reads}")


def test_every_camera_is_read_continuously_not_only_the_active_one():
    """A standby camera read at a lower rate than the stream produces builds a
    backlog inside the capture (~30 s of old video), so switching to it shows
    stale footage. Each camera must be drained at full rate by its own thread."""
    settings = _mock_settings(camera_read_fps=200.0)
    mgr = CameraManager(settings)
    active, standby = _CountingCamera("detection"), _CountingCamera("fpv")
    mgr._cameras = {"detection": active, "fpv": standby}
    mgr._active_id = "detection"
    mgr._caches = {"detection": None, "fpv": None}
    mgr._seq = {"detection": 0, "fpv": 0}

    reader = CameraReader(mgr, settings)
    reader.start()
    try:
        time.sleep(0.5)
    finally:
        reader.stop()

    assert standby.reads > 20
    assert standby.reads >= 0.6 * active.reads


def test_frames_older_than_max_age_are_never_served():
    settings = _mock_settings(camera_max_frame_age=0.05)
    mgr = CameraManager(settings)
    reader = CameraReader(mgr, settings)
    reader._tick()
    assert mgr.cached() is not None
    assert mgr.read_one_jpeg(mgr.active_id) is not None

    time.sleep(0.12)

    assert mgr.cached() is None
    assert mgr.read_active() is None
    assert mgr.read_one(mgr.active_id) is None
    assert mgr.read_inference() is None
    assert mgr.read_one_jpeg(mgr.active_id) is None


def test_annotated_frame_is_not_served_once_it_is_stale():
    import io

    from PIL import Image

    settings = _mock_settings(camera_max_frame_age=0.05)
    bundle = build_detector(settings)
    cams = _FakeCams(None)  # no live camera frame either
    svc = DetectionService(settings, cams, object(), object(), bundle)
    svc._running.set()
    svc._frame = new_scene(64, 48, "old detection")
    svc._frame_seq = 1
    svc._frame_time = time.monotonic()

    fresh = Image.open(io.BytesIO(svc.frame_jpeg()))
    assert fresh.size == (64, 48)  # a fresh annotated frame is served as is

    time.sleep(0.12)
    stale = Image.open(io.BytesIO(svc.frame_jpeg()))
    assert stale.size == (settings.frame_width, settings.frame_height)  # "no signal" placeholder


class _SplitCamera(CameraSource):
    """Counts full reads (convert) separately from advances (decode only)."""

    def __init__(self, cam_id):
        super().__init__(cam_id, cam_id, "rtsp")
        self.reads = 0
        self.advances = 0

    def read(self):
        self.reads += 1
        time.sleep(0.004)
        return new_scene(16, 12, self.id)

    def advance(self):
        self.advances += 1
        time.sleep(0.004)
        return True


def test_standby_camera_stays_live_but_is_converted_rarely():
    """Converting every frame of the camera nobody is watching cost ~30% of a core
    and slowed detection from ~4 to ~2.5 fps. A standby camera must still consume
    every frame (so nothing queues) but only convert a few frames per second."""
    settings = _mock_settings(camera_read_fps=200.0)
    mgr = CameraManager(settings)
    active, standby = _SplitCamera("detection"), _SplitCamera("fpv")
    mgr._cameras = {"detection": active, "fpv": standby}
    mgr._active_id = "detection"
    mgr._caches = {"detection": None, "fpv": None}
    mgr._seq = {"detection": 0, "fpv": 0}

    reader = CameraReader(mgr, settings)
    reader.start()
    try:
        time.sleep(1.0)
    finally:
        reader.stop()

    assert active.reads > 40 and active.advances == 0      # the watched camera: every frame
    assert standby.advances > 40                            # the other one is still drained
    assert standby.reads <= 8                               # ...but converted only a few times a second
    assert standby.reads >= 2
    assert mgr.read_one("fpv") is not None                  # and its cache is fresh for a switch


def test_default_advance_is_a_plain_read():
    cam = _CountingCamera("detection")
    assert cam.advance() is True
    assert cam.reads == 1
