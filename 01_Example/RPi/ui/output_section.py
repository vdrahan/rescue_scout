from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from ui.constants import ERROR_DELETE_BUTTON_SLOTS
from ui.history import render_history_accordion


@dataclass
class OutputSection:
    ai_history_state: gr.State
    error_history_state: gr.State
    status_output: gr.Textbox
    server_status_output: gr.JSON
    ai_accordion_output: gr.HTML
    error_accordion_output: gr.HTML
    error_delete_buttons: list[gr.Button]


def build_output_section() -> OutputSection:
    ai_history_state = gr.State([])
    error_history_state = gr.State([])

    gr.Markdown("### Output")
    status_output = gr.Textbox(label="Status", value="Ready.")
    server_status_output = gr.JSON(label="Server status/response", value={"status": "idle", "mode": "local"})

    with gr.Accordion("AI response history", open=True):
        ai_accordion_output = gr.HTML(value=render_history_accordion("AI responses", []))
    with gr.Accordion("Errors", open=True):
        error_accordion_output = gr.HTML(value=render_history_accordion("Errors", []))
        with gr.Column():
            error_delete_buttons = [
                gr.Button("x", visible=False) for _ in range(ERROR_DELETE_BUTTON_SLOTS)
            ]

    return OutputSection(
        ai_history_state=ai_history_state,
        error_history_state=error_history_state,
        status_output=status_output,
        server_status_output=server_status_output,
        ai_accordion_output=ai_accordion_output,
        error_accordion_output=error_accordion_output,
        error_delete_buttons=error_delete_buttons,
    )
