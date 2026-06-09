from __future__ import annotations

from pathlib import Path

from config import AppConfig
from core.runtime_snapshot import RuntimeSnapshot
from core.state import SharedState
from hardware.gpio_compat import GPIO
from hardware.setup import create_lcd, start_lcd_startup_display
from inputs import build_input_providers
from models.registry import build_models
from ui.context import AppContext


def bootstrap_app(cfg: AppConfig | None = None) -> AppContext:
    """Load LCD, models, and input providers. GPIO shutdown is started when the UI is ready."""
    cfg = cfg or AppConfig()
    base_dir = Path(__file__).resolve().parent.parent

    lcd = create_lcd(cfg)
    start_lcd_startup_display(cfg, lcd)

    providers = build_input_providers(cfg)
    return AppContext(
        cfg=cfg,
        base_dir=base_dir,
        shared=SharedState(),
        lcd=lcd,
        models=build_models(base_dir),
        providers=providers,
        runtime=RuntimeSnapshot(providers),
        gpio=None,
    )


def shutdown_app(ctx: AppContext) -> None:
    if ctx.gpio is not None:
        ctx.gpio.stop()
    for provider in ctx.providers.values():
        provider.close()
    for model in ctx.models.values():
        close = getattr(model, "close", None)
        if callable(close):
            close()
    GPIO.cleanup()
