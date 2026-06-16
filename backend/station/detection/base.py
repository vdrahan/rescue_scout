"""Shared detection types and the Detector interface.

Frames are plain ``numpy`` uint8 RGB arrays so they can be produced and JPEG
encoded with Pillow alone — no OpenCV needed in mock mode.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from .classes import priority_for


@dataclass
class Detection:
    class_name: str
    confidence: float  # 0.0 - 1.0
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2

    @property
    def priority(self) -> str:
        return priority_for(self.class_name)

    def to_dict(self) -> dict:
        return {
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": list(self.bbox),
            "priority": self.priority,
        }


@dataclass
class DetectionResult:
    frame: np.ndarray  # annotated RGB frame
    detections: list[Detection] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class Detector(abc.ABC):
    """A model that turns a frame into an annotated frame + detections."""

    #: implementation label, e.g. "yolo" or "mock"
    name: str = "detector"

    @abc.abstractmethod
    def infer(self, frame: np.ndarray, conf: float, iou: float) -> DetectionResult:
        ...

    def warmup(self) -> None:  # optional override
        return None

    def close(self) -> None:  # optional override
        return None
