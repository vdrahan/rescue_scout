# Hardware extensions (RPi)

How to add kit parts on top of the kickoff app.

All paths below are relative to the **`RPi/`** folder in your repo (same folder as `app.py`).

## Where to create or edit files

| What you add | Create new file? | Edit existing file |
|--------------|------------------|-------------------|
| 7-segment display | No — use [`hardware/seven_segment.py`](../hardware/seven_segment.py) | [`config.py`](../config.py) (pins), [`services/bootstrap.py`](../services/bootstrap.py), [`ui/context.py`](../ui/context.py), [`ui/inference_handlers.py`](../ui/inference_handlers.py) |
| NeoPixel ring | **Yes** → [`hardware/neopixel_ring.py`](../hardware/neopixel_ring.py) | Same as 7-segment, plus `pip install pi5-neo` in your venv |
| Buzzer | No — use [`hardware/buzzer.py`](../hardware/buzzer.py) | [`hardware/setup.py`](../hardware/setup.py), [`ui/context.py`](../ui/context.py), [`ui/inference_handlers.py`](../ui/inference_handlers.py) |
| Extra GPIO button | No | [`hardware/setup.py`](../hardware/setup.py) (`register_button` in `start_gpio`) |

**Startup wiring** for segment / NeoPixel / buzzer goes in **`services/bootstrap.py`** inside `bootstrap_app()` (right after `lcd = create_lcd(cfg)` is a good place).

**Runtime feedback** (after YOLO, etc.) goes in **`ui/inference_handlers.py`** inside `run_yolo` / `run_pose` (see comments there).

**Pass objects into handlers** via **`ui/context.py`** (`AppContext` fields), e.g. `ctx.segment`, `ctx.neo_ring`.

GPIO buttons stay in **`hardware/setup.py`** + **`ui/dashboard.py`** (`start_gpio` after the UI is built).

```
RPi/
├── config.py                    ← pin numbers (optional fields)
├── hardware/
│   ├── seven_segment.py         ← already in repo (do not duplicate)
│   ├── neopixel_ring.py         ← YOU create this for NeoPixel
│   ├── buzzer.py, gpio.py, setup.py
├── services/bootstrap.py        ← construct segment / neo_ring / buzzer here
├── ui/
│   ├── context.py               ← add fields on AppContext
│   └── inference_handlers.py    ← set_number / set_count / play()
└── docs/hardware-extensions.md  ← this file
```

## Central GPIO (`hardware/gpio.py`)

- **`GpioPlatform`** — one `GPIO.setmode(BCM)`, one **polling** thread for all buttons
- Started from **`hardware/setup.py`** → **`start_gpio()`** (wired in `ui/dashboard.py`)
- **Short press** → queue inference via `RuntimeSnapshot` + `gr.Timer` (do not run YOLO inside the GPIO thread)
- **Hold ~2 s** → shutdown (`inference_handlers.shutdown_now`)

Add a second button on the same loop:

```python
gpio.register_button(name="extra", pin=21, hold_seconds=1.0, ...)
```

## I²C LCD (`hardware/lcd_service.py`)

- Started in `services/bootstrap.py` → `create_lcd`
- Startup IP carousel: daemon thread in `lcd_startup.py`
- Inference updates: `lcd.show_result(...)` from `ui/inference_handlers.py` (main thread)

## Buzzer (`hardware/buzzer.py`)

| Buzzer | BCM | Notes |
|--------|-----|--------|
| Passive | 4 | PWM |
| Active | 12 | Digital on/off |

Smoke test: `python tests/test_buzzer.py`

**Wire into the app** (driver already at `RPi/hardware/buzzer.py`):

| Step | File |
|------|------|
| 1 | `RPi/hardware/setup.py` — inside `start_gpio()`, after `GpioPlatform(...)`, before `gpio.start()` |
| 2 | `RPi/ui/context.py` — `buzzer: BuzzerService \| None = None` on `AppContext` |
| 3 | Return buzzer from `start_gpio` or construct in `RPi/services/bootstrap.py` and pass into `AppContext` |
| 4 | `RPi/ui/inference_handlers.py` — `self._ctx.buzzer.play("success")` in `run_yolo` / `run_pose` |

```python
# RPi/hardware/setup.py (inside start_gpio)
from hardware.buzzer import BuzzerService
buzzer = BuzzerService(
    passive_pin=cfg.passive_buzzer_pin,
    active_pin=cfg.active_buzzer_pin,
    gpio=gpio,
)
```

## 4-digit 7-segment — drone count (`hardware/seven_segment.py`)

Shift register **74HC595** + multiplexed digits. The driver **already exists** at `RPi/hardware/seven_segment.py` — you do **not** create a new file for it.

| Step | File | What to do |
|------|------|------------|
| 1 | `RPi/config.py` | Uncomment / set `segment_data_pin`, `segment_clock_pin`, `segment_latch_pin` |
| 2 | `RPi/ui/context.py` | Add e.g. `segment: FourDigitSevenSegment \| None = None` on `AppContext` |
| 3 | `RPi/services/bootstrap.py` | Paste bootstrap block below inside `bootstrap_app()`, pass `segment=...` into `AppContext(...)` |
| 4 | `RPi/ui/inference_handlers.py` | In `run_yolo`, after `drone_count`: `if self._ctx.segment: self._ctx.segment.set_number(drone_count)` |

**3. Bootstrap** — edit `RPi/services/bootstrap.py`, inside `bootstrap_app()` after `lcd = create_lcd(cfg)`:

```python
from hardware.seven_segment import ShiftRegister74HC595, FourDigitSevenSegment

sr = ShiftRegister74HC595(
    data_pin=cfg.segment_data_pin,
    clock_pin=cfg.segment_clock_pin,
    latch_pin=cfg.segment_latch_pin,
)
segment = FourDigitSevenSegment(sr)
segment.start()
```

Then add `segment=segment` to the `return AppContext(...)` call in the same function.

**4. After YOLO** — edit `RPi/ui/inference_handlers.py`, in `run_yolo` (not a new file):

```python
if self._ctx.segment is not None:
    self._ctx.segment.set_number(drone_count)  # 0–9999
```

Long term: configure shift-register pins through `GpioPlatform` so `setmode` is only called once.

## NeoPixel ring — Pi 5 (`pi5-neo`)

Not part of the kickoff wiring. Uses a **dedicated data pin** and the **`pi5-neo`** library (not the GPIO poll loop).

| Step | File | What to do |
|------|------|------------|
| 1 | Terminal on the Pi | `cd RPi && source ~/.venv/bin/activate && pip install pi5-neo` |
| 2 | **`RPi/hardware/neopixel_ring.py`** | **Create this new file** (full path in repo: `RPi/hardware/neopixel_ring.py`) |
| 3 | `RPi/config.py` | Uncomment / set `neopixel_pin`, `neopixel_count` |
| 4 | `RPi/ui/context.py` | Add e.g. `neo_ring: NeoRingService \| None = None` on `AppContext` |
| 5 | `RPi/services/bootstrap.py` | Import and construct `NeoRingService`, pass into `AppContext(...)` |
| 6 | `RPi/ui/inference_handlers.py` | In `run_yolo`: `self._ctx.neo_ring.set_count(drone_count)` if not `None` |

**2. Create** `RPi/hardware/neopixel_ring.py` (new file next to `buzzer.py` and `seven_segment.py`):

```python
"""NeoPixel ring on Pi 5 — pip install pi5-neo. See RPi/docs/hardware-extensions.md."""
from __future__ import annotations

import threading

from pi5neo import Pi5Neo


class NeoRingService:
    def __init__(self, gpio_pin: int = 18, count: int = 12) -> None:
        self._neo = Pi5Neo(gpio_pin, count)
        self._lock = threading.Lock()

    def set_count(self, n: int) -> None:
        """Map detection count to LEDs (daemon thread — do not block Gradio)."""
        def _worker() -> None:
            with self._lock:
                self._neo.clear()
                for i in range(min(n, self._neo.count)):
                    self._neo.set_pixel_color(i, 0, 64, 0)
                self._neo.update()

        threading.Thread(target=_worker, daemon=True).start()
```

**5. Bootstrap** — edit `RPi/services/bootstrap.py`, inside `bootstrap_app()` after LCD init:

```python
from hardware.neopixel_ring import NeoRingService

neo_ring = NeoRingService(gpio_pin=cfg.neopixel_pin, count=cfg.neopixel_count)
```

Add `neo_ring=neo_ring` to the `return AppContext(...)` in the same function.

**6. After YOLO** — edit `RPi/ui/inference_handlers.py`, in `run_yolo`:

```python
if self._ctx.neo_ring is not None:
    self._ctx.neo_ring.set_count(drone_count)
```

## Where to hook feedback (quick reference)

| Trigger | File (under `RPi/`) |
|---------|---------------------|
| Construct hardware at startup | `services/bootstrap.py` — `bootstrap_app()` |
| GPIO buttons | `hardware/setup.py` — `start_gpio()`; called from `ui/dashboard.py` |
| After model run | `ui/inference_handlers.py` — `run_yolo`, `run_pose` |
| GPIO short press → inference | `inference_handlers.on_gpio_short_press` + `dashboard.py` timer |
| Pin numbers | `config.py` |
| Hold references on `ctx` | `ui/context.py` — `AppContext` |

## Related

- [`RPi/hardware/README.md`](../hardware/README.md)
- [Docs/1_Architecture.md](../../Docs/1_Architecture.md) — hardware diagram
- [Docs/3_Next_steps.md](../../Docs/3_Next_steps.md) — extend hardware section
