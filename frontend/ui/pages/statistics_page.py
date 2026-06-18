from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from ..handlers import build_statistics_figure, overview_figure


@dataclass
class StatisticsPage:
    source: gr.Radio
    chart_type: gr.Radio
    main_plot: gr.Plot


def build_statistics_page() -> StatisticsPage:
    with gr.Group(elem_classes=["app-card"]):
        with gr.Row():
            source = gr.Radio(["Detections", "Gas Alerts", "Temperature"], value="Detections", label="Data source")
            chart_type = gr.Radio(["Line", "Bar", "Scatter", "Area", "Histogram"], value="Line", label="Chart type")
        main_plot = gr.Plot(value=build_statistics_figure("Detections", "Line"), show_label=False, elem_classes=["plot-card"])

    gr.Markdown("### Overview", elem_classes=["compact-md"])
    with gr.Row():
        gr.Plot(value=overview_figure("detections"), show_label=False)
        gr.Plot(value=overview_figure("gas"), show_label=False)
    with gr.Row():
        gr.Plot(value=overview_figure("classes"), show_label=False)
        gr.Plot(value=overview_figure("temperature"), show_label=False)

    return StatisticsPage(source=source, chart_type=chart_type, main_plot=main_plot)
