from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from .base import InferenceResult


class YoloDroneModel:
    def __init__(self, model_path: Path) -> None:
        self._model = YOLO(str(model_path))

    def run(self, frame_rgb: np.ndarray, conf: float, iou: float) -> InferenceResult:
        
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        results = self._model.predict(frame_bgr, conf=conf, iou=iou, imgsz=640)
        result = results[0]

        cls_ids = result.boxes.cls.cpu().numpy().astype(int).tolist()
        counts = {}

        for cls_id in cls_ids:
            class_name = self._model.names[cls_id]
            counts[class_name] = counts.get(class_name, 0) + 1
        annotated_bgr = result.plot()
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

        payload = {
            "model": "best.pt",
            "detection_count": len(cls_ids),
            "counts": counts,
            "conf": float(conf),
            "iou": float(iou),
        }
        return InferenceResult(
            annotated_rgb=annotated_rgb,
            payload=payload,
            status_text=f"YOLO done. detections={len(cls_ids)}",
        )
