ARG PYTHON_VERSION=3.12.11-slim-bookworm

# ---- builder ----------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS builder

WORKDIR /app

# STATION_PROFILE: "base" (mock, light) or "full" (real detection + hardware).
ARG STATION_PROFILE=base

# Copy dependency files first so layers cache well.
COPY backend/station/requirements.txt ./requirements.txt
COPY backend/station/requirements-ml.txt ./requirements-ml.txt
COPY backend/station/requirements-hw.txt ./requirements-hw.txt

RUN pip install --no-cache-dir --user -r requirements.txt \
    && if [ "$STATION_PROFILE" = "full" ]; then \
         pip install --no-cache-dir --user -r requirements-ml.txt -r requirements-hw.txt; \
       fi

# ---- runtime ----------------------------------------------------------------
FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG STATION_PROFILE=base

# System libs only needed by the real ML/OpenCV stack.
RUN if [ "$STATION_PROFILE" = "full" ]; then \
        apt-get update \
        && apt-get install -y --no-install-recommends \
            libglib2.0-0 libgomp1 libgl1 libxcb1 \
        && rm -rf /var/lib/apt/lists/*; \
    fi

RUN useradd --create-home appuser

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH="/home/appuser/.local/bin:$PATH"

# Package lives at /app/station so `python -m station` resolves.
COPY --chown=appuser:appuser backend/station/ ./station/

ARG STATION_PORT=8000
ENV STATION_PORT=${STATION_PORT}
EXPOSE ${STATION_PORT}

USER appuser

# Exec-form CMD; port + modes come from the environment via pydantic-settings.
CMD ["python", "-m", "station"]
