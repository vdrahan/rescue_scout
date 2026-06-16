"""Synthetic detector — plausible frames + detections, no ML dependencies."""

from __future__ import annotations

import random

import numpy as np

from ..imaging import annotate
from .base import Detection, DetectionResult, Detector
from .classes import CLASSES


class MockDetector(Detector):
    name = "mock"

    def __init__(self, width: int = 640, height: int = 480, seed: int | None = None):
        self._w = width
        self._h = height
        self._rng = random.Random(seed)
        self._tick = 0

    def infer(self, frame: np.ndarray, conf: float, iou: float) -> DetectionResult:
        self._tick += 1
        h, w = frame.shape[:2]
        detections: list[Detection] = []

        # 0-2 detections, drifting horizontally so the demo looks alive.
        n = self._rng.choices([0, 1, 2], weights=[3, 5, 2])[0]
        for _ in range(n):
            confidence = round(self._rng.uniform(max(conf, 0.4), 0.97), 2)
            cls = self._rng.choice(CLASSES)
            bw = self._rng.randint(int(w * 0.12), int(w * 0.28))
            bh = self._rng.randint(int(h * 0.30), int(h * 0.55))
            drift = (self._tick * 7) % max(1, w - bw)
            x1 = (self._rng.randint(0, max(1, w - bw)) + drift) % max(1, w - bw)
            y1 = self._rng.randint(0, max(1, h - bh))
            detections.append(
                Detection(cls, confidence, (x1, y1, x1 + bw, y1 + bh))
            )

        annotated = annotate(frame, detections)
        return DetectionResult(frame=annotated, detections=detections)
