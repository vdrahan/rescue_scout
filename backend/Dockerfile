ARG PYTHON_VERSION=3.12.11-slim-bookworm

FROM python:${PYTHON_VERSION} AS builder

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgomp1 \
        libgl1 \
        libxcb1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser

COPY --from=builder /root/.local /home/appuser/.local

ENV PATH="/home/appuser/.local/bin:$PATH"
ENV GRADIO_SERVER_NAME=0.0.0.0

COPY --chown=appuser:appuser backend/ ./

ARG FRONTEND_PORT=7860
ENV FRONTEND_PORT=${FRONTEND_PORT}
ENV GRADIO_SERVER_PORT=${FRONTEND_PORT}

EXPOSE ${FRONTEND_PORT}

USER appuser

CMD ["sh", "-c", "python model/model.py"]