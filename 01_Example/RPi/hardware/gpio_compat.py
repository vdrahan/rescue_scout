from __future__ import annotations

# When NOT running on RPi, use this mock GPIO class.

class _MockPWM:
    def start(self, _duty: float) -> None:
        return None

    def stop(self) -> None:
        return None

    def ChangeDutyCycle(self, _duty: float) -> None:
        return None

    def ChangeFrequency(self, _frequency: float) -> None:
        return None


class _MockGPIO:
    BCM = "BCM"
    IN = "IN"
    OUT = "OUT"
    LOW = 0
    HIGH = 1
    PUD_UP = "PUD_UP"
    FALLING = "FALLING"

    def setmode(self, _mode: str) -> None:
        return None

    def setup(self, _pin: int, _mode: str, pull_up_down: str | None = None) -> None:
        return None

    def input(self, _pin: int) -> int:
        return 1

    def output(self, _pin: int, _value: int) -> None:
        return None

    def PWM(self, _pin: int, _frequency: float) -> _MockPWM:
        return _MockPWM()

    def cleanup(self) -> None:
        return None


try:
    import RPi.GPIO as _GPIO  # type: ignore

    GPIO = _GPIO
except Exception:  # pragma: no cover - only used when GPIO is absent
    GPIO = _MockGPIO()
