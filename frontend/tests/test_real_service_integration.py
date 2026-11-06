from __future__ import annotations

import csv
import unittest
from pathlib import Path
from unittest.mock import patch

from frontend.services import api_client
from frontend.ui import handlers


class ServiceResultTests(unittest.TestCase):
    def test_service_result_marks_none_as_unavailable(self) -> None:
        result = api_client.service_result(None, unavailable_message="Backend unavailable")

        self.assertFalse(result.available)
        self.assertFalse(result.has_data)
        self.assertEqual(result.message, "Backend unavailable")

    def test_service_result_marks_empty_list_as_empty_not_unavailable(self) -> None:
        result = api_client.service_result([], unavailable_message="Backend unavailable")

        self.assertTrue(result.available)
        self.assertFalse(result.has_data)
        self.assertEqual(result.message, "No data yet")


class HandlerNoMockFallbackTests(unittest.TestCase):
    def _read_export(self, file_update) -> list[list[str]]:
        export_path = Path(file_update['value'])
        try:
            with export_path.open(encoding='utf-8', newline='') as csv_file:
                return list(csv.reader(csv_file))
        finally:
            export_path.unlink(missing_ok=True)

    def test_export_detections_csv_writes_backend_rows(self) -> None:
        detections = [
            {
                'detection_id': 11,
                'detection_time': '2026-09-09T10:00:00',
                'class_name': 'lying_person',
                'confidence': 91.5,
                'people_count': 1,
            }
        ]
        with patch.object(handlers.api_client, 'detections', return_value=detections):
            file_update = handlers.export_detections_csv('All classes')

        self.assertTrue(file_update['visible'])
        rows = self._read_export(file_update)
        self.assertEqual(rows[0], ['ID', 'Class', 'Confidence', 'Date', 'Time', 'Priority'])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][:3], ['#11', 'lying_person', '91%'])

    def test_export_gas_csv_writes_backend_rows(self) -> None:
        readings = [
            {
                'reading_id': 13,
                'reading_time': '2026-09-09T10:02:00',
                'sensor_name': 'gas',
                'value': 260,
                'unit': 'ppm',
                'is_dangerous': True,
                'message': 'danger',
            }
        ]
        with patch.object(handlers.api_client, 'sensor_readings', return_value=readings):
            file_update = handlers.export_gas_csv()

        rows = self._read_export(file_update)
        self.assertEqual(rows[0], ['Time', 'Reading', 'Level', 'Action'])
        self.assertEqual(rows[1][:3], ['10:02:00', '260 ppm', 'Critical'])

    def test_exports_report_unavailable_backend_instead_of_fake_rows(self) -> None:
        with (
            patch.object(handlers.api_client, 'detections', return_value=None),
            patch.object(handlers.api_client, 'sensor_readings', return_value=None),
        ):
            detection_rows = self._read_export(handlers.export_detections_csv('All classes'))
            gas_rows = self._read_export(handlers.export_gas_csv())

        for rows in (detection_rows, gas_rows):
            self.assertEqual(len(rows), 2)  # header + one status row, no invented data
            self.assertEqual(rows[1][0], 'Backend unavailable')

    def test_operating_update_shows_station_unavailable_without_fake_data(self) -> None:
        with (
            patch.object(handlers.api_client, "camera_frame", return_value=None),
            patch.object(handlers.api_client, "detection_latest", return_value=None),
            patch.object(handlers.api_client, "station_status", return_value=None),
        ):
            frame, camera_status, detection_count, fps, duration, recent_html = handlers.operating_update(
                True, "Detection", 45
            )

        self.assertIsNone(frame)
        self.assertIn("Station Offline", camera_status)
        self.assertEqual(detection_count, 0)
        self.assertEqual(fps, 0)
        self.assertEqual(duration, "Station unavailable")
        self.assertIn("Station unavailable", recent_html)
        self.assertNotIn("lying_person", recent_html)

    def test_operating_update_shows_no_frame_without_fake_frame(self) -> None:
        latest = {
            "active": False,
            "fps": 0,
            "threshold": 0.45,
            "detections": [],
            "recent": [],
            "last_detection": None,
        }
        status = {
            "uptime_seconds": 12,
            "cameras": {"active": "detection", "list": [{"id": "detection", "status": "ok"}]},
            "detection": {"active": False, "fps": 0, "threshold": 0.45},
        }
        with (
            patch.object(handlers.api_client, "camera_frame", return_value=None),
            patch.object(handlers.api_client, "detection_latest", return_value=latest),
            patch.object(handlers.api_client, "station_status", return_value=status),
        ):
            frame, camera_status, detection_count, fps, duration, recent_html = handlers.operating_update(
                False, "detection", 45
            )

        self.assertIsNone(frame)
        self.assertIn("No Frame Available", camera_status)
        self.assertEqual(detection_count, 0)
        self.assertEqual(fps, 0)
        self.assertEqual(duration, "00:00:12")
        self.assertIn("No detections yet", recent_html)

    def test_operating_update_uses_station_camera_error_status(self) -> None:
        latest = {"active": False, "fps": 0, "detections": [], "recent": []}
        status = {
            "uptime_seconds": 3,
            "cameras": {
                "active": "detection",
                "list": [
                    {
                        "id": "detection",
                        "name": "Detection Camera",
                        "status": "error",
                        "last_error": "stream stopped",
                    }
                ],
            },
            "detection": {"active": False},
        }
        with (
            patch.object(handlers.api_client, "camera_frame", return_value=object()),
            patch.object(handlers.api_client, "detection_latest", return_value=latest),
            patch.object(handlers.api_client, "station_status", return_value=status),
        ):
            _, camera_status, *_ = handlers.operating_update(False, "detection", 45)

        self.assertIn("Camera Reconnecting", camera_status)
        # The station no longer replays old frames, so the UI must not promise one.
        self.assertNotIn("last frame", camera_status)

    def test_toggle_ai_does_not_enable_when_station_start_fails(self) -> None:
        with (
            patch.object(handlers.api_client, "set_detection_active", return_value=None),
            patch.object(handlers, "operating_update", return_value=(None, "Station unavailable", 0, 0, "Station unavailable", "Station unavailable")),
        ):
            ai_state, button, *_ = handlers.toggle_ai(False, "detection", 45)

        self.assertFalse(ai_state)
        self.assertEqual(button["value"], "AI unavailable")
        self.assertEqual(button["variant"], "secondary")

    def test_toggle_camera_uses_station_camera_list(self) -> None:
        cameras = {
            "active": "detection",
            "cameras": [
                {"id": "detection", "name": "Detection Camera", "active": True},
                {"id": "fpv", "name": "FPV / Nav Camera", "active": False},
            ],
        }
        with (
            patch.object(handlers.api_client, "list_cameras", return_value=cameras) as listed,
            patch.object(handlers.api_client, "set_active_camera", return_value={**cameras, "active": "fpv"}) as switched,
            patch.object(handlers, "operating_update", return_value=(None, "No frame available", 0, 0, "00:00:00", "")),
        ):
            camera_state, button, *_ = handlers.toggle_camera("detection", False, 45)

        listed.assert_called_once()
        switched.assert_called_once_with("fpv")
        self.assertEqual(camera_state, "fpv")
        self.assertIn("FPV", button["value"])

    def test_operating_initial_state_loads_station_config_and_cameras(self) -> None:
        with (
            patch.object(handlers.api_client, "get_detection_config", return_value={"conf_threshold": 0.62}),
            patch.object(handlers.api_client, "list_cameras", return_value={"active": "fpv", "cameras": [{"id": "fpv", "name": "FPV / Nav Camera"}]}),
            patch.object(handlers.api_client, "detection_latest", return_value={"active": True, "fps": 4.7, "threshold": 0.62, "detections": [], "recent": []}),
            patch.object(handlers.api_client, "station_status", return_value={"uptime_seconds": 0, "detection": {"active": True}, "cameras": {"active": "fpv", "list": []}}),
            patch.object(handlers.api_client, "camera_frame", return_value=None),
        ):
            values = handlers.operating_initial_state()

        self.assertTrue(values[0])
        self.assertEqual(values[1], "fpv")
        self.assertEqual(values[4], 62)
        self.assertIn("FPV", values[3]["value"])

    def test_apply_threshold_posts_station_config_before_refresh(self) -> None:
        with (
            patch.object(handlers.api_client, "set_detection_config", return_value={"conf_threshold": 0.51}) as set_config,
            patch.object(handlers, "operating_update", return_value=(None, "No frame available", 0, 0, "00:00:00", "")),
        ):
            threshold_head, *_ = handlers.apply_threshold(False, "detection", 51)

        set_config.assert_called_once_with(conf=0.51)
        self.assertIn("51%", threshold_head)

    def test_empty_detection_table_returns_no_data_row(self) -> None:
        with patch.object(handlers.api_client, "detections", return_value=[]):
            rows = handlers.filter_detection_events("All classes")

        self.assertEqual(rows[0][0], "No data yet")
        self.assertNotIn("lying_person", str(rows))

    def test_unavailable_detection_table_returns_backend_unavailable_row(self) -> None:
        with patch.object(handlers.api_client, "detections", return_value=None):
            rows = handlers.filter_detection_events("All classes")

        self.assertEqual(rows[0][0], "Backend unavailable")
        self.assertNotIn("lying_person", str(rows))

    def test_empty_statistics_chart_does_not_render_fake_series(self) -> None:
        with patch.object(handlers.api_client, "stat_detections_over_time", return_value=[]):
            fig = handlers.build_statistics_figure("Detections", "Line")

        self.assertEqual(len(fig.data), 0)
        self.assertEqual(fig.layout.annotations[0].text, "No data yet")

    def test_unavailable_debug_component_does_not_pass(self) -> None:
        with patch.object(handlers.api_client, "test_component", return_value=None):
            self.assertEqual(handlers._component_status("buzzer"), "failed")

    def test_skipped_debug_component_does_not_pass(self) -> None:
        with patch.object(handlers.api_client, "test_component", return_value={"status": "skipped"}):
            self.assertEqual(handlers._component_status("camera_servo"), "skipped")

    def test_debug_component_calls_station_hardware_test(self) -> None:
        with patch.object(handlers.api_client, "test_component", return_value={"status": "passed"}) as test_component:
            self.assertEqual(handlers._component_status("rgb_module"), "passed")

        test_component.assert_called_once_with("rgb_module")

    def test_old_partial_visibility_names_are_canonicalized(self) -> None:
        self.assertEqual(
            handlers._canonical_class("partially_hidden"),
            "partially_visible_person",
        )
        self.assertEqual(
            handlers._canonical_class("partially_hidden_person"),
            "partially_visible_person",
        )


class CameraTransportTests(unittest.TestCase):
    def test_live_camera_image_is_sent_as_jpeg(self) -> None:
        """Gradio re-encodes the image on every refresh. WebP (its default) costs
        ~50 ms per frame on the Pi, which capped the live view at ~9 fps and loaded
        the CPU the detector needs; JPEG costs ~3 ms."""
        import gradio as gr

        from frontend.ui.pages.operating_page import build_operating_page

        with gr.Blocks():
            page = build_operating_page()

        self.assertEqual(page.camera_output.format, "jpeg")


if __name__ == "__main__":
    unittest.main()
