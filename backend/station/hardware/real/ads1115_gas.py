"""MQ-2 gas sensor read through an ADS1115 I2C ADC (adafruit, optional import)."""

from __future__ import annotations

from ..base import GasSensor


class Ads1115GasSensor(GasSensor):
    def __init__(self, dev_id: str, name: str, i2c_addr: int = 0x48, channel: int = 0):
        super().__init__(dev_id, name)
        import adafruit_ads1x15.ads1115 as ADS  # noqa: WPS433
        import board  # noqa: WPS433
        import busio  # noqa: WPS433
        from adafruit_ads1x15.analog_in import AnalogIn  # noqa: WPS433

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c, address=i2c_addr)
        channels = (ADS.P0, ADS.P1, ADS.P2, ADS.P3)
        self._chan = AnalogIn(ads, channels[channel])

    def read_ppm(self) -> float:
        # Rough linear voltage->ppm mapping. Proper MQ-2 calibration is a TODO
        # (depends on load resistor + clean-air baseline). 3.3V ~= full scale.
        voltage = float(self._chan.voltage)
        return round(voltage / 3.3 * 1000.0, 1)

    def value(self):
        try:
            return self.read_ppm()
        except Exception:  # noqa: BLE001
            return None

    def test(self) -> tuple[bool, str]:
        ppm = self.read_ppm()
        return True, f"MQ-2 via ADS1115 reading {ppm} ppm"
