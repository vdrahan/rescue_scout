"""Sweeps old live-view frames out of Gradio's temp folder.

Gradio saves every refreshed camera image as a new file (``<hash>/image.jpeg``) and
never removes it; ``Blocks(delete_cache=...)`` does not track these files (checked on
the Pi: the oldest frame outlived the limit and the count kept growing). At the
live-view rate that is ~2 GB/hour, enough to fill the SD card of a kiosk left running.
Only ``image.*`` files are touched, so CSV exports and other downloads are never removed.
"""

from __future__ import annotations

import os
import tempfile
import threading
import time
from pathlib import Path

MAX_AGE_SECONDS = 600.0  # a frame is on screen for ~0.1 s; the rest is slack for slow clients
SWEEP_INTERVAL_SECONDS = 60.0


def cache_dir() -> Path:
    return Path(os.environ.get("GRADIO_TEMP_DIR") or Path(tempfile.gettempdir()) / "gradio")


def sweep(root: Path, max_age: float = MAX_AGE_SECONDS) -> int:
    """Delete live-view frames older than ``max_age`` seconds; return how many."""
    cutoff = time.time() - max_age
    removed = 0
    try:
        folders = [d for d in root.iterdir() if d.is_dir()]
    except OSError:
        return 0
    for folder in folders:
        for frame in folder.glob("image.*"):
            try:
                if frame.stat().st_mtime < cutoff:
                    frame.unlink()
                    removed += 1
            except OSError:
                continue  # already gone, or still being written
        try:
            folder.rmdir()  # only succeeds when empty
        except OSError:
            pass
    return removed


def start_sweeper(root: Path | None = None, interval: float = SWEEP_INTERVAL_SECONDS) -> threading.Thread:
    target = root or cache_dir()

    def loop() -> None:
        while True:
            time.sleep(interval)
            sweep(target)

    thread = threading.Thread(target=loop, name="frame-cache-sweeper", daemon=True)
    thread.start()
    return thread
