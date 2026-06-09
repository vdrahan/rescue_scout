# 2. Kickoff

We run **local AI on the Raspberry Pi**: a Gradio dashboard with **YOLO** (bee model) and **MediaPipe Pose**. Open the web UI from your laptop on the same network.

**Repository:** `2025-2026-ProjectOne-CTAI-<yourname>`  
**On the Pi:** `/home/student/2025-2026-ProjectOne-CTAI-<yourname>/`  
**Application:** `RPi/app.py` · **Docker stack:** `RPi/api/`

**Related:**

- Prepared image / broken stack: [0_Image_preparation.md](0_Image_preparation.md)
- Code layout: [1_Architecture.md](1_Architecture.md)
- After kickoff: [3_Next_steps.md](3_Next_steps.md) · Production: [4_Production.md](4_Production.md)

### IP addresses

| Network      | Pi IP              | Use for SSH and browser                  |
| ------------ | ------------------ | ---------------------------------------- |
| Lab Ethernet | `192.168.168.167`  | Default in examples below                |
| Home Wi‑Fi   | From `hostname -I` | **Replace** `192.168.168.167` everywhere |

---

## Step 0: Backup SD card and firmware

Back up the microSD with win32DiskImager or the macOS Disks tool.

To update Pi firmware, write the bootloader utility image: Raspberry Pi Imager → **Misc utility images** → **Bootloader** → **SD Card Boot**. Solid green while working; rapid blink when done.

---

## Step 1: Flash the prepared image and first login

### Download and write the image

1. Download [CTAI_P1_26_BASE.zip (OneDrive)](https://studenthowest-my.sharepoint.com/:u:/g/personal/pieter-jan_beeckman_howest_be/IQASBvEK93XvSbqlpuW8P3v6AZ8jIIV47tGsiHGQEIoCXJ0?e=e0rV74) on your laptop.  
   Also available from [Google Drive](https://drive.google.com/file/d/1EqCqr-55aS51sRGacNbrM1mm0ttE4adJ/view?usp=sharing), [TransferXL](https://www.transferxl.com/download/08vR4kHq8zrq64) and [TransferNow](https://www.transfernow.net/dl/20260525qUWW7vwt)
2. Unzip the file.
3. Write to a ≥16 GB SD card with Win32 Disk Imager or Balena Etcher.  
   With **Raspberry Pi Imager**, do **not** apply OS customisation settings.
4. Insert the SD card and boot the Pi.

### First SSH login

1. Connect Ethernet (lab) or use a screen and keyboard.
2. SSH: `ssh student@192.168.168.167` — password `P@ssw0rd`  
   Keyboard layout is QWERTY; if login fails on AZERTY keyboard, try `P2sszàrd`.
3. Set a **new** password when prompted; SSH disconnects — log in again.
4. `sudo raspi-config` → enable desktop autologin if needed.
5. Reboot: `sudo reboot` (VNC may need this once).

### Home Wi‑Fi (without Ethernet)

At home, join your Wi‑Fi so the Pi and laptop share a network:

```bash
nmcli dev wifi list
sudo nmcli dev wifi connect "WIFI-name" password "WIFI-pass"
hostname -I
```

Use that IP for SSH, VS Code, and browsers (`:7860`, `:8000`, `:5050`):

`ssh student@<pi-home-ip> -A`

The Pi remembers saved networks.

---

The prepared image already has **SSH**, **VNC**, **camera**, **I²C**, **Docker**, Python **3.11** in `~/.venv`, and pre-pulled container images (see [0_Image_preparation.md](0_Image_preparation.md) §7–8).

---

## Step 2: GitHub Classroom repo on the Pi

The project folder does not exist until you clone it.

### 2.1 Accept the assignment

Open the GitHub Classroom link and confirm the repo `2025-2026-ProjectOne-CTAI-<yourname>` exists on GitHub.

### 2.2 Remote SSH in VS Code

1. Install **Remote - SSH** in VS Code on your laptop.
2. Connect: `ssh student@192.168.168.167 -A` (or home IP).
3. Password: your **new** password.
4. Host OS: **Linux**.

### 2.3 Clone on the Pi

**VS Code:** Command Palette → **Git: Clone** → HTTPS URL → `/home/student`

**Terminal:**

```bash
cd ~
git clone https://github.com/<org>/2025-2026-ProjectOne-CTAI-<yourname>.git
ls
# Expect: RPi/  Docs/  Laptop/  PD.md  ...
```

### 2.4 Open the repo folder

**File → Open Folder** → `/home/student/2025-2026-ProjectOne-CTAI-<yourname>`

### 2.5 Git identity (once per Pi)

```bash
git config --global user.name "FIRST_NAME LAST_NAME"
git config --global user.email "your.email@example.com"
```

### 2.6 Configure cameras (USB and CSI)

Do this **before** the first `python app.py` so the Input dropdown only lists sources that work on **your** Pi.

Open a terminal in `RPi/` with the venv active (`(.venv)`).

#### USB camera (if you use one)

1. Plug in the USB webcam.
2. List devices and get the `config.py` line:

```bash
cd ~/2025-2026-projectone-ctai-<yourname>/RPi
python list_cameras.py
```

3. Edit [`RPi/config.py`](../RPi/config.py) — set **`camera_device`** to the printed `config_value` (substring match is enough):

```python
camera_device: str = "usb-Your_Camera_Name-video-index0"
```

Leave `camera_device: str = ""` only if you rely on **`camera_index`** (legacy; less stable after reboot).

4. Quick open test (optional) — use the same `camera_device` string as in `config.py`:

```bash
python -c "
from inputs.camera_devices import resolve_camera_source
import cv2
src = resolve_camera_source('YOUR_CONFIG_VALUE', 0)
cap = cv2.VideoCapture(src)
print('OK' if cap.isOpened() else 'FAIL')
cap.release()
"
```

**No USB camera on this project?** Skip the steps above and disable **USB / RPi camera** in the Gradio list (see **Disable unused input sources** below).

#### CSI camera (if you use the ribbon camera module)

1. Confirm the OS sees the sensor:

```bash
rpicam-hello --list-cameras
```

You should see at least one camera listed. If not: check the ribbon cable, enable the camera in `sudo raspi-config` → **Interface Options** → **Camera**, reboot — or see [0_Image_preparation.md](0_Image_preparation.md) Step 4.

2. Confirm Python can load Picamera2 in **the venv**:

```bash
cd ~/2025-2026-projectone-ctai-<yourname>/RPi
source ~/.venv/bin/activate
python -c "import libcamera; from picamera2 import Picamera2; print('CSI stack OK')"
```

3. Optional buffer size in `config.py`:

```python
csi_buffer_resolution: str = "1280x720"
```

**No CSI module?** Skip these checks and disable **CSI camera** in the Gradio list (below).

#### Disable unused input sources (Gradio Input dropdown)

The dashboard builds the **Input source** radio from [`RPi/inputs/registry.py`](../RPi/inputs/registry.py):

- **`input_radio_choices()`** — what appears in Gradio
- **`build_input_providers()`** — what the app can actually run

Remove any source you do **not** use so students do not pick a broken option.

| Source ID              | Gradio label           | Disable when                                                                      |
| ---------------------- | ---------------------- | --------------------------------------------------------------------------------- |
| `INPUT_RPI_CAMERA`     | USB / RPi camera       | No USB webcam                                                                     |
| `INPUT_CSI_CAMERA`     | CSI camera (Picamera2) | No CSI module or CSI stack fails                                                  |
| `INPUT_UPLOAD`         | Browser upload         | Keep for kickoff (YOLO + Pose demos)                                              |
| `INPUT_BROWSER_WEBCAM` | Browser webcam         | Optional; often disabled (needs localhost/HTTPS — see [Appendix.md](Appendix.md)) |

**Example — USB + upload only** (no CSI, no browser webcam):

In `registry.py`, trim **`INPUT_OPTIONS`**, **`build_input_providers()`**, and **`input_radio_choices()`**:

```python
INPUT_OPTIONS = (
    INPUT_RPI_CAMERA,
    INPUT_UPLOAD,
)

def build_input_providers(cfg: AppConfig) -> dict[str, InputProvider]:
    # ... imports unchanged ...
    return {
        INPUT_RPI_CAMERA: UsbCameraInput(cfg.camera_device, cfg.camera_index),
        INPUT_UPLOAD: UploadInput(),
    }

def input_radio_choices() -> list[tuple[str, str]]:
    # ... imports unchanged ...
    return [
        (UsbCameraInput.meta.label, INPUT_RPI_CAMERA),
        (UploadInput.meta.label, INPUT_UPLOAD),
    ]
```

**Example — CSI + upload only** (no USB): omit `INPUT_RPI_CAMERA` / `UsbCameraInput` from all three places; keep `INPUT_CSI_CAMERA` and `INPUT_UPLOAD`.

Restart `python app.py` after editing `registry.py`. The default radio value in `ui/input_section.py` is **upload** (`INPUT_UPLOAD`) — leave that unless you change it.

More detail: [`RPi/inputs/README.md`](../RPi/inputs/README.md).

---

## Step 3: Python and first Gradio run

### 3.1 Interpreter

Select **`/home/student/.venv/bin/python`** (Python 3.11) in VS Code. New terminals should show `(.venv)`.

Broken imports after an upgrade → [0_Image_preparation.md](0_Image_preparation.md).

### 3.2 Run the dashboard

```bash
cd ~/2025-2026-ProjectOne-CTAI-<yourname>/RPi
python app.py
```

Leave this running.

### 3.3 Browser

On your laptop: `http://192.168.168.167:7860` (or `http://<pi-ip>:7860`).

You should see **Input**, **Model** (YOLO + Pose), and **Output**. Do not create a new venv on the prepared image.

---

## Step 4: Docker — PostgreSQL, pgAdmin, FastAPI

Files in **`RPi/api/`**:

| File                 | Purpose                      |
| -------------------- | ---------------------------- |
| `docker-compose.yml` | `postgres`, `pgadmin`, `api` |
| `.env.example`       | Copy to `.env`               |
| `main.py`            | `/health`, `/db-health`      |
| `Dockerfile`         | Builds the API image         |

| Setting                     | Value                                             |
| --------------------------- | ------------------------------------------------- |
| Database                    | `projectone`                                      |
| DB user / password          | `ctai` / `ctai`                                   |
| `DATABASE_URL` (in Compose) | `postgresql://ctai:ctai@postgres:5432/projectone` |
| pgAdmin                     | `student@howest.be` / `ctai`                      |
| FastAPI port                | `8000`                                            |

### 4.1 Verify Docker

Docker and the three base images are **already on the prepared image** ([0_Image_preparation.md](0_Image_preparation.md) §7–8). Check:

```bash
docker --version
docker compose version
```

`permission denied` → log out and in after being added to the `docker` group.

### 4.2 Create `.env`

```bash
cd ~/2025-2026-ProjectOne-CTAI-<yourname>/RPi/api
cp .env.example .env
```

Confirm `DATABASE_URL` uses host **`postgres`** (Compose service name).

### 4.3 Review `docker-compose.yml`

Three services: `postgres` (5432), `pgadmin` (5050), `api` (8000, `build: .`, `env_file: .env`).

### 4.4 Build API and start

```bash
docker compose up -d --build
docker compose ps
```

`--build` creates `ctai-api` from `Dockerfile`. Postgres and pgAdmin use pre-pulled images.

Running containers: `ctai-postgres` (healthy), `ctai-pgadmin`, `ctai-api`.

At home, if an image is missing: `docker pull` commands in [0_Image_preparation.md](0_Image_preparation.md) §8, then `docker compose up -d --build` again.

### 4.5 Test FastAPI

| URL                             | Expected                          |
| ------------------------------- | --------------------------------- |
| `http://<pi-ip>:8000/health`    | `{"status":"ok","service":"api"}` |
| `http://<pi-ip>:8000/db-health` | `"database":"connected"`          |

```bash
curl -s http://127.0.0.1:8000/db-health
```

### 4.6 pgAdmin

1. `http://<pi-ip>:5050` — login `student@howest.be` / `ctai`
2. **Register → Server** — Name `CTAI local`, Host `postgres`, Port `5432`, User/Password `ctai`, Database `projectone`
3. Expand **Databases → projectone**

Gradio → Postgres in Python comes later; kickoff needs Docker, `/db-health`, and pgAdmin connected.

---

## Step 5: Dashboard overview

| Part               | Role                                                           |
| ------------------ | -------------------------------------------------------------- |
| **Input**          | Upload, USB, CSI, browser webcam — same source for both models |
| **Drone YOLO**     | `best.pt` — demo uses **upload**; camera works too             |
| **MediaPipe Pose** | **Camera** and **upload** must both work                       |
| **Output**         | Images, status, JSON, history                                  |
| **LCD**            | I²C (Step 6)                                                   |

---

## Step 6: Code completion

Work in `RPi/`. Search for `# TODO:` — that is what you must implement. The reference repo leaves those stubs empty on purpose.

### What is stripped out (your tasks)

| File                        | `# TODO:` location                    | What must work when you are done                                                        |
| --------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------- |
| `hardware/lcd_service.py`   | `I2CLCD._init_lcd`                    | LCD powers on in 4-bit mode; display is usable                                          |
| `hardware/lcd_service.py`   | `I2CLCD.message`                      | Text appears on line 1 or line 2 (20 chars)                                             |
| `models/yolo_detector.py`   | `YoloDroneModel.run`                  | YOLO runs on a frame; returns annotated image + `counts` per class                      |
| `ui/inference_handlers.py`  | (no `# TODO` — you edit logic)        | After YOLO, LCD shows **bee** count from `counts` (class name in `best.pt`, e.g. `Bee`) |
| `ui/dashboard.py`           | `start_gpio(..., on_short_press=...)` | Short press triggers GPIO inference (see **6E**)                                        |
| `hardware/network.py`       | `request_sudo_poweroff`               | Hold shutdown + UI **Shutdown** button call `sudo poweroff`                             |
| `hardware/seven_segment.py` | optional                              | Shift register + 16-bit shift (not required for demo checklist)                         |

### 6A. Smoke tests

| Test       | Command                                                              |
| ---------- | -------------------------------------------------------------------- |
| LCD        | `cd RPi && python tests/test_lcd.py`                                 |
| IP         | `cd RPi && python tests/test_ip.py`                                  |
| Buzzer     | `cd RPi && python tests/test_buzzer.py` (Optional today, see **6F**) |
| USB camera | Done in **Step 2.6** — else `python list_cameras.py` → `config.py`   |

### 6B. LCD (I²C) — `hardware/lcd_service.py`

The low-level driver (`I2CLCD`) is partly written: SMBus, `_toggle_enable`, `_send_byte`, `send_command`, and `clear` are already there. You finish the two `# TODO:` blocks.

**`_init_lcd`**

- Run the standard HD44780 **4-bit init** sequence using the existing helpers (`_toggle_enable`, `send_command`, `clear`).
- Typical steps: wake the controller (enable toggles), set 4-bit mode, turn display on, entry mode, then clear.
- Lab hint: use the constants already on the class (`LINE_1`, `LINE_2`, etc.) and the command bytes from the course slides or `test_lcd.py` expectations.

**`message(text, line)`**

- Select line 1 or line 2 (`LINE_1` / `LINE_2`).
- Pad or truncate to `self.width` characters.
- Send each character with `_send_byte(..., LCD_CHR)`.

When this works, `python tests/test_lcd.py` passes and the app can show `show_waiting` / `show_result` via `LCDService` (no changes needed in `LCDService` if `I2CLCD` is correct).

### 6C. YOLO — `models/yolo_detector.py` + LCD bee count

**`YoloDroneModel.run`** (main `# TODO`)

You must:

1. Convert `frame_rgb` to the colour layout YOLO expects (OpenCV BGR is usual).
2. Call `self._model.predict(...)` with `conf`, `iou`, and a sensible `imgsz` (e.g. 640).
3. Build **`annotated_rgb`** from the result plot (remember RGB vs BGR when converting back).
4. Read box class IDs from the result; build a **`counts`** dict: class name → number of detections (use `self._model.names`).
5. Return `InferenceResult` with `payload` containing at least `detection_count`, `counts`, `conf`, `iou` (the stub after the `# TODO` shows the expected shape — define `cls_ids`, `counts`, and `annotated_rgb` in your implementation).

**LCD bee count** — `ui/inference_handlers.py` in `run_yolo`

After inference, the handler already reads `counts` from the payload. Change the LCD line so it shows the **bee** class count (key must match your `best.pt` label, e.g. `Bee`), not only total detections. The demo checklist expects a visible bee count after **Run Drone YOLO**.

### 6D. MediaPipe — camera and upload

Pose code is already in the repo. Verify:

1. USB/CSI → preview → **Run Pose Detection**
2. Upload an image with a person → **Run Pose Detection**

### 6E. GPIO button (BCM 20)

| Action          | Behaviour                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------- |
| **Short press** | Run the model selected under **GPIO short press runs** (YOLO or Pose) when a frame is available |
| **Hold ~2 s**   | Shutdown (same as UI shutdown button)                                                           |

**Already wired for you:** `GpioPlatform` poll loop, `start_gpio()`, `RuntimeSnapshot`, `gr.Timer` → `dispatch_gpio_inference`, model tab + **GPIO short press runs** radio in `ui/model_section.py`.

**Your `# TODO` in `ui/dashboard.py`**

- `on_short_press` is `None` in the student repo. Connect it to the handler that **only sets a flag** (does not run YOLO inside the GPIO thread): use `inference.on_gpio_short_press`.
- Hold is already `inference.shutdown_now` — but shutdown only works after you implement **`request_sudo_poweroff`** in `hardware/network.py` (see below).

**`hardware/network.py` — `request_sudo_poweroff`**

- Start `sudo poweroff` with `subprocess.Popen` so the process is detached (`start_new_session=True`, redirect stdin/stdout/stderr to `DEVNULL` so the app does not hang).
- Requires passwordless sudo for `poweroff` on the Pi (see [4_Production.md](4_Production.md) / Appendix).

Set **GPIO short press runs** before testing. After a GPIO run, the UI switches to the matching model tab so the result image is visible.

More hardware (buzzer, 7-segment, NeoPixel): [`RPi/docs/hardware-extensions.md`](../RPi/docs/hardware-extensions.md).

### 6E-bis. Optional

- **7-segment (Optional for Kickoff)** (`hardware/seven_segment.py`): `# TODO` GPIO setup for the 74HC595 pins and `shift_out_16bit` — see [hardware-extensions.md](../RPi/docs/hardware-extensions.md) to show drone count after YOLO.
- LCD IP at startup: `hardware/network.py` + `tests/test_ip.py` (IP wait logic is already implemented).

### 6F. Buzzers (Optional for Kickoff)

| Buzzer  | BCM    | Type                       |
| ------- | ------ | -------------------------- |
| Passive | **4**  | PWM (`hardware/buzzer.py`) |
| Active  | **12** | Digital                    |

Pins in `config.py`. Commands:

```bash
cd RPi
python tests/test_buzzer.py
python tests/test_buzzer.py --target passive
python tests/test_buzzer.py --target active
```

---

## Step 7: Demo checklist

Show on **your** Pi and **your** repo.

### AI / Gradio

1. MediaPipe + **camera**
2. MediaPipe + **upload**
3. YOLO + **upload** (needs **6C** `yolo_detector.py` complete)
4. LCD **bee count** after YOLO (needs **6B** + **6C** LCD line in `inference_handlers.py`)
5. **GPIO short press** runs the model selected under **GPIO short press runs** (needs **6E**)

### Database and API

6. `docker compose ps` — all three containers up
7. `http://<pi-ip>:8000/db-health` — connected
8. pgAdmin — `projectone` visible

| #   | Check                        |
| --- | ---------------------------- |
| 1   | Pose + camera                |
| 2   | Pose + upload                |
| 3   | YOLO + upload                |
| 4   | LCD bee count                |
| 5   | GPIO short → YOLO or Pose    |
| 6   | `docker compose ps` (all up) |
| 7   | FastAPI `/db-health`         |
| 8   | pgAdmin → `projectone`       |

---

## Submit

- Submit the GitHub Classroom repo in LeHo.
- Pass the demo checklist (Step 7).

---

## After kickoff

- Continue with [3_Next_steps.md](3_Next_steps.md) (home Wi‑Fi, training, extensions).
- Complete [PD.md](../PD.md).
- Do not commit `~/.venv` or any training data.
- Autostart for demos: [4_Production.md](4_Production.md) (after next steps).

---

You cloned the repo, ran YOLO and MediaPipe, started Postgres + pgAdmin + FastAPI, and implemented the hardware tasks. Continue with Project One.
