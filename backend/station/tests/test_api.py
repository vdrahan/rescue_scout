"""API endpoint smoke tests (mock modes, sink disabled)."""

from __future__ import annotations

import time


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "station"


def test_status_snapshot(client):
    body = client.get("/api/status").json()
    assert body["detection"]["mode"] == "mock"
    assert body["hardware"]["mode"] == "mock"
    assert body["cameras"]["active"] in {c["id"] for c in body["cameras"]["list"]}


def test_detection_lifecycle(client):
    started = client.post("/api/detection/start").json()
    assert started["started"] is True
    assert started["active"] is True

    time.sleep(0.2)  # let the worker process a couple of frames
    latest = client.get("/api/detection/latest").json()
    assert latest["active"] is True
    assert "counts" in latest

    stopped = client.post("/api/detection/stop").json()
    assert stopped["stopped"] is True
    assert stopped["active"] is False


def test_detection_processes_frames_from_background_reader(client):
    """Detection must consume frames the background reader caches (not block on
    its own capture). If the reader→cache pipeline is wired, fps climbs above 0."""
    client.post("/api/detection/start")
    deadline = time.time() + 3.0
    fps = 0.0
    while time.time() < deadline:
        fps = client.get("/api/detection/latest").json()["fps"]
        if fps > 0:
            break
        time.sleep(0.05)
    client.post("/api/detection/stop")
    assert fps > 0


def test_detection_config_roundtrip(client):
    updated = client.post("/api/detection/config",
                          json={"conf_threshold": 0.7, "target_fps": 5}).json()
    assert updated["conf_threshold"] == 0.7
    assert updated["target_fps"] == 5
    again = client.get("/api/detection/config").json()
    assert again["conf_threshold"] == 0.7


def test_cameras_list_switch_and_frame(client):
    listing = client.get("/api/cameras").json()
    ids = [c["id"] for c in listing["cameras"]]
    assert "detection" in ids and "fpv" in ids

    switched = client.post("/api/cameras/active", json={"camera_id": "fpv"}).json()
    assert switched["active"] == "fpv"

    assert client.post("/api/cameras/active", json={"camera_id": "nope"}).status_code == 404

    frame = client.get("/api/cameras/detection/frame")
    assert frame.status_code == 200
    assert frame.headers["content-type"] == "image/jpeg"
    assert frame.content[:2] == b"\xff\xd8"  # JPEG magic


def test_hardware_status_and_tests(client):
    status = client.get("/api/hardware/status").json()
    assert status["mode"] == "mock"
    # gas is a cache filled by the 2 s gas-poll thread; wait for the first poll.
    deadline = time.monotonic() + 5.0
    while status["gas"]["ppm"] is None and time.monotonic() < deadline:
        time.sleep(0.2)
        status = client.get("/api/hardware/status").json()
    assert status["gas"]["ppm"] is not None, "gas cache not filled within 5 s"

    assert client.post("/api/hardware/test/buzzer").json()["status"] == "passed"
    assert client.post("/api/hardware/test/rgb_module").json()["status"] == "passed"
    assert client.post("/api/hardware/test/rgb_status").json()["status"] == "passed"
    assert client.post("/api/hardware/test/detection_camera").json()["status"] == "passed"
    assert client.post("/api/hardware/test/touchscreen").json()["status"] == "passed"
    assert client.post("/api/hardware/test/camera_servo").json()["status"] == "skipped"
