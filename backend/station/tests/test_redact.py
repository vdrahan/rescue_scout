from types import SimpleNamespace

from station.cameras.rtsp_camera import _CvCamera, redact_url


def test_redacts_password():
    assert redact_url("rtsp://bob:secret@10.0.0.5:554/stream1") == "rtsp://bob:***@10.0.0.5:554/stream1"


def test_leaves_url_without_credentials():
    assert redact_url("rtsp://10.0.0.5/stream1") == "rtsp://10.0.0.5/stream1"


def test_non_url_source_unchanged():
    assert redact_url("/models/demo.mp4") == "/models/demo.mp4"


def test_scrub_masks_url_in_exception():
    url = "rtsp://bob:secret@10.0.0.5:554/s"
    out = _CvCamera._scrub(SimpleNamespace(_source=url), RuntimeError(f"open failed: {url}"))
    assert "secret" not in out
    assert "bob:***@" in out


def test_scrub_leaves_usb_index_message_unchanged():
    out = _CvCamera._scrub(SimpleNamespace(_source=0), RuntimeError("device busy"))
    assert out == "device busy"
