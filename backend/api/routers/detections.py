from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from models.detection import DetectionIn, DetectionUpdate
from repositories import detection as repo

router = APIRouter(tags=["detections"])


# --- Detections ---

@router.get("/detections")
def list_detections(
    class_name: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
) -> list[dict[str, Any]]:
    return repo.get_many(class_name, limit, from_time, to_time)


@router.get("/detections/recent")
def recent(limit: int = Query(default=10, ge=1, le=100)) -> list[dict[str, Any]]:
    return repo.get_recent(limit)


@router.get("/detections/stats")
def stats() -> dict[str, Any]:
    return repo.get_stats()


@router.get("/detections/{detection_id}")
def get_detection(detection_id: int) -> dict[str, Any]:
    row = repo.get_by_id(detection_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return row


@router.post("/detections", status_code=201)
def create_detection(body: DetectionIn) -> dict[str, Any]:
    return repo.create(body.class_id, body.people_count, body.confidence)


@router.patch("/detections/{detection_id}")
def update_detection(detection_id: int, body: DetectionUpdate) -> dict[str, Any]:
    fields = body.model_dump(exclude_unset=True)
    row = repo.update(detection_id, fields)
    if row is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return row


@router.delete("/detections/{detection_id}", status_code=200)
def delete_detection(detection_id: int) -> dict[str, Any]:
    if not repo.delete(detection_id):
        raise HTTPException(status_code=404, detail="Detection not found")
    return {"deleted": detection_id}
