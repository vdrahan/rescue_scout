# Appendix

Extra procedures that do not belong in the main 0–3 flow. Nothing here replaces [0_Image_preparation.md](0_Image_preparation.md) or [2_Kickoff.md](2_Kickoff.md) for the standard path.

---

## System upgrade (`apt`)

After a major upgrade, cameras or MediaPipe may break. Re-check [0_Image_preparation.md](0_Image_preparation.md) from the failing step.

```bash
sudo apt update
sudo apt upgrade
```

Confirm with `Y` when prompted and wait until finished.

---

## GPIO — `rpi-lgpio` (kernel ≥ 6.6)

On newer kernels, **RPi.GPIO** edge detection may fail. Use **rpi-lgpio** (same syntax). Do not install both — they conflict on the `RPi` package name.

```bash
sudo apt remove python3-rpi.gpio -y
sudo apt install python3-rpi-lgpio -y
```

In the venv, if `RuntimeError: Failed to add edge detection` appears after other pip installs:

```bash
source ~/.venv/bin/activate
pip uninstall rpi-lgpio RPi.GPIO
pip install rpi-lgpio
```

---

## Home Wi‑Fi — alternative (`wpa_supplicant`)

Prefer `nmcli` from [2_Kickoff.md](2_Kickoff.md). Legacy method:

```bash
sudo -i
wpa_passphrase "<SSID>" "<password>" >> /etc/wpa_supplicant/wpa_supplicant.conf
wpa_cli -i wlan0 reconfigure
exit
```

---

## Gradio browser webcam (HTTPS / localhost)

The **Browser webcam** input needs **localhost** or **HTTPS**. Plain `http://<pi-ip>:7860` from a laptop will not grant `getUserMedia`.

| Approach | Works from laptop? |
|----------|-------------------|
| USB / CSI / upload on Pi | Yes |
| `http://<pi-ip>:7860` + browser webcam | No |
| VS Code port forward → `localhost:7860` | Yes |
| SSH `-L 7860:127.0.0.1:7860` then `http://127.0.0.1:7860` | Yes |
| HTTPS tunnel (e.g. Cloudflare) | Yes |

See [1_Architecture.md](1_Architecture.md) (input sources).

---

## Reference repo — optional student strip

When maintaining the kickoff reference repo, these areas are often left for students to complete:

| Area | Students implement (`# TODO:` in repo) |
|------|----------------------------------------|
| USB camera | `inputs/usb_camera.py`; `list_cameras.py` → `config.camera_device` |
| CSI camera | `inputs/csi_camera.py` |
| LCD | `I2CLCD._init_lcd` + `I2CLCD.message` in `hardware/lcd_service.py` |
| YOLO | `YoloDroneModel.run` in `models/yolo_detector.py` |
| YOLO LCD bee count | `ui/inference_handlers.py` `run_yolo` |
| GPIO short press | `ui/dashboard.py` → `on_short_press` → `on_gpio_short_press` |
| Shutdown | `hardware/network.py` → `request_sudo_poweroff` |
| 7-segment (optional) | `hardware/seven_segment.py` |
