# `RPi/api` — Docker stack (Postgres + pgAdmin + FastAPI)

Kickoff database and API layer. The Gradio app in `../` runs separately (`python app.py`); this stack is for **Docker + DB + FastAPI** as required by Project One.

## Quick start

On the **prepared image**, `postgres:16-alpine`, `dpage/pgadmin4:latest`, and `python:3.11-slim-bookworm` are **pre-pulled**. You still **build** the API image from `Dockerfile` (see [`Docs/2_Kickoff.md`](../../Docs/2_Kickoff.md) Step 4).

```bash
cd RPi/api
cp .env.example .env
docker compose up -d --build
docker compose ps
```

| Service      | URL (Pi IP `192.168.168.167`)         |
| ------------ | ------------------------------------- |
| FastAPI docs | http://192.168.168.167:8000/docs      |
| API health   | http://192.168.168.167:8000/health    |
| DB health    | http://192.168.168.167:8000/db-health |
| pgAdmin      | http://192.168.168.167:5050           |

## Files

| File                 | Purpose                            |
| -------------------- | ---------------------------------- |
| `docker-compose.yml` | postgres, pgadmin, api services    |
| `.env.example`       | Copy to `.env` (not committed)     |
| `main.py`            | FastAPI `/health` and `/db-health` |
| `Dockerfile`         | API container image                |

See [`Docs/2_Kickoff.md`](../../Docs/2_Kickoff.md) Step 4. Image build: [`Docs/0_Image_preparation.md`](../../Docs/0_Image_preparation.md) §7–8.
