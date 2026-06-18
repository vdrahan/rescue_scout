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
    system_events_html,
)


@dataclass
class DataLogsPage:
    gas_kpi: gr.HTML
    gas_history_plot: gr.Plot
    class_dist_plot: gr.Plot
    class_filter: gr.Dropdown
    detection_table: gr.HTML
    gas_table: gr.HTML
    export_button: gr.Button
    export_banner: gr.HTML


def build_data_logs_page() -> DataLogsPage:
    cards = data_kpi_cards()
    with gr.Row(elem_classes=["kpi-row"]):
        # First 3 cards are static (don't change second-to-second)
        for label, value, note, color in cards:
            with gr.Column(elem_classes=["metric-card"], min_width=150):
                gr.Markdown(metric_html(label, value, note, color), elem_classes=["compact-md"])
        # Gas Alerts card is a tracked gr.HTML so the timer can update it
        with gr.Column(elem_classes=["metric-card"], min_width=150):
            gas_kpi = gr.HTML(value=gas_kpi_card_html(), elem_classes=["compact-md"])

    with gr.Row(elem_classes=["data-chart-row"]):
        with gr.Column(scale=1, min_width=300, elem_classes=["app-card", "plot-cell"]):
            gas_history_plot = gr.Plot(value=gas_history_figure(), show_label=False, elem_classes=["plot-card"])
        with gr.Column(scale=1, min_width=300, elem_classes=["app-card", "plot-cell"]):
            class_dist_plot = gr.Plot(value=class_distribution_figure(), show_label=False, elem_classes=["plot-card"])

    with gr.Group(elem_classes=["app-card", "logs-card"]):
        export_banner = gr.HTML(value="", visible=False, elem_classes=["export-banner-wrap"])

        with gr.Row(elem_classes=["logs-header"]):
            gr.HTML(
                "<div class='logs-title'><span class='logs-title-main'>Stored Logs</span>"
                "<span class='logs-title-sub'>Detection, system, and gas alert history</span></div>"
            )
            with gr.Column(scale=0, min_width=140, elem_classes=["logs-export-col"]):
                export_button = gr.Button("Export CSV", variant="primary", size="md")

        with gr.Column(elem_classes=["logs-filter-col-top"]):
            class_filter = gr.Dropdown(
                CANONICAL_CLASS_CHOICES, value="All classes", label="Class filter",
                elem_classes=["logs-filter"],
            )

        with gr.Accordion("Detection Events", open=True, elem_classes=["logs-accordion"]):
            detection_table = gr.HTML(
                value=detection_events_html("All classes"),
                elem_classes=["log-table-container"],
            )

        with gr.Accordion("System Events", open=False, elem_classes=["logs-accordion"]):
            gr.HTML(
                value=system_events_html(),
                elem_classes=["log-table-container"],
            )

        with gr.Accordion("Gas Alerts", open=True, elem_classes=["logs-accordion"]):
            gas_table = gr.HTML(
                value=gas_alerts_html(),
                elem_classes=["log-table-container"],
            )

    return DataLogsPage(
        gas_kpi=gas_kpi,
        gas_history_plot=gas_history_plot,
        class_dist_plot=class_dist_plot,
        class_filter=class_filter,
        detection_table=detection_table,
        gas_table=gas_table,
        export_button=export_button,
        export_banner=export_banner,
    )
