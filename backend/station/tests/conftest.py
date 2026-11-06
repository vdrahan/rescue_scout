"""Test fixtures. Forces mock modes before the station package is imported."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `import station` work regardless of the pytest invocation directory.
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Force a dependency-light, deterministic environment for every test run.
os.environ.setdefault("DETECTION_MODE", "mock")
os.environ.setdefault("HARDWARE_MODE", "mock")
os.environ.setdefault("SINK_ENABLED", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from station.config import Settings  # noqa: E402
from station.main import create_app  # noqa: E402

# Tests must never pick up a developer's real `.env` (camera URLs would make "mock"
# tests open real cameras and take seconds per test) or camera URLs from the shell.
Settings.model_config["env_file"] = None
for _name in ("RTSP_CAMERA_1_URL", "RTSP_CAMERA_2_URL"):
    os.environ.pop(_name, None)


@pytest.fixture()
def client():
    with TestClient(create_app()) as test_client:
        yield test_client
