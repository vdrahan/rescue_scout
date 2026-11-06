"""Frontend runtime configuration (backend URLs), read from the environment."""

from __future__ import annotations

import os

# Service-name URLs inside Docker; localhost defaults for local development.
STATION_URL = os.getenv("STATION_URL", "http://localhost:8001").rstrip("/")
API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

# Keep HTTP calls snappy so the Gradio UI never blocks on a slow/absent backend.
REQUEST_TIMEOUT = float(os.getenv("FRONTEND_HTTP_TIMEOUT", "2.5"))

# Some physical self-tests intentionally blink/beep/read for a few seconds.
HARDWARE_TEST_TIMEOUT = float(os.getenv("FRONTEND_HARDWARE_TEST_TIMEOUT", "8.0"))

# After a failed call, skip that backend for this long (circuit breaker).
BACKEND_COOLDOWN_SECONDS = float(os.getenv("FRONTEND_BACKEND_COOLDOWN", "5.0"))

_DEFAULT_CAMERA_REFRESH = 0.1
_MIN_CAMERA_REFRESH = 0.05


def camera_refresh_seconds(env) -> float:
    """Seconds between live-view refreshes (FRONTEND_CAMERA_REFRESH_SECONDS).

    Every refresh is a Gradio event that costs real CPU on the Pi, so the rate is
    capped at 20 Hz and a bad value falls back to the default (10 Hz)."""
    try:
        value = float(env.get("FRONTEND_CAMERA_REFRESH_SECONDS", _DEFAULT_CAMERA_REFRESH))
    except ValueError:
        return _DEFAULT_CAMERA_REFRESH
    return max(_MIN_CAMERA_REFRESH, value)


CAMERA_REFRESH_SECONDS = camera_refresh_seconds(os.environ)

# Optional: start station detection once when the dashboard opens.
AUTO_START_DETECTION = os.getenv("FRONTEND_AUTO_START_DETECTION", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
