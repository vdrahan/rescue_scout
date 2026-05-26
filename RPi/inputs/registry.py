from __future__ import annotations

from typing import Mapping

import numpy as np

from config import AppConfig

from .base import InputProvider

# ---------------------------------------------------------------------------
# Input source IDs (Gradio Radio values — must match keys in build_input_providers)
# ---------------------------------------------------------------------------
INPUT_RPI_CAMERA = "rpi_camera"
INPUT_CSI_CAMERA = "csi_camera"
INPUT_UPLOAD = "browser_upload"
INPUT_BROWSER_WEBCAM = "browser_webcam"

INPUT_OPTIONS = (
    INPUT_RPI_CAMERA,
    INPUT_UPLOAD,
    INPUT_BROWSER_WEBCAM,
)

HARDWARE_PREVIEW_SOURCES = frozenset({INPUT_RPI_CAMERA, INPUT_CSI_CAMERA})

# ---------------------------------------------------------------------------
# USB / CSI preview helpers (used by camera input classes)
# ---------------------------------------------------------------------------
RESOLUTION_OPTIONS = ("320x240", "640x480", "1280x720")
SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


def parse_resolution(value: str) -> tuple[int, int]:
    if value not in RESOLUTION_OPTIONS:
        raise ValueError(f"Unsupported resolution: {value}")
    w, h = value.split("x", maxsplit=1)
    return int(w), int(h)


def max_resolution_size() -> tuple[int, int]:
    return max(parse_resolution(r) for r in RESOLUTION_OPTIONS)


# ---------------------------------------------------------------------------
# Used by model run handlers (ui/inference_handlers.py)
# ---------------------------------------------------------------------------
def pick_source_frame(
    providers: Mapping[str, InputProvider],
    source_type: str,
    latest_capture: np.ndarray | None,
    upload_rgb: np.ndarray | None,
    browser_webcam_rgb: np.ndarray | None,
) -> np.ndarray:
    if source_type not in providers:
        raise ValueError(f"Unknown source type: {source_type}")
    return providers[source_type].pick_frame(latest_capture, upload_rgb, browser_webcam_rgb)


def rpi_panel_visibility(yolo_source: str, pose_source: str) -> bool:
    """True when either model tab uses a hardware-preview camera."""
    return yolo_source in HARDWARE_PREVIEW_SOURCES or pose_source in HARDWARE_PREVIEW_SOURCES


# ---------------------------------------------------------------------------
# Register input classes (imports inside functions — avoids circular imports)
# ---------------------------------------------------------------------------
def build_input_providers(cfg: AppConfig) -> dict[str, InputProvider]:
    from .browser_webcam import BrowserWebcamInput
    from .upload import UploadInput
    from .usb_camera import UsbCameraInput

    return {
        INPUT_RPI_CAMERA: UsbCameraInput(cfg.camera_device, cfg.camera_index),
        INPUT_UPLOAD: UploadInput(),
        INPUT_BROWSER_WEBCAM: BrowserWebcamInput(),
    }


def input_radio_choices() -> list[tuple[str, str]]:
    from .browser_webcam import BrowserWebcamInput
    from .upload import UploadInput
    from .usb_camera import UsbCameraInput

    return [
        (UsbCameraInput.meta.label, INPUT_RPI_CAMERA),
        (UploadInput.meta.label, INPUT_UPLOAD),
        (BrowserWebcamInput.meta.label, INPUT_BROWSER_WEBCAM),
    ]
