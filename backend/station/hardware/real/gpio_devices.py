"""GPIO actuators/inputs via gpiozero (Pi 5-safe through the lgpio backend).

Importing this module requires ``gpiozero``; the hardware manager only imports
it inside a try/except so a missing library degrades to mock instead of crashing.
"""

from __future__ import annotations

from gpiozero import LED as GzLED  # noqa: N811
from gpiozero import RGBLED as GzRGBLED  # noqa: N811
from gpiozero import Button as GzButton
from gpiozero import TonalBuzzer  # fallback handled below

from ..base import Button, Buzzer, Led, RgbLed


class GpioLed(Led):
    def __init__(self, dev_id: str, name: str, pin: int):
        super().__init__(dev_id, name)
        self._led = GzLED(pin)

    def on(self) -> None:
        self._led.on()

    def off(self) -> None:
        self._led.off()

    def value(self):
        return "on" if self._led.is_lit else "off"

    def test(self) -> tuple[bool, str]:
        import time

        self.on()
        time.sleep(0.3)
        self.off()
        return True, f"LED on pin {self._led.pin} toggled"

    def close(self) -> None:
        self._led.close()


class GpioRgbLed(RgbLed):
    def __init__(self, dev_id: str, name: str, r: int, g: int, b: int):
        super().__init__(dev_id, name)
        self._rgb = GzRGBLED(r, g, b)

    def set_color(self, r: float, g: float, b: float) -> None:
        self._rgb.color = (r / 100.0, g / 100.0, b / 100.0)

    def value(self):
        return tuple(round(c, 2) for c in self._rgb.color)

    def test(self) -> tuple[bool, str]:
        import time

        for color in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            self._rgb.color = color
            time.sleep(0.25)
        self._rgb.color = (0, 0, 0)
        return True, "RGB cycled R/G/B"

    def close(self) -> None:
        self._rgb.close()


class GpioBuzzer(Buzzer):
    """Active buzzer driven as a simple on/off LED-style output."""

    def __init__(self, dev_id: str, name: str, pin: int):
        super().__init__(dev_id, name)
        # An active buzzer behaves like an LED (digital on/off).
        self._out = GzLED(pin)

    def beep(self, times: int = 1, on: float = 0.1, off: float = 0.05) -> None:
        import time

        for _ in range(times):
            self._out.on()
            time.sleep(on)
            self._out.off()
            time.sleep(off)

    def test(self) -> tuple[bool, str]:
        self.beep(3)
        return True, "buzzer pulsed 3x"

    def close(self) -> None:
        self._out.close()


class GpioButton(Button):
    def __init__(self, dev_id: str, name: str, pin: int):
        super().__init__(dev_id, name)
        self._btn = GzButton(pin)

    def is_pressed(self) -> bool:
        return bool(self._btn.is_pressed)

    def value(self):
        return self.is_pressed()

    def test(self) -> tuple[bool, str]:
        return True, f"button on pin {self._btn.pin} ready"

    def close(self) -> None:
        self._btn.close()


# Re-exported so unused TonalBuzzer import is intentional documentation of the
# alternative passive-buzzer path (see requirements-hw.txt notes).
__all__ = ["GpioLed", "GpioRgbLed", "GpioBuzzer", "GpioButton", "TonalBuzzer"]
