"""Minimal I2C HD44780 LCD driver (smbus2, optional import).

Mirrors the proven low-level sequence from the project's ``tests/test.py`` so it
works with the same 0x27 PCF8574 backpack, without pulling an extra LCD library.
"""

from __future__ import annotations

import time

from ..base import Lcd
from .i2c_lock import BUS_1_LOCK

_BACKLIGHT = 0x08
_ENABLE = 0b00000100


class I2cLcd(Lcd):
    def __init__(self, dev_id: str, name: str, addr: int = 0x27, bus: int = 1, width: int = 16):
        super().__init__(dev_id, name)
        import smbus2  # noqa: WPS433

        self._addr = addr
        self._width = width
        self._bus = smbus2.SMBus(bus)
        self._init_display()

    def _write_byte(self, bits: int, mode: int) -> None:
        high = mode | (bits & 0xF0) | _BACKLIGHT
        low = mode | ((bits << 4) & 0xF0) | _BACKLIGHT
        for payload in (high, low):
            self._bus.write_byte(self._addr, payload)
            self._toggle(payload)

    def _toggle(self, bits: int) -> None:
        time.sleep(0.0005)
        self._bus.write_byte(self._addr, bits | _ENABLE)
        time.sleep(0.0005)
        self._bus.write_byte(self._addr, bits & ~_ENABLE)
        time.sleep(0.0005)

    def _init_display(self) -> None:
        for cmd in (0x33, 0x32, 0x06, 0x0C, 0x28, 0x01):
            self._write_byte(cmd, 0)
        time.sleep(0.005)

    def _clear(self) -> None:
        self._write_byte(0x01, 0)
        time.sleep(0.005)

    def write(self, lines: list[str]) -> None:
        with BUS_1_LOCK:
            self._clear()
            addresses = (0x80, 0xC0, 0x94, 0xD4)
            for line, addr in zip(lines, addresses):
                self._write_byte(addr, 0)
                for ch in line.ljust(self._width)[: self._width]:
                    self._write_byte(ord(ch), 1)

    def write_line(self, line_idx: int, text: str) -> None:
        """Overwrite a single line without clearing the display (no flicker)."""
        with BUS_1_LOCK:
            addresses = (0x80, 0xC0, 0x94, 0xD4)
            self._write_byte(addresses[line_idx], 0)
            for ch in text.ljust(self._width)[: self._width]:
                self._write_byte(ord(ch), 1)

    def value(self):
        return None

    def test(self) -> tuple[bool, str]:
        self.write(["HARDWARE TEST", "LCD OK"])
        time.sleep(2)
        self._clear()
        return True, "LCD wrote 2 lines"

    def close(self) -> None:
        try:
            self._clear()
            self._bus.close()
        except Exception:  # noqa: BLE001
            pass
