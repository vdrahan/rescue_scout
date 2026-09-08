from __future__ import annotations

import os

import gradio as gr

try:
    from ui.constants import ASSET_DIR, CUSTOM_CSS
    from ui.dashboard import build_dashboard
except ModuleNotFoundError:  # pragma: no cover - keeps the entrypoint flexible in different launch modes
    from frontend.ui.constants import ASSET_DIR, CUSTOM_CSS
    from frontend.ui.dashboard import build_dashboard


demo = build_dashboard()


if __name__ == "__main__":
    demo.queue().launch(
        server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.environ.get("GRADIO_SERVER_PORT", "7860")),
        show_error=True,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(primary_hue="orange", secondary_hue="blue", neutral_hue="slate"),
        allowed_paths=[str(ASSET_DIR)],
    )
