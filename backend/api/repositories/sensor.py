from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg2.extras

from database import db



def get_sensors() -> list[dict[str, Any]]:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT sensor_id, sensor_name, unit, min_value, max_value,
                       description, is_active, danger_level
                FROM sensor
                ORDER BY sensor_id;
                """
            )
            return [dict(r) for r in cur.fetchall()]


def get_readings(
    sensor_id: int | None,
    sensor_name: str | None,
    dangerous_only: bool,
    limit: int,
    from_time: datetime | None,
    to_time: datetime | None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []

    if sensor_id is not None:
        conditions.append("sr.sensor_id = %s")
        params.append(sensor_id)
    if sensor_name:
        conditions.append("s.sensor_name = %s")
        params.append(sensor_name)
    if dangerous_only:
        conditions.append("sr.is_dangerous = TRUE")
    if from_time:
        conditions.append("sr.reading_time >= %s")
        params.append(from_time)
    if to_time:
        conditions.append("sr.reading_time <= %s")
        params.append(to_time)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT sr.reading_id, s.sensor_name, s.unit, s.danger_level,
                       sr.reading_time, sr.value, sr.message, sr.is_dangerous
                FROM sensor_reading sr
                JOIN sensor s ON sr.sensor_id = s.sensor_id
                {where}
                ORDER BY sr.reading_time DESC
                LIMIT %s;
                """,
                params,
            )
            return [dict(r) for r in cur.fetchall()]


def get_recent_readings(limit: int) -> list[dict[str, Any]]:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT sr.reading_id, s.sensor_name, s.unit, s.danger_level,
                       sr.reading_time, sr.value, sr.message, sr.is_dangerous
                FROM sensor_reading sr
                JOIN sensor s ON sr.sensor_id = s.sensor_id
                ORDER BY sr.reading_time DESC
                LIMIT %s;
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_reading_by_id(reading_id: int) -> dict[str, Any] | None:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT sr.reading_id, s.sensor_name, s.unit, s.danger_level,
                       sr.reading_time, sr.value, sr.message, sr.is_dangerous
                FROM sensor_reading sr
                JOIN sensor s ON sr.sensor_id = s.sensor_id
                WHERE sr.reading_id = %s;
                """,
                (reading_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def create_reading(
    sensor_id: int, value: float, message: str | None, is_dangerous: bool
) -> dict[str, Any]:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sensor_reading (sensor_id, value, message, is_dangerous)
                VALUES (%s, %s, %s, %s)
                RETURNING reading_id, reading_time;
                """,
                (sensor_id, value, message, is_dangerous),
            )
            row = cur.fetchone()
        conn.commit()
    return {"reading_id": row[0], "reading_time": row[1].isoformat()}


def delete_reading(reading_id: int) -> bool:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM sensor_reading WHERE reading_id = %s RETURNING reading_id;",
                (reading_id,),
            )
            deleted = cur.fetchone() is not None
        conn.commit()
    return deleted


def bulk_delete_readings(before: datetime, sensor_id: int | None = None) -> int:
    params: list[Any] = [before]
    extra = ""
    if sensor_id is not None:
        extra = " AND sensor_id = %s"
        params.append(sensor_id)
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM sensor_reading WHERE reading_time < %s{extra};", params)
            count = cur.rowcount
        conn.commit()
    return count
