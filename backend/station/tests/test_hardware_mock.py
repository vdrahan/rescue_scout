"""Mock hardware manager."""

from __future__ import annotations

from station.config import Settings
from station.hardware.manager import HardwareManager


def _mgr() -> HardwareManager:
    return HardwareManager(Settings(hardware_mode="mock", sink_enabled=False))


def test_mock_hardware_builds_in_mock_mode():
    hw = _mgr()
    assert hw.mode == "mock"
    assert hw.degraded is False
    status = hw.status()
    assert status["mode"] == "mock"
    assert len(status["devices"]) >= 6


def test_component_tests_pass():
    hw = _mgr()
    for component in ("buzzer", "detection_led", "system_led", "gas_sensor",
                      "temp_humidity", "lcd_display"):
        result = hw.test(component)
        assert result is not None
        assert result["status"] == "passed", result

    assert hw.test("camera_servo") is None  # not a hardware device here


def test_sensor_reads_and_actuators_do_not_crash():
    hw = _mgr()
    gas = hw.read_gas()
    assert gas["ppm"] is not None
    climate = hw.read_climate()
    assert climate["temperature"] is not None
    hw.signal_detection(True)
    hw.signal_detection(False)
    hw.alert()
    hw.write_lcd(["line1", "line2"])
    hw.cleanup()
