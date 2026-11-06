"""Camera source interface."""

from __future__ import annotations

import abc

import numpy as np


class CameraSource(abc.ABC):
    def __init__(self, cam_id: str, name: str, kind: str):
        self.id = cam_id
        self.name = name
        self.kind = kind  # "mock" | "rtsp" | "usb"
        self.status = "unknown"  # "ok" | "error" | "unknown"
        self.last_error = ""

    @abc.abstractmethod
    def read(self) -> np.ndarray | None:
        """Return the latest frame as an RGB uint8 array, or None on failure."""

    def advance(self) -> bool:
        """Consume the next frame without handing it out; False if the camera is down.

        A live stream must be read at the rate it is produced or old frames queue up.
        Sources where converting a frame is costly override this to skip the conversion."""
        return self.read() is not None

    def close(self) -> None:
        return None

    def info(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.kind,
            "status": self.status,
            "last_error": self.last_error,
        }
