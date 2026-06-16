"""Request/response models for the station API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DetectionConfigIn(BaseModel):
    conf_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    target_fps: float | None = Field(default=None, ge=0.5, le=30.0)


class DetectionConfigOut(BaseModel):
    conf_threshold: float
    iou_threshold: float
    target_fps: float


class SetActiveCameraIn(BaseModel):
    camera_id: str


class HealthOut(BaseModel):
    status: str
    service: str
    version: str
