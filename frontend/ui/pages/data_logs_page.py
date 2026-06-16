from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from ..constants import (
    DETECTION_HEADERS,
    GAS_ALERT_HEADERS,
    SYSTEM_EVENT_HEADERS,
)
from ..handlers import (
    CANONICAL_CLASS_CHOICES,
    class_distribution_figure,
    data_kpi_cards,
    filter_detection_events,
    gas_alert_rows,
    gas_history_figure,
    metric_html,
    system_event_rows,
)


@dataclass
class DataLogsPage:
    class_filter: gr.Dropdown
    detection_table: gr.Dataframe
    export_button: gr.Button
    export_banner: gr.HTML


def build_data_logs_page() -> DataLogsPage:
    with gr.Row(elem_classes=["kpi-row"]):
        for label, value, note, color in data_kpi_cards():
            with gr.Column(elem_classes=["metric-card"], min_width=150):
                gr.Markdown(metric_html(label, value, note, color), elem_classes=["compact-md"])

    with gr.Row(elem_classes=["data-chart-row"]):
        with gr.Column(scale=1, min_width=300, elem_classes=["app-card", "plot-cell"]):
            gr.Plot(value=gas_history_figure(), show_label=False, elem_classes=["plot-card"])
        with gr.Column(scale=1, min_width=300, elem_classes=["app-card", "plot-cell"]):
            gr.Plot(value=class_distribution_figure(), show_label=False, elem_classes=["plot-card"])

    with gr.Group(elem_classes=["app-card", "logs-card"]):
        export_banner = gr.HTML(value="", visible=False, elem_classes=["export-banner-wrap"])

        with gr.Row(elem_classes=["logs-header"]):
            gr.HTML(
                "<div class='logs-title'><span class='logs-title-main'>Stored Logs</span>"
                "<span class='logs-title-sub'>Detection, system, and gas alert history</span></div>"
            )
            with gr.Column(scale=0, min_width=140, elem_classes=["logs-export-col"]):
                export_button = gr.Button("Export CSV", variant="primary", size="md")

        with gr.Row(elem_classes=["logs-nav-row"]):
            with gr.Column(scale=1, elem_classes=["logs-tabs-col"]):
                with gr.Tabs(elem_classes=["logs-tabs"]):
                    with gr.TabItem("Detection Events"):
                        detection_table = gr.Dataframe(
                            value=filter_detection_events("All classes"),
                            headers=DETECTION_HEADERS,
                            interactive=False,
                            row_count=7,
                            column_count=6,
                            elem_classes=["compact-table"],
                        )
                    with gr.TabItem("System Events"):
                        gr.Dataframe(
                            value=system_event_rows(),
                            headers=SYSTEM_EVENT_HEADERS,
                            interactive=False,
                            row_count=6,
                            column_count=4,
                            elem_classes=["compact-table"],
                        )
                    with gr.TabItem("Gas Alerts"):
                        gr.Dataframe(
                            value=gas_alert_rows(),
                            headers=GAS_ALERT_HEADERS,
                            interactive=False,
                            row_count=4,
                            column_count=4,
                            elem_classes=["compact-table"],
                        )
            with gr.Column(scale=0, min_width=220, elem_classes=["logs-filter-col"]):
                class_filter = gr.Dropdown(
                    CANONICAL_CLASS_CHOICES, value="All classes", label="Class filter",
                    elem_classes=["logs-filter"],
                )

    return DataLogsPage(
        class_filter=class_filter,
        detection_table=detection_table,
        export_button=export_button,
        export_banner=export_banner,
    )
