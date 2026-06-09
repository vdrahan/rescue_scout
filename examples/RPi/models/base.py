from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class InferenceResult:
    annotated_rgb: np.ndarray | None
    payload: dict[str, Any]
    status_text: str
