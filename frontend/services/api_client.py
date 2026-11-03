"""Thin HTTP client for the station + data-api backends.

Calls are best-effort and return ``None`` when a service is unavailable. UI code
must turn that into an honest unavailable state, never demo data.
"""

from __future__ import annotations

import io
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import httpx

from .config import API_URL, BACKEND_COOLDOWN_SECONDS, HARDWARE_TEST_TIMEOUT, REQUEST_TIMEOUT, STATION_URL

log = logging.getLogger(__name__)

_station = httpx.Client(base_url=STATION_URL, timeout=REQUEST_TIMEOUT)
_api = httpx.Client(base_url=API_URL, timeout=REQUEST_TIMEOUT)

# circuit breaker state: backend label -> timestamp until which we skip it
_down_until: dict[str, float] = {"station": 0.0, "api": 0.0}


@dataclass(frozen=True)
class ServiceResult:
    data: Any
    available: bool
    has_data: bool
    message: str


def service_result(data: Any, unavailable_message: str,
                   empty_message: str = "No data yet") -> ServiceResult:
    """Classify a backend response for UI rendering."""
    if data is None:
        return ServiceResult(data=None, available=False, has_data=False,
                             message=unavailable_message)
    if data == [] or data == {}:
        return ServiceResult(data=data, available=True, has_data=False,
                             message=empty_message)
    return ServiceResult(data=data, available=True, has_data=True, message="")


def _available(label: str) -> bool:
    return time.monotonic() >= _down_until[label]


def _trip(label: str) -> None:
    _down_until[label] = time.monotonic() + BACKEND_COOLDOWN_SECONDS


def _ok(label: str) -> None:
    _down_until[label] = 0.0


def _request(
    label: str,
    client: httpx.Client,
    method: str,
    path: str,
    *,
    trip_on_error: bool = True,
    **kw,
) -> Any | None:
    if not _available(label):
        return None
    try:
        resp = client.request(method, path, **kw)
        resp.raise_for_status()
        _ok(label)
        return resp
    except Exception as exc:  # noqa: BLE001
        if trip_on_error:
            _trip(label)
        log.debug("%s %s %s failed: %s", label, method, path, exc)
        return None


def _json(label: str, client: httpx.Client, method: str, path: str, **kw) -> Any | None:
    resp = _request(label, client, method, path, **kw)
    return resp.json() if resp is not None else None


def backend_online() -> bool:
    return _available("station") or _available("api")


def api_health() -> dict | None:
    return _json("api", _api, "GET", "/health")


def station_health() -> dict | None:
    return _json("station", _station, "GET", "/health")


# ---------------------------------------------------------------------------
# Station (live detection / cameras / hardware)
# ---------------------------------------------------------------------------
def station_status() -> dict | None:
    return _json("station", _station, "GET", "/api/status")


def detection_latest() -> dict | None:
    return _json("station", _station, "GET", "/api/detection/latest")


def start_detection() -> dict | None:
    return _json("station", _station, "POST", "/api/detection/start")


def stop_detection() -> dict | None:
    return _json("station", _station, "POST", "/api/detection/stop")


def set_detection_active(active: bool) -> dict | None:
    return start_detection() if active else stop_detection()


def get_detection_config() -> dict | None:
    return _json("station", _station, "GET", "/api/detection/config")


def set_detection_config(conf: float | None = None, target_fps: float | None = None) -> dict | None:
    body = {k: v for k, v in {"conf_threshold": conf, "target_fps": target_fps}.items() if v is not None}
    return _json("station", _station, "POST", "/api/detection/config", json=body)


def list_cameras() -> dict | None:
    return _json("station", _station, "GET", "/api/cameras")


def set_active_camera(camera_id: str) -> dict | None:
    return _json("station", _station, "POST", "/api/cameras/active", json={"camera_id": camera_id})


def camera_frame(camera_id: str):
    """Return the latest JPEG as a PIL Image, or None on failure."""
    resp = _request(
        "station",
        _station,
        "GET",
        f"/api/cameras/{camera_id}/frame",
        params={"_": int(time.time() * 1000)},
        trip_on_error=False,
    )
    if resp is None:
        return None
    try:
        from PIL import Image

        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception:  # noqa: BLE001
        return None


def hardware_status() -> dict | None:
    return _json("station", _station, "GET", "/api/hardware/status")


def test_component(component: str) -> dict | None:
    return _json(
        "station",
        _station,
        "POST",
        f"/api/hardware/test/{component}",
        timeout=HARDWARE_TEST_TIMEOUT,
    )


def cycle_lcd_screen() -> dict | None:
    return _json("station", _station, "POST", "/api/hardware/lcd/cycle")


def reboot_pi() -> dict | None:
    return _json("station", _station, "POST", "/api/system/reboot")


# ---------------------------------------------------------------------------
# Data API (history / statistics)
# ---------------------------------------------------------------------------
def detections(class_name: str | None = None, limit: int = 50) -> list[dict] | None:
    params: dict[str, Any] = {"limit": limit}
    if class_name and class_name != "All classes":
        params["class_name"] = class_name
    return _json("api", _api, "GET", "/detections", params=params)


def detection_stats() -> dict | None:
    return _json("api", _api, "GET", "/detections/stats")


def detection_classes() -> list[dict] | None:
    return _json("api", _api, "GET", "/detection-classes")


def sensor_readings(sensor_name: str | None = None, dangerous_only: bool = False,
                    limit: int = 50) -> list[dict] | None:
    params: dict[str, Any] = {"limit": limit, "dangerous_only": dangerous_only}
    if sensor_name:
        params["sensor_name"] = sensor_name
    return _json("api", _api, "GET", "/sensor-readings", params=params)


def sensor_readings_count(sensor_name: str | None = None, dangerous_only: bool = False) -> int | None:
    params: dict[str, Any] = {"dangerous_only": dangerous_only}
    if sensor_name:
        params["sensor_name"] = sensor_name
    result = _json("api", _api, "GET", "/sensor-readings/count", params=params)
    if result is None:
        return None
    return result.get("count")


def events(limit: int = 50) -> list[dict] | None:
    return _json("api", _api, "GET", "/events", params={"limit": limit})


def stat_detections_over_time(bucket: str = "minute", hours: int = 2) -> list[dict] | None:
    from_time = (datetime.now() - timedelta(hours=hours)).isoformat()
    return _json("api", _api, "GET", "/statistics/detections-over-time",
                 params={"bucket": bucket, "from_time": from_time})


def stat_class_distribution() -> list[dict] | None:
    return _json("api", _api, "GET", "/statistics/class-distribution")


def stat_sensor_over_time(sensor_name: str = "gas", bucket: str = "minute", hours: int = 2) -> list[dict] | None:
    from_time = (datetime.now() - timedelta(hours=hours)).isoformat()
    return _json("api", _api, "GET", "/statistics/sensor-over-time",
                 params={"sensor_name": sensor_name, "bucket": bucket, "from_time": from_time})
