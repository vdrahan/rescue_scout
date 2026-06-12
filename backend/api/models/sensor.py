from __future__ import annotations

from pydantic import BaseModel


class SensorReadingIn(BaseModel):
    sensor_id: int
    value: float
    message: str | None = None
    is_dangerous: bool = False
