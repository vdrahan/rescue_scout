from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

import cv2
import numpy as np

from .base import InferenceResult

try:
    import mediapipe as mp
except Exception:
    mp = None

DEFAULT_TASK_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

POSE_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10), (11, 12),
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19), (12, 14), (14, 16), (16, 18),
    (16, 20), (16, 22), (18, 20), (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (27, 29),
    (29, 31), (24, 26), (26, 28), (28, 30), (30, 32), (27, 31), (28, 32),
)


class MediaPipePoseModel:
    def __init__(self, base_dir: Path) -> None:
        self.mode = "unavailable"
        self.detector = None
        self.init_error: str | None = None
        if mp is None:
            self.init_error = (
                "MediaPipe import failed. Install `mediapipe` (or `mediapipe-rpi4`) in this venv. "
                "If wheels are unavailable, use Python 3.11/3.12."
            )
            return
        self._init_tasks(base_dir)
        if self.mode == "unavailable":
            self._init_solutions()

    def _init_tasks(self, base_dir: Path) -> None:
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision

            task_model_path = base_dir / "ai" / "pose_landmarker_lite.task"
            if not task_model_path.exists():
                urlretrieve(DEFAULT_TASK_MODEL_URL, str(task_model_path))
            options = vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(task_model_path)),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.detector = vision.PoseLandmarker.create_from_options(options)
            self.mode = "tasks"
        except Exception as exc:
            self.init_error = f"MediaPipe tasks init failed: {exc}"

    def _init_solutions(self) -> None:
        try:
            if not hasattr(mp, "solutions"):
                raise RuntimeError("mp.solutions not available")
            self.detector = mp.solutions.pose.Pose(  # type: ignore[union-attr]
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.mode = "solutions"
        except Exception as exc:
            self.init_error = f"{self.init_error or ''} | solutions init failed: {exc}".strip(" |")

    def _draw_pose(self, frame_bgr: np.ndarray, points: dict[int, tuple[int, int]]) -> np.ndarray:
        out = frame_bgr.copy()
        for start, end in POSE_CONNECTIONS:
            a = points.get(start)
            b = points.get(end)
            if a is None or b is None:
                continue
            cv2.line(out, a, b, (0, 220, 255), 2, cv2.LINE_AA)
        for pt in points.values():
            cv2.circle(out, pt, 4, (0, 255, 0), -1, cv2.LINE_AA)
        return out

    def run(self, frame_rgb: np.ndarray) -> InferenceResult:
        if self.detector is None:
            raise ValueError(self.init_error or "MediaPipe pose detector unavailable.")

        src_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        h, w, _ = src_bgr.shape
        points: dict[int, tuple[int, int]] = {}

        if self.mode == "tasks":
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            task_result = self.detector.detect(mp_image)
            if task_result.pose_landmarks:
                for idx, lm in enumerate(task_result.pose_landmarks[0]):
                    visibility = float(getattr(lm, "visibility", 1.0))
                    if visibility < 0.5:
                        continue
                    points[idx] = (int(lm.x * w), int(lm.y * h))
        elif self.mode == "solutions":
            result = self.detector.process(frame_rgb)
            if result.pose_landmarks:
                for idx, lm in enumerate(result.pose_landmarks.landmark):
                    visibility = float(getattr(lm, "visibility", 1.0))
                    if visibility < 0.5:
                        continue
                    points[idx] = (int(lm.x * w), int(lm.y * h))
        else:
            raise ValueError(self.init_error or "MediaPipe pose detector unavailable.")

        ann_rgb = cv2.cvtColor(self._draw_pose(src_bgr, points), cv2.COLOR_BGR2RGB)
        payload = {
            "model": "mediapipe_pose",
            "pose_mode": self.mode,
            "found_person": len(points) > 0,
            "landmark_count": len(points),
        }
        return InferenceResult(
            annotated_rgb=ann_rgb,
            payload=payload,
            status_text=f"Pose done. landmarks={len(points)}",
        )

    def close(self) -> None:
        if self.detector is not None and hasattr(self.detector, "close"):
            self.detector.close()
