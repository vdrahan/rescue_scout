"""DHT11 temperature/humidity sensor via the dht11 library (uses RPi.GPIO / rpi-lgpio)."""

from __future__ import annotations

from ..base import ClimateSensor


class DhtClimateSensor(ClimateSensor):
    def __init__(self, dev_id: str, name: str, pin: int = 25):
        super().__init__(dev_id, name)
        import RPi.GPIO as GPIO  # noqa: WPS433
        import dht11  # noqa: WPS433

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self._dht = dht11.DHT11(pin=pin)
        self._last = (0.0, 0.0)

    def read(self) -> tuple[float, float]:
        try:
            result = self._dht.read()
            if result.is_valid():
                self._last = (float(result.temperature), float(result.humidity))
        except Exception:  # noqa: BLE001
            pass  # keep last good reading on transient errors
        return self._last

    def value(self):
        t, h = self._last
        return {"temperature": t, "humidity": h}

    def test(self) -> tuple[bool, str]:
        import time  # noqa: WPS433

        for _ in range(3):
            t, h = self.read()
            if not (t == 0.0 and h == 0.0):
                return True, f"DHT11 {t}C / {h}%"
            time.sleep(1)
        return False, "DHT11 no valid reading after 3 attempts"

    def close(self) -> None:
        pass
