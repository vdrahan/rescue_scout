"""RPi Local Multi-Model Dashboard — entry point."""

from __future__ import annotations

from config import AppConfig
from services.bootstrap import bootstrap_app, shutdown_app
from ui.dashboard import build_dashboard, launch_dashboard


def main() -> None:
    # --- init ---
    ctx = bootstrap_app(AppConfig())
    demo, _inference = build_dashboard(ctx)

    # --- gradio run ---
    try:
        launch_dashboard(ctx, demo)
    finally:
        shutdown_app(ctx)


if __name__ == "__main__":
    main()
