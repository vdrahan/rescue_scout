from __future__ import annotations

from pydantic import BaseModel, Field


class DetectionIn(BaseModel):
    class_id: int
    people_count: int = Field(default=1, ge=0)
    confidence: float = Field(ge=0, le=100)


class DetectionUpdate(BaseModel):
    people_count: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=100)
