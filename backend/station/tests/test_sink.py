from __future__ import annotations

from station.config import Settings
from station.sink import DataApiSink


def _sink() -> DataApiSink:
    return DataApiSink(
        Settings(detection_mode='mock', hardware_mode='mock', sink_enabled=False)
    )


def test_detection_lookup_never_uses_a_sensor_id(monkeypatch) -> None:
    sink = _sink()
    sink._class_map = {}
    sink._sensor_map = {'gas': 7}
    monkeypatch.setattr(sink, '_refresh_maps', lambda: None)
    posted: list[tuple[str, dict]] = []
    monkeypatch.setattr(sink, '_post', lambda path, body: posted.append((path, body)))

    sink._post_detection({'class_name': 'gas', 'confidence': 90.0, 'people_count': 1})

    assert posted == []


def test_sensor_lookup_never_uses_a_detection_class_id(monkeypatch) -> None:
    sink = _sink()
    sink._class_map = {'standing_person': 3}
    sink._sensor_map = {}
    monkeypatch.setattr(sink, '_refresh_maps', lambda: None)
    posted: list[tuple[str, dict]] = []
    monkeypatch.setattr(sink, '_post', lambda path, body: posted.append((path, body)))

    sink._post_sensor(
        {
            'sensor_name': 'standing_person',
            'value': 10.0,
            'message': 'normal',
            'is_dangerous': False,
        }
    )

    assert posted == []


def test_detection_lookup_uses_the_refreshed_class_map(monkeypatch) -> None:
    sink = _sink()
    sink._class_map = {}
    posted: list[tuple[str, dict]] = []

    def refresh() -> None:
        sink._class_map = {'lying_person': 4}

    monkeypatch.setattr(sink, '_refresh_maps', refresh)
    monkeypatch.setattr(sink, '_post', lambda path, body: posted.append((path, body)))

    sink._post_detection(
        {'class_name': 'lying_person', 'confidence': 88.0, 'people_count': 1}
    )

    assert posted == [
        (
            '/detections',
            {'class_id': 4, 'people_count': 1, 'confidence': 88.0},
        )
    ]
