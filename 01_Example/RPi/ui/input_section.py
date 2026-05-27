from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from config import AppConfig
from inputs import INPUT_UPLOAD, RESOLUTION_OPTIONS, SPINNER_FRAMES, input_radio_choices


@dataclass
class InputSection:
    resolution: gr.Dropdown
    target_fps: gr.Slider
    shutdown_button: gr.Button
    latest_capture_frame: gr.State
    perf_state: gr.State
    input_source: gr.Radio
    rpi_note: gr.Markdown
    upload_input: gr.Image
    browser_webcam_input: gr.Image
    input_preview: gr.Image
    camera_status_output: gr.Textbox
    timer: gr.Timer


def build_input_section(cfg: AppConfig) -> InputSection:
    with gr.Row():
        resolution = gr.Dropdown(
            choices=list(RESOLUTION_OPTIONS),
            value=cfg.default_resolution,
            label="Preview resolution (USB / CSI)",
            visible=False,
        )
        target_fps = gr.Slider(
            minimum=1.0,
            maximum=cfg.max_target_fps,
            value=cfg.default_target_fps,
            step=1.0,
            label="Target preview FPS",
            visible=False,
        )
        shutdown_button = gr.Button("Shutdown Raspberry Pi")

    latest_capture_frame = gr.State(None)
    perf_state = gr.State({"spinner_idx": -1, "label": SPINNER_FRAMES[0]})

    gr.Markdown("### Input")
    input_source = gr.Radio(choices=input_radio_choices(), value=INPUT_UPLOAD, label="Input source")
    rpi_note = gr.Markdown("", visible=False)
    upload_input = gr.Image(type="numpy", label="Upload image (browser)", visible=True)
    browser_webcam_input = gr.Image(type="numpy", sources=["webcam"], label="Browser webcam", visible=False)
    input_preview = gr.Image(label="Camera feed", visible=False)
    camera_status_output = gr.Textbox(label="Camera status", value="RPi camera idle.", visible=False)
    timer = gr.Timer(value=1.0 / cfg.default_target_fps)

    return InputSection(
        resolution=resolution,
        target_fps=target_fps,
        shutdown_button=shutdown_button,
        latest_capture_frame=latest_capture_frame,
        perf_state=perf_state,
        input_source=input_source,
        rpi_note=rpi_note,
        upload_input=upload_input,
        browser_webcam_input=browser_webcam_input,
        input_preview=input_preview,
        camera_status_output=camera_status_output,
        timer=timer,
    )
