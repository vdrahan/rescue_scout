# 1. Architecture — repository layout

End-of-year-1 bachelor kickoff: a **Gradio dashboard** on the Raspberry Pi with **local YOLO + MediaPipe**, several **input sources**, and **GPIO / I²C hardware** feedback. Students will later implement stripped-out parts (camera open, LCD, GPIO actions).

**Run:** `python app.py` from [`RPi/`](RPi/)

---

## Phase ①②③ — Startup (detail)

| Step | File | What happens |
|------|------|----------------|
| ① | `app.py` | `main()` starts |
| ② | `config.py` | Ports, `camera_device` / `camera_index`, LCD/GPIO pins |
| ③ | `services/bootstrap.py` | LCD + models dict + inputs dict → `AppContext` |
| ④ | `ui/dashboard.py` | Gradio layout, event wiring, GPIO shutdown attached |
| ⑤ | `ui/dashboard.py` | HTTP server listens on LAN |
| ⑥ | — | Timer + GPIO threads run in background |
| ⑦ | `services/bootstrap.py` | `finally:` cleanup |

---

## Phase ⑥ — Runtime actions (detail)

While the app is live, these triggers do work:

- **Preview timer** — `InputHandlers.sync_video_preview` (USB/CSI camera feed)
- **GPIO timer (0.15 s)** — `dispatch_gpio_inference` when short press was queued
- **Input source** — show/hide upload, preview, FPS controls
- **Run YOLO / Run Pose** — `InferenceHandlers` + history + LCD
- **GPIO short press** — queue inference for **GPIO short press runs** model (see `model_section.py`)
- **GPIO hold / UI Shutdown** — `request_sudo_poweroff`

---

## Three pillars in the UI

Gradio is built in three labeled blocks in `ui/`:

| Pillar | UI module | Registry / logic | Student edits |
|--------|-----------|-------------------|---------------|
| **Input** | `input_section.py` | `inputs/registry.py` | `usb_camera.py`, `csi_camera.py`, … |
| **Model** | `model_section.py` | `models/registry.py` | `yolo_detector.py`, `pose_detector.py`, …; **GPIO short press runs** radio |
| **Output** | `output_section.py` | `history.py` | Usually only handlers |

### Input sources

| ID (`INPUT_*`) | Class | Preview | Frame for inference |
|----------------|-------|---------|---------------------|
| `rpi_camera` | `UsbCameraInput` | Timer + OpenCV | `latest_capture` state |
| `csi_camera` | `CsiCameraInput` | Timer + Picamera2 | same |
| `browser_upload` | `UploadInput` | — | uploaded image |
| `browser_webcam` | `BrowserWebcamInput` | browser stream | webcam component |

**Browser webcam (`browser_webcam`) — security context**

Browsers only allow `getUserMedia` (the laptop webcam in Gradio) on **localhost** or **HTTPS**. Opening the dashboard as plain `http://<pi-ip>:7860` from another machine will **not** expose the browser webcam tab reliably.

| Access | Works for browser webcam? |
|--------|---------------------------|
| `http://127.0.0.1:7860` on the Pi itself | Yes |
| **VS Code** port forwarding to `localhost:7860` on your laptop | Yes |
| **SSH** manual forward, e.g. `ssh -L 7860:127.0.0.1:7860 student@<pi>` then open `http://127.0.0.1:7860` | Yes |
| Plain `http://<pi-lan-ip>:7860` from your laptop | No (use USB/CSI/upload instead) |
| **HTTPS** via a tunnel (e.g. Cloudflare Tunnel, ngrok, …) | Yes |

For **Project One**, use **hardware on the Pi** — **USB** (`rpi_camera`) or **CSI** (`csi_camera`) — plus **upload** for still images. Browser webcam is optional for demos; it is not required for the kickoff goals.

- IDs and `pick_source_frame()` live in **`inputs/registry.py`** (one file).
- USB camera name: run `python list_cameras.py` → set `camera_device` in `config.py`.
- Hardware preview capped by **target FPS** (default 6, max 20).

### Models

| ID (`MODEL_*`) | Class | File |
|----------------|-------|------|
| `yolo` | `YoloDroneModel` | `models/yolo_detector.py` |
| `pose` | `MediaPipePoseModel` | `models/pose_detector.py` |

- IDs and `build_models()` live in **`models/registry.py`** (one file).
- Handlers: `ui/inference_handlers.py` → `ctx.models[MODEL_YOLO]` / `MODEL_POSE`.

### Output (same for every model run)

1. Tab image (`yolo_output` / `pose_output`)
2. Status textbox
3. `gr.JSON` server status
4. AI history accordion (optional thumbnail)
5. Error history accordion

LCD updates are **outside** Gradio JSON (`lcd.show_result`, etc.).

---

## Hardware (background)

| Piece | File | Role |
|-------|------|------|
| Setup | `hardware/setup.py` | `create_lcd`, `start_lcd_startup_display`, `start_gpio` |
| GPIO | `hardware/gpio.py` | `GpioPlatform` — one poll loop, `register_button()` |
| LCD | `hardware/lcd_service.py` | Two-line I²C display |
| Network | `hardware/network.py` | Read IPs, `sudo poweroff` |
| GPIO compat | `hardware/gpio_compat.py` | Real Pi GPIO or laptop mock |
| Runtime bridge | `core/runtime_snapshot.py` | GPIO short press queues model; timer runs `dispatch_gpio_inference` |

Optional (see [`RPi/docs/hardware-extensions.md`](../RPi/docs/hardware-extensions.md)): `buzzer.py`, `seven_segment.py`, NeoPixel (`pi5-neo`).

---

## Repository layout

```
CTAI_P1_26_KICKOFF/
├── Docs/
│   ├── README.md
│   ├── 0_Image_preparation.md
│   ├── 1_Architecture.md
│   ├── 2_Kickoff.md
│   ├── 3_Next_steps.md
│   └── 4_Production.md
├── RPi/
│   ├── app.py                 ← ① entry
│   ├── config.py              ← ② settings
│   ├── list_cameras.py        ← USB camera discovery
│   ├── services/bootstrap.py  ← ③⑦ init / shutdown
│   ├── core/state.py          ← shutdown guard only
│   ├── hardware/              ← gpio.py, setup.py, lcd_service.py, …
│   ├── docs/                  ← hardware-extensions.md, CSI redirect
│   ├── ui/                    ← ④ Gradio + handlers
│   ├── inputs/
│   │   ├── base.py            ← InputProvider ABC + shared types (do not delete)
│   │   ├── registry.py        ← IDs + build_input_providers
│   │   ├── camera_devices.py  ← list_cameras / resolve by name
│   │   └── usb_camera.py, csi_camera.py, upload.py, browser_webcam.py
│   ├── models/
│   │   ├── base.py            ← InferenceResult (do not delete)
│   │   ├── registry.py        ← IDs + build_models
│   │   └── yolo_detector.py, pose_detector.py
│   ├── tests/                 ← test_ip.py, test_lcd.py, test_buzzer.py
│   ├── ai/                    ← best.pt, pose .task
│   └── students/
├── Laptop/                    ← code to train model
└── Extra/                     ← remote variant (not kickoff)
```

---


### Hardware

- **GPIO buttons:** [`hardware/gpio.py`](RPi/hardware/gpio.py) + [`hardware/setup.py`](RPi/hardware/setup.py) (`start_gpio`)
- **LCD (I²C):** [`hardware/lcd_service.py`](RPi/hardware/lcd_service.py) — update from `inference_handlers`
- **GPIO short → run model:** short press sets flag + freezes **GPIO short press runs** model; `gr.Timer` calls `dispatch_gpio_inference` and switches to the matching tab so `yolo_output` / `pose_output` updates visibly
- **Buzzer / 7-segment / NeoPixel:** [`RPi/docs/hardware-extensions.md`](../RPi/docs/hardware-extensions.md)


---

## Related docs

- [`Docs/README.md`](README.md) — documentation index
- [`Docs/0_Image_preparation.md`](0_Image_preparation.md) — Python, CSI, Docker on the Pi
- [`Docs/2_Kickoff.md`](2_Kickoff.md) — lab day steps
- [`Docs/3_Next_steps.md`](3_Next_steps.md) — Wi‑Fi, training, extensions
- [`Docs/4_Production.md`](4_Production.md) — autostart
- [`RPi/inputs/README.md`](../RPi/inputs/README.md)
- [`RPi/models/README.md`](../RPi/models/README.md)
- [`RPi/hardware/README.md`](../RPi/hardware/README.md)
- [`RPi/docs/hardware-extensions.md`](../RPi/docs/hardware-extensions.md)

---

## Config defaults

From [`RPi/config.py`](RPi/config.py):

| Setting | Default |
|---------|---------|
| Gradio | `0.0.0.0:7860` |
| Preview FPS | 6 (max 20) |
| Preview resolution | 640×480 |
| CSI color fix | `csi_bgr_to_rgb=True` (Picamera2 BGR→RGB for Gradio; set `False` if hues invert) |
| USB camera | `camera_device` substring or `camera_index` fallback |
| Buzzer (passive / active) | BCM **4** / **12** (`passive_buzzer_pin`, `active_buzzer_pin`) |
| Shutdown GPIO | BCM 20, hold 2 s |
| LCD I²C | `0x27`, bus 1, 20 cols |
