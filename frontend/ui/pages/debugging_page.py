from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from ..constants import TEST_GROUPS
from ..handlers import (
    diagnostic_progress,
    diagnostic_summary_html,
    initial_test_state,
    test_header_html,
    test_rows_html,
)


@dataclass
class DebuggingPage:
    test_state: gr.State
    reset_button: gr.Button
    run_all_button: gr.Button
    progress_output: gr.Markdown
    summary_output: gr.HTML
    test_buttons: dict[str, gr.Button]
    test_headers: dict[str, gr.HTML]
    test_outputs: dict[str, gr.HTML]


def _build_test_card(test: dict) -> tuple[str, gr.Button, gr.HTML, gr.HTML]:
    with gr.Group(elem_classes=["test-card-v2"]):
        with gr.Row(elem_classes=["tcv2-header-row"]):
            header_html = gr.HTML(
                value=test_header_html(test, "not_tested"),
                elem_classes=["tcv2-header"],
            )
            button = gr.Button("▷ Test", size="sm", elem_classes=["tcv2-btn"])
        rows_html = gr.HTML(
            value=test_rows_html(test, "not_tested"),
            elem_classes=["tcv2-rows"],
        )
    return test["id"], button, header_html, rows_html


def build_debugging_page() -> DebuggingPage:
    test_state = gr.State(initial_test_state())
    test_buttons: dict[str, gr.Button] = {}
    test_headers: dict[str, gr.HTML] = {}
    test_outputs: dict[str, gr.HTML] = {}

    with gr.Row():
        with gr.Column(scale=4):
            with gr.Row():
                progress_output = gr.Markdown(diagnostic_progress(initial_test_state()), elem_classes=["compact-md"])
                reset_button = gr.Button("Reset", size="md")
                run_all_button = gr.Button("Run All", variant="primary", size="md")

            for group_name, _accent, tests in TEST_GROUPS:
                with gr.Accordion(
                    label=group_name,
                    open=(group_name == "Visual"),
                    elem_id=f"debug-acc-{group_name.lower()}",
                    elem_classes=["debug-accordion"],
                ):
                    for start in range(0, len(tests), 2):
                        with gr.Row(elem_classes=["debug-grid"]):
                            for test in tests[start:start + 2]:
                                test_id, button, header_html, rows_html = _build_test_card(test)
                                test_buttons[test_id] = button
                                test_headers[test_id] = header_html
                                test_outputs[test_id] = rows_html

        with gr.Column(scale=1, min_width=270, elem_id="diag-summary-col"):
            summary_output = gr.HTML(
                value=diagnostic_summary_html(initial_test_state()),
                elem_id="diag-summary-html",
            )

    return DebuggingPage(
        test_state=test_state,
        reset_button=reset_button,
        run_all_button=run_all_button,
        progress_output=progress_output,
        summary_output=summary_output,
        test_buttons=test_buttons,
        test_headers=test_headers,
        test_outputs=test_outputs,
    )
