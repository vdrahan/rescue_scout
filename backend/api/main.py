from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from .database import db
from .routers import classes, detections, events, sensors, statistics

app = FastAPI(title="Search and Rescue API", version="1.0.0")

app.include_router(detections.router)
app.include_router(sensors.router)
app.include_router(events.router)
app.include_router(statistics.router)
app.include_router(classes.router)


@app.get("/live", tags=["health"])
def live() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    db_health()
    return {"status": "ok", "service": "api"}


@app.get("/db-health", tags=["health"])
def db_health() -> dict[str, Any]:
    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                row = cur.fetchone()
        return {"status": "ok", "database": "connected", "check": row[0] if row else None}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
