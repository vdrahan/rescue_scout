"""Hardware status + per-component self-test endpoints (Debugging page)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from .deps import AppServices, get_services

router = APIRouter(prefix="/api/hardware", tags=["hardware"])

# Frontend Debugging component ids that map to cameras / UI rather than GPIO.
_CAMERA_COMPONENTS = {"detection_camera": "detection", "fpv_camera": "fpv"}
_UI_COMPONENTS = {"touchscreen"}


@router.get("/status")
def status(services: AppServices = Depends(get_services)) -> dict[str, Any]:
    hw = services.hardware
    data = hw.status()
    data["gas"] = hw.gas_status()   # cached — updated by gas-poll thread, no I2C here
    data["climate"] = hw.read_climate()
    return data


@router.post("/test/{component}")
def test_component(component: str,
                   services: AppServices = Depends(get_services)) -> dict[str, Any]:
    # Cameras: report based on the camera source status.
    if component in _CAMERA_COMPONENTS:
        cam_id = _CAMERA_COMPONENTS[component]
        info = next((c for c in services.cameras.list() if c["id"] == cam_id), None)
        ok = bool(info) and info["status"] == "ok"
        return {"component": component, "status": "passed" if ok else "failed",
                "detail": f"{info['type']} camera {info['status']}" if info else "camera missing"}

    # Touchscreen is a UI surface — nothing to probe from the backend.
    if component in _UI_COMPONENTS:
        return {"component": component, "status": "passed", "detail": "UI component (no backend probe)"}

    result = services.hardware.test(component)
    if result is None:
        # e.g. camera_servo not wired in this build
        return {"component": component, "status": "skipped", "detail": "not present in this build"}
    return result


@router.post("/lcd/cycle")
def lcd_cycle(services: AppServices = Depends(get_services)) -> dict[str, Any]:
    latest = services.detection.latest()
    counts: dict = latest.get("counts") or {}
    gas = services.hardware.gas_status()
    sink = services.sink
    screen = services.hardware.cycle_lcd_screen(
        last_detection=latest.get("last_detection"),
        total=sum(counts.values()),
        class_num=len(counts),
        hw_ok=not services.hardware.degraded,
        video_ok=not services.cameras.degraded,
        gas_ppm=gas.get("ppm"),
        gas_dangerous=bool(gas.get("dangerous")),
        gas_warnings=sink.count_dangerous("gas"),
        temp_warnings=sink.count_dangerous("temperature"),
    )
    return {"screen": screen}
