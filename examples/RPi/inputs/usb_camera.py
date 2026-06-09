from __future__ import annotations

from typing import Any

import cv2
import gradio as gr
import numpy as np

from .base import CameraCaptureResult, InputProvider, InputSourceMeta, SourceUiVisibility
from .camera_devices import resolve_camera_source
from .registry import INPUT_RPI_CAMERA, SPINNER_FRAMES, parse_resolution


def _try_single_frame_buffer(cap: cv2.VideoCapture) -> None:
    """Ask V4L2 to keep a one-frame queue so each read() is the latest image.

    A per-tick multi-grab() drain is not used here: each grab can block until the
    next frame arrives, so N grabs per tick can stall the UI for N frame intervals.
    """
    if not cap.isOpened():
        return
    if cap.set(cv2.CAP_PROP_BUFFERSIZE, 1):
        print("[USB] CAP_PROP_BUFFERSIZE=1 (minimize stale frames between timer ticks).")
    else:
        print("[USB] Warning: could not set CAP_PROP_BUFFERSIZE=1; latency may be higher.")


class UsbCameraInput(InputProvider):
    """USB / V4L2 camera via OpenCV."""

    meta = InputSourceMeta(source_id=INPUT_RPI_CAMERA, label="USB camera (OpenCV)")

    def __init__(self, camera_device: str = "", camera_index: int = 8) -> None:
        source = resolve_camera_source(camera_device, camera_index)
        print(f"[USB] Opening camera: {source!r} ...")
        self._cap = cv2.VideoCapture(source, cv2.CAP_V4L2)

        if not self._cap.isOpened():
            print(f"[USB] FAILED to open camera {source!r}")
        else:
            print(f"[USB] Camera opened successfully.")
            _try_single_frame_buffer(self._cap)

    def ui_visibility(self) -> SourceUiVisibility:
        return SourceUiVisibility(
            show_note=True,
            note_markdown="Using synced USB camera preview below.",
            show_upload=False,
            show_browser_webcam=False,
            show_preview=True,
            show_camera_status=True,
            show_resolution_fps_controls=True,
        )

    def sync_preview(
        self,
        resolution: str,
        target_fps: float,
        browser_webcam: np.ndarray | None,
        latest_capture: np.ndarray | None,
        perf_state: dict[str, Any] | None,
    ) -> CameraCaptureResult:
        del target_fps, browser_webcam, latest_capture
        if perf_state is None:
            perf_state = {"spinner_idx": -1, "label": SPINNER_FRAMES[0]}
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return CameraCaptureResult(
                preview_update=gr.update(value=None, label=f"{perf_state.get('label', SPINNER_FRAMES[0])} Camera feed"),
                frame_rgb=None,
                perf_state=perf_state,
                status_text="Camera error",
                refresh_latest=True,
            )
        width, height = parse_resolution(resolution)
        frame = cv2.resize(frame, (width, height))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        spinner_idx = (int(perf_state.get("spinner_idx", -1)) + 1) % len(SPINNER_FRAMES)
        label = SPINNER_FRAMES[spinner_idx]
        new_perf = {"spinner_idx": spinner_idx, "label": label}
        return CameraCaptureResult(
            preview_update=gr.update(value=frame_rgb, label=f"{label} Camera feed"),
            frame_rgb=frame_rgb,
            perf_state=new_perf,
            status_text="Camera synced.",
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
            raise ValueError("No USB camera frame available yet.")
        return latest_capture

    def close(self) -> None:
        self._cap.release()
