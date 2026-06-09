# `inputs` — video / image sources for the dashboard

This package defines **input modes** for `app.py`: each mode is a class implementing `InputProvider`. The app builds a registry with `build_input_providers()`, shows modes in a Gradio Radio via `input_radio_choices()`, and delegates preview ticks plus inference frame selection to the active provider.

## Modules

| File | Purpose |
|------|---------|
| `registry.py` | **`INPUT_*` IDs**, preview helpers, `pick_source_frame`, **`build_input_providers()`** |
| `base.py` | `InputProvider` ABC, `CameraCaptureResult`, `SourceUiVisibility`, `InputSourceMeta` |
| `usb_camera.py` | USB / V4L2 camera via OpenCV (`INPUT_RPI_CAMERA`) |
| `camera_devices.py` | List / resolve cameras by name (`list_cameras.py`) |
| `csi_camera.py` | Raspberry Pi CSI via Picamera2 (`INPUT_CSI_CAMERA`) |
| `upload.py` | Static image from browser upload (`INPUT_UPLOAD`) |
| `browser_webcam.py` | Browser webcam stream (`INPUT_BROWSER_WEBCAM`) |

### Browser webcam — localhost or HTTPS only

`BrowserWebcamInput` uses the **browser’s** camera via Gradio. Browsers allow that only on **localhost** or **HTTPS**, not on `http://<remote-ip>:7860`.

- **OK:** VS Code port forward to `localhost:7860`; SSH `ssh -L 7860:127.0.0.1:7860 …` then `http://127.0.0.1:7860`; HTTPS tunnel (Cloudflare, etc.).
- **Project default:** USB / CSI on the Pi — browser webcam is optional.

Details: **[Docs/1_Architecture.md](../../Docs/1_Architecture.md)** (Input sources).

## Source IDs

These strings are the **Radio values** stored in Gradio state and passed through inference hooks:

- `rpi_camera` — OpenCV capture (`UsbCameraInput`)
- `csi_camera` — Picamera2 CSI (`CsiCameraInput`)
- `browser_upload` — upload (`UploadInput`)
- `browser_webcam` — webcam (`BrowserWebcamInput`)

Order for menus / iteration: see `INPUT_OPTIONS` in `registry.py`.

## `InputProvider` contract

Each concrete class:

1. Sets **`meta`** (`InputSourceMeta`) with `source_id` and a human-readable `label`.
2. Implements **`ui_visibility()`** → `SourceUiVisibility` (which panels and controls are visible in the UI).
3. Implements **`sync_preview(resolution, target_fps, browser_webcam, latest_capture, perf_state)`** → `CameraCaptureResult`:
   - Drives the timer-driven preview line (`preview_update`, `status_text`, `perf_state`).
   - Sets **`refresh_latest`** when `latest_capture` state should be replaced by **`frame_rgb`** (hardware cameras); upload / browser typically leave `refresh_latest=False`.
4. Implements **`pick_frame(latest_capture, upload_rgb, browser_webcam_rgb)`** → RGB `numpy` array for YOLO / Pose (raises if the chosen mode has no frame yet).
5. Optionally overrides **`close()`** to release cameras or devices.

## Wiring from `app.py`

Typical usage:

```python
from inputs import build_input_providers, input_radio_choices, pick_source_frame

providers = build_input_providers(cfg)
# Radio: choices=input_radio_choices(), value=INPUT_UPLOAD
# Timer tick: providers[source_type].sync_preview(...)
# Run models: pick_source_frame(providers, source_type, latest_capture, upload_rgb, browser_webcam_rgb)
# Shutdown: for p in providers.values(): p.close()
```

## Adding a new input mode

1. Add a new **`INPUT_*`** constant and append it to **`INPUT_OPTIONS`** in **`registry.py`**.
2. Create **`inputs/my_input.py`** with a class subclassing **`InputProvider`** (follow `upload.py` as the simplest template).
3. Register it in **`build_input_providers()`** and **`input_radio_choices()`** in the same file.
4. Update **`app.py`** Gradio layout / callbacks if the new mode needs extra widgets beyond visibility toggles.

## USB camera by name (not fixed index)

On the Pi, run from the `RPi` folder:

```bash
python list_cameras.py
```

Copy the suggested line into `config.py`:

```python
camera_device: str = "usb-Your_Camera-video-index0"
```

Leave `camera_device` empty to keep using `camera_index` (legacy).

OpenCV opens the stable path under `/dev/v4l/by-id/`, so the numeric index can change after reboot without breaking your config.

## CSI camera notes

`CsiCameraInput` uses Picamera2 (`RGB888`). Sensor buffer size comes from **`AppConfig.csi_buffer_resolution`**; the dropdown **preview resolution** resizes in software. If skin looks blue/cyan in Gradio, keep **`csi_bgr_to_rgb: bool = True`** in `config.py` (default). If colors look swapped the other way on your stack, try `False`. **Target preview FPS** is applied both by the Gradio timer interval and Picamera2 **`FrameDurationLimits`** so capture rate matches the slider where the driver allows it.

Picamera2 is listed in `requirements-rpi.txt`; on Raspberry Pi OS you may prefer installing **`python3-picamera2`** via apt if pip packages conflict with system libraries.

### CSI + pip + venv (“picamera2 installed but UI says unavailable”)

Installing **`picamera2` from pip inside a normal venv is not enough.** Importing `picamera2` pulls in **`libcamera`**, which on Raspberry Pi OS is shipped as **`python3-libcamera`** under the system `dist-packages`. **Isolated venvs do not see those modules**, so you get errors such as `ModuleNotFoundError: No module named 'libcamera'` even though `pip install picamera2` succeeded.

Practical fixes (pick one):

1. **System packages in the venv** (recommended): recreate the environment with  
   `python3 -m venv .venv --system-site-packages`  
   then reinstall your project deps and ensure **`sudo apt install python3-libcamera`** (and Pi camera stack) is present.

2. **Run with system Python**: use `/usr/bin/python3` (after `pip install --user picamera2` or apt `python3-picamera2`) so `libcamera` and `picamera2` share the same interpreter.

3. Confirm which interpreter runs the app: `which python` and  
   `python -c "import libcamera; from picamera2 import Picamera2"` — both must succeed in **that** interpreter.
