from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np


@dataclass(frozen=True)
class InputSourceMeta:
    """Declared metadata for Gradio UI wiring (unchanged at runtime)."""

    source_id: str
    label: str


@dataclass(frozen=True)
class SourceUiVisibility:
    show_note: bool
    note_markdown: str
    show_upload: bool
    show_browser_webcam: bool
    show_preview: bool
    show_camera_status: bool
    show_resolution_fps_controls: bool


@dataclass
class CameraCaptureResult:
    preview_update: Any
    frame_rgb: np.ndarray | None
    perf_state: dict[str, Any]
    status_text: str
    refresh_latest: bool = False


class InputProvider(ABC):
    """Single input mode: preview sync + frame selection for inference."""

    meta: ClassVar[InputSourceMeta]

    @abstractmethod
    def ui_visibility(self) -> SourceUiVisibility:
        pass

    @abstractmethod
    def sync_preview(
        self,
        resolution: str,
        target_fps: float,
        browser_webcam: np.ndarray | None,
        latest_capture: np.ndarray | None,
        perf_state: dict[str, Any] | None,
    ) -> CameraCaptureResult:
        """Timer-driven preview tick."""

    @abstractmethod
    def pick_frame(
        self,
        latest_capture: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
    ) -> np.ndarray:
        pass

    def close(self) -> None:
        pass
