"""Mock detector + class helpers."""

from __future__ import annotations

from station.detection.classes import CLASSES, normalize, priority_for
from station.detection.mock_detector import MockDetector
from station.imaging import new_scene


def test_classes_and_priority():
    assert "partially_visible_person" in CLASSES
    assert normalize("partially_hidden") == "partially_visible_person"
    assert normalize("partially_hidden_person") == "partially_visible_person"
    assert priority_for("lying_person") == "HIGH"
    assert priority_for("crawling_person") == "HIGH"
    assert priority_for("standing_person") == "LOW"


def test_mock_detector_shape_and_detections():
    detector = MockDetector(width=128, height=96, seed=7)
    frame = new_scene(128, 96, "test")
    result = detector.infer(frame, conf=0.4, iou=0.45)

    assert result.frame.shape == (96, 128, 3)
    for det in result.detections:
        assert det.class_name in CLASSES
        assert 0.0 <= det.confidence <= 1.0
        assert det.priority in {"HIGH", "MEDIUM", "LOW"}
        x1, y1, x2, y2 = det.bbox
        assert x2 > x1 and y2 > y1


def test_mock_detector_is_deterministic_with_seed():
    a = MockDetector(seed=1).infer(new_scene(64, 64, "a"), 0.4, 0.45)
    b = MockDetector(seed=1).infer(new_scene(64, 64, "a"), 0.4, 0.45)
    assert [d.class_name for d in a.detections] == [d.class_name for d in b.detections]
