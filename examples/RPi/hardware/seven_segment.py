"""
4-digit 7-segment display via 74HC595 shift register (BCM GPIO bit-bang).

Extend for Project One — show YOLO drone count on the physical display::

  1. Wire DATA/CLK/LATCH to BCM pins (add to ``config.py`` if you like).
  2. In ``services/bootstrap.py`` after LCD init::

         sr = ShiftRegister74HC595(data_pin=..., clock_pin=..., latch_pin=...)
         segment = FourDigitSevenSegment(sr)
         segment.start()   # daemon refresh thread (~250 Hz multiplex)

  3. In ``ui/inference_handlers.py`` inside ``run_yolo`` after you have
     ``drone_count``::

         segment.set_number(drone_count)   # 0–9999

  Prefer a shared ``GpioPlatform`` for shift-register pins once you merge
  ``ShiftRegister74HC595`` with ``hardware/gpio.py`` (today it calls setmode itself).

NeoPixel ring: use ``pi5-neo``, not this module — see ``RPi/docs/hardware-extensions.md``.
"""

from __future__ import annotations

import threading
import time
from typing import List

from .gpio_compat import GPIO, GPIO_AVAILABLE


class ShiftRegister74HC595:
    def __init__(self, data_pin: int, clock_pin: int, latch_pin: int) -> None:
        self.data_pin = data_pin
        self.clock_pin = clock_pin
        self.latch_pin = latch_pin
        self.enabled = GPIO_AVAILABLE

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        # TODO: GPIO setup
       

    def _pulse(self, pin: int) -> None:
        GPIO.output(pin, GPIO.HIGH)
        GPIO.output(pin, GPIO.LOW)

    def _write_one_bit(self, bit: int) -> None:
        GPIO.output(self.data_pin, GPIO.HIGH if bit else GPIO.LOW)
        self._pulse(self.clock_pin)

    def _shift_byte_out(self, value: int) -> None:
        for i in range(8):
            bit = 1 if (value & (0x80 >> i)) else 0
            self._write_one_bit(bit)

    def shift_out_16bit(self, value: int) -> None:
        # TODO: shift out 16bit
        pass

    def clear(self) -> None:
        self.shift_out_16bit(0x0000)


class FourDigitSevenSegment:
    # Segment bit order: A B C D E F G DP (LSB -> MSB)
    _BASE_DIGIT_TO_SEGMENTS = {
        0: 0x3F,
        1: 0x06,
        2: 0x5B,
        3: 0x4F,
        4: 0x66,
        5: 0x6D,
        6: 0x7D,
        7: 0x07,
        8: 0x7F,
        9: 0x6F,
    }

    def __init__(
        self,
        shift_register: ShiftRegister74HC595,
        refresh_hz: int = 250,
        segment_active_low: bool = True,
        digit_active_high: bool = True,
    ) -> None:
        self.shift_register = shift_register
        self.refresh_hz = max(80, refresh_hz)
        self.segment_active_low = segment_active_low
        self.digit_active_high = digit_active_high
        self._digits = [0, 0, 0, 0]
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _encode_segment(self, value: int) -> int:
        raw = self._BASE_DIGIT_TO_SEGMENTS.get(value, 0x00)
        if self.segment_active_low:
            return (~raw) & 0xFF
        return raw & 0xFF

    def _encode_digit_select(self, digit_idx: int) -> int:
        if self.digit_active_high:
            return 1 << digit_idx
        return (~(1 << digit_idx)) & 0x0F

    def _refresh_loop(self) -> None:
        delay = 1.0 / float(self.refresh_hz * 4)
        while not self._stop_event.is_set():
            with self._lock:
                snapshot = list(self._digits)

            for idx, val in enumerate(snapshot):
                select_mask = self._encode_digit_select(idx)
                segment_mask = self._encode_segment(val)
                frame = ((select_mask & 0xFF) << 8) | (segment_mask & 0xFF)
                self.shift_register.shift_out_16bit(frame)
                time.sleep(delay)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self.shift_register.clear()

    def set_number(self, number: int) -> None:
        """Show 0–9999 on the display (thread-safe; refresh loop reads _digits)."""
        clamped = max(0, min(9999, int(number)))
        text = f"{clamped:04d}"
        digits: List[int] = [int(ch) for ch in text]
        with self._lock:
            self._digits = digits[::-1]

