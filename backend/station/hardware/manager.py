"""Builds the device set for the active HARDWARE_MODE and exposes high-level ops.

Auto/real failures degrade to mock so the API never crashes when hardware or its
libraries are missing. Cleanup runs on FastAPI shutdown.
"""

from __future__ import annotations

from ..config import Settings
from ..logging_conf import get_logger
from .base import Buzzer, ClimateSensor, Device, GasSensor, Lcd, Led
from .mock.devices import (
    MockBuzzer,
    MockButton,
    MockClimateSensor,
    MockGasSensor,
    MockLcd,
    MockLed,
    MockRgbModule,
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
    "rgb_module": "rgb_module",
    "rgb_status": "rgb_status",
}


class UnavailableDevice(Device):
    def __init__(self, dev_id: str, name: str, reason: str):
        super().__init__(dev_id, name)
        self.ok = False
        self._reason = reason

    def test(self) -> tuple[bool, str]:
        return False, self._reason

    def status(self) -> dict:
        data = super().status()
        data["error"] = self._reason
        return data


class HardwareManager:
    def __init__(self, settings: Settings):
        self._settings = settings
        self.degraded = False
        self.note = ""
        self.mode = "mock"
        self._devices: dict[str, Device] = {}
        # Cache updated exclusively by the gas-poll background thread.
        # The HTTP status endpoint reads this instead of touching I2C directly,
        # which eliminates the smbus2 race condition.
        self._gas_cache: dict = {"ppm": None, "dangerous": False}
        self._build()

    # -- construction -------------------------------------------------------
    def _build(self) -> None:
        want = self._settings.hardware_mode
        if want == "mock":
            self._devices = self._build_mock()
            self.mode = "mock"
            return

        self._devices, failures, real_count = self._build_real(want)
        self.mode = "real" if want == "real" or real_count else "mock"
        if failures:
            self.degraded = True
            self.note = "; ".join(failures)
            level = log.error if want == "real" else log.warning
            level("HARDWARE_MODE=%s degraded: %s", want, self.note)

    def _build_mock(self) -> dict[str, Device]:
        return {
            "system_led": MockLed("system_led", "System LED"),
            "detection_led": MockLed("detection_led", "Detection LED"),
            "rgb_module": MockRgbModule("rgb_module", "Digital RGB Module"),
            "rgb_status": MockRgbLed("rgb_status", "Status RGB"),
            "buzzer": MockBuzzer("buzzer", "Buzzer"),
            "gas": MockGasSensor("gas", "Gas Sensor MQ-2"),
            "climate": MockClimateSensor("climate", "DHT11 Temp/Humidity"),
            "button_page": MockButton("button_page", "Display Page Button"),
            "button_camera": MockButton("button_camera", "Camera Switch Button"),
            "lcd": MockLcd("lcd", "LCD Display"),
        }

    def _build_real(self, want: str) -> tuple[dict[str, Device], list[str], int]:
        s = self._settings
        devices = self._build_mock()
        failures: list[str] = []
        real_count = 0

        def add(dev_id: str, name: str, factory) -> None:
            nonlocal real_count
            try:
                devices[dev_id] = factory()
                real_count += 1
            except Exception as exc:  # noqa: BLE001
                reason = f"{name}: {exc}"
                failures.append(reason)
                if want == "real":
                    devices[dev_id] = UnavailableDevice(dev_id, name, reason)

        try:
            from .real.gpio_devices import (
                GpioBuzzer,
                GpioButton,
                GpioLed,
                GpioRgbLed,
                GpioRgbModule,
            )
        except Exception as exc:  # noqa: BLE001
            reason = f"GPIO devices unavailable: {exc}"
            failures.append(reason)
            if want == "real":
                for dev_id, name in (
                    ("system_led", "System LED"),
                    ("detection_led", "Detection LED"),
                    ("rgb_module", "Digital RGB Module"),
                    ("rgb_status", "Status RGB"),
                    ("buzzer", "Buzzer"),
                    ("button_page", "Display Page Button"),
                    ("button_camera", "Camera Switch Button"),
                ):
                    devices[dev_id] = UnavailableDevice(dev_id, name, reason)
        else:
            add("system_led", "System LED",
                lambda: GpioLed("system_led", "System LED", s.system_led_pin, s.gpio_chip))
            add("detection_led", "Detection LED",
                lambda: GpioLed("detection_led", "Detection LED", s.detection_led_pin, s.gpio_chip))
            add("rgb_module", "Digital RGB Module",
                lambda: GpioRgbModule("rgb_module", "Digital RGB Module",
                                      s.rgb1_r_pin, s.rgb1_g_pin, s.rgb1_b_pin, s.gpio_chip))
            add("rgb_status", "Status RGB",
                lambda: GpioRgbLed("rgb_status", "Status RGB",
                                   s.rgb2_r_pin, s.rgb2_g_pin, s.rgb2_b_pin, s.gpio_chip))
            add("buzzer", "Buzzer",
                lambda: GpioBuzzer("buzzer", "Buzzer", s.buzzer_pin, s.gpio_chip))
            add("button_page", "Display Page Button",
                lambda: GpioButton("button_page", "Display Page Button", s.button_page_pin, s.gpio_chip))
            add("button_camera", "Camera Switch Button",
                lambda: GpioButton("button_camera", "Camera Switch Button", s.button_camera_pin, s.gpio_chip))

        try:
            from .real.ads1115_gas import Ads1115GasSensor
        except Exception as exc:  # noqa: BLE001
            reason = f"Gas Sensor MQ-2: {exc}"
            failures.append(reason)
            if want == "real":
                devices["gas"] = UnavailableDevice("gas", "Gas Sensor MQ-2", reason)
        else:
            add("gas", "Gas Sensor MQ-2",
                lambda: Ads1115GasSensor("gas", "Gas Sensor MQ-2",
                                         s.ads1115_i2c_addr, s.mq2_channel))

        try:
            from .real.dht_sensor import DhtClimateSensor
        except Exception as exc:  # noqa: BLE001
            reason = f"DHT11 Temp/Humidity: {exc}"
            failures.append(reason)
            if want == "real":
                devices["climate"] = UnavailableDevice("climate", "DHT11 Temp/Humidity", reason)
        else:
            add("climate", "DHT11 Temp/Humidity",
                lambda: DhtClimateSensor("climate", "DHT11 Temp/Humidity", s.dht_pin))

        try:
            from .real.lcd_display import I2cLcd
        except Exception as exc:  # noqa: BLE001
            reason = f"LCD Display: {exc}"
            failures.append(reason)
            if want == "real":
                devices["lcd"] = UnavailableDevice("lcd", "LCD Display", reason)
        else:
            add("lcd", "LCD Display",
                lambda: I2cLcd("lcd", "LCD Display", s.lcd_i2c_addr, s.lcd_i2c_bus))

        return devices, failures, real_count

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
            if passed and component == "temp_humidity" and isinstance(device, ClimateSensor):
                try:
                    temperature, humidity = device.read()
                    lcd = self._devices.get("lcd")
                    if isinstance(lcd, Lcd):
                        lcd.write([f"Temp:{temperature}C", f"Hum:{humidity}%"])
                except Exception as exc:  # noqa: BLE001
                    detail = f"{detail}; LCD update failed: {exc}"
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
        """Person detection alert: 2 short beeps."""
        buzzer = self._devices.get("buzzer")
        if isinstance(buzzer, Buzzer):
            buzzer.beep(times=2, on=0.1, off=0.05)

    def gas_alert(self) -> None:
        """Gas warning alert: 5 rapid beeps — clearly distinct from person detection."""
        buzzer = self._devices.get("buzzer")
        if isinstance(buzzer, Buzzer):
            buzzer.beep(times=5, on=0.08, off=0.06)

    def read_gas(self) -> dict:
        """Read sensor and update cache. Called only from the gas-poll thread."""
        gas = self._devices.get("gas")
        if isinstance(gas, GasSensor):
            ppm = gas.read_ppm()
            self._gas_cache = {"ppm": ppm, "dangerous": ppm >= self._settings.gas_danger_ppm}
        return self._gas_cache

    def gas_status(self) -> dict:
        """Return last cached gas reading — safe to call from any thread, no I2C."""
        return self._gas_cache

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
