from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg2.extras

from database import db


def get_many(
    class_name: str | None,
    limit: int,
    from_time: datetime | None,
    to_time: datetime | None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []

    if class_name and class_name != "All classes":
        conditions.append("dc.class_name = %s")
        params.append(class_name)
    if from_time:
        conditions.append("d.detection_time >= %s")
        params.append(from_time)
    if to_time:
        conditions.append("d.detection_time <= %s")
        params.append(to_time)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT d.detection_id, dc.class_name, d.people_count,
                       d.detection_time, d.confidence
                FROM detection d
                JOIN detection_class dc ON d.class_id = dc.class_id
                {where}
                ORDER BY d.detection_time DESC
                LIMIT %s;
                """,
                params,
            )
            return [dict(r) for r in cur.fetchall()]


def get_recent(limit: int) -> list[dict[str, Any]]:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT d.detection_id, dc.class_name, d.people_count,
                       d.detection_time, d.confidence
                FROM detection d
                JOIN detection_class dc ON d.class_id = dc.class_id
                ORDER BY d.detection_time DESC
                LIMIT %s;
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_stats() -> dict[str, Any]:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT dc.class_name, COUNT(*) AS count,
                       ROUND(AVG(d.confidence), 2) AS avg_confidence
                FROM detection d
                JOIN detection_class dc ON d.class_id = dc.class_id
                GROUP BY dc.class_name
                ORDER BY count DESC;
                """
            )
            by_class = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT COUNT(*) AS total FROM detection;")
            total = cur.fetchone()["total"]

            cur.execute(
                "SELECT COUNT(*) AS today FROM detection WHERE detection_time::date = CURRENT_DATE;"
            )
            today = cur.fetchone()["today"]

    return {"total": total, "today": today, "by_class": by_class}


def get_by_id(detection_id: int) -> dict[str, Any] | None:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT d.detection_id, dc.class_name, d.people_count,
                       d.detection_time, d.confidence
                FROM detection d
                JOIN detection_class dc ON d.class_id = dc.class_id
                WHERE d.detection_id = %s;
                """,
                (detection_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def create(class_id: int, people_count: int, confidence: float) -> dict[str, Any]:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO detection (class_id, people_count, confidence)
                VALUES (%s, %s, %s)
                RETURNING detection_id, detection_time;
                """,
                (class_id, people_count, confidence),
            )
            row = cur.fetchone()
        conn.commit()
    return {"detection_id": row[0], "detection_time": row[1].isoformat()}


def update(detection_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not fields:
        return get_by_id(detection_id)
    set_clause = ", ".join(f"{col} = %s" for col in fields)
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE detection SET {set_clause} WHERE detection_id = %s RETURNING detection_id;",
                [*fields.values(), detection_id],
            )
            row = cur.fetchone()
        conn.commit()
    return get_by_id(detection_id) if row else None


def delete(detection_id: int) -> bool:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM detection WHERE detection_id = %s RETURNING detection_id;",
                (detection_id,),
            )
            deleted = cur.fetchone() is not None
        conn.commit()
    return deleted


def bulk_delete(before: datetime) -> int:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM detection WHERE detection_time < %s;",
                (before,),
            )
            count = cur.rowcount
        conn.commit()
    return count
