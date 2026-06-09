# `hardware` — Raspberry Pi peripherals

GPIO (polling), I²C LCD, buzzers, and startup behaviour.

## Layout

| File | Purpose |
|------|---------|
| **`gpio.py`** | **`GpioPlatform`** — one BCM mode, one poll thread, `register_button()` for short/hold |
| `setup.py` | **`create_lcd`**, **`start_lcd_startup_display`**, **`start_gpio`** (thin wiring) |
| `lcd_service.py` | I²C 20×4 display (lock; no permanent thread) |
| `lcd_startup.py` | Daemon thread: LAN/Wi-Fi IP carousel at boot |
| `buzzer.py` | Melodies on daemon threads; optional shared `GpioPlatform` for pin setup |
| `network.py` | Pi IP addresses, `sudo poweroff` |
| `gpio_compat.py` | Real GPIO on Pi, mock on laptop |

**Pins (BCM):** button **20**, passive buzzer **4** (PWM), active buzzer **12**. See `config.py`.

## GPIO (extendable)

```python
from hardware.gpio import GpioPlatform

gpio = GpioPlatform(poll_interval=0.02)
gpio.register_button(
    name="main",
    pin=20,
    hold_seconds=2.0,
    on_short_press=lambda: ...,
    on_hold_press=lambda: ...,
)
# gpio.register_button(name="extra", pin=21, ...)  # second button, same poll loop
gpio.start()
```

Callbacks run on the poll thread — set flags only; Gradio runs inference via `RuntimeSnapshot` + timer.

**I²C LCD** is started from `setup.py`, not from `gpio.py`.

## Student tasks (typical)

- Fix or complete LCD init in `lcd_service.py`
- Short GPIO press runs the **active model tab** when the input has a valid frame
- Add buzzer: `BuzzerService(gpio=gpio)` in `start_gpio` / bootstrap, call from `ui/inference_handlers.py`

Buzzer smoke test (standalone): `python tests/test_buzzer.py`

**Extension guide (buzzer, 7-segment, NeoPixel):** [`../docs/hardware-extensions.md`](../docs/hardware-extensions.md)
