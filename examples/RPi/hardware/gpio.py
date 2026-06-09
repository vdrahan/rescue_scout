"""
Central BCM GPIO for the P1 kit.

One ``GPIO.setmode(BCM)`` per app, one polling thread for all buttons.

Extend with more inputs::

    gpio = GpioPlatform(poll_interval=cfg.shutdown_poll_interval)
    gpio.register_button(
        name="run",
        pin=cfg.shutdown_button_pin,
        hold_seconds=cfg.shutdown_hold_seconds,
        on_short_press=on_short,
        on_hold_press=on_hold,
    )
    gpio.register_button(name="extra", pin=21, ...)  # optional second button
    gpio.start()

I²C LCD is separate (``lcd_service.py``); wire LCD + GPIO from ``setup.py``.

Other outputs (extend here or in a new module)::

    # Buzzer pins — share this platform so setmode is called once::
    #   from hardware.buzzer import BuzzerService
    #   buzzer = BuzzerService(passive_pin=4, active_pin=12, gpio=gpio)

    # NeoPixel ring (Pi 5) — not BCM bit-banging; use pi5-neo on a data pin::
    #   pip install pi5-neo   # see RPi/docs/hardware-extensions.md
    #   Start a daemon thread; call from inference_handlers after YOLO (e.g. count).

    # 4-digit 7-segment (shift register) — see hardware/seven_segment.py::
    #   display.set_number(drone_count) after inference; own refresh thread inside.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable

from .gpio_compat import GPIO


@dataclass(frozen=True)
class ButtonSpec:
    """Configuration for one active-low button (internal pull-up)."""

    pin: int
    hold_seconds: float
    on_short_press: Callable[[], None]
    on_hold_press: Callable[[], None]
    name: str = "button"


@dataclass
class _ButtonRuntime:
    spec: ButtonSpec
    pressed_at: float | None = None
    hold_triggered: bool = False


class GpioPlatform:
    """
    Shared GPIO layer: configure pins once, poll all registered buttons.

    Callbacks run on the poll thread — keep them fast (set flags, log).
    Do not call Gradio or heavy inference from callbacks.
    """

    def __init__(self, poll_interval: float = 0.02) -> None:
        self.poll_interval = poll_interval
        self._buttons: list[_ButtonRuntime] = []
        self._mode_set = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def ensure_mode(self) -> None:
        if not self._mode_set:
            GPIO.setmode(GPIO.BCM)
            self._mode_set = True

    def register_button(
        self,
        *,
        pin: int,
        hold_seconds: float,
        on_short_press: Callable[[], None],
        on_hold_press: Callable[[], None],
        name: str = "button",
    ) -> None:
        """Register a button. Call before :meth:`start`. Pressed = pin LOW."""
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("Cannot register buttons after start()")
        self.ensure_mode()
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self._buttons.append(
            _ButtonRuntime(
                spec=ButtonSpec(
                    pin=pin,
                    hold_seconds=hold_seconds,
                    on_short_press=on_short_press,
                    on_hold_press=on_hold_press,
                    name=name,
                )
            )
        )

    def setup_output_low(self, pin: int) -> None:
        """Configure a pin as digital output, driven LOW."""
        self.ensure_mode()
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    def setup_pwm(self, pin: int, frequency: float = 440):
        """Configure a pin for PWM (e.g. passive buzzer). Returns the PWM instance.

        NeoPixel data lines are not configured here — use ``pi5-neo`` (see
        ``RPi/docs/hardware-extensions.md``).
        """
        self.ensure_mode()
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, frequency)
        pwm.start(0)
        return pwm

    def start(self) -> None:
        if not self._buttons:
            raise RuntimeError("register_button() required before start()")
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="gpio-poll")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
            self._thread = None

    def _poll_loop(self) -> None:
        while not self._stop.is_set():
            for runtime in self._buttons:
                self._tick_button(runtime)
            time.sleep(self.poll_interval)

    def _tick_button(self, runtime: _ButtonRuntime) -> None:
        spec = runtime.spec
        pressed = GPIO.input(spec.pin) == 0
        if pressed:
            if runtime.pressed_at is None:
                runtime.pressed_at = time.time()
                runtime.hold_triggered = False
            elif (
                not runtime.hold_triggered
                and time.time() - runtime.pressed_at >= spec.hold_seconds
            ):
                runtime.hold_triggered = True
                spec.on_hold_press()
        else:
            if runtime.pressed_at is not None and not runtime.hold_triggered:
                spec.on_short_press()
            runtime.pressed_at = None


class ButtonService(GpioPlatform):
    """
    Convenience wrapper: one button on a dedicated :class:`GpioPlatform`.

    For multiple buttons, use :class:`GpioPlatform` directly.
    """

    def __init__(
        self,
        pin: int,
        hold_seconds: float,
        on_short_press: Callable[[], None],
        on_hold_press: Callable[[], None],
        poll_interval: float = 0.02,
        name: str = "button",
    ) -> None:
        super().__init__(poll_interval=poll_interval)
        self.register_button(
            pin=pin,
            hold_seconds=hold_seconds,
            on_short_press=on_short_press,
            on_hold_press=on_hold_press,
            name=name,
        )
