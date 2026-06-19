"""FastAPI application factory and lifespan wiring for the station service."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api import cameras, detection, hardware, health, status, system
from .api.deps import AppServices
from .cameras.manager import CameraManager
from .cameras.reader import CameraReader
from .config import get_settings
from .detection.registry import build_detector
from .detection.service import DetectionService
from .hardware.manager import HardwareManager
from .logging_conf import get_logger, setup_logging
from .sink import DataApiSink

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)

    hardware_mgr = HardwareManager(settings)
    hardware_mgr.set_status_led(100, 40, 0)   # orange = starting up

    camera_mgr = CameraManager(settings)
    camera_reader = CameraReader(camera_mgr, settings)
    camera_reader.start()
    sink = DataApiSink(settings)
    sink.start()
    bundle = build_detector(settings)
    detection_svc = DetectionService(settings, camera_mgr, hardware_mgr, sink, bundle)

    app.state.services = AppServices(
        settings=settings,
        cameras=camera_mgr,
        hardware=hardware_mgr,
        sink=sink,
        detection=detection_svc,
    )
    log.info(
        "Station ready | detection=%s%s hardware=%s%s",
        bundle.mode, " (degraded)" if bundle.degraded else "",
        hardware_mgr.mode, " (degraded)" if hardware_mgr.degraded else "",
    )
    hardware_mgr.set_status_led(0, 100, 0)   # green = system ready
    hardware_mgr.set_detection_feed_led(True)  # detection camera is active by default
    error_parts = []
    if hardware_mgr.degraded:
        error_parts.append(hardware_mgr.note)
    if camera_mgr.degraded:
        error_parts.append("camera unavailable")
    hardware_mgr.show_startup_lcd(
        hw_ok=not hardware_mgr.degraded,
        video_ok=not camera_mgr.degraded,
        error="; ".join(error_parts),
    )
    try:
        yield
    finally:
        hardware_mgr.set_status_led(0, 0, 0)  # off = shutting down
        detection_svc.stop()
        camera_reader.stop()
        sink.close()
        camera_mgr.close_all()
        hardware_mgr.cleanup()
        log.info("Station shut down cleanly")


def create_app() -> FastAPI:
    app = FastAPI(title="RC SAR Station", version=__version__, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (health, status, detection, cameras, hardware, system):
        app.include_router(module.router)
    return app


app = create_app()
