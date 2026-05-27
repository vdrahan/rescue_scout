from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    gradio_host: str = "0.0.0.0"
    gradio_port: int = 7860

    # USB camera: run `python list_cameras.py` on the Pi, then paste config_value here.
    # Substring match works (e.g. "usb-OmniVision"). Leave empty to use camera_index.
    camera_device: str = "usb-USB_Camera_USB_Camera_202403071520007-video-index0"
    camera_index: int = 8  # fallback when camera_device is ""
    csi_buffer_resolution: str = "1280x720"
    # Picamera2 "RGB888" buffers are often BGR-ordered; set False if colors look wrong the other way.
    csi_bgr_to_rgb: bool = True
    default_resolution: str = "640x480"
    default_mode: str = "off"
    default_target_fps: float = 6.0
    max_target_fps: float = 20.0

    startup_ip_seconds: float = 8.0

    lcd_i2c_addr: int = 0x27
    lcd_i2c_bus: int = 1
    lcd_width: int = 20
    lcd_min_update_interval: float = 0.2

    active_buzzer_pin: int = 12  # active buzzer (digital on/off)
    passive_buzzer_pin: int = 4  # passive buzzer (PWM tones)

    shutdown_button_pin: int = 20
    shutdown_hold_seconds: float = 2.0
    shutdown_poll_interval: float = 0.02

    # Optional 7-segment (74HC595) — uncomment when wired; see hardware/seven_segment.py
    # segment_data_pin: int = 17
    # segment_clock_pin: int = 27
    # segment_latch_pin: int = 22

    # Optional NeoPixel ring data pin (Pi 5, pi5-neo library) — see RPi/docs/hardware-extensions.md
    # neopixel_pin: int = 18
    # neopixel_count: int = 12
