"""Builds the device set for the active HARDWARE_MODE and exposes high-level ops.

Auto/real failures degrade to mock so the API never crashes when hardware or its
libraries are missing. Cleanup runs on FastAPI shutdown.
"""

from __future__ import annotations

from ..config import Settings
from ..logging_conf import get_logger
from .base import Buzzer, ClimateSensor, Device, GasSensor, Lcd, Led
from .mock.devices import (
    MockButton,
    MockBuzzer,
    MockClimateSensor,
    MockGasSensor,
    MockLcd,
    MockLed,
    MockRgbLed,
)

log = get_logger(__name__)

# Frontend Debugging component id -> internal device id (hardware-only ones).
COMPONENT_MAP = {
    "detection_led": "detection_led",
    "system_led": "system_led",
    "buzzer": "buzzer",
    "gas_sensor": "gas",
    "temp_humidity": "climate",
    "lcd_display": "lcd",
}


class HardwareManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self.degraded = False
        self.note = ""
        self.mode = "mock"
        self._devices: dict[str, Device] = {}
        self._build()

    # -- construction -------------------------------------------------------
    def _build(self) -> None:
        want = self._settings.hardware_mode
        if want == "mock":
            self._devices = self._build_mock()
            self.mode = "mock"
            return
        try:
            self._devices = self._build_real()
            self.mode = "real"
        except Exception as exc:  # noqa: BLE001
            self._devices = self._build_mock()
            self.mode = "mock"
            self.degraded = True
            self.note = f"real hardware unavailable: {exc}"
            level = log.error if want == "real" else log.warning
            level("HARDWARE_MODE=%s falling back to mock: %s", want, exc)

    def _build_mock(self) -> dict[str, Device]:
        return {
            "system_led": MockLed("system_led", "System LED"),
            "detection_led": MockLed("detection_led", "Detection LED"),
            "rgb_status": MockRgbLed("rgb_status", "Status RGB"),
            "buzzer": MockBuzzer("buzzer", "Buzzer"),
            "gas": MockGasSensor("gas", "Gas Sensor MQ-2"),
            "climate": MockClimateSensor("climate", "DHT11 Temp/Humidity"),
            "button_page": MockButton("button_page", "Display Page Button"),
            "button_camera": MockButton("button_camera", "Camera Switch Button"),
            "lcd": MockLcd("lcd", "LCD Display"),
        }

    def _build_real(self) -> dict[str, Device]:
        s = self._settings
        # Lazy imports: missing libs raise here and trigger mock fallback.
        from .real.ads1115_gas import Ads1115GasSensor
        from .real.dht_sensor import DhtClimateSensor
        from .real.gpio_devices import GpioButton, GpioBuzzer, GpioLed, GpioRgbLed
        from .real.lcd_display import I2cLcd

        return {
            "system_led": GpioLed("system_led", "System LED", s.system_led_pin),
            "detection_led": GpioLed("detection_led", "Detection LED", s.detection_led_pin),
            "rgb_status": GpioRgbLed("rgb_status", "Status RGB",
                                     s.rgb2_r_pin, s.rgb2_g_pin, s.rgb2_b_pin),
            "buzzer": GpioBuzzer("buzzer", "Buzzer", s.buzzer_pin),
            "gas": Ads1115GasSensor("gas", "Gas Sensor MQ-2",
                                    s.ads1115_i2c_addr, s.mq2_channel),
            "climate": DhtClimateSensor("climate", "DHT11 Temp/Humidity", s.dht_pin),
            "button_page": GpioButton("button_page", "Display Page Button", s.button_page_pin),
            "button_camera": GpioButton("button_camera", "Camera Switch Button", s.button_camera_pin),
            "lcd": I2cLcd("lcd", "LCD Display", s.lcd_i2c_addr, s.lcd_i2c_bus),
        }

    # -- queries ------------------------------------------------------------
    def status(self) -> dict:
        return {
            "mode": self.mode,
            "degraded": self.degraded,
            "note": self.note,
            "devices": [d.status() for d in self._devices.values()],
        }

    def test(self, component: str) -> dict | None:
        dev_id = COMPONENT_MAP.get(component, component)
        device = self._devices.get(dev_id)
        if device is None:
            return None  # not a hardware device — caller handles (camera/UI)
        try:
            passed, detail = device.test()
        except Exception as exc:  # noqa: BLE001
            return {"component": component, "status": "failed", "detail": str(exc)}
        return {"component": component, "status": "passed" if passed else "failed",
                "detail": detail}

    # -- high level (used by detection worker) ------------------------------
    def signal_detection(self, active: bool) -> None:
        led = self._devices.get("detection_led")
        if isinstance(led, Led):
            led.on() if active else led.off()

    def alert(self) -> None:
        buzzer = self._devices.get("buzzer")
        if isinstance(buzzer, Buzzer):
            buzzer.beep(times=2)

    def read_gas(self) -> dict:
        gas = self._devices.get("gas")
        if isinstance(gas, GasSensor):
            ppm = gas.read_ppm()
            return {"ppm": ppm, "dangerous": ppm >= self._settings.gas_danger_ppm}
        return {"ppm": None, "dangerous": False}

    def read_climate(self) -> dict:
        climate = self._devices.get("climate")
        if isinstance(climate, ClimateSensor):
            t, h = climate.read()
            return {"temperature": t, "humidity": h}
        return {"temperature": None, "humidity": None}

    def write_lcd(self, lines: list[str]) -> None:
        lcd = self._devices.get("lcd")
        if isinstance(lcd, Lcd):
            lcd.write(lines)

    def cleanup(self) -> None:
        for device in self._devices.values():
            try:
                device.close()
            except Exception as exc:  # noqa: BLE001
                log.warning("cleanup failed for %s: %s", device.id, exc)
