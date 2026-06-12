from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
import psycopg2.extras


def _url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return url


@contextmanager
def db() -> Iterator[Any]:
    conn = psycopg2.connect(_url())
    try:
        yield conn
    finally:
        conn.close()
