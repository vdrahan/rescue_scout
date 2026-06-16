"""Run the station with ``python -m station`` (from the backend/ directory)."""

from __future__ import annotations

import uvicorn

from .config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "station.main:app",
        host=settings.station_host,
        port=settings.station_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
