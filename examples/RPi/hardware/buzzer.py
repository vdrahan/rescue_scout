"""
Passive (PWM) and active (digital) buzzers.

Wire into the app: ``BuzzerService(..., gpio=gpio)`` in ``hardware/setup.py``,
store on ``AppContext``, call ``play("success")`` from ``inference_handlers``.
See ``RPi/docs/hardware-extensions.md``.
"""

from __future__ import annotations

import threading
import time
from typing import Dict, List, Literal, Tuple

from typing import TYPE_CHECKING

from .gpio_compat import GPIO

if TYPE_CHECKING:
    from .gpio import GpioPlatform

Tone = Tuple[float, float, float]
BuzzerTarget = Literal["passive", "active", "both"]

# Classroom kit wiring (BCM): passive = PWM melodies, active = fixed tone on/off.
DEFAULT_PASSIVE_BUZZER_PIN = 4
DEFAULT_ACTIVE_BUZZER_PIN = 12


class BuzzerService:
    def __init__(
        self,
        passive_pin: int = DEFAULT_PASSIVE_BUZZER_PIN,
        active_pin: int = DEFAULT_ACTIVE_BUZZER_PIN,
        *,
        pin: int | None = None,
        gpio: GpioPlatform | None = None,
    ) -> None:
        if pin is not None:
            passive_pin = pin
        self.passive_pin = passive_pin
        self.active_pin = active_pin
        self._gpio = gpio
        self._muted = False
        self._lock = threading.Lock()
        self._tone_lock = threading.Lock()
        self._last_played: Dict[str, float] = {}
        self._pwm = None
        self.passive_enabled = False
        self.active_enabled = False

        self.patterns: Dict[str, List[Tone]] = {
            "boot": [(659, 0.08, 50), (784, 0.08, 50), (988, 0.10, 50)],
            "shutdown": [(880, 0.10, 45), (659, 0.12, 45), (440, 0.16, 45)],
            "success": [(1047, 0.05, 40), (1319, 0.05, 40)],
            "error": [(330, 0.15, 55), (220, 0.18, 55)],
        }

        try:
            if gpio is not None:
                gpio.setup_output_low(self.active_pin)
                self.active_enabled = True
                self._pwm = gpio.setup_pwm(self.passive_pin, frequency=440)
                self.passive_enabled = True
            else:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.active_pin, GPIO.OUT)
                GPIO.output(self.active_pin, GPIO.LOW)
                self.active_enabled = True

                GPIO.setup(self.passive_pin, GPIO.OUT)
                self._pwm = GPIO.PWM(self.passive_pin, 440)
                self._pwm.start(0)
                self.passive_enabled = True
        except Exception as exc:
            print(f"[Buzzer] Disabled ({exc})")

    @property
    def enabled(self) -> bool:
        return self.passive_enabled or self.active_enabled

    def is_muted(self) -> bool:
        with self._lock:
            return self._muted

    def set_muted(self, muted: bool) -> bool:
        with self._lock:
            self._muted = bool(muted)
        if self._muted:
            self._silence_outputs()
        return self._muted

    def toggle_mute(self) -> bool:
        return self.set_muted(not self.is_muted())

    def _silence_outputs(self) -> None:
        if self._pwm is not None:
            self._pwm.ChangeDutyCycle(0)
        if self.active_enabled:
            GPIO.output(self.active_pin, GPIO.LOW)

    def _play_passive_pattern_sync(self, tones: List[Tone]) -> None:
        if not self.passive_enabled or self._pwm is None or self.is_muted():
            return
        with self._tone_lock:
            for frequency, duration, duty in tones:
                if self.is_muted():
                    self._pwm.ChangeDutyCycle(0)
                    return
                if frequency <= 0:
                    self._pwm.ChangeDutyCycle(0)
                    time.sleep(duration)
                    continue
                self._pwm.ChangeFrequency(frequency)
                self._pwm.ChangeDutyCycle(max(0.0, min(100.0, duty)))
                time.sleep(duration)
            self._pwm.ChangeDutyCycle(0)

    def _play_active_pattern_sync(self, tones: List[Tone]) -> None:
        if not self.active_enabled or self.is_muted():
            return
        with self._tone_lock:
            for _frequency, duration, _duty in tones:
                if self.is_muted():
                    GPIO.output(self.active_pin, GPIO.LOW)
                    return
                GPIO.output(self.active_pin, GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(self.active_pin, GPIO.LOW)
                time.sleep(0.02)

    def play(self, name: str, target: BuzzerTarget = "passive") -> None:
        tones = self.patterns.get(name)
        if not tones:
            return

        if target in ("passive", "both"):
            threading.Thread(
                target=self._play_passive_pattern_sync,
                args=(tones,),
                daemon=True,
            ).start()
        if target in ("active", "both"):
            threading.Thread(
                target=self._play_active_pattern_sync,
                args=(tones,),
                daemon=True,
            ).start()

    def play_cooldown(
        self,
        name: str,
        key: str,
        cooldown_sec: float,
        target: BuzzerTarget = "passive",
    ) -> None:
        now = time.time()
        last = self._last_played.get(key, 0.0)
        if (now - last) < cooldown_sec:
            return
        self._last_played[key] = now
        self.play(name, target=target)

    def cleanup(self) -> None:
        self._silence_outputs()
        if self._pwm is not None:
            self._pwm.stop()
