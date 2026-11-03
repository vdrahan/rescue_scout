from station.cameras.rtsp_camera import redact_url


def test_redacts_password():
    assert redact_url("rtsp://bob:secret@10.0.0.5:554/stream1") == "rtsp://bob:***@10.0.0.5:554/stream1"


def test_leaves_url_without_credentials():
    assert redact_url("rtsp://10.0.0.5/stream1") == "rtsp://10.0.0.5/stream1"


def test_non_url_source_unchanged():
    assert redact_url("/models/demo.mp4") == "/models/demo.mp4"
