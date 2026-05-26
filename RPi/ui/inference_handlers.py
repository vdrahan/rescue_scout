from __future__ import annotations

import threading
import time
from typing import Any

import gradio as gr
import numpy as np

from hardware.network import request_sudo_poweroff
from inputs import pick_source_frame
from models.registry import MODEL_POSE, MODEL_YOLO
from ui.constants import ERROR_DELETE_BUTTON_SLOTS
from ui.context import AppContext
from ui.history import HistoryStore, render_history_accordion
from ui.model_section import model_to_tab_id, tab_value_to_model

# Must match gpio_timer.tick outputs in ui/dashboard.py (18 total).
_GPIO_DISPATCH_OUTPUT_COUNT = 10 + ERROR_DELETE_BUTTON_SLOTS  # 3 model + 6 shared + tabs + delete buttons


def _pack_yolo_gpio_outputs(yolo_out: tuple) -> tuple:
    return (
        yolo_out[0],
        yolo_out[1],
        gr.update(),
        *yolo_out[2:],
        gr.Tabs(selected=model_to_tab_id(MODEL_YOLO)),
    )


def _pack_pose_gpio_outputs(pose_out: tuple) -> tuple:
    return (
        gr.update(),
        gr.update(),
        pose_out[0],
        *pose_out[1:],
        gr.Tabs(selected=model_to_tab_id(MODEL_POSE)),
    )


class InferenceHandlers:
    def __init__(self, ctx: AppContext, history: HistoryStore) -> None:
        self._ctx = ctx
        self._history = history

    def shutdown_now(self) -> str:
        if not self._ctx.shared.mark_shutdown():
            return "Shutdown already requested."
        self._ctx.lcd.show_shutdown()

        def _worker() -> None:
            time.sleep(0.5)
            request_sudo_poweroff()

        threading.Thread(target=_worker, daemon=True).start()
        return "Shutdown requested."

    @staticmethod
    def _gpio_dispatch_no_op():
        return (gr.update(),) * _GPIO_DISPATCH_OUTPUT_COUNT

    def sync_selected_model(self, model: str) -> str:
        """Keep runtime + UI radio aligned (tab select, radio, run buttons)."""
        model_id = tab_value_to_model(model)
        self._ctx.runtime.set_selected_model(model_id)
        return model_id

    def on_gpio_short_press(self) -> None:
        # Called from GPIO poll thread — only set a flag; Gradio runs inference via Timer.
        if self._ctx.runtime.request_gpio_inference():
            snap = self._ctx.runtime.read_inference_snapshot()
            print(f"[GPIO] Short press -> queue {snap.selected_model} inference")

    def dispatch_gpio_inference(
        self,
        source_type: str,
        latest_capture_rgb: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
        yolo_conf: float,
        yolo_iou: float,
        ai_history: list[dict[str, Any]],
        error_history: list[dict[str, Any]],
    ):
        self._ctx.runtime.sync_gradio_state(
            source_type,
            latest_capture_rgb,
            upload_rgb,
            browser_webcam_rgb,
            yolo_conf,
            yolo_iou,
            ai_history,
            error_history,
        )
        gpio_model = self._ctx.runtime.take_gpio_model()
        if gpio_model is None:
            return self._gpio_dispatch_no_op()

        snap = self._ctx.runtime.read_inference_snapshot()
        print(f"[GPIO] Running inference for model={gpio_model!r}")

        if gpio_model == MODEL_YOLO:
            yolo_out = self.run_yolo(
                snap.source_type,
                snap.latest_capture_rgb,
                snap.upload_rgb,
                snap.browser_webcam_rgb,
                snap.yolo_conf,
                snap.yolo_iou,
                snap.ai_history,
                snap.error_history,
            )
            return _pack_yolo_gpio_outputs(yolo_out)

        if gpio_model == MODEL_POSE:
            pose_out = self.run_pose(
                snap.source_type,
                snap.latest_capture_rgb,
                snap.upload_rgb,
                snap.browser_webcam_rgb,
                snap.ai_history,
                snap.error_history,
            )
            return _pack_pose_gpio_outputs(pose_out)

        print(f"[GPIO] Unknown model {gpio_model!r}; no inference run.")
        return self._gpio_dispatch_no_op()

    def run_yolo(
        self,
        source_type: str,
        latest_capture_rgb: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
        conf: float,
        iou: float,
        ai_history: list[dict[str, Any]],
        error_history: list[dict[str, Any]],
        
    ):
        try:
            src_rgb = pick_source_frame(
                self._ctx.providers,
                source_type,
                latest_capture_rgb,
                upload_rgb,
                browser_webcam_rgb,
            )
            result = self._ctx.models[MODEL_YOLO].run(src_rgb, conf=conf, iou=iou)
            det_count = int(result.payload.get("detection_count", 0))
            counts = result.payload.get("counts", {})

            drone_count = int(counts.get("Drone", 0)) if isinstance(counts, dict) else 0
            worker_count = int(counts.get("Worker", 0)) if isinstance(counts, dict) else 0
            bee_count = drone_count + worker_count
            self._ctx.lcd.show_result(f"Bees: {bee_count}")
            # Extend hardware feedback here (after you wire it in bootstrap/setup):
            #   self._ctx.buzzer.play("success")  # hardware/buzzer.py
            #   self._ctx.segment.set_number(drone_count)  # hardware/seven_segment.py
            #   neo_ring.set_count(drone_count)  # pi5-neo — RPi/docs/hardware-extensions.md
            payload = {**result.payload, "source_type": source_type}
            ai_history = self._history.append_ai(
                ai_history, "Drone YOLO response", payload, result.annotated_rgb
            )
            return (
                result.annotated_rgb,
                f"Total detections: {det_count}\nDrone: {drone_count}",
                result.status_text,
                self._history.server_status_update(payload),
                ai_history,
                error_history,
                render_history_accordion("AI responses", ai_history),
                gr.update(),
                *self._history.error_button_updates(error_history),
            )
        except Exception as exc:
            msg = str(exc)
            self._ctx.lcd.show_result("yolo error")
            error_history = self._history.append_error(error_history, "YOLO inference failed", msg)
            return (
                None,
                "",
                f"YOLO error: {msg}",
                self._history.server_status_update({"error": msg, "model": "best.pt"}),
                ai_history,
                error_history,
                gr.update(),
                render_history_accordion("Errors", error_history),
                *self._history.error_button_updates(error_history),
            )

    def run_pose(
        self,
        source_type: str,
        latest_capture_rgb: np.ndarray | None,
        upload_rgb: np.ndarray | None,
        browser_webcam_rgb: np.ndarray | None,
        ai_history: list[dict[str, Any]],
        error_history: list[dict[str, Any]],
    ):
        try:
            src_rgb = pick_source_frame(
                self._ctx.providers,
                source_type,
                latest_capture_rgb,
                upload_rgb,
                browser_webcam_rgb,
            )
            result = self._ctx.models[MODEL_POSE].run(src_rgb)
            lm_count = int(result.payload.get("landmark_count", 0))
            self._ctx.lcd.show_result(f"lm: {lm_count}" if lm_count else "no person")
            payload = {**result.payload, "source_type": source_type}
            ai_history = self._history.append_ai(
                ai_history, "MediaPipe Pose response", payload, result.annotated_rgb
            )
            return (
                result.annotated_rgb,
                result.status_text,
                self._history.server_status_update(payload),
                ai_history,
                error_history,
                render_history_accordion("AI responses", ai_history),
                gr.update(),
                *self._history.error_button_updates(error_history),
            )
        except Exception as exc:
            msg = str(exc)
            self._ctx.lcd.show_result("pose error")
            error_history = self._history.append_error(error_history, "Pose inference failed", msg)
            return (
                None,
                f"Pose error: {msg}",
                self._history.server_status_update({"error": msg, "model": "mediapipe_pose"}),
                ai_history,
                error_history,
                gr.update(),
                render_history_accordion("Errors", error_history),
                *self._history.error_button_updates(error_history),
            )
