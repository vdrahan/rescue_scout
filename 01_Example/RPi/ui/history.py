from __future__ import annotations

import base64
import html
import json
import time
from typing import Any

import cv2
import gradio as gr
import numpy as np

from ui.constants import ERROR_DELETE_BUTTON_SLOTS, MAX_HISTORY_ITEMS


def frame_to_b64(image_rgb: np.ndarray) -> str:
    bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("ascii")


def render_history_accordion(title: str, items: list[dict[str, Any]]) -> str:
    blocks = [f"<div><strong>{html.escape(title)}</strong></div>"]
    if not items:
        blocks.append("<div><em>No entries yet.</em></div>")
        return "".join(blocks)
    for idx, item in enumerate(items):
        ts = str(item.get("timestamp", ""))
        summary_base = str(item.get("summary", f"Entry {idx + 1}"))
        summary = html.escape(f"[{ts}] {summary_base}" if ts else summary_base)
        details = html.escape(str(item.get("details", "")))
        image_b64 = item.get("image_base64")
        image_html = ""
        if isinstance(image_b64, str) and image_b64:
            image_html = (
                "<div style='margin-top:8px;'>"
                f"<img src='data:image/jpeg;base64,{image_b64}' style='max-width:100%; max-height:280px; border-radius:6px;'/>"
                "</div>"
            )
        blocks.append(
            f"<details {'open' if idx == 0 else ''}>"
            f"<summary>{summary}</summary>"
            f"<pre style='white-space: pre-wrap; margin: 6px 0 0 0;'>{details}</pre>"
            f"{image_html}</details>"
        )
    return "".join(blocks)


class HistoryStore:
    def now_hms(self) -> str:
        return time.strftime("%H:%M:%S")

    def server_status_update(self, payload: dict[str, Any]) -> Any:
        return gr.update(value=payload, label=f"Server status/response ({self.now_hms()})")

    def append_ai(
        self,
        ai_history: list[dict[str, Any]],
        summary: str,
        details: dict[str, Any],
        image_rgb: np.ndarray | None,
    ) -> list[dict[str, Any]]:
        entry: dict[str, Any] = {
            "summary": summary,
            "details": json.dumps(details, indent=2),
            "timestamp": self.now_hms(),
        }
        if image_rgb is not None:
            image_b64 = frame_to_b64(image_rgb)
            if image_b64:
                entry["image_base64"] = image_b64
        return [entry, *ai_history][:MAX_HISTORY_ITEMS]

    def append_error(
        self,
        error_history: list[dict[str, Any]],
        summary: str,
        details: str,
    ) -> list[dict[str, Any]]:
        entry = {"summary": summary, "details": details, "timestamp": self.now_hms()}
        return [entry, *error_history][:MAX_HISTORY_ITEMS]

    def error_button_updates(self, error_history: list[dict[str, Any]]) -> list[Any]:
        updates: list[Any] = []
        for i in range(ERROR_DELETE_BUTTON_SLOTS):
            if i < len(error_history):
                summary = str(error_history[i].get("summary", "Error"))
                updates.append(gr.update(value=f"x {i}: {summary[:40]}", visible=True))
            else:
                updates.append(gr.update(value="x", visible=False))
        return updates

    def delete_error_at_index(
        self,
        error_history: list[dict[str, Any]],
        index: int,
    ) -> tuple[list[dict[str, Any]], str, list[Any]]:
        if 0 <= index < len(error_history):
            del error_history[index]
        return (
            error_history,
            render_history_accordion("Errors", error_history),
            *self.error_button_updates(error_history),
        )
