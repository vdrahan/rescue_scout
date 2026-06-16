from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from ..handlers import recent_detections_html, threshold_head_html


@dataclass
class OperatingPage:
    ai_state: gr.State
    cam_state: gr.State
    ai_btn: gr.Button
    cam_btn: gr.Button
    threshold_head: gr.HTML
    threshold: gr.Slider
    camera_output: gr.Image
    camera_status: gr.HTML
    detection_count: gr.Number
    fps_output: gr.Number
    mission_duration: gr.Textbox
    recent_html: gr.HTML
    reset_log_button: gr.Button
    view_all_button: gr.Button


def build_operating_page() -> OperatingPage:
    ai_state = gr.State(value=False)
    cam_state = gr.State(value="detection")

    with gr.Row(elem_classes=["op-controls-row"], equal_height=True):
        with gr.Column(min_width=0, elem_classes=["control-card", "op-control-cell"]):
            gr.HTML("<span class='op-control-label'>AI Detection</span>")
            ai_btn = gr.Button("AI Off", variant="secondary", size="sm", elem_classes=["op-toggle-btn", "op-ai-btn"])
        with gr.Column(min_width=0, elem_classes=["control-card", "op-control-cell"]):
            gr.HTML("<span class='op-control-label'>Camera Feed</span>")
            cam_btn = gr.Button("Camera: Detection Camera", size="sm", elem_classes=["op-toggle-btn", "op-cam-btn"])
        with gr.Column(min_width=0, elem_classes=["control-card", "op-control-cell", "op-threshold-cell"]):
            threshold_head = gr.HTML(threshold_head_html(45))
            threshold = gr.Slider(
                0, 100, value=45, step=5,
                label="Confidence threshold",
                show_label=False,
                elem_id="op-threshold-slider",
                elem_classes=["op-threshold"],
            )

    camera_output = gr.Image(
        value=None,
        show_label=False,
        type="pil",
        height=400,
        interactive=False,
        elem_classes=["camera-image", "camera-fullwidth"],
    )
    camera_status = gr.HTML(
        "<div class='op-camera-status op-camera-status-error'>Station unavailable</div>",
        elem_classes=["op-camera-status-wrap"],
    )

    with gr.Row(elem_classes=["op-stats-row"]):
        with gr.Column(scale=1, min_width=200):
            with gr.Group(elem_classes=["app-card"]):
                gr.HTML('<h3 class="op-section-title">📊 Live Stats</h3>')
                with gr.Row():
                    detection_count = gr.Number(value=0, label="Detections", interactive=False, elem_classes=["stat-number"])
                    fps_output = gr.Number(value=0, label="AI FPS", interactive=False, elem_classes=["stat-number"])
                    mission_duration = gr.Textbox(value="Station unavailable", label="Mission Duration", interactive=False, lines=1)

        with gr.Column(scale=2, min_width=300, elem_classes=["recent-outer-col"]):
            with gr.Group(elem_classes=["app-card", "recent-group"]):
                recent_html = gr.HTML(
                    value=recent_detections_html([], "Station unavailable"),
                    elem_classes=["recent-html-wrap"],
                )
                with gr.Row(elem_classes=["recent-btn-row"]):
                    reset_log_button = gr.Button("Reset Log", size="md")
                    view_all_button = gr.Button("View All", variant="primary", size="md")

    return OperatingPage(
        ai_state=ai_state,
        cam_state=cam_state,
        ai_btn=ai_btn,
        cam_btn=cam_btn,
        threshold_head=threshold_head,
        threshold=threshold,
        camera_output=camera_output,
        camera_status=camera_status,
        detection_count=detection_count,
        fps_output=fps_output,
        mission_duration=mission_duration,
        recent_html=recent_html,
        reset_log_button=reset_log_button,
        view_all_button=view_all_button,
    )
