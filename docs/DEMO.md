# Demo runbook

## Must work end to end
Camera (RTSP) → station (YOLO, real hardware) → buzzer, LEDs, LCD alert → data-api → Postgres → Gradio pages.

## Demo script (~6 min)
1. **About / Onboarding** (30 s): problem, target users, the workflow strip.
2. **Operating** (2 min): live camera; start detection; a person in frame gets boxes and a class
   (standing / sitting / crawling / lying / partially visible); buzzer, detection LED and LCD react;
   change the confidence threshold.
3. **Gas / temperature alert** (45 s): live readings and the alert banner when a threshold is crossed.
   Only if the gas sensor passed the pre-check — rehearse it first.
4. **Data logs** (45 s): filter by class, export CSV.
5. **Statistics** (45 s): detections over time, class distribution, time filter.
6. **Debugging** (45 s): Run All hardware tests; component status.
7. **Architecture** (1 min): README diagram; four containers; why the camera reader is non-blocking.

## First deploy on the Pi (from ~/rescue_scout)
1. `cp ~/backups/env-original .env && chmod 600 .env`
2. Weights: `mkdir -p backend/model/weights && cp ~/backups/best.pt backend/model/weights/best.pt`
3. In `.env`, set `MODEL_DIR=./backend/model/weights`. The original `.env` points at a training-run folder that does not exist in this checkout, which would mount an empty folder and leave the detector without weights.
4. `docker compose -f compose.yaml -f compose.pi.yaml up -d --build`. This builds `0.2.0` images; the original's `0.1.0` images stay untouched for the fallback.

## T-24 h checklist
- [ ] `docker compose ps`: all services healthy
- [ ] `ip route get <camera-ip>` goes via `wlan0`, not a `br-*` Docker bridge
- [ ] `curl -s http://127.0.0.1:8001/api/cameras` shows camera `detection` with `"status": "ok"` (the frame endpoint returns 200 even with no signal)
- [ ] no `gas poll error` in the last minute of station logs
- [ ] Debugging page: Run All is green
- [ ] reboot once; the kiosk opens http://localhost:7860 on its own
- [ ] free disk above 5 GB (`df -h /`)
- [ ] screen recording of a full rehearsal saved on the laptop (last-resort fallback)
- [ ] laptop with the repo and `docker compose up` (mock mode) tested

## Fallbacks (in order)
Do not use the Reboot button on the Debugging page; the endpoint currently does nothing.

| Failure | Fallback | Command |
|---|---|---|
| Camera down | Restart station; check route and hotspot | `docker compose -f compose.yaml -f compose.pi.yaml restart station` |
| Camera still down | Video file as source — **unverified, test before relying on it** | set `RTSP_CAMERA_1_URL=/models/demo.mp4`, restart station |
| Gas sensor down | Skip step 3; show its status on the Debugging page | — |
| This build misbehaves | Switch back to the frozen original build | see `~/backups/RESTORE.txt` on the Pi |
| Pi dead | Laptop, everything mocked | `cp .env.example .env && docker compose up -d --build`, then http://localhost:7860 |
| Everything fails | Play the rehearsal recording | — |
