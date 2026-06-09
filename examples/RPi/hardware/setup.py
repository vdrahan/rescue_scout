"""
Hardware orchestration: I²C LCD + GPIO buttons (separate buses).

Extend this file when you add kit parts::

  - Buzzer: after ``gpio = GpioPlatform(...)``, before ``gpio.start()``::
        ``BuzzerService(..., gpio=gpio)`` and store on ``AppContext``
  - 7-segment drone count: ``hardware/seven_segment.py`` — start display thread
        in ``bootstrap_app``, call ``set_number()`` from ``inference_handlers.run_yolo``
  - NeoPixel ring: ``pi5-neo`` library, own module + thread — see
        ``RPi/docs/hardware-extensions.md``

GPIO callbacks must stay fast (flags only). Gradio inference uses
``RuntimeSnapshot`` + ``gr.Timer`` in ``ui/dashboard.py``.
"""

from __future__ import annotations

import threading
from typing import Callable

from config import AppConfig
from hardware.gpio import GpioPlatform
from hardware.lcd_service import LCDService
from hardware.lcd_startup import lcd_startup_network_carousel

def create_lcd(cfg: AppConfig) -> LCDService:
    return LCDService(
        addr=cfg.lcd_i2c_addr,
        bus=cfg.lcd_i2c_bus,
        width=cfg.lcd_width,
        min_update_interval=cfg.lcd_min_update_interval,
    )


def start_lcd_startup_display(cfg: AppConfig, lcd: LCDService) -> None:
    """Show LAN/Wi-Fi IPs on the LCD while the app is starting (background thread)."""
    threading.Thread(
        target=lcd_startup_network_carousel,
        args=(cfg, lcd),
        daemon=True,
        name="lcd-startup",
    ).start()


def start_gpio(
    cfg: AppConfig,
    on_short_press: Callable[[], None],
    on_hold_press: Callable[[], str],
) -> GpioPlatform:
    """
    Start the central GPIO poll loop with the main kit button (BCM 20 by default).

    Short press → ``on_short_press`` (e.g. queue model inference).
    Hold → ``on_hold_press`` (e.g. shutdown); return value is logged only.
    """

    def on_hold() -> None:
        message = on_hold_press()
        print(f"[GPIO] Hold press -> {message}")

    gpio = GpioPlatform(poll_interval=cfg.shutdown_poll_interval)
    gpio.register_button(
        name="main",
        pin=cfg.shutdown_button_pin,
        hold_seconds=cfg.shutdown_hold_seconds,
        on_short_press=on_short_press,
        on_hold_press=on_hold,
    )
    # Optional: register more buttons on the same poll loop, e.g.
    # gpio.register_button(name="mute", pin=21, hold_seconds=1.0, ...)

    # Optional: BuzzerService(passive_pin=cfg.passive_buzzer_pin,
    #     active_pin=cfg.active_buzzer_pin, gpio=gpio)

    gpio.start()
    return gpio


# Backward-compatible name used by dashboard
start_gpio_button = start_gpio
