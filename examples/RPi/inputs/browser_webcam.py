from __future__ import annotations

from typing import Any

import gradio as gr
import numpy as np

from .base import CameraCaptureResult, InputProvider, InputSourceMeta, SourceUiVisibility
from .registry import INPUT_BROWSER_WEBCAM, SPINNER_FRAMES


class BrowserWebcamInput(InputProvider):
    meta = InputSourceMeta(source_id=INPUT_BROWSER_WEBCAM, label="Browser webcam")

    def ui_visibility(self) -> SourceUiVisibility:
        return SourceUiVisibility(
            show_note=False,
            note_markdown="",
            show_upload=False,
            show_browser_webcam=True,
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
        del resolution, target_fps
        if perf_state is None:
            perf_state = {"spinner_idx": -1, "label": SPINNER_FRAMES[0]}
        if browser_webcam is None:
            return CameraCaptureResult(
                preview_update=gr.update(),
                frame_rgb=latest_capture,
                perf_state=perf_state,
                status_text="Waiting for browser webcam frame.",
                refresh_latest=False,
            )
        spinner_idx = (int(perf_state.get("spinner_idx", -1)) + 1) % len(SPINNER_FRAMES)
        label = SPINNER_FRAMES[spinner_idx]
        next_perf = {"spinner_idx": spinner_idx, "label": label}
        preview_update = gr.update(value=browser_webcam, label=f"{label} Camera feed")
        return CameraCaptureResult(
            preview_update=preview_update,
            frame_rgb=latest_capture,
            perf_state=next_perf,
            status_text="Browser webcam synced.",
            refresh_latest=False,
        )

    def pick_frame(
        self,
        latest_capture: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
    ) -> np.ndarray:
        del latest_capture, upload_rgb
        if browser_webcam_rgb is None:
            raise ValueError("Capture a browser webcam image first.")
        return browser_webcam_rgb
