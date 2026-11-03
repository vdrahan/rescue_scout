"""System control endpoints."""

from __future__ import annotations

import subprocess
import threading

from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])


@router.post("/reboot")
def reboot_pi() -> dict[str, str]:
    """Schedule a system reboot after a short delay so the HTTP response
    can be delivered before the OS goes down."""
    threading.Timer(2.0, lambda: subprocess.Popen(["reboot"])).start()
    return {"status": "rebooting"}
