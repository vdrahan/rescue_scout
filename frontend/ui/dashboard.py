from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from .constants import APP_TITLE, DEFAULT_PAGE, PAGE_DETAILS, PAGE_KEYS, PAGE_UI_LABELS
from .handlers import (
    current_clock,
    gas_banner_html,
    header_icon_html,
    logo_html,
    operating_initial_state,
    sidebar_status_html,
    wire_callbacks,
)
from .pages.data_logs_page import DataLogsPage, build_data_logs_page
from .pages.debugging_page import DebuggingPage, build_debugging_page
from .pages.onboarding_page import OnboardingPage, build_onboarding_page
from .pages.operating_page import OperatingPage, build_operating_page
from .pages.statistics_page import StatisticsPage, build_statistics_page

try:  # package import used by tests and python -m frontend.app
    from frontend.services.config import CAMERA_REFRESH_SECONDS
except ModuleNotFoundError:  # script mode: cd frontend then python app.py
    from services.config import CAMERA_REFRESH_SECONDS


@dataclass
class DashboardLayout:
    nav: gr.Radio
    header_icon: gr.HTML
    header_title: gr.Markdown
    header_subtitle: gr.Markdown
    lcd_button: gr.Button
    lcd_status: gr.Textbox
    clock: gr.Markdown
    timer: gr.Timer
    camera_timer: gr.Timer
    gas_banner: gr.HTML
    page_columns: list[gr.Column]
    operating: OperatingPage
    onboarding: OnboardingPage
    data_logs: DataLogsPage
    statistics: StatisticsPage
    debugging: DebuggingPage


def _build_shell() -> DashboardLayout:
    details = PAGE_DETAILS[DEFAULT_PAGE]

    with gr.Row(elem_id="app-shell"):
        with gr.Column(elem_id="sidebar", scale=0, min_width=180):
            gr.HTML(logo_html())
            nav = gr.Radio(
                choices=[(PAGE_UI_LABELS[key], key) for key in PAGE_KEYS],
                value=DEFAULT_PAGE,
                label="Navigation",
                elem_classes=["nav-radio"],
                interactive=True,
            )
            gr.HTML(sidebar_status_html())
            clock = gr.Markdown(current_clock(), elem_classes=["compact-md", "clock-line"])

        with gr.Column(elem_id="main-area", scale=1):
            with gr.Row(elem_id="top-header"):
                header_icon = gr.HTML(header_icon_html(DEFAULT_PAGE), scale=0, min_width=54, elem_id="header-icon")
                with gr.Column(scale=4):
                    header_title = gr.Markdown(f"### {PAGE_UI_LABELS[DEFAULT_PAGE]}", elem_classes=["header-title"])
                    header_subtitle = gr.Markdown(details["subtitle"], elem_classes=["header-subtitle"])
                with gr.Column(scale=0, min_width=152, elem_classes=["lcd-column"]):
                    lcd_button = gr.Button("Info LCD", size="md")
                    lcd_status = gr.Textbox(
                        value="LCD ready",
                        label=None,
                        interactive=False,
                        container=False,
                        elem_classes=["lcd-status"],
                    )

            gas_banner = gr.HTML(gas_banner_html(), elem_id="gas-banner")

            with gr.Column(elem_id="page-stack"):
                page_columns: list[gr.Column] = []

                with gr.Column(visible=DEFAULT_PAGE == "Operating", elem_classes=["page-pane"]) as operating_column:
                    operating = build_operating_page()
                page_columns.append(operating_column)

                with gr.Column(visible=DEFAULT_PAGE == "About", elem_classes=["page-pane"]) as onboarding_column:
                    onboarding = build_onboarding_page()
                page_columns.append(onboarding_column)

                with gr.Column(visible=DEFAULT_PAGE == "Data", elem_classes=["page-pane"]) as data_column:
                    data_logs = build_data_logs_page()
                page_columns.append(data_column)

                with gr.Column(visible=DEFAULT_PAGE == "Statistics", elem_classes=["page-pane"]) as statistics_column:
                    statistics = build_statistics_page()
                page_columns.append(statistics_column)

                with gr.Column(visible=DEFAULT_PAGE == "Debugging", elem_classes=["page-pane"]) as debugging_column:
                    debugging = build_debugging_page()
                page_columns.append(debugging_column)

    timer = gr.Timer(value=1.0, active=True)
    # Live-view polling (default 10 Hz, FRONTEND_CAMERA_REFRESH_SECONDS). Each tick is a
    # Gradio event that costs real CPU on the Pi, and that CPU is shared with the
    # detector, so this is deliberately not as fast as the camera (~15 fps).
    camera_timer = gr.Timer(value=CAMERA_REFRESH_SECONDS, active=True)

    return DashboardLayout(
        nav=nav,
        header_icon=header_icon,
        header_title=header_title,
        header_subtitle=header_subtitle,
        lcd_button=lcd_button,
        lcd_status=lcd_status,
        clock=clock,
        timer=timer,
        camera_timer=camera_timer,
        gas_banner=gas_banner,
        page_columns=page_columns,
        operating=operating,
        onboarding=onboarding,
        data_logs=data_logs,
        statistics=statistics,
        debugging=debugging,
    )


_RUNTIME_CSS_FIX = """() => {
    const s = document.createElement('style');
    s.id = 'sar-runtime-fixes';
    s.textContent = [
        /* slider_input_container is Gradio's Svelte-scoped div that holds the gray bg */
        '.slider_input_container { background: transparent !important; background-color: transparent !important; box-shadow: none !important; border: 0 !important; }',
        '.op-threshold .wrap { background: transparent !important; background-color: transparent !important; }',
        '.op-threshold.block, .op-threshold.block.padded { background: transparent !important; border: 0 !important; box-shadow: none !important; padding: 0 !important; }',
    ].join('');
    document.head.appendChild(s);
}"""

# When a .page-pane column transitions from display:none to visible, Plotly charts
# inside it have 0-dimension initialisation and render blank. Dispatching a resize
# event tells Plotly to recalculate dimensions and re-render correctly.
_PLOTLY_RESIZE_FIX = """() => {
    const fireResize = () => setTimeout(() => window.dispatchEvent(new Event('resize')), 200);
    const attach = () => {
        const panes = document.querySelectorAll('.page-pane');
        if (!panes.length) { setTimeout(attach, 400); return; }
        const obs = new MutationObserver(muts => {
            for (const m of muts) {
                if (m.target.style.display !== 'none') { fireResize(); return; }
            }
        });
        panes.forEach(p => obs.observe(p, { attributes: true, attributeFilter: ['style'] }));
    };
    attach();
}"""


def build_dashboard() -> gr.Blocks:
    # Gradio saves every refreshed camera image as a new file and never removes it
    # (~2 GB/hour at the live-view rate): sweep files older than 2 minutes every minute.
    with gr.Blocks(title=APP_TITLE, delete_cache=(60, 120)) as demo:
        layout = _build_shell()
        wire_callbacks(layout)
        demo.load(
            fn=operating_initial_state,
            inputs=None,
            outputs=[
                layout.operating.ai_state,
                layout.operating.cam_state,
                layout.operating.ai_btn,
                layout.operating.cam_btn,
                layout.operating.threshold,
                layout.operating.threshold_head,
                layout.operating.camera_output,
                layout.operating.camera_status,
                layout.operating.detection_count,
                layout.operating.fps_output,
                layout.operating.mission_duration,
                layout.operating.recent_html,
            ],
            show_progress="hidden",
        )
        demo.load(js=_RUNTIME_CSS_FIX)
        demo.load(js=_PLOTLY_RESIZE_FIX)
    return demo
