"""Synthetic devices that need no Raspberry Pi hardware or libraries."""

from __future__ import annotations

import random

from ...logging_conf import get_logger
from ..base import Button, Buzzer, ClimateSensor, GasSensor, Lcd, Led, RgbLed, RgbModule

log = get_logger(__name__)


class MockLed(Led):
    def __init__(self, dev_id: str, name: str):
        super().__init__(dev_id, name)
        self._on = False

    def on(self) -> None:
        self._on = True
        log.debug("[mock] LED %s ON", self.id)

    def off(self) -> None:
        self._on = False
        log.debug("[mock] LED %s OFF", self.id)

    def value(self):
        return "on" if self._on else "off"

    def test(self) -> tuple[bool, str]:
        self.on()
        self.off()
        return True, "mock LED toggled"


class MockRgbLed(RgbLed):
    def __init__(self, dev_id: str, name: str):
        super().__init__(dev_id, name)
        self._color = (0, 0, 0)

    def set_color(self, r: float, g: float, b: float) -> None:
        self._color = (r, g, b)
        log.debug("[mock] RGB %s -> %s", self.id, self._color)

    def value(self):
        return self._color

    def test(self) -> tuple[bool, str]:
        for color in ((0, 100, 0), (100, 0, 0), (0, 0, 100), (100, 100, 0)):
            self.set_color(*color)
        self.set_color(0, 0, 0)
        return True, "mock RGB PWM LED cycled"


class MockRgbModule(RgbModule):
    def __init__(self, dev_id: str, name: str):
        super().__init__(dev_id, name)
        self._channel: str | None = None

    def set_channel(self, channel: str | None) -> None:
        self._channel = channel
        log.debug("[mock] RGB module %s -> %s", self.id, channel or "off")

    def value(self):
        return self._channel or "off"

    def test(self) -> tuple[bool, str]:
        for channel in ("red", "green", "blue"):
            self.set_channel(channel)
        self.set_channel(None)
        return True, "mock RGB module cycled"


class MockBuzzer(Buzzer):
    def beep(self, times: int = 1, on: float = 0.1, off: float = 0.05) -> None:
        log.debug("[mock] buzzer beep x%d", times)

    def test(self) -> tuple[bool, str]:
        self.beep(3)
        return True, "mock buzzer pulsed reference pattern"


class MockGasSensor(GasSensor):
    """Random-walk ppm with occasional danger spikes for a lively demo."""

    def __init__(self, dev_id: str, name: str, seed: int | None = None):
        super().__init__(dev_id, name)
        self._rng = random.Random(seed)
        self._ppm = 120.0

    def read_ppm(self) -> float:
        self._ppm += self._rng.uniform(-12, 12)
        if self._rng.random() < 0.04:  # rare spike
            self._ppm += self._rng.uniform(120, 220)
        self._ppm = max(80.0, min(600.0, self._ppm))
        return round(self._ppm, 1)

    def value(self):
        return round(self._ppm, 1)

    def test(self) -> tuple[bool, str]:
        return True, f"mock gas reading {self.read_ppm()} ppm"


class MockClimateSensor(ClimateSensor):
    def __init__(self, dev_id: str, name: str, seed: int | None = None):
        super().__init__(dev_id, name)
        self._rng = random.Random(seed)
        self._t = 22.0
        self._h = 45.0

    def read(self) -> tuple[float, float]:
        self._t = max(10.0, min(40.0, self._t + self._rng.uniform(-0.4, 0.4)))
        self._h = max(20.0, min(90.0, self._h + self._rng.uniform(-1.5, 1.5)))
        return round(self._t, 1), round(self._h, 1)

    def value(self):
        return {"temperature": round(self._t, 1), "humidity": round(self._h, 1)}

    def test(self) -> tuple[bool, str]:
        t, h = self.read()
        return True, f"mock DHT11 {t}C / {h}%"


class MockButton(Button):
    def is_pressed(self) -> bool:
        return False

    def value(self):
        return False

    def test(self) -> tuple[bool, str]:
        return True, "mock button responsive"


class MockLcd(Lcd):
    def __init__(self, dev_id: str, name: str):
        super().__init__(dev_id, name)
        self._lines: list[str] = []

    def write(self, lines: list[str]) -> None:
        self._lines = lines
        log.debug("[mock] LCD %s: %s", self.id, " | ".join(lines))

    def value(self):
        return self._lines

    def test(self) -> tuple[bool, str]:
        self.write(["HARDWARE TEST", "LCD OK"])
        return True, "mock LCD wrote 2 lines"
