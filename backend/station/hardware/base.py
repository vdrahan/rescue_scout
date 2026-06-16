"""Device interfaces shared by mock and real hardware.

Kept deliberately small and practical: each device knows its id/name/kind, can
report status, run a self-test and clean up. Mock and real implementations live
in ``hardware/mock`` and ``hardware/real``.
"""

from __future__ import annotations

import abc
from typing import Any


class Device(abc.ABC):
    kind = "device"

    def __init__(self, dev_id: str, name: str):
        self.id = dev_id
        self.name = name
        self.ok = True

    def value(self) -> Any:
        """Current reading for sensors; current state for actuators (or None)."""
        return None

    @abc.abstractmethod
    def test(self) -> tuple[bool, str]:
        """Exercise the device; return (passed, detail)."""

    def status(self) -> dict:
        return {"id": self.id, "name": self.name, "kind": self.kind,
                "ok": self.ok, "value": self.value()}

    def close(self) -> None:
        return None


class Led(Device):
    kind = "led"

    @abc.abstractmethod
    def on(self) -> None: ...

    @abc.abstractmethod
    def off(self) -> None: ...


class RgbLed(Device):
    kind = "rgb_led"

    @abc.abstractmethod
    def set_color(self, r: float, g: float, b: float) -> None: ...


class Buzzer(Device):
    kind = "buzzer"

    @abc.abstractmethod
    def beep(self, times: int = 1, on: float = 0.1, off: float = 0.05) -> None: ...


class GasSensor(Device):
    kind = "gas_sensor"

    @abc.abstractmethod
    def read_ppm(self) -> float: ...

    def is_dangerous(self, threshold: float) -> bool:
        return self.read_ppm() >= threshold


class ClimateSensor(Device):
    kind = "climate"

    @abc.abstractmethod
    def read(self) -> tuple[float, float]:
        """Return (temperature_c, humidity_pct)."""


class Button(Device):
    kind = "button"

    @abc.abstractmethod
    def is_pressed(self) -> bool: ...


class Lcd(Device):
    kind = "lcd"

    @abc.abstractmethod
    def write(self, lines: list[str]) -> None: ...
