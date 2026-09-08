ARG PYTHON_VERSION=3.12.11-slim-bookworm

FROM python:${PYTHON_VERSION} AS builder

WORKDIR /app

COPY backend/api/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /root/.local /home/appuser/.local

ENV PATH="/home/appuser/.local/bin:$PATH"

COPY --chown=appuser:appuser backend/api/ ./api/

ARG API_PORT=8000
ENV API_PORT=${API_PORT}

EXPOSE ${API_PORT}

USER appuser

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${API_PORT}"]
