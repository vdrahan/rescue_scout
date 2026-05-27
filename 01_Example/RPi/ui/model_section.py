from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from models.registry import MODEL_POSE, MODEL_YOLO


@dataclass
class ModelSection:
    model_tabs: gr.Tabs
    selected_model: gr.Radio  # synced to runtime on tab/radio change (not GPIO timer input)
    yolo_conf: gr.Slider
    yolo_iou: gr.Slider
    yolo_run: gr.Button
    yolo_output: gr.Image
    yolo_count_output: gr.Textbox
    pose_run: gr.Button
    pose_output: gr.Image


def tab_value_to_model(value: Any) -> str:
    """Map Tabs value (id, label, or index) to MODEL_* — used by select event and GPIO timer."""
    if value is None:
        return MODEL_YOLO
    if isinstance(value, int):
        return MODEL_YOLO if value == 0 else MODEL_POSE
    token = str(value).strip().lower()
    if token in (MODEL_YOLO, "yolo", "0"):
        return MODEL_YOLO
    if token in (MODEL_POSE, "pose", "1"):
        return MODEL_POSE
    if "yolo" in token or "drone" in token or "best.pt" in token:
        return MODEL_YOLO
    if "pose" in token or "mediapipe" in token:
        return MODEL_POSE
    return MODEL_YOLO


def _tab_id_to_model(evt: gr.SelectData) -> str:
    return tab_value_to_model(evt.value)


def model_to_tab_id(model_id: str) -> str:
    return MODEL_YOLO if tab_value_to_model(model_id) == MODEL_YOLO else MODEL_POSE


def build_model_section() -> ModelSection:
    gr.Markdown("### Model")
    selected_model = gr.Radio(
        choices=[("Drone YOLO", MODEL_YOLO), ("MediaPipe Pose", MODEL_POSE)],
        value=MODEL_YOLO,
        label="GPIO short press runs",
    )
    with gr.Tabs() as model_tabs:
        with gr.TabItem("Drone YOLO (best.pt)", id="yolo"):
            with gr.Row():
                yolo_conf = gr.Slider(0.0, 1.0, value=0.25, step=0.05, label="Confidence threshold")
                yolo_iou = gr.Slider(0.0, 1.0, value=0.45, step=0.05, label="IoU threshold")
            yolo_run = gr.Button("Run Drone YOLO", variant="primary")
            yolo_output = gr.Image(label="YOLO output", type="numpy")
            yolo_count_output = gr.Textbox(label="Drone count summary", lines=2)

        with gr.TabItem("MediaPipe Pose", id="pose"):
            pose_run = gr.Button("Run Pose Detection", variant="primary")
            pose_output = gr.Image(label="Pose output", type="numpy")

    return ModelSection(
        model_tabs=model_tabs,
        selected_model=selected_model,
        yolo_conf=yolo_conf,
        yolo_iou=yolo_iou,
        yolo_run=yolo_run,
        yolo_output=yolo_output,
        yolo_count_output=yolo_count_output,
        pose_run=pose_run,
        pose_output=pose_output,
    )
