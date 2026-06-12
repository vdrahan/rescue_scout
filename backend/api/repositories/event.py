from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg2.extras

from database import db


def get_latest_status() -> dict[str, Any] | None:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM system_status ORDER BY saved_at DESC LIMIT 1;")
            row = cur.fetchone()
    return dict(row) if row else None


def get_status_list(limit: int) -> list[dict[str, Any]]:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM system_status ORDER BY saved_at DESC LIMIT %s;",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]


def create_status(
    ai_status: str,
    front_camera_status: str,
    detection_camera_status: str,
    processing_status: str,
) -> dict[str, Any]:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_status
                    (ai_status, front_camera_status, detection_camera_status, processing_status)
                VALUES (%s, %s, %s, %s)
                RETURNING status_id, saved_at;
                """,
                (ai_status, front_camera_status, detection_camera_status, processing_status),
            )
            row = cur.fetchone()
        conn.commit()
    return {"status_id": row[0], "saved_at": row[1].isoformat()}


def delete_status(status_id: int) -> bool:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM system_status WHERE status_id = %s RETURNING status_id;",
                (status_id,),
            )
            deleted = cur.fetchone() is not None
        conn.commit()
    return deleted


def bulk_delete_status(before: datetime) -> int:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM system_status WHERE saved_at < %s;", (before,))
            count = cur.rowcount
        conn.commit()
    return count


def get_events(
    importance_level: str | None,
    event_type: str | None,
    limit: int,
    from_time: datetime | None,
    to_time: datetime | None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []

    if importance_level:
        conditions.append("e.importance_level = %s")
        params.append(importance_level)
    if event_type:
        conditions.append("e.event_type = %s")
        params.append(event_type)
    if from_time:
        conditions.append("e.event_time >= %s")
        params.append(from_time)
    if to_time:
        conditions.append("e.event_time <= %s")
        params.append(to_time)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT e.event_id, e.event_type, e.event_time, e.importance_level,
                       e.message, e.detection_id, e.status_id, e.reading_id
                FROM event_log e
                {where}
                ORDER BY e.event_time DESC
                LIMIT %s;
                """,
                params,
            )
            return [dict(r) for r in cur.fetchall()]


def get_event_by_id(event_id: int) -> dict[str, Any] | None:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT event_id, event_type, event_time, importance_level,
                       message, detection_id, status_id, reading_id
                FROM event_log
                WHERE event_id = %s;
                """,
                (event_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def create_event(
    event_type: str,
    importance_level: str,
    message: str | None,
    detection_id: int | None,
    status_id: int | None,
    reading_id: int | None,
) -> dict[str, Any]:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO event_log
                    (event_type, importance_level, message, detection_id, status_id, reading_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING event_id, event_time;
                """,
                (event_type, importance_level, message, detection_id, status_id, reading_id),
            )
            row = cur.fetchone()
        conn.commit()
    return {"event_id": row[0], "event_time": row[1].isoformat()}


def update_event(event_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not fields:
        return get_event_by_id(event_id)
    set_clause = ", ".join(f"{col} = %s" for col in fields)
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE event_log SET {set_clause} WHERE event_id = %s RETURNING event_id;",
                [*fields.values(), event_id],
            )
            row = cur.fetchone()
        conn.commit()
    return get_event_by_id(event_id) if row else None


def delete_event(event_id: int) -> bool:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM event_log WHERE event_id = %s RETURNING event_id;",
                (event_id,),
            )
            deleted = cur.fetchone() is not None
        conn.commit()
    return deleted


def bulk_delete_events(before: datetime, importance_level: str | None = None) -> int:
    params: list[Any] = [before]
    extra = ""
    if importance_level:
        extra = " AND importance_level = %s"
        params.append(importance_level)
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM event_log WHERE event_time < %s{extra};", params)
            count = cur.rowcount
        conn.commit()
    return count
