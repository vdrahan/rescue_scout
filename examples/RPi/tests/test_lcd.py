#!/usr/bin/env python3
"""
Smoke test: show text on the I2C LCD via hardware.lcd_service (same as the kickoff app).

Run on the Pi (from repo root or from RPi/):
    python RPi/tests/test_lcd.py
    cd RPi && python tests/test_lcd.py

Requires LCD at the address in config.py (default 0x27, bus 1).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_RPI_ROOT = Path(__file__).resolve().parents[1]
if str(_RPI_ROOT) not in sys.path:
    sys.path.insert(0, str(_RPI_ROOT))

from config import AppConfig
from hardware.lcd_service import LCDService


def main() -> None:
    cfg = AppConfig()
    print("=== LCD smoke test (hardware.lcd_service) ===\n")
    print(f"I2C addr={hex(cfg.lcd_i2c_addr)} bus={cfg.lcd_i2c_bus} width={cfg.lcd_width}")

    lcd = LCDService(
        addr=cfg.lcd_i2c_addr,
        bus=cfg.lcd_i2c_bus,
        width=cfg.lcd_width,
        min_update_interval=cfg.lcd_min_update_interval,
    )

    if not lcd.enabled:
        print("\nLCD not available — check wiring, I2C enable, and address.")
        sys.exit(1)

    line1 = "CTAI LCD test"
    line2 = "Line 2 OK"
    print(f"\nShowing on LCD:\n  {line1!r}\n  {line2!r}\n")
    lcd.show_lines(line1, line2, force=True)

    hold_s = 5.0
    print(f"Holding for {hold_s:.0f}s (Ctrl+C to exit early)...")
    try:
        time.sleep(hold_s)
    except KeyboardInterrupt:
        print("\nInterrupted.")

    lcd.show_waiting()
    print("Restored idle lines (Status: WAITING / Mode idle).")
    print("Done.")


if __name__ == "__main__":
    main()
