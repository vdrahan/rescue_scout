"""Shared application services, attached to ``app.state`` and read by routers."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from ..config import Settings


@dataclass
class AppServices:
    settings: Settings
    cameras: object
    hardware: object
    sink: object
    detection: object


def get_services(request: Request) -> AppServices:
    return request.app.state.services
