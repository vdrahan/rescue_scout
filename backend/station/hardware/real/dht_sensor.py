"""DHT11 temperature/humidity sensor (adafruit_dht, optional import)."""

from __future__ import annotations

from ..base import ClimateSensor


class DhtClimateSensor(ClimateSensor):
    def __init__(self, dev_id: str, name: str, pin: int = 25):
        super().__init__(dev_id, name)
        import adafruit_dht  # noqa: WPS433
        import board  # noqa: WPS433

        board_pin = getattr(board, f"D{pin}")
        self._dht = adafruit_dht.DHT11(board_pin)
        self._last = (0.0, 0.0)

    def read(self) -> tuple[float, float]:
        # DHT11 reads fail intermittently; keep the last good value on error.
        try:
            t = self._dht.temperature
            h = self._dht.humidity
            if t is not None and h is not None:
                self._last = (float(t), float(h))
        except RuntimeError:
            pass  # transient read error — DHT11 is noisy
        return self._last

    def value(self):
        t, h = self._last
        return {"temperature": t, "humidity": h}

    def test(self) -> tuple[bool, str]:
        t, h = self.read()
        ok = not (t == 0.0 and h == 0.0)
        return ok, f"DHT11 {t}C / {h}%" if ok else "DHT11 no valid reading yet"

    def close(self) -> None:
        try:
            self._dht.exit()
        except Exception:  # noqa: BLE001
            pass
