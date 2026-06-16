"""Pick a detector based on configured mode, degrading to mock when needed."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings
from ..logging_conf import get_logger
from .base import Detector
from .mock_detector import MockDetector

log = get_logger(__name__)


@dataclass
class DetectorBundle:
    detector: Detector
    mode: str          # actual mode in use: "real" or "mock"
    degraded: bool     # True if we wanted real but fell back to mock
    note: str = ""


def _build_real(settings: Settings) -> Detector:
    from .yolo_detector import YoloDetector  # lazy: avoids torch import in mock

    return YoloDetector(
        model_path=settings.model_path,
        img_size=settings.img_size,
        max_det=settings.max_detections,
    )


def build_detector(settings: Settings) -> DetectorBundle:
    mock = lambda: MockDetector(settings.frame_width, settings.frame_height)  # noqa: E731

    if settings.detection_mode == "mock":
        return DetectorBundle(mock(), "mock", degraded=False, note="DETECTION_MODE=mock")

    try:
        detector = _build_real(settings)
        return DetectorBundle(detector, "real", degraded=False)
    except Exception as exc:  # noqa: BLE001 - any failure must degrade, not crash
        if settings.detection_mode == "real":
            # Explicit real requested but unavailable — still degrade so the API
            # stays up, but make the failure loud in the status note.
            log.error("DETECTION_MODE=real but real detector failed: %s", exc)
            return DetectorBundle(mock(), "mock", degraded=True,
                                  note=f"real detector unavailable: {exc}")
        log.warning("Real detector unavailable, using mock: %s", exc)
        return DetectorBundle(mock(), "mock", degraded=True,
                              note=f"auto fell back to mock: {exc}")
