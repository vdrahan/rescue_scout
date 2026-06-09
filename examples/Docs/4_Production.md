# 4. Production

We autostart the Gradio app for demos and production. First confirm everything works on the **real Pi IP** — especially after home Wi‑Fi — then enable systemd.

**Lab Ethernet** often uses `192.168.168.167`. **That address is not valid on home Wi‑Fi.** Do not hardcode it in scripts, bookmarks, or the systemd unit.

Complete [3_Next_steps.md](3_Next_steps.md) (Wi‑Fi, training, extending the app) before locking in production autostart.

---

## Step 1 — Find the Pi IP and test services

Connect the Pi to Wi‑Fi if needed ([3_Next_steps.md](3_Next_steps.md) or [2_Kickoff.md](2_Kickoff.md)).

```bash
hostname -I
ip -4 addr show wlan0
```

Pick the LAN address your laptop can reach. From the laptop (same network), open:

| Service        | URL                             |
| -------------- | ------------------------------- |
| Gradio         | `http://<pi-ip>:7860`           |
| FastAPI health | `http://<pi-ip>:8000/health`    |
| FastAPI DB     | `http://<pi-ip>:8000/db-health` |
| pgAdmin        | `http://<pi-ip>:5050`           |

Run the app manually before enabling autostart:

```bash
cd ~/2025-2026-ProjectOne-CTAI-<yourname>/RPi
source ~/.venv/bin/activate
python app.py
```

Stop any old site service while debugging:

```bash
sudo systemctl stop p1.service    # if present
sudo systemctl stop myproject.service
```

---

## Step 2 — systemd unit for `app.py`

Create `myproject.service` on the Pi:

```ini
[Unit]
Description=ProjectOne Gradio app
After=network.target
Wants=network.target

[Service]
ExecStart=/home/student/.venv/bin/python -u /home/student/<name_of_your_repo>/RPi/app.py
WorkingDirectory=/home/student/<name_of_your_repo>/RPi
StandardOutput=journal
StandardError=journal
Restart=always
User=student

[Install]
WantedBy=multi-user.target
```

Replace `<name_of_your_repo>` with `2025-2026-ProjectOne-CTAI-<yourname>`.

Install and test:

```bash
sudo cp myproject.service /etc/systemd/system/myproject.service
sudo systemctl daemon-reload
sudo systemctl start myproject.service
sudo systemctl status myproject.service
```

Open Gradio at `http://<pi-ip>:7860` again (Wi‑Fi IP, not `192.168.168.167` unless you are on lab Ethernet).

Enable on boot:

```bash
sudo systemctl enable myproject.service
```

Logs:

```bash
sudo journalctl -u myproject.service -f
```

Stop / disable:

```bash
sudo systemctl stop myproject.service
sudo systemctl disable myproject.service
```

---

## Step 3 — Docker stack at boot (optional)

The database stack is separate from Gradio. To start Postgres, pgAdmin, and the API on boot:

```bash
cd ~/2025-2026-ProjectOne-CTAI-<yourname>/RPi/api
docker compose up -d
```

For a systemd unit, set `WorkingDirectory` to `RPi/api`, `ExecStart=/usr/bin/docker compose up -d`, and add `After=docker.service` / `Requires=docker.service`. Ensure `.env` exists before enable.

Test pgAdmin and `/db-health` on `http://<pi-ip>:...` after reboot.

---

## Step 4 — Shutdown button (optional)

The UI may call `sudo poweroff`. Allow passwordless shutdown once:

```bash
sudo visudo
```

Add:

```text
student ALL=(ALL) NOPASSWD: /sbin/poweroff, /usr/sbin/poweroff
```

---

## Checklist before presenting

- [ ] `hostname -I` on the presentation network (Wi‑Fi or lab)
- [ ] Gradio loads on `http://<pi-ip>:7860`
- [ ] `docker compose ps` OK if the DB demo is required
- [ ] `http://<pi-ip>:8000/db-health` connected
- [ ] `systemctl status myproject.service` active after reboot test

---

See also: [Appendix.md](Appendix.md) (port forwarding, `p1.service`, upgrades).
