"""Detection control + latest state endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from .deps import AppServices, get_services
from .schemas import DetectionConfigIn, DetectionConfigOut

router = APIRouter(prefix="/api/detection", tags=["detection"])


@router.post("/start")
def start(services: AppServices = Depends(get_services)) -> dict[str, Any]:
    started = services.detection.start()
    return {"started": started, "active": services.detection.active,
            "mode": services.detection.mode}


@router.post("/stop")
def stop(services: AppServices = Depends(get_services)) -> dict[str, Any]:
    stopped = services.detection.stop()
    return {"stopped": stopped, "active": services.detection.active}


@router.get("/latest")
def latest(services: AppServices = Depends(get_services)) -> dict[str, Any]:
    return services.detection.latest()


@router.get("/config", response_model=DetectionConfigOut)
def get_config(services: AppServices = Depends(get_services)) -> DetectionConfigOut:
    return DetectionConfigOut(**services.detection.get_config())


@router.post("/config", response_model=DetectionConfigOut)
def set_config(body: DetectionConfigIn,
               services: AppServices = Depends(get_services)) -> DetectionConfigOut:
    cfg = services.detection.set_config(conf=body.conf_threshold, target_fps=body.target_fps)
    return DetectionConfigOut(**cfg)
