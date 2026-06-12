from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from models.event import EventIn, EventUpdate, SystemStatusIn
from repositories import event as repo

router = APIRouter(tags=["events & status"])


# --- System Status ---

@router.get("/system-status/latest")
def latest_status() -> dict[str, Any]:
    row = repo.get_latest_status()
    if row is None:
        raise HTTPException(status_code=404, detail="No system status recorded yet")
    return row


@router.get("/system-status")
def list_status(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    return repo.get_status_list(limit)


@router.post("/system-status", status_code=201)
def create_status(body: SystemStatusIn) -> dict[str, Any]:
    return repo.create_status(
        body.ai_status, body.front_camera_status,
        body.detection_camera_status, body.processing_status,
    )


@router.delete("/system-status/{status_id}", status_code=200)
def delete_status(status_id: int) -> dict[str, Any]:
    if not repo.delete_status(status_id):
        raise HTTPException(status_code=404, detail="System status not found")
    return {"deleted": status_id}


# --- Events ---

@router.get("/events")
def list_events(
    importance_level: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[dict[str, Any]]:
    return repo.get_events(importance_level, event_type, limit, None, None)


@router.get("/events/{event_id}")
def get_event(event_id: int) -> dict[str, Any]:
    row = repo.get_event_by_id(event_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return row


@router.post("/events", status_code=201)
def create_event(body: EventIn) -> dict[str, Any]:
    return repo.create_event(
        body.event_type, body.importance_level, body.message,
        body.detection_id, body.status_id, body.reading_id,
    )


@router.patch("/events/{event_id}")
def update_event(event_id: int, body: EventUpdate) -> dict[str, Any]:
    fields = body.model_dump(exclude_unset=True)
    row = repo.update_event(event_id, fields)
    if row is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return row


@router.delete("/events/{event_id}", status_code=200)
def delete_event(event_id: int) -> dict[str, Any]:
    if not repo.delete_event(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"deleted": event_id}
