#!/usr/bin/env python3
"""
Smoke test: passive (GPIO4, PWM) and active (GPIO12, digital) buzzers.

Run on the Pi (from repo root or from RPi/):
    python RPi/tests/test_buzzer.py
    cd RPi && python tests/test_buzzer.py

Optional:
    python tests/test_buzzer.py --pattern success
    python tests/test_buzzer.py --target active
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_RPI_ROOT = Path(__file__).resolve().parents[1]
if str(_RPI_ROOT) not in sys.path:
    sys.path.insert(0, str(_RPI_ROOT))

from config import AppConfig
from hardware.buzzer import (
    DEFAULT_ACTIVE_BUZZER_PIN,
    DEFAULT_PASSIVE_BUZZER_PIN,
    BuzzerService,
)

PATTERN_NAMES = ("boot", "shutdown", "success", "error")
TARGET_CHOICES = ("passive", "active", "both")
# Sum of tone durations in hardware/buzzer.py + small gap
_PATTERN_WAIT_S = {
    "boot": 0.35,
    "shutdown": 0.55,
    "success": 0.25,
    "error": 0.6,
}


def _wait_for_pattern(name: str) -> None:
    time.sleep(_PATTERN_WAIT_S.get(name, 0.5))


def main() -> None:
    cfg = AppConfig()
    parser = argparse.ArgumentParser(description="Buzzer smoke test (passive PWM + active digital)")
    parser.add_argument(
        "--passive-pin",
        type=int,
        default=cfg.passive_buzzer_pin,
        help=f"BCM GPIO for passive buzzer / PWM (default {DEFAULT_PASSIVE_BUZZER_PIN})",
    )
    parser.add_argument(
        "--active-pin",
        type=int,
        default=cfg.active_buzzer_pin,
        help=f"BCM GPIO for active buzzer / on-off (default {DEFAULT_ACTIVE_BUZZER_PIN})",
    )
    parser.add_argument(
        "--pattern",
        choices=PATTERN_NAMES,
        default="",
        help="Play one pattern only; default plays boot, success, error",
    )
    parser.add_argument(
        "--target",
        choices=TARGET_CHOICES,
        default="both",
        help="Which buzzer to exercise (default both)",
    )
    args = parser.parse_args()

    print("=== Buzzer smoke test (hardware.buzzer) ===\n")
    print(f"Passive (PWM) BCM {args.passive_pin}  |  Active (digital) BCM {args.active_pin}")

    buzzer = BuzzerService(passive_pin=args.passive_pin, active_pin=args.active_pin)

    if not buzzer.enabled:
        print("\nBuzzer not available — check wiring and GPIO permissions.")
        sys.exit(1)

    print(
        f"\nPassive enabled: {buzzer.passive_enabled}  |  Active enabled: {buzzer.active_enabled}"
    )

    patterns = [args.pattern] if args.pattern else ["boot", "success", "error"]

    print("\nMute check (success on passive should be silent)...")
    buzzer.set_muted(True)
    buzzer.play("success", target="passive")
    time.sleep(0.8)
    buzzer.set_muted(False)

    for name in patterns:
        print(f"Playing pattern {name!r} on {args.target!r}...")
        buzzer.play(name, target=args.target)
        _wait_for_pattern(name)

    print("\nCooldown check (three error triggers, ~2s apart — passive only)...")
    for _ in range(3):
        buzzer.play_cooldown("error", key="smoke-test", cooldown_sec=2.0, target="passive")
        time.sleep(0.15)
    time.sleep(2.5)

    print("\nUnknown pattern (no sound, no error)...")
    buzzer.play("nonexistent")

    buzzer.cleanup()
    print("Done.")


if __name__ == "__main__":
    main()
