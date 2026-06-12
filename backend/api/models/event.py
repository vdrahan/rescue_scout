from __future__ import annotations

from pydantic import BaseModel


class SystemStatusIn(BaseModel):
    ai_status: str
    front_camera_status: str
    detection_camera_status: str
    processing_status: str


class EventIn(BaseModel):
    event_type: str
    importance_level: str
    message: str | None = None
    detection_id: int | None = None
    status_id: int | None = None
    reading_id: int | None = None


class EventUpdate(BaseModel):
    importance_level: str | None = None
    message: str | None = None
