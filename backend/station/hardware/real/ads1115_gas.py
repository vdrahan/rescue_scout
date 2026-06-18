"""MQ-2 gas sensor via PCF8591 I2C ADC (8-bit, 4-channel).

Protocol:
  write_byte(addr, 0x40 | channel)  — select channel
  read_byte(addr)                   — discard (PCF8591 returns previous sample first)
  read_byte(addr)                   — actual current sample (0–255)

Calibration:
  MQ-2 voltage drops when gas concentration rises (lower resistance → less voltage
  across the sensor in the voltage-divider circuit).  Clean air gives raw ≈ 195–205.
  Gas (lighter / LPG) pulls raw significantly lower.

  avg_raw = average of _SAMPLES single reads (reduces noise)
  ppm = max(0, CLEAN_AIR_RAW - avg_raw) / CLEAN_AIR_RAW * MAX_PPM

  Scale: 0 ppm = clean air, 200 ppm = sensor saturated (avg_raw = 0).
  Danger threshold (set in config): 30 ppm (avg_raw drops ~30 counts below baseline).
"""

from __future__ import annotations

import logging
import time

from ..base import GasSensor
from .i2c_lock import BUS_1_LOCK

log = logging.getLogger(__name__)

# Baseline anchored to the bottom of the observed clean-air noise range (raw ≈ 176–205).
# Using the lower bound (185) means clean-air readings always stay near 0 ppm and only
# a genuine gas drop pulls the averaged raw below the baseline.
_CLEAN_AIR_RAW: int = 185
# Full-scale output in ppm (when avg_raw = 0, i.e. sensor fully saturated with gas)
_MAX_PPM: float = 200.0
# Number of consecutive reads to average — reduces single-read noise (±13 raw counts)
_SAMPLES: int = 5
# Delay between samples in seconds
_SAMPLE_DELAY: float = 0.05


class Ads1115GasSensor(GasSensor):
    """Kept as Ads1115GasSensor for compatibility — actual chip is PCF8591."""

    def __init__(self, dev_id: str, name: str, i2c_addr: int = 0x48, channel: int = 0):
        super().__init__(dev_id, name)
        import smbus2  # noqa: WPS433

        self._bus = smbus2.SMBus(1)
        self._addr = i2c_addr
        self._control = 0x40 | (channel & 0x03)

    def _read_raw_once(self) -> int:
        # Select channel
        self._bus.write_byte(self._addr, self._control)
        # PCF8591 quirk: first read returns the previous conversion result
        self._bus.read_byte(self._addr)
        # Second read returns the current sample
        return self._bus.read_byte(self._addr)

    def _read_raw(self) -> float:
        """Average _SAMPLES reads to smooth out ADC noise."""
        total = 0
        for i in range(_SAMPLES):
            if i:
                time.sleep(_SAMPLE_DELAY)
            total += self._read_raw_once()
        return total / _SAMPLES

    def read_ppm(self) -> float:
        with BUS_1_LOCK:
            avg_raw = self._read_raw()
        drop = max(0.0, _CLEAN_AIR_RAW - avg_raw)
        ppm = drop / _CLEAN_AIR_RAW * _MAX_PPM
        return round(ppm, 1)

    def value(self):
        try:
            return self.read_ppm()
        except Exception:  # noqa: BLE001
            return None

    def test(self) -> tuple[bool, str]:
        try:
            with BUS_1_LOCK:
                avg_raw = self._read_raw()
            drop = max(0.0, _CLEAN_AIR_RAW - avg_raw)
            ppm = round(drop / _CLEAN_AIR_RAW * _MAX_PPM, 1)
            return True, f"MQ-2 via PCF8591 avg_raw={avg_raw:.1f} baseline={_CLEAN_AIR_RAW} → {ppm} ppm"
        except Exception as exc:  # noqa: BLE001
            return False, f"MQ-2 read error: {exc}"

    def close(self) -> None:
        try:
            self._bus.close()
        except Exception:  # noqa: BLE001
            pass
