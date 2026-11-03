"""GPIO actuators/inputs via direct lgpio calls.

gpiozero's LGPIOFactory auto-selects gpiochip4 on some Pi revisions. This
project's container exposes gpiochip0, so direct lgpio control is more reliable
for the debugging hardware tests.
"""

from __future__ import annotations

from ..base import Buzzer, Button, Led, RgbLed, RgbModule


PWM_FREQUENCY = 1000


class _LgpioDevice:
    def __init__(self, chip: int = 0):
        import lgpio  # noqa: WPS433

        self._lgpio = lgpio
        self._handle = lgpio.gpiochip_open(chip)
        self._chip = chip

    def _claim_output(self, pin: int, initial: int = 0) -> None:
        self._lgpio.gpio_claim_output(self._handle, pin, initial)

    def _claim_input(self, pin: int) -> None:
        self._lgpio.gpio_claim_input(self._handle, pin)

    def _write(self, pin: int, value: int) -> None:
        self._lgpio.gpio_write(self._handle, pin, value)

    def _read(self, pin: int) -> int:
        return int(self._lgpio.gpio_read(self._handle, pin))

    def _pwm(self, pin: int, duty: float) -> None:
        self._lgpio.tx_pwm(self._handle, pin, PWM_FREQUENCY, duty)

    def _close_chip(self) -> None:
        try:
            self._lgpio.gpiochip_close(self._handle)
        except Exception:  # noqa: BLE001
            pass


class GpioLed(_LgpioDevice, Led):
    def __init__(self, dev_id: str, name: str, pin: int, chip: int = 0):
        Led.__init__(self, dev_id, name)
        _LgpioDevice.__init__(self, chip)
        self._pin = pin
        self._on = False
        self._claim_output(pin, 0)

    def on(self) -> None:
        self._write(self._pin, 1)
        self._on = True

    def off(self) -> None:
        self._write(self._pin, 0)
        self._on = False

    def value(self):
        return "on" if self._on else "off"

    def test(self) -> tuple[bool, str]:
        import time

        self.on()
        time.sleep(1)
        self.off()
        return True, f"LED on GPIO {self._pin} toggled"

    def close(self) -> None:
        self.off()
        self._close_chip()


class GpioRgbLed(_LgpioDevice, RgbLed):
    def __init__(self, dev_id: str, name: str, r: int, g: int, b: int, chip: int = 0):
        RgbLed.__init__(self, dev_id, name)
        _LgpioDevice.__init__(self, chip)
        self._pins = (r, g, b)
        self._color = (0.0, 0.0, 0.0)
        for pin in self._pins:
            self._claim_output(pin, 0)
            self._pwm(pin, 100)  # common anode: 100% duty = off

    def set_color(self, r: float, g: float, b: float) -> None:
        self._color = (r, g, b)
        for pin, duty in zip(self._pins, self._color):
            self._pwm(pin, 100.0 - duty)  # common anode: invert duty

    def value(self):
        return self._color

    def test(self) -> tuple[bool, str]:
        import time

        for color in ((0, 100, 0), (100, 0, 0), (0, 0, 100), (100, 100, 0)):
            self.set_color(*color)
            time.sleep(1)
        self.set_color(0, 0, 0)
        return True, "RGB PWM LED cycled green/red/blue/yellow"

    def close(self) -> None:
        self.set_color(0, 0, 0)
        self._close_chip()


class GpioRgbModule(_LgpioDevice, RgbModule):
    """Three-pin digital RGB module from tests/test.py (RGB1_R/G/B)."""

    def __init__(self, dev_id: str, name: str, r: int, g: int, b: int, chip: int = 0):
        RgbModule.__init__(self, dev_id, name)
        _LgpioDevice.__init__(self, chip)
        self._channels = {"red": r, "green": g, "blue": b}
        self._active: str | None = None
        for pin in self._channels.values():
            self._claim_output(pin, 1)  # common anode: 1 = off

    def set_channel(self, channel: str | None) -> None:
        for name, pin in self._channels.items():
            self._write(pin, 0 if name == channel else 1)  # common anode: 0 = on
        self._active = channel

    def value(self):
        return self._active or "off"

    def test(self) -> tuple[bool, str]:
        import time

        for channel in ("red", "green", "blue"):
            self.set_channel(channel)
            time.sleep(0.5)
        self.set_channel(None)
        return True, "RGB module cycled red/green/blue"

    def close(self) -> None:
        self.set_channel(None)
        self._close_chip()


class GpioBuzzer(_LgpioDevice, Buzzer):
    """Active buzzer driven as a simple on/off GPIO output."""

    def __init__(self, dev_id: str, name: str, pin: int, chip: int = 0):
        Buzzer.__init__(self, dev_id, name)
        _LgpioDevice.__init__(self, chip)
        self._pin = pin
        self._claim_output(pin, 0)

    def beep(self, times: int = 1, on: float = 0.1, off: float = 0.05) -> None:
        import time

        for _ in range(times):
            self._write(self._pin, 1)
            time.sleep(on)
            self._write(self._pin, 0)
            time.sleep(off)

    def test(self) -> tuple[bool, str]:
        import time

        for on_time, off_time in ((0.1, 0.05), (0.1, 0.05), (0.2, 0.1)):
            self._write(self._pin, 1)
            time.sleep(on_time)
            self._write(self._pin, 0)
            time.sleep(off_time)
        return True, f"buzzer pulsed reference pattern on GPIO {self._pin}"

    def close(self) -> None:
        self._write(self._pin, 0)
        self._close_chip()


class GpioButton(_LgpioDevice, Button):
    def __init__(self, dev_id: str, name: str, pin: int, chip: int = 0):
        Button.__init__(self, dev_id, name)
        _LgpioDevice.__init__(self, chip)
        self._pin = pin
        self._claim_input(pin)

    def is_pressed(self) -> bool:
        return bool(self._read(self._pin))

    def value(self):
        return self.is_pressed()

    def test(self) -> tuple[bool, str]:
        return True, f"button on GPIO {self._pin} ready"

    def close(self) -> None:
        self._close_chip()


__all__ = ["GpioLed", "GpioRgbLed", "GpioRgbModule", "GpioBuzzer", "GpioButton"]
