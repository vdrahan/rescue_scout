from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from ..handlers import (
    CANONICAL_CLASS_CHOICES,
    class_distribution_figure,
    data_kpi_cards,
    gas_kpi_card_html,
    detection_events_html,
    gas_alerts_html,
    gas_history_figure,
    metric_html,
)


@dataclass
class DataLogsPage:
    gas_kpi: gr.HTML
    gas_history_plot: gr.Plot
    class_dist_plot: gr.Plot
    class_filter: gr.Dropdown
    detection_export_button: gr.Button
    detection_export_file: gr.File
    detection_table: gr.HTML
    gas_export_button: gr.Button
    gas_export_file: gr.File
    gas_table: gr.HTML


def build_data_logs_page() -> DataLogsPage:
    cards = data_kpi_cards()
    with gr.Row(elem_classes=["kpi-row"]):
        # First 2 cards are static (don't change second-to-second)
        for label, value, note, color in cards:
            with gr.Column(elem_classes=["metric-card"], scale=1, min_width=200):
                gr.Markdown(metric_html(label, value, note, color), elem_classes=["compact-md"])
        # Gas Alerts card is a tracked gr.HTML so the timer can update it
        with gr.Column(elem_classes=["metric-card"], scale=1, min_width=200):
            gas_kpi = gr.HTML(value=gas_kpi_card_html(), elem_classes=["compact-md"])

    with gr.Row(elem_classes=["data-chart-row"]):
        with gr.Column(scale=1, min_width=300, elem_classes=["app-card", "plot-cell"]):
            gas_history_plot = gr.Plot(value=gas_history_figure(), show_label=False, elem_classes=["plot-card"])
        with gr.Column(scale=1, min_width=300, elem_classes=["app-card", "plot-cell"]):
            class_dist_plot = gr.Plot(value=class_distribution_figure(), show_label=False, elem_classes=["plot-card"])

    with gr.Group(elem_classes=["app-card", "logs-card"]):
        with gr.Row(elem_classes=["logs-header"]):
            gr.HTML(
                "<div class='logs-title'><span class='logs-title-main'>Data</span>"
                "<span class='logs-title-sub'>Detection and gas alert history</span></div>"
            )

        with gr.Accordion("🎯 Detection Events", open=True, elem_classes=["logs-accordion"]):
            with gr.Row(elem_classes=["logs-filter-row"]):
                with gr.Column(scale=1):
                    class_filter = gr.Dropdown(
                        CANONICAL_CLASS_CHOICES, value="All classes", label="Class filter",
                        elem_classes=["logs-filter"],
                    )
                with gr.Column(scale=0, min_width=140, elem_classes=["logs-export-col"]):
                    detection_export_button = gr.Button("Export CSV", variant="primary", size="md")
            detection_export_file = gr.File(visible=False, label="Download")
            detection_table = gr.HTML(
                value=detection_events_html("All classes"),
                elem_classes=["log-table-container"],
            )

        with gr.Accordion("☢️ Gas Alerts", open=True, elem_classes=["logs-accordion"]):
            with gr.Row(elem_classes=["logs-filter-row"]):
                with gr.Column(scale=0, min_width=140, elem_classes=["logs-export-col"]):
                    gas_export_button = gr.Button("Export CSV", variant="primary", size="md")
            gas_export_file = gr.File(visible=False, label="Download")
            gas_table = gr.HTML(
                value=gas_alerts_html(),
                elem_classes=["log-table-container"],
            )

    return DataLogsPage(
        gas_kpi=gas_kpi,
        gas_history_plot=gas_history_plot,
        class_dist_plot=class_dist_plot,
        class_filter=class_filter,
        detection_export_button=detection_export_button,
        detection_export_file=detection_export_file,
        detection_table=detection_table,
        gas_export_button=gas_export_button,
        gas_export_file=gas_export_file,
        gas_table=gas_table,
    )
