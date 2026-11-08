# Rescue Scout

Real-time computer vision for search and rescue. A custom-trained YOLO model detects people in five poses (standing, sitting, lying, crawling, partially hidden) on live camera feeds from an RC car, and a ground station raises visual and audio alerts for the operator.

## What it does

- Detects people in difficult positions, not just upright ones, on live RTSP or USB camera streams.
- Serves detection as a FastAPI service, separate from the data API, so the model can be swapped without touching storage or UI.
- Stores detections, events and sensor readings in PostgreSQL.
- Shows live feeds, detection history, statistics and alerts in a Gradio operator dashboard.
- Runs on a Raspberry Pi 5 ground station with an LCD, LEDs, a buzzer and a gas sensor.

## Architecture

```
RC car cameras (RTSP)
        |
        v
  station (FastAPI)  --->  data API (FastAPI)  --->  PostgreSQL
  YOLO detection,           detections, events,
  cameras, GPIO/I2C         sensors, statistics
        |                          ^
        +----------> frontend (Gradio operator dashboard)
```

| Service | Path | Role |
|---|---|---|
| `station` | `backend/station` | Runs detection in a background thread, owns cameras and Raspberry Pi hardware |
| `api` | `backend/api` | REST API over PostgreSQL (repositories, routers, statistics) |
| `frontend` | `frontend` | Gradio dashboard: live view, data logs, statistics, debugging |
| `db` | `backend/database` | Schema, ERD and migrations |

Detection and hardware each run in `mock`, `real` or `auto` mode. Real-mode failures such as missing weights or a missing camera degrade to mock and are reported in `GET /api/status`, so the API never crashes. This is what lets the full stack run on a laptop without a GPU or a Pi.

## Run it

Everything mocked, on any machine with Docker:

```bash
cp .env.example .env      # set POSTGRES_PASSWORD
docker compose up --build
```

- Dashboard: http://localhost:7860
- Data API docs: http://localhost:8000/docs
- Station API docs: http://localhost:8001/docs

Raspberry Pi 5 with real detection and hardware:

```bash
docker compose -f compose.yaml -f compose.pi.yaml up -d --build
```

Local development without Docker and the full environment reference are in [docs/PROJECT_DEFINITION.md](docs/PROJECT_DEFINITION.md#9-running-the-system).

## Tech

Python, YOLO, PyTorch, OpenCV, FastAPI, PostgreSQL, Docker Compose, Gradio, Raspberry Pi 5 (gpiozero, ADS1115, I2C LCD), GitHub Actions, Ruff, pytest.

## Quality

CI runs Ruff and the pytest suites for the API, station and frontend on every push.

## Status and limits

Working end-to-end prototype for supervised demonstrations. It is not a certified emergency-response product.

## Documentation

- [Full project definition](docs/PROJECT_DEFINITION.md): problem, dataset, hardware plan, software design, enhancements, and how AI was used.
- [`examples/`](examples/README.md): original course starter and hardware smoke tests. Not part of the deployed application.

## License

MIT. See [LICENSE](LICENSE).
