from __future__ import annotations

from typing import Any

import gradio as gr
import numpy as np

from .base import CameraCaptureResult, InputProvider, InputSourceMeta, SourceUiVisibility
from .registry import INPUT_UPLOAD, SPINNER_FRAMES


class UploadInput(InputProvider):
    meta = InputSourceMeta(source_id=INPUT_UPLOAD, label="Browser upload")

    def ui_visibility(self) -> SourceUiVisibility:
        return SourceUiVisibility(
            show_note=False,
            note_markdown="",
            show_upload=True,
            show_browser_webcam=False,
            show_preview=False,
            show_camera_status=False,
            show_resolution_fps_controls=False,
        )

    def sync_preview(
        self,
        resolution: str,
        target_fps: float,
        browser_webcam: np.ndarray | None,
        latest_capture: np.ndarray | None,
        perf_state: dict[str, Any] | None,
    ) -> CameraCaptureResult:
        del resolution, target_fps, browser_webcam
        return CameraCaptureResult(
            preview_update=gr.update(),
            frame_rgb=latest_capture,
            perf_state=perf_state if perf_state is not None else {"spinner_idx": -1, "label": SPINNER_FRAMES[0]},
            status_text="Preview idle.",
            refresh_latest=False,
        )

    def pick_frame(
        self,
        latest_capture: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
    ) -> np.ndarray:
        del latest_capture, browser_webcam_rgb
        if upload_rgb is None:
            raise ValueError("Upload an image first.")
        return upload_rgb
