"""Synthetic camera — animated scene, always available, no cv2."""

from __future__ import annotations

import numpy as np

from ..imaging import new_scene
from .base import CameraSource


class MockCamera(CameraSource):
    def __init__(self, cam_id: str, name: str, width: int = 640, height: int = 480):
        super().__init__(cam_id, name, kind="mock")
        self._w = width
        self._h = height
        self.status = "ok"
        self.last_error = ""

    def read(self) -> np.ndarray | None:
        return new_scene(self._w, self._h, title=self.name, subtitle="mock feed")
