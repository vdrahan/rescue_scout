#!/usr/bin/env python3
"""
List USB / V4L2 cameras on the Raspberry Pi.

Run on the Pi (SSH or terminal):
    python list_cameras.py

Copy a `config_value` into RPi/config.py:
    camera_device: str = "usb-Your_Camera_Name-video-index0"
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_list_cameras():
    """Load camera_devices without importing the full inputs package (no numpy/gradio)."""
    module_path = Path(__file__).resolve().parent / "inputs" / "camera_devices.py"
    spec = importlib.util.spec_from_file_location("camera_devices", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_path}")
    mod = importlib.util.module_from_spec(spec)
    # Required before exec_module: @dataclass looks up sys.modules[cls.__module__].
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.list_cameras


def main() -> None:
    cameras = _load_list_cameras()()
    if not cameras:
        print("No capture cameras found.")
        print("Check: ls -l /dev/v4l/by-id/   and   ls /dev/video*")
        return

    print("Available cameras\n" + "=" * 60)
    for i, cam in enumerate(cameras, start=1):
        print(f"\n[{i}] {cam.label}")
        print(f"    device node : {cam.device_node}")
        print(f"    open path   : {cam.open_path}")
        print(f"    config.py   : camera_device: str = \"{cam.config_value}\"")
        if cam.index is not None:
            print(f"    (legacy)    : camera_index: int = {cam.index}")

    best = cameras[0]
    print("\n" + "=" * 60)
    print("Recommended — paste into config.py:\n")
    print(f'    camera_device: str = "{best.config_value}"')
    print('    camera_index: int = 8  # ignored when camera_device is set')
    print("\nMatching is case-insensitive substring (e.g. \"Logitech\" or \"OmniVision\").")


if __name__ == "__main__":
    main()
