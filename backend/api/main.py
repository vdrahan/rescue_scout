from contextlib import contextmanager
import os
from typing import Any, Iterator

import psycopg2
from fastapi import FastAPI


app = FastAPI(title="Search and Rescue API", version="0.1.0")


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return database_url


@contextmanager
def db_connection() -> Iterator[Any]:
    connection = psycopg2.connect(get_database_url())
    try:
        yield connection
    finally:
        connection.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/db-health")
def db_health() -> dict[str, Any]:
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()

        return {
            "status": "ok",
            "database": "connected",
            "check": result[0] if result else None,
        }
    except Exception as error:
        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(error),
        }
