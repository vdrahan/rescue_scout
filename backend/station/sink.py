"""Best-effort event sink: ships detections/sensor/status events to the data-api.

Runs its own worker thread + bounded queue so the detection loop never blocks on
HTTP. Failures are logged and dropped — the live system keeps running even when
the data-api or database is down. The station holds no DB credentials.
"""

from __future__ import annotations

import queue
import threading
from typing import Any

import httpx

from .config import Settings
from .detection.classes import normalize
from .logging_conf import get_logger

log = get_logger(__name__)


class DataApiSink:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._url = settings.api_url.rstrip("/")
        self._q: "queue.Queue[tuple[str, dict]]" = queue.Queue(maxsize=settings.sink_queue_size)
        self._client: httpx.Client | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._class_map: dict[str, int] = {}
        self._sensor_map: dict[str, int] = {}
        self.connected = False

    # -- lifecycle ----------------------------------------------------------
    def start(self) -> None:
        if not self._settings.sink_enabled:
            log.info("Event sink disabled (SINK_ENABLED=false)")
            return
        self._client = httpx.Client(base_url=self._url, timeout=4.0)
        self._refresh_maps()
        self._thread = threading.Thread(target=self._worker, name="sink", daemon=True)
        self._thread.start()
        log.info("Event sink started -> %s", self._url)

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._client is not None:
            self._client.close()

    # -- public enqueue API (called from the detection worker) --------------
    def record_detection(self, class_name: str, confidence: float, people_count: int = 1) -> None:
        self._enqueue("detection", {
            "class_name": normalize(class_name),
            "confidence": round(confidence * 100.0, 2),  # DB stores 0-100
            "people_count": people_count,
        })

    def record_gas(self, ppm: float, dangerous: bool, message: str = "") -> None:
        if not message:
            if ppm >= 250:
                message = "Critical — do not enter"
            elif ppm >= 200:
                message = "Warning — use caution"
            else:
                message = "Normal — safe to proceed"
        self._enqueue("sensor", {
            "sensor_name": "gas", "value": round(ppm, 2),
            "message": message,
            "is_dangerous": dangerous,
        })

    def count_dangerous(self, sensor_name: str) -> int:
        """Return total dangerous reading count for a sensor from the data-api."""
        if self._client is None:
            return 0
        try:
            r = self._client.get(
                "/sensor-readings/count",
                params={"sensor_name": sensor_name, "dangerous_only": True},
                timeout=2.0,
            )
            return int(r.json().get("count", 0))
        except Exception:  # noqa: BLE001
            return 0

    def record_temperature(self, celsius: float, dangerous: bool) -> None:
        self._enqueue("sensor", {
            "sensor_name": "temperature", "value": round(celsius, 1),
            "message": f"High temperature: {celsius:.0f}°C" if dangerous else f"Temperature: {celsius:.0f}°C",
            "is_dangerous": dangerous,
        })

    def record_event(self, event_type: str, importance: str = "INFO", message: str = "") -> None:
        self._enqueue("event", {
            "event_type": event_type, "importance_level": importance, "message": message,
        })

    # -- internals ----------------------------------------------------------
    def _enqueue(self, kind: str, payload: dict) -> None:
        if not self._settings.sink_enabled:
            return
        try:
            self._q.put_nowait((kind, payload))
        except queue.Full:
            log.debug("sink queue full, dropping %s event", kind)

    def _refresh_maps(self) -> None:
        if self._client is None:
            return
        self._class_map = self._fetch_map("/detection-classes", "class_name", "class_id")
        self._sensor_map = self._fetch_map("/sensors", "sensor_name", "sensor_id")
        self.connected = bool(self._class_map)

    def _fetch_map(self, path: str, name_key: str, id_key: str) -> dict[str, int]:
        try:
            resp = self._client.get(path)
            resp.raise_for_status()
            return {row[name_key]: row[id_key] for row in resp.json()}
        except Exception as exc:  # noqa: BLE001
            log.warning("could not load %s map: %s", path, exc)
            return {}

    def _worker(self) -> None:
        handlers = {
            "detection": self._post_detection,
            "sensor": self._post_sensor,
            "event": self._post_event,
        }
        while not self._stop.is_set():
            try:
                kind, payload = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            handler = handlers.get(kind)
            if handler is None:
                continue
            try:
                handler(payload)
                self.connected = True
            except Exception as exc:  # noqa: BLE001
                self.connected = False
                log.warning("sink failed to post %s: %s", kind, exc)

    def _post_detection(self, payload: dict) -> None:
        class_id = self._resolve_class(payload["class_name"])
        if class_id is None:
            log.warning("no class_id for %s, skipping detection", payload["class_name"])
            return
        self._post("/detections", {
            "class_id": class_id,
            "people_count": payload["people_count"],
            "confidence": payload["confidence"],
        })

    def _post_sensor(self, payload: dict) -> None:
        sensor_id = self._resolve_sensor(payload["sensor_name"])
        if sensor_id is None:
            log.warning("no sensor_id for %s, skipping reading", payload["sensor_name"])
            return
        self._post("/sensor-readings", {
            "sensor_id": sensor_id,
            "value": payload["value"],
            "message": payload["message"],
            "is_dangerous": payload["is_dangerous"],
        })

    def _post_event(self, payload: dict) -> None:
        self._post("/events", payload)

    def _resolve_class(self, name: str) -> int | None:
        class_id = self._class_map.get(name)
        if class_id is None:
            self._refresh_maps()  # data-api may have started after the station
            class_id = self._class_map.get(name)
        return class_id

    def _resolve_sensor(self, name: str) -> int | None:
        sensor_id = self._sensor_map.get(name)
        if sensor_id is None:
            self._refresh_maps()
            sensor_id = self._sensor_map.get(name)
        return sensor_id

    def _post(self, path: str, body: dict[str, Any]) -> None:
        assert self._client is not None
        resp = self._client.post(path, json=body)
        resp.raise_for_status()
