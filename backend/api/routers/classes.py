from __future__ import annotations

from typing import Any

import psycopg2.extras
from fastapi import APIRouter

from database import db

router = APIRouter(tags=["detection classes"])


# Exposed so the station can resolve class-name -> class_id when persisting.
@router.get("/detection-classes")
def list_detection_classes() -> list[dict[str, Any]]:
    with db() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT class_id, class_name, description FROM detection_class ORDER BY class_id;"
            )
            return [dict(r) for r in cur.fetchall()]
