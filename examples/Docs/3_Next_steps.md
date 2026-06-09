# 3. Next steps

After [2_Kickoff.md](2_Kickoff.md), continue Project One at home: network the Pi, train on your laptop, deploy weights to the Pi, and extend the app and hardware.

**Final autostart and demo networking:** see [4_Production.md](4_Production.md).

---

## 1. Connect the Pi at home

Lab Ethernet often uses `192.168.168.167`. At home you need Wi‑Fi and the **new IP** for SSH, VS Code, VNC, and the browser.

### 1.1 Wi‑Fi with `nmcli` (recommended)

On the Pi (SSH or VS Code terminal):

```bash
nmcli dev wifi list
sudo nmcli dev wifi connect "WIFI-name" password "WIFI-pass"
hostname -I
```

Use that IP everywhere instead of `192.168.168.167`:

- SSH: `ssh student@<pi-home-ip> -A`
- Gradio: `http://<pi-home-ip>:7860`
- FastAPI: `http://<pi-home-ip>:8000`
- pgAdmin: `http://<pi-home-ip>:5050`

The Pi remembers saved networks. To add another SSID later, run `nmcli` again with the other name and password.

### 1.2 Wi‑Fi with `raspi-config`

```bash
sudo raspi-config
```

**System Options → Wireless LAN** — enter SSID and passphrase, finish, reboot if asked.

### 1.3 VNC (desktop on the Pi)

VNC is enabled on the prepared image.

1. Note `hostname -I` after Wi‑Fi is up.
2. On the laptop, open a VNC client (RealVNC Viewer, etc.).
3. Connect to `<pi-home-ip>:5900` (or the display number your client expects).
4. Log in as `student` with your Pi password.

Use VNC for `raspi-config`, desktop testing, or wiring checks. Day-to-day coding stays easier over **Remote SSH** in VS Code.

### 1.4 Check connectivity

```bash
ping -c 3 1.1.1.1
```

From the laptop, ping the Pi IP and open `http://<pi-home-ip>:7860` while `python app.py` runs.

More Wi‑Fi options: [Appendix.md](Appendix.md).

---

## 2. Train on the laptop (`Laptop/`)

YOLO training runs on your **laptop** (GPU or CPU), not on the Pi. The repo includes a starter notebook:

- [`Laptop/yolo.ipynb`](../Laptop/yolo.ipynb)

### 2.1 Keep large files out of git

Training creates **datasets**, **runs/**, checkpoints, and caches. Do **not** commit those to GitHub Classroom.

| Location                                    | Purpose                                                                         |
| ------------------------------------------- | ------------------------------------------------------------------------------- |
| [`Laptop/.gitignore`](../Laptop/.gitignore) | Ignores training data and run outputs under `Laptop/`                           |
| Repo root [`.gitignore`](../.gitignore)     | Ignores `.venv`, `.env`, caches — add patterns here if you store data elsewhere |

Typical additions inside `Laptop/.gitignore` (adjust to your layout):

```gitignore
datasets/
runs/
*.cache
wandb/
```

Commit **notebooks**, **scripts**, and **small config** files — not raw image folders or `runs/train/.../weights/`.

### 2.2 Workflow

1. Collect and label images (your own data; see [PD.md](../PD.md)).
2. Train in `Laptop/yolo.ipynb` (or export a `.py` script from the notebook).
3. Export the best weights as **`best.pt`** (Ultralytics naming).
4. Copy only the **`.pt` file** to the Pi (next section) — not the whole `runs/` tree.

---

## 3. Deploy the trained model (`RPi/ai/`)

The kickoff app loads YOLO from:

```text
RPi/ai/best.pt
```

Registered in [`RPi/models/registry.py`](../RPi/models/registry.py):

```python
YoloDroneModel(base_dir / "ai" / "best.pt")
```

### 3.1 On the Pi

```bash
mkdir -p ~/2025-2026-ProjectOne-CTAI-<yourname>/RPi/ai
```

Copy `best.pt` from the laptop (SCP, VS Code drag-and-drop, or `rsync`):

```bash
# From laptop (example)
scp best.pt student@<pi-home-ip>:~/2025-2026-ProjectOne-CTAI-<yourname>/RPi/ai/best.pt
```

### 3.2 Git and file size

- **Small** custom `.pt` files may be committed if Classroom allows and the file stays reasonable (e.g. under 50 MB — check your quota).
- **Large** weights: keep `RPi/ai/best.pt` **local on the Pi** or use **Git LFS**; add `RPi/ai/*.pt` to `.gitignore` if you never want weights in git.

Restart the app after replacing the file:

```bash
cd ~/2025-2026-ProjectOne-CTAI-<yourname>/RPi
python app.py
```

Run **Drone YOLO** in Gradio and confirm class names match your training labels (update LCD / handlers if the class name changed, e.g. `Bee`).

MediaPipe pose assets stay under `RPi/ai/` as well (e.g. `.task` files) when you add or replace them.

---

## 4. Extend the Gradio interface

Structure is documented in [1_Architecture.md](1_Architecture.md).

| Goal                                  | Where to work                                                                      |
| ------------------------------------- | ---------------------------------------------------------------------------------- |
| New input (sensor, file type, camera) | `RPi/inputs/` + [`inputs/registry.py`](../RPi/inputs/registry.py)                  |
| New model tab                         | `RPi/models/` + [`models/registry.py`](../RPi/models/registry.py)                  |
| New UI / pages                        | `RPi/ui/dashboard.py`, `input_section.py`, `model_section.py`, `output_section.py` |
| Run / history logic                   | `RPi/ui/inference_handlers.py`, `input_handlers.py`                                |
| Settings                              | `RPi/config.py`                                                                    |

Add a tab in `model_section.py`, wire a handler in `inference_handlers.py`, and register the model in `build_models()`.

Later: send results to Postgres via `RPi/api/` (FastAPI) instead of only showing them in Gradio.

---

## 5. Extend hardware

| Component           | Code                                            | Smoke test                    |
| ------------------- | ----------------------------------------------- | ----------------------------- |
| LCD                 | `RPi/hardware/lcd_service.py`, `lcd_startup.py` | `python tests/test_lcd.py`    |
| Buzzer              | `RPi/hardware/buzzer.py`                        | `python tests/test_buzzer.py` |
| GPIO / buttons      | `RPi/hardware/gpio.py`, `setup.py` (`start_gpio`) | —                             |
| 7-segment count     | `RPi/hardware/seven_segment.py`                 | wire + `set_number()` in YOLO |
| NeoPixel ring (Pi5) | `pi5-neo` — see extension doc                   | —                             |
| Network / IP on LCD | `RPi/hardware/network.py`                       | `python tests/test_ip.py`     |

Call hardware from `RPi/ui/inference_handlers.py` (LCD, buzzer, segment, NeoPixel) or from `hardware/setup.py` (button callbacks).

Pins and defaults: `RPi/config.py`. Guides: [`RPi/hardware/README.md`](../RPi/hardware/README.md), [`RPi/docs/hardware-extensions.md`](../RPi/docs/hardware-extensions.md).

---

## 6. Then: production

When the app works on your **home Wi‑Fi IP** with your **own model** and hardware:

→ [4_Production.md](4_Production.md) — systemd autostart, optional Docker at boot, presentation checklist.

---

**Also:** complete [PD.md](../PD.md) and use [Feedforward.md](Feedforward.md) for progress conversations.
