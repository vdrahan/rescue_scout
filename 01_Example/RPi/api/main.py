"""Kickoff FastAPI — health checks and PostgreSQL connectivity."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI

# Load RPi/api/.env (local uvicorn). In Docker, compose env_file wins (no override).
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

app = FastAPI(title="CTAI Kickoff API", version="0.1.0")


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        msg = f"Missing {name} in RPi/api/.env — copy .env.example to .env and fill it in."
        raise RuntimeError(msg)
    return value


DATABASE_URL = _require_env("DATABASE_URL")


@contextmanager
def _db_connection() -> Iterator[Any]:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/db-health")
def db_health() -> dict[str, Any]:
    """Verify the API container can reach PostgreSQL."""
    try:
        with _db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                row = cur.fetchone()
        return {
            "status": "ok",
            "database": "connected",
            "check": row[0] if row else None,
        }
    except Exception as exc:
        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(exc),
        }
