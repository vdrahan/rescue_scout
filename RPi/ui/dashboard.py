from __future__ import annotations

import gradio as gr

from hardware.setup import start_gpio
from models.registry import MODEL_POSE, MODEL_YOLO
from ui.context import AppContext
from ui.history import HistoryStore
from ui.inference_handlers import InferenceHandlers
from ui.input_handlers import InputHandlers
from ui.input_section import build_input_section
from ui.model_section import build_model_section
from ui.model_section import model_to_tab_id, tab_value_to_model
from ui.output_section import build_output_section


def _wire_callbacks(inp, model, out, input_handlers, inference, history) -> None:
    inp.shutdown_button.click(
        fn=inference.shutdown_now,
        inputs=None,
        outputs=[out.status_output],
        show_progress="hidden",
    )

    inp.target_fps.change(
        fn=input_handlers.timer_interval_update,
        inputs=[inp.target_fps],
        outputs=[inp.timer],
        show_progress="hidden",
    )
    inp.timer.tick(
        fn=input_handlers.sync_video_preview,
        inputs=[
            inp.resolution,
            inp.input_source,
            inp.browser_webcam_input,
            inp.latest_capture_frame,
            inp.perf_state,
            inp.target_fps,
        ],
        outputs=[
            inp.input_preview,
            inp.camera_status_output,
            inp.latest_capture_frame,
            inp.perf_state,
        ],
        show_progress="hidden",
    )
    inp.input_source.change(
        fn=input_handlers.source_visibility,
        inputs=[inp.input_source],
        outputs=[
            inp.rpi_note,
            inp.upload_input,
            inp.browser_webcam_input,
            inp.input_preview,
            inp.camera_status_output,
            inp.resolution,
            inp.target_fps,
        ],
        show_progress="hidden",
    )

    def on_model_tab(evt: gr.SelectData) -> str:
        return inference.sync_selected_model(tab_value_to_model(evt.value))

    def on_gpio_model_radio(model: str) -> tuple[str, dict]:
        model_id = inference.sync_selected_model(model)
        return model_id, gr.Tabs(selected=model_to_tab_id(model_id))

    model.model_tabs.select(on_model_tab, None, model.selected_model, show_progress="hidden")
    model.selected_model.change(
        fn=on_gpio_model_radio,
        inputs=[model.selected_model],
        outputs=[model.selected_model, model.model_tabs],
        show_progress="hidden",
    )

    model.yolo_run.click(
        lambda: inference.sync_selected_model(MODEL_YOLO),
        None,
        model.selected_model,
        show_progress="hidden",
    )
    model.pose_run.click(
        lambda: inference.sync_selected_model(MODEL_POSE),
        None,
        model.selected_model,
        show_progress="hidden",
    )

    model.yolo_run.click(
        fn=inference.run_yolo,
        inputs=[
            inp.input_source,
            inp.latest_capture_frame,
            inp.upload_input,
            inp.browser_webcam_input,
            model.yolo_conf,
            model.yolo_iou,
            out.ai_history_state,
            out.error_history_state,
        ],
        outputs=[
            model.yolo_output,
            model.yolo_count_output,
            out.status_output,
            out.server_status_output,
            out.ai_history_state,
            out.error_history_state,
            out.ai_accordion_output,
            out.error_accordion_output,
            *out.error_delete_buttons,
        ],
        show_progress="hidden",
    )
    model.pose_run.click(
        fn=inference.run_pose,
        inputs=[
            inp.input_source,
            inp.latest_capture_frame,
            inp.upload_input,
            inp.browser_webcam_input,
            out.ai_history_state,
            out.error_history_state,
        ],
        outputs=[
            model.pose_output,
            out.status_output,
            out.server_status_output,
            out.ai_history_state,
            out.error_history_state,
            out.ai_accordion_output,
            out.error_accordion_output,
            *out.error_delete_buttons,
        ],
        show_progress="hidden",
    )

    gpio_timer = gr.Timer(value=0.15, active=True)
    gpio_timer.tick(
        fn=inference.dispatch_gpio_inference,
        inputs=[
            inp.input_source,
            inp.latest_capture_frame,
            inp.upload_input,
            inp.browser_webcam_input,
            model.yolo_conf,
            model.yolo_iou,
            out.ai_history_state,
            out.error_history_state,
        ],
        outputs=[
            model.yolo_output,
            model.yolo_count_output,
            model.pose_output,
            out.status_output,
            out.server_status_output,
            out.ai_history_state,
            out.error_history_state,
            out.ai_accordion_output,
            out.error_accordion_output,
            *out.error_delete_buttons,
            model.model_tabs,
        ],
        show_progress="hidden",
    )

    for idx, delete_button in enumerate(out.error_delete_buttons):
        delete_button.click(
            fn=lambda errors, idx=idx: history.delete_error_at_index(errors, idx),
            inputs=[out.error_history_state],
            outputs=[out.error_history_state, out.error_accordion_output, *out.error_delete_buttons],
            show_progress="hidden",
        )


def build_dashboard(ctx: AppContext) -> tuple[gr.Blocks, InferenceHandlers]:
    history = HistoryStore()
    input_handlers = InputHandlers(ctx)
    inference = InferenceHandlers(ctx, history)

    with gr.Blocks(title="RPi Local Multi-Model Dashboard") as demo:
        gr.Markdown("## RPi Local Multi-Model Dashboard")
        inp = build_input_section(ctx.cfg)
        model = build_model_section()
        out = build_output_section()
        _wire_callbacks(inp, model, out, input_handlers, inference, history)
        demo.load(
            fn=lambda: inference.sync_selected_model(MODEL_YOLO),
            inputs=None,
            outputs=model.selected_model,
            show_progress="hidden",
        )

    ctx.gpio = start_gpio(
        ctx.cfg,
        on_short_press=inference.on_gpio_short_press,
        on_hold_press=inference.shutdown_now,
    )
    return demo, inference


def launch_dashboard(ctx: AppContext, demo: gr.Blocks) -> None:
    demo.queue().launch(
        server_name=ctx.cfg.gradio_host,
        server_port=ctx.cfg.gradio_port,
        show_error=True,
    )
