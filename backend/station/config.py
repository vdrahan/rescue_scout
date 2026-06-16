"""Central configuration for the station service.

All tunables live here and are read from environment variables (or a local
``.env``) via pydantic-settings. Hardware pin defaults match the existing
``tests/test.py`` wiring so real mode works on the project's Raspberry Pi.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Mode = Literal["mock", "real", "auto"]


class Settings(BaseSettings):
    # ``protected_namespaces=()`` lets us use ``model_path`` without pydantic
    # warning about the reserved ``model_`` namespace.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )

    # --- Service ---
    station_host: str = "0.0.0.0"
    station_port: int = 8000
    log_level: str = "INFO"

    # Data API (single DB owner) — station POSTs events here. Service name in Docker.
    api_url: str = "http://localhost:8000"

    # --- Modes ---
    detection_mode: Mode = "auto"
    hardware_mode: Mode = "auto"

    # --- Detection / model ---
    model_path: str = "model/best.pt"  # trained YOLOv26 weights
    conf_threshold: float = 0.45
    iou_threshold: float = 0.45
    target_fps: float = 8.0
    img_size: int = 320
    frame_skip: int = 0  # extra frames to drop between inferences (0 = none)
    max_detections: int = 20

    # --- Cameras ---
    rtsp_camera_1_url: str = ""  # detection camera (telescopic pole)
    rtsp_camera_2_url: str = ""  # FPV / navigation camera
    usb_camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480

    # --- Hardware pins (BCM) — defaults from tests/test.py wiring ---
    buzzer_pin: int = 5
    system_led_pin: int = 23     # LED1
    detection_led_pin: int = 17  # LED2
    rgb1_r_pin: int = 26
    rgb1_g_pin: int = 16
    rgb1_b_pin: int = 6
    rgb2_r_pin: int = 22
    rgb2_g_pin: int = 24
    rgb2_b_pin: int = 27
    button_page_pin: int = 20
    button_camera_pin: int = 21
    dht_pin: int = 25

    # I2C
    ads1115_i2c_addr: int = 0x48
    mq2_channel: int = 0
    gas_danger_ppm: float = 250.0
    lcd_i2c_addr: int = 0x27
    lcd_i2c_bus: int = 1

    # --- Event sink behaviour ---
    sink_enabled: bool = True
    sink_queue_size: int = 256
    detection_debounce_seconds: float = 5.0  # per class, avoid spamming the DB


@lru_cache
def get_settings() -> Settings:
    return Settings()
