from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from inputs import pick_source_frame
from inputs.base import InputProvider
from models.registry import MODEL_POSE, MODEL_YOLO


@dataclass(frozen=True)
class InferenceSnapshot:
    source_type: str
    latest_capture_rgb: np.ndarray | None
    upload_rgb: np.ndarray | None
    browser_webcam_rgb: np.ndarray | None
    selected_model: str
    yolo_conf: float
    yolo_iou: float
    ai_history: list[dict[str, Any]]
    error_history: list[dict[str, Any]]


class RuntimeSnapshot:
    """Thread-safe mirror of Gradio state for GPIO-triggered inference."""

    def __init__(self, providers: Mapping[str, InputProvider]) -> None:
        self._providers = providers
        self._lock = threading.Lock()
        self._gpio_pending = False
        self._gpio_model: str = MODEL_YOLO
        self.source_type: str = ""
        self.latest_capture_rgb: np.ndarray | None = None
        self.upload_rgb: np.ndarray | None = None
        self.browser_webcam_rgb: np.ndarray | None = None
        self.selected_model: str = MODEL_YOLO
        self.yolo_conf: float = 0.25
        self.yolo_iou: float = 0.45
        self.ai_history: list[dict[str, Any]] = []
        self.error_history: list[dict[str, Any]] = []

    def set_selected_model(self, model: str) -> None:
        with self._lock:
            self.selected_model = model

    def sync_gradio_state(
        self,
        source_type: str,
        latest_capture_rgb: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
        yolo_conf: float,
        yolo_iou: float,
        ai_history: list[dict[str, Any]],
        error_history: list[dict[str, Any]],
    ) -> None:
        """Mirror Gradio frame/history inputs; selected_model is set via tab/radio only."""
        with self._lock:
            self.source_type = source_type
            self.latest_capture_rgb = latest_capture_rgb
            self.upload_rgb = upload_rgb
            self.browser_webcam_rgb = browser_webcam_rgb
            self.yolo_conf = float(yolo_conf)
            self.yolo_iou = float(yolo_iou)
            self.ai_history = ai_history
            self.error_history = error_history

    def _frame_available_locked(self) -> bool:
        try:
            pick_source_frame(
                self._providers,
                self.source_type,
                self.latest_capture_rgb,
                self.upload_rgb,
                self.browser_webcam_rgb,
            )
            return True
        except ValueError:
            return False

    def request_gpio_inference(self) -> bool:
        """GPIO short press: queue run only when the current input has a valid frame."""
        with self._lock:
            if not self._frame_available_locked():
                return False
            self._gpio_pending = True
            self._gpio_model = self.selected_model
            return True

    def take_gpio_model(self) -> str | None:
        """Model frozen at short-press time; clears pending flag."""
        with self._lock:
            if not self._gpio_pending:
                return None
            self._gpio_pending = False
            return self._gpio_model

    def read_inference_snapshot(self) -> InferenceSnapshot:
        with self._lock:
            return InferenceSnapshot(
                source_type=self.source_type,
                latest_capture_rgb=self.latest_capture_rgb,
                upload_rgb=self.upload_rgb,
                browser_webcam_rgb=self.browser_webcam_rgb,
                selected_model=self.selected_model,
                yolo_conf=self.yolo_conf,
                yolo_iou=self.yolo_iou,
                ai_history=list(self.ai_history),
                error_history=list(self.error_history),
            )
