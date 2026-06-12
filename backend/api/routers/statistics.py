from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query

from database import db

router = APIRouter(prefix="/statistics", tags=["statistics"])

_BUCKETS = {"minute", "hour", "day", "week"}


def _validate_bucket(bucket: str) -> None:
    if bucket not in _BUCKETS:
        raise HTTPException(status_code=400, detail=f"bucket must be one of: {_BUCKETS}")


@router.get("/detections-over-time")
def detections_over_time(
    bucket: str = Query(default="minute"),
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
) -> list[dict[str, Any]]:
    _validate_bucket(bucket)
    conditions: list[str] = []
    params: list[Any] = []
    if from_time:
        conditions.append("detection_time >= %s")
        params.append(from_time)
    if to_time:
        conditions.append("detection_time <= %s")
        params.append(to_time)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT date_trunc('{bucket}', detection_time) AS bucket,
                       COUNT(*) AS count,
                       ROUND(AVG(confidence), 2) AS avg_confidence
                FROM detection
                {where}
                GROUP BY bucket
                ORDER BY bucket;
                """,
                params,
            )
            return [dict(r) for r in cur.fetchall()]


@router.get("/class-distribution")
def class_distribution() -> list[dict[str, Any]]:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT dc.class_name, COUNT(*) AS count
                FROM detection d
                JOIN detection_class dc ON d.class_id = dc.class_id
                GROUP BY dc.class_name
                ORDER BY count DESC;
                """
            )
            return [dict(r) for r in cur.fetchall()]


@router.get("/confidence-over-time")
def confidence_over_time(
    bucket: str = Query(default="minute"),
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
) -> list[dict[str, Any]]:
    _validate_bucket(bucket)
    conditions: list[str] = []
    params: list[Any] = []
    if from_time:
        conditions.append("detection_time >= %s")
        params.append(from_time)
    if to_time:
        conditions.append("detection_time <= %s")
        params.append(to_time)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT date_trunc('{bucket}', detection_time) AS bucket,
                       ROUND(AVG(confidence), 2) AS avg_confidence,
                       ROUND(MIN(confidence), 2) AS min_confidence,
                       ROUND(MAX(confidence), 2) AS max_confidence
                FROM detection
                {where}
                GROUP BY bucket
                ORDER BY bucket;
                """,
                params,
            )
            return [dict(r) for r in cur.fetchall()]


@router.get("/sensor-over-time")
def sensor_over_time(
    sensor_name: str = Query(...),
    bucket: str = Query(default="minute"),
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
) -> list[dict[str, Any]]:
    _validate_bucket(bucket)
    conditions = ["s.sensor_name = %s"]
    params: list[Any] = [sensor_name]
    if from_time:
        conditions.append("sr.reading_time >= %s")
        params.append(from_time)
    if to_time:
        conditions.append("sr.reading_time <= %s")
        params.append(to_time)

    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT date_trunc('{bucket}', sr.reading_time) AS bucket,
                       ROUND(AVG(sr.value), 2) AS avg_value,
                       ROUND(MIN(sr.value), 2) AS min_value,
                       ROUND(MAX(sr.value), 2) AS max_value,
                       BOOL_OR(sr.is_dangerous) AS any_dangerous
                FROM sensor_reading sr
                JOIN sensor s ON sr.sensor_id = s.sensor_id
                WHERE {" AND ".join(conditions)}
                GROUP BY bucket
                ORDER BY bucket;
                """,
                params,
            )
            return [dict(r) for r in cur.fetchall()]
