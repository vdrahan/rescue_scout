# Station service

The realtime "brain" of the RC SAR ground station: it loads the YOLOv26 model
once, runs detection in a background thread, owns the cameras and the Raspberry
Pi hardware (GPIO / sensors), and exposes everything over a small FastAPI app.

Everything runs in a dependency-light **mock** mode by default, so the whole
system works on a laptop with no torch, OpenCV, GPIO, ADS1115, DHT or Pi
libraries installed.

## Layout

```
station/
  config.py          pydantic-settings config (all env vars)
  logging_conf.py    logging setup
  main.py            FastAPI app + lifespan wiring
  __main__.py        python -m station entrypoint
  sink.py            best-effort event POSTs to the data-api
  imaging.py         Pillow-only frame helpers (no cv2)
  api/               health, status, detection, cameras, hardware routers
  detection/         classes, mock + yolo detectors, registry, worker service
  cameras/           mock + rtsp/usb sources, manager
  hardware/          device interfaces, mock + real (gpiozero/ADS1115/DHT/LCD), manager
  tests/             mock detection, mock hardware, API smoke tests
```

## Modes

| Env | Values | Meaning |
|-----|--------|---------|
| `DETECTION_MODE` | `mock` \| `real` \| `auto` | `auto` = real if torch + weights present, else mock |
| `HARDWARE_MODE`  | `mock` \| `real` \| `auto` | `auto` = real if Pi libraries present, else mock |

Any real-mode failure (missing weights, camera, library) degrades to mock and is
reported in `GET /api/status` (`degraded: true`), never crashing the API.

## Run locally (mock, no extra deps beyond requirements.txt)

```bash
cd backend
pip install -r station/requirements.txt
STATION_PORT=8001 DETECTION_MODE=mock HARDWARE_MODE=mock python -m station
# open http://localhost:8001/docs
```

## Tests

```bash
cd backend
pip install -r station/requirements.txt pytest
pytest station/tests -q
```

## Endpoints

```
GET  /health
GET  /api/status
POST /api/detection/start | /stop
GET  /api/detection/latest
GET  /api/detection/config        POST /api/detection/config
GET  /api/cameras                 POST /api/cameras/active
GET  /api/cameras/{id}/frame      (image/jpeg, annotated when detection is on)
GET  /api/hardware/status
POST /api/hardware/test/{component}
```

See the repo root `README.md` for the full system run instructions (Docker
Compose + Raspberry Pi deployment).
