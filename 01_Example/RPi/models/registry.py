from __future__ import annotations

from pathlib import Path

from .pose_detector import MediaPipePoseModel
from .yolo_detector import YoloDroneModel

# ---------------------------------------------------------------------------
# Model IDs — used in ui/inference_handlers.py and in build_models() below.
# ---------------------------------------------------------------------------
MODEL_YOLO = "yolo"
MODEL_POSE = "pose"
MODEL_IDS = (MODEL_YOLO, MODEL_POSE)


def build_models(base_dir: Path) -> dict[str, object]:
    """Load every AI model. Add new entries here when you add a model file."""
    return {
        MODEL_YOLO: YoloDroneModel(base_dir / "ai" / "best.pt"),
        MODEL_POSE: MediaPipePoseModel(base_dir),
    }
