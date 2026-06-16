"""Real YOLOv26 detector.

Heavy imports (torch / ultralytics / OpenCV) happen lazily inside ``__init__``
so this module can be imported in mock mode without those packages installed.
Refactored from the proven inference logic in ``backend/model/model.py``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..logging_conf import get_logger
from .base import Detection, DetectionResult, Detector
from .classes import normalize

log = get_logger(__name__)


class YoloDetector(Detector):
    name = "yolo"

    def __init__(self, model_path: str, img_size: int = 320, max_det: int = 20):
        # Imported here on purpose — only real mode pays the cost.
        import torch  # noqa: WPS433
        from ultralytics import YOLO  # noqa: WPS433

        self._img_size = img_size
        self._max_det = max_det
        self._device = 0 if torch.cuda.is_available() else "cpu"
        self._half = bool(torch.cuda.is_available())

        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"YOLOv26 weights not found: {path}")

        log.info("Loading YOLOv26 weights from %s (device=%s)", path, self._device)
        self._model = YOLO(str(path))  # loaded ONCE
        self._names = dict(self._model.names)

    def warmup(self) -> None:
        dummy = np.zeros((self._img_size, self._img_size, 3), dtype=np.uint8)
        self.infer(dummy, conf=0.25, iou=0.45)

    def infer(self, frame: np.ndarray, conf: float, iou: float) -> DetectionResult:
        results = self._model.predict(
            source=frame,
            conf=conf,
            iou=iou,
            imgsz=self._img_size,
            device=self._device,
            half=self._half,
            max_det=self._max_det,
            agnostic_nms=True,
            verbose=False,
        )
        detections: list[Detection] = []
        annotated = frame
        for r in results:
            # r.plot() returns a BGR array; flip to RGB for our pipeline.
            annotated = r.plot()[..., ::-1].copy()
            for box in r.boxes:
                cls_idx = int(box.cls[0])
                name = normalize(self._names.get(cls_idx, str(cls_idx)))
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = (int(v) for v in box.xyxy[0])
                detections.append(Detection(name, confidence, (x1, y1, x2, y2)))
        return DetectionResult(frame=annotated, detections=detections)

    def close(self) -> None:
        self._model = None
