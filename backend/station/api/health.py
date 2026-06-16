"""Liveness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from .. import __version__
from .schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", service="station", version=__version__)
