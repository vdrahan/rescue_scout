from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import AppConfig
from core.runtime_snapshot import RuntimeSnapshot
from core.state import SharedState
from hardware.gpio import GpioPlatform
from hardware.lcd_service import LCDService
from inputs.base import InputProvider


@dataclass
class AppContext:
    cfg: AppConfig
    base_dir: Path
    shared: SharedState
    lcd: LCDService
    models: dict[str, object]
    providers: dict[str, InputProvider]
    runtime: RuntimeSnapshot
    gpio: GpioPlatform | None = None
    # Optional extensions (see RPi/docs/hardware-extensions.md):
    # buzzer: BuzzerService | None = None
    # segment: FourDigitSevenSegment | None = None
