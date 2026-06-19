"""Camera listing, active switching and JPEG frame endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from ..imaging import placeholder, to_jpeg
from .deps import AppServices, get_services
from .schemas import SetActiveCameraIn

router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("")
def list_cameras(services: AppServices = Depends(get_services)) -> dict[str, Any]:
    cams = services.cameras
    return {"active": cams.active_id, "cameras": cams.list()}


@router.post("/active")
def set_active(body: SetActiveCameraIn,
               services: AppServices = Depends(get_services)) -> dict[str, Any]:
    if not services.cameras.set_active(body.camera_id):
        raise HTTPException(status_code=404, detail=f"Unknown camera: {body.camera_id}")
    services.hardware.set_fpv_led(body.camera_id == "fpv")
    services.hardware.set_detection_feed_led(body.camera_id == "detection")
    return {"active": services.cameras.active_id, "cameras": services.cameras.list()}


@router.get("/{camera_id}/frame")
def frame(camera_id: str, services: AppServices = Depends(get_services)) -> Response:
    cams = services.cameras
    if not cams.has(camera_id):
        raise HTTPException(status_code=404, detail=f"Unknown camera: {camera_id}")

    if camera_id == cams.inference_source_id() and services.detection.active:
        # Detection camera with AI on → annotated frame from inference
        data = services.detection.frame_jpeg()
    else:
        # FPV or detection with AI off → cached frame, aggressively downscaled and
        # low-quality for a minimum-latency live feed (encoded once per frame).
        s = services.settings
        data = cams.read_one_jpeg(
            camera_id,
            max_width=s.camera_stream_max_width or None,
            quality=s.camera_stream_quality,
        )
        if data is None:
            data = to_jpeg(placeholder(s.frame_width, s.frame_height, "no signal"))
    return Response(content=data, media_type="image/jpeg")
