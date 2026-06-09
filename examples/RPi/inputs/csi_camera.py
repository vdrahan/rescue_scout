from __future__ import annotations

from typing import Any

import cv2
import gradio as gr
import numpy as np

from .base import CameraCaptureResult, InputProvider, InputSourceMeta, SourceUiVisibility
from .registry import INPUT_CSI_CAMERA, SPINNER_FRAMES, parse_resolution

_PICAMERA2_IMPORT_ERROR: str | None = None
try:
    from picamera2 import Picamera2 as _Picamera2
except Exception as exc:  # noqa: BLE001 — load failure must not abort app import
    _Picamera2 = None  # type: ignore[misc, assignment]
    _PICAMERA2_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


def _picamera2_unavailable_detail() -> str:
    """Explain missing CSI stack (pip picamera2 alone is often not enough)."""
    base = _PICAMERA2_IMPORT_ERROR or "picamera2 could not be imported."
    lower = base.lower()
    if "libcamera" in lower:
        return (
            f"{base} "
            "The `libcamera` Python module comes from the OS (apt), not pip — standard "
            "venv isolation hides it. Fix: install `python3-libcamera` (and related Pi packages), "
            "then either recreate the venv with `python3 -m venv .venv --system-site-packages` "
            "or run the app with system Python (`/usr/bin/python3`) after installing picamera2 "
            "for that interpreter."
        )
    return base


class CsiCameraInput(InputProvider):
    """Raspberry Pi CSI camera via Picamera2 (RGB888), with sensor FPS capped to match target FPS."""

    meta = InputSourceMeta(source_id=INPUT_CSI_CAMERA, label="CSI camera (Picamera2)")

    def __init__(self, buffer_resolution: str = "1280x720", bgr_to_rgb: bool = True) -> None:
        self._picam2: Any = None
        self._buffer_w, self._buffer_h = parse_resolution(buffer_resolution)
        self._bgr_to_rgb = bgr_to_rgb
        self._last_fps_applied = -1.0

    def _to_display_rgb(self, frame: np.ndarray) -> np.ndarray:
        if self._bgr_to_rgb:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

    def ui_visibility(self) -> SourceUiVisibility:
        return SourceUiVisibility(
            show_note=True,
            note_markdown="Using CSI camera (Picamera2) preview below.",
            show_upload=False,
            show_browser_webcam=False,
            show_preview=True,
            show_camera_status=True,
            show_resolution_fps_controls=True,
        )

    def _ensure_camera(self) -> tuple[Any, str]:
        if _Picamera2 is None:
            return None, _picamera2_unavailable_detail()
        if self._picam2 is None:
            picam2 = _Picamera2()
            config = picam2.create_preview_configuration(
                main={"format": "RGB888", "size": (self._buffer_w, self._buffer_h)}
            )
            picam2.configure(config)
            picam2.start()
            self._picam2 = picam2
        return self._picam2, ""

    def _apply_fps_cap(self, picam2: Any, target_fps: float) -> None:
        fps = max(1.0, float(target_fps))
        if abs(fps - self._last_fps_applied) < 0.01:
            return
        self._last_fps_applied = fps
        duration_us = max(1, int(round(1_000_000 / fps)))
        picam2.set_controls({"FrameDurationLimits": (duration_us, duration_us)})

    def sync_preview(
        self,
        resolution: str,
        target_fps: float,
        browser_webcam: np.ndarray | None,
        latest_capture: np.ndarray | None,
        perf_state: dict[str, Any] | None,
    ) -> CameraCaptureResult:
        del browser_webcam, latest_capture
        if perf_state is None:
            perf_state = {"spinner_idx": -1, "label": SPINNER_FRAMES[0]}
        picam2, err = self._ensure_camera()
        if picam2 is None:
            return CameraCaptureResult(
                preview_update=gr.update(value=None, label=f"{perf_state.get('label', SPINNER_FRAMES[0])} Camera feed"),
                frame_rgb=None,
                perf_state=perf_state,
                status_text=f"CSI camera error: {err}",
                refresh_latest=True,
            )
        try:
            self._apply_fps_cap(picam2, target_fps)
            frame = picam2.capture_array()
        except Exception as exc:
            return CameraCaptureResult(
                preview_update=gr.update(value=None, label=f"{perf_state.get('label', SPINNER_FRAMES[0])} Camera feed"),
                frame_rgb=None,
                perf_state=perf_state,
                status_text=f"CSI capture failed: {exc}",
                refresh_latest=True,
            )
        width, height = parse_resolution(resolution)
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
        frame_rgb = self._to_display_rgb(frame)
        spinner_idx = (int(perf_state.get("spinner_idx", -1)) + 1) % len(SPINNER_FRAMES)
        label = SPINNER_FRAMES[spinner_idx]
        new_perf = {"spinner_idx": spinner_idx, "label": label}
        return CameraCaptureResult(
            preview_update=gr.update(value=frame_rgb, label=f"{label} Camera feed"),
            frame_rgb=frame_rgb,
            perf_state=new_perf,
            status_text="CSI camera synced.",
            refresh_latest=True,
        )

    def pick_frame(
        self,
        latest_capture: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
    ) -> np.ndarray:
        del upload_rgb, browser_webcam_rgb
        if latest_capture is None:
            raise ValueError("No CSI camera frame available yet.")
        return latest_capture

    def close(self) -> None:
        if self._picam2 is None:
            return
        try:
            self._picam2.stop()
        finally:
            self._picam2.close()
            self._picam2 = None
