from __future__ import annotations

from typing import Any

import gradio as gr
import numpy as np

from inputs import HARDWARE_PREVIEW_SOURCES
from ui.context import AppContext


class InputHandlers:
    def __init__(self, ctx: AppContext) -> None:
        self._ctx = ctx

    def sync_video_preview(
        self,
        resolution: str,
        source_type: str,
        browser_webcam: np.ndarray | None,
        latest_capture_frame: np.ndarray | None,
        perf_state: dict[str, Any],
        target_fps: float,
    ):
        provider = self._ctx.providers[source_type]
        result = provider.sync_preview(
            resolution, target_fps, browser_webcam, latest_capture_frame, perf_state
        )
        if source_type in HARDWARE_PREVIEW_SOURCES:
            if result.frame_rgb is None:
                self._ctx.lcd.show_result("camera error")
            else:
                self._ctx.lcd.show_waiting()
        next_latest = result.frame_rgb if result.refresh_latest else latest_capture_frame
        return result.preview_update, result.status_text, next_latest, result.perf_state

    @staticmethod
    def timer_interval_update(fps: float):
        safe_fps = max(1.0, float(fps))
        return gr.update(value=1.0 / safe_fps)

    def source_visibility(self, source_type: str):
        v = self._ctx.providers[source_type].ui_visibility()
        return (
            gr.update(visible=v.show_note, value=v.note_markdown),
            gr.update(visible=v.show_upload),
            gr.update(visible=v.show_browser_webcam),
            gr.update(visible=v.show_preview),
            gr.update(visible=v.show_camera_status),
            gr.update(visible=v.show_resolution_fps_controls),
            gr.update(visible=v.show_resolution_fps_controls),
        )
