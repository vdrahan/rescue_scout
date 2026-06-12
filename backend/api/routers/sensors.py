from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from models.sensor import SensorReadingIn
from repositories import sensor as repo

router = APIRouter(tags=["sensors"])


# --- Sensor Readings ---

@router.get("/sensor-readings")
def list_readings(
    sensor_id: int | None = Query(default=None),
    sensor_name: str | None = Query(default=None),
    dangerous_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
) -> list[dict[str, Any]]:
    return repo.get_readings(sensor_id, sensor_name, dangerous_only, limit, from_time, to_time)


@router.get("/sensor-readings/recent")
def recent_readings(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    return repo.get_recent_readings(limit)


@router.get("/sensor-readings/{reading_id}")
def get_reading(reading_id: int) -> dict[str, Any]:
    row = repo.get_reading_by_id(reading_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sensor reading not found")
    return row


@router.post("/sensor-readings", status_code=201)
def create_reading(body: SensorReadingIn) -> dict[str, Any]:
    return repo.create_reading(body.sensor_id, body.value, body.message, body.is_dangerous)


@router.delete("/sensor-readings/{reading_id}", status_code=200)
def delete_reading(reading_id: int) -> dict[str, Any]:
    if not repo.delete_reading(reading_id):
        raise HTTPException(status_code=404, detail="Sensor reading not found")
    return {"deleted": reading_id}
