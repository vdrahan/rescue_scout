"""Builds the device set for the active HARDWARE_MODE and exposes high-level ops.

Auto/real failures degrade to mock so the API never crashes when hardware or its
libraries are missing. Cleanup runs on FastAPI shutdown.
"""

from __future__ import annotations

import threading
import time

from ..config import Settings
from ..logging_conf import get_logger
from .base import Buzzer, ClimateSensor, Device, GasSensor, Lcd, Led, RgbLed, RgbModule
from .mock.devices import (
    MockButton,
    MockBuzzer,
    MockClimateSensor,
    MockGasSensor,
    MockLcd,
    MockLed,
    MockRgbLed,
    MockRgbModule,
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
        self._rgb_blink_stop = threading.Event()
        self._lcd_scroll_stop = threading.Event()
        self._lcd_last_update: float = 0.0
        self._LCD_COOLDOWN = 5.0  # seconds between LCD detection messages
        self._lcd_screen_idx: int = -1  # -1 = no screen shown yet
        # Track intended LED states so tests can restore them
        self._status_led_color: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._fpv_led_on: bool = False
        self._detection_feed_led_on: bool = False
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
                GpioButton,
                GpioBuzzer,
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
        finally:
            self._restore_led_state(dev_id)
        return {"component": component, "status": "passed" if passed else "failed",
                "detail": detail}

    def _restore_led_state(self, dev_id: str) -> None:
        if dev_id == "rgb_status":
            led = self._devices.get("rgb_status")
            if isinstance(led, RgbLed):
                led.set_color(*self._status_led_color)
        elif dev_id == "detection_led":
            led = self._devices.get("detection_led")
            if isinstance(led, Led):
                led.on() if self._fpv_led_on else led.off()
        elif dev_id == "system_led":
            led = self._devices.get("system_led")
            if isinstance(led, Led):
                led.on() if self._detection_feed_led_on else led.off()
        elif dev_id == "rgb_module":
            module = self._devices.get("rgb_module")
            if isinstance(module, RgbModule):
                module.set_channel(None)

    def set_status_led(self, r: float, g: float, b: float) -> None:
        """Set the PWM RGB status LED colour. Values 0–100 (duty cycle %)."""
        self._status_led_color = (r, g, b)
        led = self._devices.get("rgb_status")
        if isinstance(led, RgbLed):
            led.set_color(r, g, b)

    # -- high level (used by detection worker) ------------------------------
    def signal_detection(self, active: bool) -> None:
        pass  # detection_led is now FPV Feed LED (controlled by set_fpv_led)

    def set_fpv_led(self, active: bool) -> None:
        """Turn the FPV Feed LED (detection_led pin) on/off when FPV camera is active."""
        self._fpv_led_on = active
        led = self._devices.get("detection_led")
        if isinstance(led, Led):
            led.on() if active else led.off()

    def set_detection_feed_led(self, active: bool) -> None:
        """Turn the Detection Feed LED (system_led pin) on/off when Detection camera is active."""
        self._detection_feed_led_on = active
        led = self._devices.get("system_led")
        if isinstance(led, Led):
            led.on() if active else led.off()

    def blink_rgb_module_red(self, duration: float = 3.0) -> None:
        """Blink the RGB module red for `duration` seconds in a background thread."""
        self._rgb_blink_stop.set()
        stop = threading.Event()
        self._rgb_blink_stop = stop
        threading.Thread(
            target=self._rgb_blink_worker,
            args=(duration, stop),
            name="rgb-blink",
            daemon=True,
        ).start()

    def _rgb_blink_worker(self, duration: float, stop: threading.Event) -> None:
        module = self._devices.get("rgb_module")
        if not isinstance(module, RgbModule):
            return
        module.set_channel("red")
        stop.wait(duration)
        module.set_channel(None)

    def startup_melody(self) -> None:
        """Triumphant startup fanfare played once when the station is ready.

        Three-phase structure (~1.6 s total):
          CALL    da — DA          short tap → accented hit
          BUILD   da · da · dA     rapid triplet rushing into an accent
          FINALE  DA ——— DAAAA     medium note → dramatic pause → long hold

        Active buzzers can't change pitch; rhythm alone shapes the character.
        Short notes feel sharp/high, long notes feel deep/resolved.
        Skipped silently when no buzzer is present.
        """
        buzzer = self._devices.get("buzzer")
        if not isinstance(buzzer, Buzzer):
            return

        # --- CALL: quick tap + accented hit (grabs attention) ---
        buzzer.beep(times=1, on=0.06, off=0.05)   # da  (sharp tap)
        buzzer.beep(times=1, on=0.13, off=0.07)   # DA  (strong accent)

        # --- BUILD: three fast notes rushing to a heavier beat ---
        buzzer.beep(times=1, on=0.06, off=0.04)   # da
        buzzer.beep(times=1, on=0.06, off=0.04)   # da
        buzzer.beep(times=1, on=0.11, off=0.10)   # dA  (longer rest = breath)

        # --- FINALE: medium note → micro-pause → triumphant long hold ---
        buzzer.beep(times=1, on=0.16, off=0.06)   # DA
        time.sleep(0.06)                            # dramatic silence
        buzzer.beep(times=1, on=0.50, off=0.0)    # DAAAA

    def show_startup_lcd(self, hw_ok: bool, video_ok: bool, error: str = "") -> None:
        lcd = self._devices.get("lcd")
        if not isinstance(lcd, Lcd):
            return
        if hw_ok and video_ok:
            self._lcd_scroll_stop.set()
            lcd.write(["STATUS: ACTIVE", "VIDEO: CONNECTED"])
        else:
            line1 = "STATUS: ERROR" if not hw_ok else "VIDEO: ERROR"
            msg = error if error else ("HW degraded" if not hw_ok else "Camera unavailable")
            self._start_scroll(line1, msg)

    def show_detection_on_lcd(self, class_name: str, detection_time: str) -> None:
        now = time.time()
        if now - self._lcd_last_update < self._LCD_COOLDOWN:
            return
        lcd = self._devices.get("lcd")
        if not isinstance(lcd, Lcd):
            return
        self._lcd_last_update = now
        short = class_name.replace("_person", "").replace("partially_visible", "partial")
        line2 = f"{short} {detection_time}"
        self._start_scroll("PERSON DETECTED", line2)

    def _start_scroll(self, line1: str, line2: str) -> None:
        """Cancel any current scroll and start a new one."""
        self._lcd_scroll_stop.set()
        stop = threading.Event()
        self._lcd_scroll_stop = stop
        threading.Thread(
            target=self._lcd_scroll_worker,
            args=(line1, line2, stop),
            name="lcd-scroll",
            daemon=True,
        ).start()

    def cycle_lcd_screen(self, last_detection: dict | None, total: int, class_num: int,
                         hw_ok: bool, video_ok: bool,
                         gas_ppm: float | None = None, gas_dangerous: bool = False,
                         gas_warnings: int = 0, temp_warnings: int = 0) -> int:
        """Cycle to the next info screen and display it. Returns new screen index."""
        self._lcd_screen_idx = (self._lcd_screen_idx + 1) % 4
        lcd = self._devices.get("lcd")
        if not isinstance(lcd, Lcd):
            return self._lcd_screen_idx

        if self._lcd_screen_idx == 0:
            # System Status Screen
            self._lcd_scroll_stop.set()
            status = "ACTIVE" if hw_ok else "ERROR"
            video = "CONNECTED" if video_ok else "ERROR"
            lcd.write([f"STATUS: {status}", f"VIDEO: {video}"])

        elif self._lcd_screen_idx == 1:
            # Last Detection Screen
            if last_detection:
                cls = last_detection.get("class_name", "unknown")
                t = last_detection.get("time", "")
                line2 = f"CLASS: {cls}, TIME: {t}"
            else:
                line2 = "NO DETECTIONS YET"
            self._start_scroll("LAST DETECTION", line2)

        elif self._lcd_screen_idx == 2:
            # Detection Statistics Screen
            self._lcd_scroll_stop.set()
            lcd.write([f"DETECTIONS: {total}", f"CLASS NUM: {class_num}"])

        elif self._lcd_screen_idx == 3:
            # Warnings summary screen
            self._lcd_scroll_stop.set()
            total_warn = gas_warnings + temp_warnings
            lcd.write([
                f"Warnings: {total_warn}",
                f"TEMP:{temp_warnings} GAS:{gas_warnings}",
            ])

        return self._lcd_screen_idx

    def _lcd_scroll_worker(self, line1: str, line2: str, stop: threading.Event) -> None:
        from .real.lcd_display import I2cLcd
        lcd = self._devices.get("lcd")
        if not isinstance(lcd, I2cLcd):
            return
        width = 16
        lcd.write([line1, ""])
        if len(line2) <= width:
            lcd.write_line(1, line2)
            return
        # Scroll indefinitely until stopped
        padded = line2 + " " * width
        total = len(padded) - width
        pos = 0
        while not stop.is_set():
            lcd.write_line(1, padded[pos: pos + width])
            stop.wait(0.5)
            pos += 1
            if pos > total:
                pos = 0
                stop.wait(1.2)

    def _lcd_gas_worker(self, stop: threading.Event) -> None:
        from .real.lcd_display import I2cLcd
        lcd = self._devices.get("lcd")
        if not isinstance(lcd, I2cLcd):
            return
        lcd.write(["GAS SENSOR", ""])
        while not stop.is_set():
            gas = self._gas_cache
            ppm = gas.get("ppm")
            dangerous = bool(gas.get("dangerous"))
            ppm_str = f"{ppm:.0f}" if ppm is not None else "N/A"
            status = "GAS DETECTED!" if dangerous else "NO GASSES"
            lcd.write_line(0, f"GAS: {ppm_str} ppm")
            lcd.write_line(1, status)
            stop.wait(3.0)

    def priority_alert(self, priority: str) -> None:
        """Alert based on detection priority in a background thread."""
        threading.Thread(
            target=self._priority_alert_worker,
            args=(priority,),
            name="buzz-alert",
            daemon=True,
        ).start()

    def _priority_alert_worker(self, priority: str) -> None:
        buzzer = self._devices.get("buzzer")
        if not isinstance(buzzer, Buzzer):
            return
        if priority == "HIGH":
            # Siren: 3 rapid bursts separated by short pauses
            for _ in range(3):
                buzzer.beep(times=6, on=0.04, off=0.02)
                time.sleep(0.12)
        elif priority == "MEDIUM":
            # 3 moderate beeps
            buzzer.beep(times=3, on=0.15, off=0.08)
        else:
            # LOW: 1 short beep
            buzzer.beep(times=1, on=0.2, off=0.0)

    def alert(self) -> None:
        """Person detection alert: 2 short beeps."""
        buzzer = self._devices.get("buzzer")
        if isinstance(buzzer, Buzzer):
            buzzer.beep(times=2, on=0.1, off=0.05)

    def temp_alert(self, temperature: float) -> None:
        """High temperature warning — LCD + 4 long urgent beeps."""
        lcd = self._devices.get("lcd")
        if isinstance(lcd, Lcd):
            temp_str = f"{temperature:.0f}C"
            self._start_scroll("HIGH TEMPERATURE!", f"TEMP: {temp_str} WARNING")
        buzzer = self._devices.get("buzzer")
        if not isinstance(buzzer, Buzzer):
            return
        # 4 long urgent beeps — distinct from gas siren
        for _ in range(2):
            buzzer.beep(times=4, on=0.4, off=0.15)
            time.sleep(0.3)

    def gas_alert(self, ppm: float = 0.0) -> None:
        """Gas warning alert — LCD + escalating siren pattern."""
        lcd = self._devices.get("lcd")
        if isinstance(lcd, Lcd):
            ppm_str = f"{ppm:.0f} ppm" if ppm else "HIGH"
            self._start_scroll("GAS DETECTED!", f"MQ-2: {ppm_str} DANGER")
        buzzer = self._devices.get("buzzer")
        if not isinstance(buzzer, Buzzer):
            return
        for on_t, off_t, count in ((0.3, 0.1, 3), (0.15, 0.05, 5), (0.07, 0.03, 8)):
            buzzer.beep(times=count, on=on_t, off=off_t)
            time.sleep(0.1)

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
