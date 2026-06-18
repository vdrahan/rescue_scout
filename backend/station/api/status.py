"""Aggregated live status snapshot for the dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from .. import __version__
from .deps import AppServices, get_services

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status")
def status(services: AppServices = Depends(get_services)) -> dict[str, Any]:
    det = services.detection
    hw = services.hardware
    cams = services.cameras
    return {
        "service": "station",
        "version": __version__,
        "time": datetime.now().isoformat(timespec="seconds"),
        "uptime_seconds": det.uptime_seconds(),
        "detection": {
            "active": det.active,
            "mode": det.mode,
            "degraded": det.degraded,
            "fps": det.latest()["fps"],
            "threshold": det.get_config()["conf_threshold"],
            "note": det.note,
        },
        "cameras": {"active": cams.active_id, "list": cams.list()},
        "hardware": {
            "mode": hw.mode,
            "degraded": hw.degraded,
            "gas": hw.gas_status(),
            "climate": hw.read_climate(),
        },
        "sink": {
            "enabled": services.settings.sink_enabled,
            "connected": getattr(services.sink, "connected", False),
        },
    }
