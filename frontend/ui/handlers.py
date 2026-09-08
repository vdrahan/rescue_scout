from __future__ import annotations

import base64
import csv
import html
import tempfile
from datetime import datetime
from typing import Any

import gradio as gr
import plotly.graph_objects as go

from .constants import (
    ASSET_LOGO,
    BLUE,
    DEFAULT_PAGE,
    GREEN,
    ORANGE,
    PAGE_DETAILS,
    PAGE_RENDER_ORDER,
    PAGE_UI_LABELS,
    PURPLE,
    RED,
    TEST_IDS,
    TEST_LOOKUP,
    YELLOW,
)

try:  # package import used by tests and python -m frontend.app
    from frontend.services import api_client
    from frontend.services.config import AUTO_START_DETECTION
except ModuleNotFoundError:  # script mode: cd frontend then python app.py
    from services import api_client
    from services.config import AUTO_START_DETECTION


_PRIORITY = {
    "lying_person": "HIGH",
    "crawling_person": "HIGH",
    "sitting_person": "MEDIUM",
    "partially_visible_person": "MEDIUM",
    "standing_person": "LOW",
}
_CLASS_ALIASES = {
    "partially_hidden": "partially_visible_person",
    "partially_hidden_person": "partially_visible_person",
    "partially_visible": "partially_visible_person",
}
CANONICAL_CLASS_CHOICES = [
    "All classes",
    "standing_person",
    "sitting_person",
    "crawling_person",
    "lying_person",
    "partially_visible_person",
]

DETECTION_TABLE_COLUMNS = 6
SYSTEM_EVENT_COLUMNS = 4
GAS_ALERT_COLUMNS = 4
_AUTO_START_ATTEMPTED = False


def _status_row(message: str, columns: int) -> list[str]:
    return [message] + [""] * (columns - 1)


def _canonical_class(name: str) -> str:
    key = (name or "").strip().lower().replace(" ", "_")
    return _CLASS_ALIASES.get(key, key)


def _priority_for(name: str) -> str:
    return _PRIORITY.get(_canonical_class(name), "LOW")


def _format_uptime(seconds) -> str:
    if not seconds or seconds <= 0:
        return "00:00:00"
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def header_icon_html(page: str) -> str:
    icon = PAGE_DETAILS[page]["icon"]
    return f"<div class='header-icon'>{icon}</div>"



def logo_html() -> str:
    if ASSET_LOGO.exists():
        b64 = base64.b64encode(ASSET_LOGO.read_bytes()).decode()
        mark = f'<img class="logo-img" src="data:image/png;base64,{b64}" alt="">'
    else:
        mark = '<div class="logo-mark">SAR</div>'
    return (
        '<div class="logo-card">'
        f'{mark}'
        '<p class="logo-title">RC SAR System</p>'
        '</div>'
    )


def sidebar_status_html() -> str:
    station = api_client.station_status()
    api = api_client.api_health()

    api_label = "Backend online" if api is not None else "Backend unavailable"
    api_color = "var(--sar-green)" if api is not None else "var(--sar-red)"

    if station is None:
        station_label = "Station unavailable"
        video_label = "Video unavailable"
        ai_label = "AI unavailable"
        station_color = video_color = ai_color = "var(--sar-red)"
    else:
        station_label = "Station online"
        station_color = "var(--sar-green)"
        cameras = station.get("cameras", {}).get("list", [])
        video_ok = bool(cameras) and any(c.get("status") == "ok" for c in cameras)
        video_label = "Video connected" if video_ok else "Video unavailable"
        video_color = "var(--sar-blue)" if video_ok else "var(--sar-red)"
        detection = station.get("detection", {})
        ai_label = "AI active" if detection.get("active") else "AI inactive"
        ai_color = "var(--sar-orange)" if detection.get("active") else "var(--sar-yellow)"

    return f"""
    <div class="sidebar-status">
      <div class="status-line"><span class="status-dot" style="background:{api_color};color:{api_color}"></span> {api_label}</div>
      <div class="status-line"><span class="status-dot" style="background:{station_color};color:{station_color}"></span> {station_label}</div>
      <div class="status-line"><span class="status-dot" style="background:{video_color};color:{video_color}"></span> {video_label}</div>
      <div class="status-line"><span class="status-dot" style="background:{ai_color};color:{ai_color}"></span> {ai_label}</div>
    </div>
    """


def current_clock() -> str:
    return f"`{datetime.now().strftime('%H:%M:%S  |  %d %b %Y')}`"


def page_updates(page: str) -> tuple[Any, ...]:
    selected = page if page in PAGE_DETAILS else DEFAULT_PAGE
    details = PAGE_DETAILS[selected]
    visibility = [gr.update(visible=(key == selected)) for key in PAGE_RENDER_ORDER]
    return header_icon_html(selected), f"### {PAGE_UI_LABELS[selected]}", details["subtitle"], *visibility


def metric_html(label: str, value: str, note: str, color: str = ORANGE) -> str:
    font_size = "16px" if len(value) > 10 else "24px"
    return (
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value' style='color:{color};font-size:{font_size}'>{value}</div>"
        f"<div class='metric-note'>{note}</div>"
    )


def badge_row(*labels: str) -> str:
    return "<div class='badge-row'>" + "".join(f"<span class='badge'>{label}</span>" for label in labels) + "</div>"


def threshold_head_html(value: float) -> str:
    return (
        "<div class='op-threshold-head'>"
        "<span class='op-control-label'>Confidence Threshold</span>"
        f"<span class='op-threshold-value'>{int(value)}%</span>"
        "</div>"
    )


def camera_status_html(message: str, tone: str = "neutral") -> str:
    tone = tone if tone in {"ok", "warning", "error", "neutral"} else "neutral"
    return f"<div class='op-camera-status op-camera-status-{tone}'>{message}</div>"


def _camera_id(value: str | None) -> str:
    if value in ("Detection", None, ""):
        return "detection"
    if value == "FPV / Nav":
        return "fpv"
    return str(value)


def _camera_name(camera_id: str, cameras_payload: dict | None = None) -> str:
    cameras = (cameras_payload or {}).get("cameras") or []
    for camera in cameras:
        if camera.get("id") == camera_id:
            return str(camera.get("name") or camera_id)
    if camera_id == "detection":
        return "Detection Camera"
    if camera_id == "fpv":
        return "FPV / Nav Camera"
    return camera_id


def _camera_button(camera_id: str, cameras_payload: dict | None = None):
    return gr.update(value=f"Camera: {_camera_name(camera_id, cameras_payload)}")


def _camera_info(camera_id: str, status_payload: dict | None) -> dict:
    cameras = (status_payload or {}).get("cameras", {}).get("list") or []
    for camera in cameras:
        if camera.get("id") == camera_id:
            return camera
    return {}


def _ai_button(active: bool | None, unavailable: bool = False):
    if unavailable:
        return gr.update(value="AI unavailable", variant="secondary")
    if active:
        return gr.update(value="AI On", variant="primary")
    return gr.update(value="AI Off", variant="secondary")


def _percent(value: Any) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    if numeric <= 1:
        numeric *= 100
    return int(round(numeric))


def _latest_recent_rows(latest: dict) -> list[list[str]]:
    rows = latest.get("recent") or []
    if not rows and latest.get("last_detection"):
        rows = [latest["last_detection"]]
    if not rows:
        rows = latest.get("detections") or []

    formatted = []
    for item in rows:
        cls = _canonical_class(item.get("class_name", ""))
        confidence = f"{_percent(item.get('confidence'))}%"
        timestamp = str(item.get("time") or item.get("timestamp") or "--")[:8]
        priority = str(item.get("priority") or _priority_for(cls))
        formatted.append([cls, confidence, timestamp, priority])
    return formatted


def recent_detections_html(rows: list, empty_message: str = "No detections yet") -> str:
    if not rows:
        tbody = f'<tr><td colspan="4" class="rh-empty">{empty_message}</td></tr>'
    else:
        def _row(r: list) -> str:
            cls, conf, t, pri = r[0], r[1], r[2], r[3]
            return (
                f'<tr>'
                f'<td class="rh-cls">{cls}</td>'
                f'<td class="rh-conf">{conf}</td>'
                f'<td class="rh-time">{t}</td>'
                f'<td><span class="rh-pri rh-pri-{pri.lower()}">{pri}</span></td>'
                f'</tr>'
            )
        tbody = "".join(_row(r) for r in rows)
    return (
        '<div class="rh-card">'
        '<div class="rh-header"><span class="rh-icon">🕒</span>'
        '<span class="rh-title">Recent</span></div>'
        '<table class="rh-table">'
        '<thead><tr>'
        '<th>Class</th><th>Confidence</th><th>Time</th><th>Priority</th>'
        '</tr></thead>'
        f'<tbody>{tbody}</tbody>'
        '</table>'
        '</div>'
    )


def operating_update(ai_enabled: bool, camera_mode: str, threshold: float) -> tuple[Any, ...]:
    """Live Operating-page snapshot from the station."""
    cam_id = _camera_id(camera_mode)
    latest = api_client.detection_latest()
    status = api_client.station_status()

    if latest is None and status is None:
        return (
            None,
            camera_status_html("Station unavailable", "error"),
            0,
            0,
            "Station unavailable",
            recent_detections_html([], "Station unavailable"),
        )

    camera_info = _camera_info(cam_id, status)
    frame = api_client.camera_frame(cam_id)
    if camera_info.get("status") == "error":
        detail = html.escape(str(camera_info.get("last_error") or "camera signal unavailable"))
        camera_status = camera_status_html(f"Camera unavailable - {detail}", "error")
    elif frame is None:
        camera_status = camera_status_html("No frame available", "warning")
    else:
        active_camera = (status or {}).get("cameras", {}).get("active", cam_id)
        camera_status = camera_status_html(f"Camera live - {_camera_name(active_camera)}", "ok")

    recent = _latest_recent_rows(latest or {})
    detection_count = len((latest or {}).get("detections") or [])
    fps = round(float((latest or {}).get("fps") or 0), 1)
    duration = _format_uptime((status or {}).get("uptime_seconds"))
    return frame, camera_status, detection_count, fps, duration, recent_detections_html(recent)


def live_operating(page: str, ai_enabled: bool, camera_mode: str, threshold: float) -> tuple[Any, ...]:
    """Timer-driven refresh; only hits the backend while on the Operating page."""
    if page != "Operating":
        return tuple(gr.update() for _ in range(6))
    return operating_update(ai_enabled, camera_mode, threshold)


def apply_threshold(ai_enabled: bool, camera_mode: str, threshold: float) -> tuple[Any, ...]:
    """Send the confidence threshold (0-100 slider) to the station as 0-1."""
    api_client.set_detection_config(conf=float(threshold) / 100.0)
    return (threshold_head_html(threshold),) + operating_update(ai_enabled, camera_mode, threshold)


def toggle_ai(ai_enabled: bool, camera_mode: str, threshold: float) -> tuple[Any, ...]:
    new_ai = not ai_enabled
    result = api_client.set_detection_active(new_ai)
    if result is None:
        return (ai_enabled, _ai_button(ai_enabled, unavailable=True)) + operating_update(
            ai_enabled, camera_mode, threshold
        )
    active = bool(result.get("active", new_ai))
    return (active, _ai_button(active)) + operating_update(active, camera_mode, threshold)


def toggle_camera(camera_mode: str, ai_enabled: bool, threshold: float) -> tuple[Any, ...]:
    payload = api_client.list_cameras()
    if payload is None:
        return (_camera_id(camera_mode), gr.update(value="Camera unavailable")) + operating_update(
            ai_enabled, camera_mode, threshold
        )

    cameras = payload.get("cameras") or []
    ids = [camera.get("id") for camera in cameras if camera.get("id")]
    current = _camera_id(camera_mode)
    if not ids:
        return (current, gr.update(value="Camera unavailable")) + operating_update(
            ai_enabled, current, threshold
        )

    try:
        next_id = ids[(ids.index(current) + 1) % len(ids)]
    except ValueError:
        next_id = str(payload.get("active") or ids[0])

    switched = api_client.set_active_camera(next_id)
    if switched is None:
        return (current, gr.update(value="Camera unavailable")) + operating_update(
            ai_enabled, current, threshold
        )

    active = str(switched.get("active") or next_id)
    return (active, _camera_button(active, switched)) + operating_update(ai_enabled, active, threshold)


def operating_initial_state() -> tuple[Any, ...]:
    """Initial Operating-page values from station config/status."""
    global _AUTO_START_ATTEMPTED

    if AUTO_START_DETECTION and not _AUTO_START_ATTEMPTED:
        _AUTO_START_ATTEMPTED = True
        api_client.start_detection()

    cfg = api_client.get_detection_config() or {}
    threshold = _percent(cfg.get("conf_threshold", 0.45))
    cameras = api_client.list_cameras()
    cam_id = str((cameras or {}).get("active") or "detection")
    latest = api_client.detection_latest() or {}
    active = bool(latest.get("active"))

    return (
        active,
        cam_id,
        _ai_button(active, unavailable=latest == {}),
        _camera_button(cam_id, cameras),
        threshold,
        threshold_head_html(threshold),
        *operating_update(active, cam_id, threshold),
    )


def reset_recent_log() -> str:
    return recent_detections_html([])


def lcd_message(page: str) -> str:
    title = PAGE_DETAILS.get(page, PAGE_DETAILS[DEFAULT_PAGE])["title"]
    return f"LCD cycle: {title} | STATUS ACTIVE | VIDEO CONNECTED"


def _format_detection_row(r: dict) -> list[str]:
    dt = str(r.get("detection_time", ""))
    date_part, _, time_part = dt.replace(" ", "T").partition("T")
    cls = _canonical_class(r.get("class_name", ""))
    try:
        conf = f"{int(float(r.get('confidence') or 0))}%"
    except (TypeError, ValueError):
        conf = "0%"
    return [f"#{r.get('detection_id', '')}", cls, conf, date_part, time_part[:8], _priority_for(cls)]


def filter_detection_events(class_filter: str) -> list[list[str]]:
    selected = _canonical_class(class_filter) if class_filter != "All classes" else class_filter
    rows = api_client.detections(class_name=selected, limit=50)
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available:
        return [_status_row(result.message, DETECTION_TABLE_COLUMNS)]
    if not result.has_data:
        return [_status_row(result.message, DETECTION_TABLE_COLUMNS)]
    return [_format_detection_row(r) for r in rows]


def _format_event_row(r: dict) -> list[str]:
    dt = str(r.get("event_time", ""))
    _, _, time_part = dt.replace(" ", "T").partition("T")
    return [
        time_part[:8] or dt[:19],
        str(r.get("event_type", "")),
        str(r.get("message") or ""),
        str(r.get("importance_level", "")),
    ]


def system_event_rows() -> list[list[str]]:
    rows = api_client.events(limit=50)
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        return [_status_row(result.message, SYSTEM_EVENT_COLUMNS)]
    return [_format_event_row(r) for r in rows]


def _format_gas_row(r: dict) -> list[str]:
    dt = str(r.get("reading_time", ""))
    _, _, time_part = dt.replace(" ", "T").partition("T")
    value = r.get("value")
    reading = "unknown" if value is None else f"{float(value):.0f} ppm"
    is_dangerous = bool(r.get("is_dangerous"))
    return [
        time_part[:8] or dt[:19],
        reading,
        "Critical" if is_dangerous else "Normal",
        str(r.get("message") or ("Do not enter" if is_dangerous else "Safe to proceed")),
    ]


def gas_alert_rows() -> list[list[str]]:
    rows = api_client.sensor_readings(sensor_name="gas", dangerous_only=True, limit=50)
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        return [_status_row(result.message, GAS_ALERT_COLUMNS)]
    return [_format_gas_row(r) for r in rows]


def data_kpi_cards() -> list[tuple[str, str, str, str]]:
    stats = api_client.detection_stats()
    latest = api_client.detections(limit=1)
    events = api_client.events(limit=50)
    gas_alerts = api_client.sensor_readings(sensor_name="gas", dangerous_only=True, limit=50)

    if any(value is None for value in (stats, latest, events, gas_alerts)):
        return [
            ("Total Detections", "Backend unavailable", "Data API", RED),
            ("Last Detection", "Backend unavailable", "Data API", RED),
            ("System Events", "Backend unavailable", "Data API", RED),
            ("Gas Alerts", "Backend unavailable", "Data API", RED),
        ]

    total = int(stats.get("total") or 0)
    last = latest[0] if latest else None
    return [
        ("Total Detections", str(total) if total else "No data yet", "Saved records", ORANGE),
        ("Last Detection", _canonical_class(last["class_name"]) if last else "No data yet",
         str(last.get("detection_time", ""))[:19] if last else "No saved detection", PURPLE),
        ("System Events", str(len(events)) if events else "No data yet", "Recent event log", BLUE),
        ("Gas Alerts", str(len(gas_alerts)) if gas_alerts else "No data yet", "Danger readings", YELLOW),
    ]


_CSV_FIELDS = [
    'record_type',
    'id',
    'timestamp',
    'category',
    'value',
    'unit',
    'confidence_percent',
    'people_count',
    'importance',
    'is_dangerous',
    'message',
]


def export_logs_csv():
    detections = api_client.detections(limit=500)
    events = api_client.events(limit=500)
    readings = api_client.sensor_readings(limit=500)
    if any(records is None for records in (detections, events, readings)):
        notice = "<div class='export-banner'>Backend unavailable. CSV was not created.</div>"
        return gr.update(value=None, visible=False), gr.update(value=notice, visible=True)

    rows: list[dict[str, Any]] = []
    for record in detections:
        rows.append({
            'record_type': 'detection',
            'id': record.get('detection_id', ''),
            'timestamp': record.get('detection_time', ''),
            'category': _canonical_class(record.get('class_name', '')),
            'confidence_percent': record.get('confidence', ''),
            'people_count': record.get('people_count', ''),
        })
    for record in events:
        rows.append({
            'record_type': 'event',
            'id': record.get('event_id', ''),
            'timestamp': record.get('event_time', ''),
            'category': record.get('event_type', ''),
            'importance': record.get('importance_level', ''),
            'message': record.get('message', ''),
        })
    for record in readings:
        rows.append({
            'record_type': 'sensor',
            'id': record.get('reading_id', ''),
            'timestamp': record.get('reading_time', ''),
            'category': record.get('sensor_name', ''),
            'value': record.get('value', ''),
            'unit': record.get('unit', ''),
            'is_dangerous': record.get('is_dangerous', False),
            'message': record.get('message', ''),
        })

    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8-sig',
        newline='',
        prefix='search-rescue-logs-',
        suffix='.csv',
        delete=False,
    ) as export_file:
        writer = csv.DictWriter(export_file, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    notice = f"<div class='export-banner'>CSV export ready: {len(rows)} records.</div>"
    return (
        gr.update(value=export_file.name, visible=True),
        gr.update(value=notice, visible=True),
    )


def _base_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left", "font": {"size": 18}},
        margin={"l": 54, "r": 20, "t": 48, "b": 48},
        height=350,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"color": "#111827", "size": 14},
        xaxis={"gridcolor": "#eef2f7"},
        yaxis={"gridcolor": "#eef2f7"},
        legend={"orientation": "h", "y": -0.24, "font": {"size": 13}},
    )
    return fig


def _fmt_bucket(value) -> str:
    s = str(value)
    return s[11:16] if "T" in s else s[:5]


def _empty_figure(title: str, message: str) -> go.Figure:
    fig = _base_figure(title)
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 16, "color": "#64748b"},
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _series_for(data_source: str):
    """Return (times, values, y_label, color, threshold, message)."""
    if data_source == "Gas Alerts":
        rows = api_client.stat_sensor_over_time("gas", "minute")
        result = api_client.service_result(rows, "Backend unavailable")
        if not result.available or not result.has_data:
            return [], [], "Gas ppm", YELLOW, 250, result.message
        return ([_fmt_bucket(r["bucket"]) for r in rows],
                [float(r.get("avg_value") or 0) for r in rows], "Gas ppm", YELLOW, 250, "")

    rows = api_client.stat_detections_over_time("minute")
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        return [], [], "Count", ORANGE, 0, result.message
    return ([_fmt_bucket(r["bucket"]) for r in rows],
            [int(r.get("count") or 0) for r in rows], "Count", ORANGE, 0, "")


def build_statistics_figure(data_source: str = "Detections", chart_type: str = "Line") -> go.Figure:
    times, y_values, y_label, color, threshold, message = _series_for(data_source)
    if message:
        return _empty_figure(f"{data_source} - {chart_type}", message)

    fig = _base_figure(f"{data_source} - {chart_type}")
    chart_type = chart_type or "Line"
    if chart_type == "Bar":
        fig.add_bar(x=times, y=y_values, marker_color=color, name=data_source)
    elif chart_type == "Scatter":
        fig.add_scatter(x=times, y=y_values, mode="markers", marker={"size": 10, "color": color}, name=data_source)
    elif chart_type == "Area":
        fig.add_scatter(x=times, y=y_values, mode="lines", fill="tozeroy", line={"color": color, "width": 3}, name=data_source)
    elif chart_type == "Histogram":
        fig.add_histogram(x=y_values, marker_color=color, name=data_source)
        fig.update_xaxes(title_text=y_label, title_font={"size": 14}, tickfont={"size": 13})
        fig.update_yaxes(title_text="Frequency", title_font={"size": 14}, tickfont={"size": 13})
        return fig
    else:
        fig.add_scatter(x=times, y=y_values, mode="lines+markers", line={"color": color, "width": 3}, name=data_source)

    if times:
        fig.add_scatter(x=times, y=[threshold] * len(times), mode="lines", line={"color": RED, "width": 2, "dash": "dot"}, name="Threshold")
    fig.update_xaxes(title_text="Time", title_font={"size": 14}, tickfont={"size": 13})
    fig.update_yaxes(title_text=y_label, title_font={"size": 14}, tickfont={"size": 13})
    return fig


def overview_figure(kind: str) -> go.Figure:
    if kind == "gas":
        fig = build_statistics_figure("Gas Alerts", "Line")
        fig.update_layout(title_text="Gas Sensor Readings", height=280)
        return fig
    if kind == "classes":
        fig = class_distribution_figure()
        fig.update_layout(title_text="Detections by Class", height=280)
        return fig
    if kind == "performance":
        fig = _empty_figure("System Performance", "No data yet")
        fig.update_layout(height=280)
        return fig
    fig = build_statistics_figure("Detections", "Area")
    fig.update_layout(title_text="Detection Events Timeline", height=280)
    return fig


def data_timeline_figure() -> go.Figure:
    rows = api_client.stat_detections_over_time("minute")
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        fig = _empty_figure("Detection Timeline", result.message)
        fig.update_layout(height=280)
        return fig
    fig = _base_figure("Detection Timeline")
    fig.add_scatter(
        x=[_fmt_bucket(r["bucket"]) for r in rows],
        y=[int(r.get("count") or 0) for r in rows],
        mode="lines+markers",
        line={"color": ORANGE, "width": 3},
        marker={"size": 8, "color": ORANGE},
        name="Detections",
    )
    fig.update_layout(height=280, showlegend=False)
    return fig


def gas_history_figure() -> go.Figure:
    rows = api_client.stat_sensor_over_time("gas", "minute")
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        fig = _empty_figure("Gas Sensor History", result.message)
        fig.update_layout(height=280, showlegend=False)
        return fig
    times = [_fmt_bucket(r["bucket"]) for r in rows]
    values = [float(r.get("avg_value") or 0) for r in rows]
    fig = _base_figure("Gas Sensor History")
    fig.add_bar(x=times, y=values, marker_color=YELLOW, name="Gas ppm")
    if times:
        fig.add_scatter(x=times, y=[250] * len(times), mode="lines", line={"color": RED, "dash": "dot"}, name="Danger")
    fig.update_layout(height=280)
    fig.update_yaxes(title_text="ppm", title_font={"size": 14}, tickfont={"size": 13})
    return fig


def class_distribution_figure() -> go.Figure:
    rows = api_client.stat_class_distribution()
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        fig = _empty_figure("By Class", result.message)
        fig.update_layout(height=280)
        return fig
    labels = [_canonical_class(r["class_name"]) for r in rows]
    values = [int(r.get("count") or 0) for r in rows]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.52,
                marker={"colors": [RED, GREEN, ORANGE, YELLOW, PURPLE]},
                textinfo="none",
            )
        ]
    )
    fig.update_layout(
        title={"text": "By Class", "x": 0.02, "xanchor": "left", "font": {"size": 18}},
        height=280,
        margin={"l": 8, "r": 8, "t": 48, "b": 8},
        paper_bgcolor="white",
        legend={"orientation": "v", "x": 1.02, "y": 0.5},
        font={"color": "#0f172a", "size": 14},
    )
    return fig

def statistics_status(data_source: str, chart_type: str) -> str:
    return f"Showing **{data_source}** as a **{chart_type}** chart from the data API."


def initial_test_state() -> dict[str, str]:
    return {test_id: "not_tested" for test_id in TEST_IDS}


_TEST_ICONS: dict[str, str] = {
    "fpv_camera":       "📷",
    "detection_camera": "📸",
    "touchscreen":      "📱",
    "lcd_display":      "🖥",
    "gas_sensor":       "☁",
    "temp_humidity":    "🌡",
    "detection_led":    "💡",
    "buzzer":           "🔔",
    "system_led":       "🟢",
    "camera_servo":     "🔧",
}


def test_header_html(test: dict, status: str) -> str:
    icon = _TEST_ICONS.get(test["id"], "🔧")
    icon_bg = test["accent"] + "20"
    if status == "passed":
        badge = "<span class='ts-passed' style='color:#10b981;font-size:15px;font-weight:700'>✓</span>"
    elif status == "failed":
        badge = "<span class='ts-failed' style='color:#ef4444;font-size:15px;font-weight:700'>✗</span>"
    else:
        badge = "<span class='ts-none'></span>"
    return (
        f"<div style='display:flex;align-items:center;gap:9px'>"
        f"<div style='width:32px;height:32px;border-radius:8px;background:{icon_bg};"
        f"display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0'>{icon}</div>"
        f"<span style='font-size:13px;font-weight:700;color:#1e293b;flex:1'>{test['name']}</span>"
        f"{badge}</div>"
    )


def test_rows_html(test: dict, status: str) -> str:
    rows = ""
    for label, expected in test["checks"]:
        if status == "not_tested":
            actual = "<span style='color:#94a3b8;font-size:11px'>not tested</span>"
        elif status == "passed":
            actual = (
                f"<span style='color:#10b981;font-size:11px;font-weight:600'>{expected} ✓</span>"
            )
        else:
            actual = "<span style='color:#ef4444;font-size:11px;font-weight:600'>Error ✗</span>"
        rows += (
            f"<div style='display:flex;align-items:center;padding:4px 0;border-bottom:1px solid #f3f4f6'>"
            f"<span style='font-size:11px;color:#64748b;flex:1'>{label}</span>"
            f"<span style='font-size:11px;color:#cbd5e1;margin-right:10px'>{expected}</span>"
            f"{actual}</div>"
        )
    return f"<div style='margin-top:7px'>{rows}</div>"


def test_status_text(test_id: str, status: str) -> str:
    test = TEST_LOOKUP[test_id]
    display_status = status.replace("_", " ")
    lines = [f"{test['name']} - {display_status.upper()}"]
    for label, expected in test["checks"]:
        result = "pass" if status == "passed" else ("running" if status == "testing" else "waiting")
        lines.append(f"{label}: expected {expected} | {result}")
    return "\n".join(lines)


def diagnostic_summary(state: dict[str, str] | None) -> str:
    state = state or initial_test_state()
    passed = sum(1 for value in state.values() if value == "passed")
    total = len(TEST_IDS)
    if passed == 0:
        return "No tests have run yet. Press **Run All** or test an individual component."
    if passed == total:
        return f"**System Healthy** - {passed}/{total} component tests passed."
    return f"**Partial diagnostics** - {passed}/{total} component tests passed."


def diagnostic_summary_html(state: dict[str, str] | None) -> str:
    state = state or initial_test_state()
    total = len(TEST_IDS)
    passed = sum(1 for v in state.values() if v == "passed")
    failed_ids = [k for k, v in state.items() if v == "failed"]
    all_not_tested = all(v == "not_tested" for v in state.values())

    if all_not_tested:
        hw = api_client.hardware_status()
        if hw is None:
            pct, ok_count, fail_count = 0, 0, 0
            status_label, ring_color = "Station unavailable", "#ef4444"
            issues = [
                {"name": "Station", "check": "Hardware API", "result": "Unavailable",
                 "hint": "Start the station service and retry diagnostics"},
            ]
        else:
            devices = hw.get("devices", [])
            ok_count = sum(1 for d in devices if d.get("ok"))
            fail_count = len(devices) - ok_count
            pct = int(100 * ok_count / len(devices)) if devices else 0
            status_label = "Hardware Ready" if fail_count == 0 else "Hardware Degraded"
            ring_color = "#10b981" if fail_count == 0 else "#f05a24"
            issues = [
                {"name": d.get("name", d.get("id", "Device")), "check": "Status",
                 "result": "Failed", "hint": "Run the individual component test"}
                for d in devices if not d.get("ok")
            ]
    elif passed == total:
        pct, ok_count, fail_count = 100, total, 0
        status_label, ring_color = "System Healthy", "#10b981"
        issues = []
    else:
        pct = int(100 * passed / total)
        ok_count, fail_count = passed, len(failed_ids)
        status_label, ring_color = "Partially Degraded", "#f05a24"
        issues = [
            {"name": TEST_LOOKUP[fid]["name"], "check": "Diagnostics",
             "result": "Failed", "hint": "Re-run individual test for details"}
            for fid in failed_ids
        ]

    r, circ = 30, 188.5
    offset = circ * (1 - pct / 100)
    svg = (
        f'<svg width="76" height="76" viewBox="0 0 76 76">'
        f'<circle cx="38" cy="38" r="{r}" fill="none" stroke="#e5e7eb" stroke-width="7"/>'
        f'<circle cx="38" cy="38" r="{r}" fill="none" stroke="{ring_color}" stroke-width="7"'
        f' stroke-dasharray="{circ}" stroke-dashoffset="{offset:.1f}"'
        f' stroke-linecap="round" transform="rotate(-90 38 38)"/>'
        f'<text x="38" y="43" text-anchor="middle" font-size="14" font-weight="800"'
        f' fill="{ring_color}">{pct}%</text></svg>'
    )
    ok_badge = (
        f"<span style='background:#d1fae5;color:#065f46;border-radius:999px;"
        f"font-size:11px;font-weight:600;padding:2px 8px'>{ok_count} params OK</span>"
    )
    fail_badge = (
        f"<span style='background:#fee2e2;color:#991b1b;border-radius:999px;"
        f"font-size:11px;font-weight:600;padding:2px 8px'>{fail_count} failed</span>"
    )

    issue_cards = ""
    for issue in issues:
        issue_cards += (
            f"<div style='background:#fef2f2;border:1px solid #fecaca;border-radius:8px;"
            f"padding:10px;margin-bottom:8px'>"
            f"<div style='font-size:13px;font-weight:700;color:#1e293b;margin-bottom:4px'>"
            f"🔴 {issue['name']}</div>"
            f"<div style='display:flex;justify-content:space-between;font-size:12px;"
            f"color:#64748b;margin-bottom:6px'>"
            f"<span>{issue['check']}</span>"
            f"<span style='color:#ef4444;font-weight:600'>{issue['result']}</span></div>"
            f"<div style='background:#fffbeb;border:1px solid #fde68a;border-radius:6px;"
            f"padding:5px 8px;font-size:11px;color:#92400e'>⚠ {issue['hint']}</div>"
            f"</div>"
        )

    issues_html = (
        f"<div style='font-size:10px;font-weight:700;color:#94a3b8;"
        f"letter-spacing:0.08em;margin-bottom:8px;margin-top:4px'>ISSUES</div>{issue_cards}"
        if issues else ""
    )

    # Full card rendered as plain HTML — no Gradio Group/Markdown wrappers
    return (
        f"<div style='background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;"
        f"padding:12px;box-shadow:0 1px 2px rgba(15,23,42,0.04)'>"
        f"<div style='font-size:14px;font-weight:800;color:#1e293b;margin-bottom:10px'>"
        f"Diagnostic Summary</div>"
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:4px'>"
        f"{svg}<div>"
        f"<div style='font-size:15px;font-weight:800;color:#1e293b'>{status_label}</div>"
        f"<div style='display:flex;gap:6px;margin-top:4px'>{ok_badge} {fail_badge}</div>"
        f"</div></div>"
        f"{issues_html}"
        f"</div>"
    )


def diagnostic_progress(state: dict[str, str] | None) -> str:
    state = state or initial_test_state()
    passed = sum(1 for value in state.values() if value == "passed")
    return f"### Component Tests\n{passed}/{len(TEST_IDS)} tested"


def _component_status(test_id: str) -> str:
    """Run a real station hardware self-test."""
    result = api_client.test_component(test_id)
    if result is None:
        return "failed"
    return "passed" if result.get("status") in ("passed", "skipped") else "failed"


def run_single_test(state: dict[str, str] | None, test_id: str) -> tuple[Any, ...]:
    next_state = dict(state or initial_test_state())
    status = _component_status(test_id)
    next_state[test_id] = status
    t = TEST_LOOKUP[test_id]
    return (
        next_state,
        test_header_html(t, status),
        test_rows_html(t, status),
        diagnostic_summary_html(next_state),
        diagnostic_progress(next_state),
    )


def run_all_tests(state: dict[str, str] | None) -> tuple[Any, ...]:
    next_state: dict[str, str] = {}
    pairs: list[str] = []
    for tid in TEST_IDS:
        status = _component_status(tid)
        next_state[tid] = status
        t = TEST_LOOKUP[tid]
        pairs.append(test_header_html(t, status))
        pairs.append(test_rows_html(t, status))
    return (next_state, *pairs, diagnostic_summary_html(next_state), diagnostic_progress(next_state))


def reset_tests() -> tuple[Any, ...]:
    next_state = initial_test_state()
    pairs: list[str] = []
    for tid in TEST_IDS:
        t = TEST_LOOKUP[tid]
        pairs.append(test_header_html(t, "not_tested"))
        pairs.append(test_rows_html(t, "not_tested"))
    return (next_state, *pairs, diagnostic_summary_html(next_state), diagnostic_progress(next_state))


def wire_operating_page(operating: Any, nav: gr.Radio) -> None:
    common_outputs = [
        operating.camera_output,
        operating.camera_status,
        operating.detection_count,
        operating.fps_output,
        operating.mission_duration,
        operating.recent_html,
    ]
    operating.ai_btn.click(
        fn=toggle_ai,
        inputs=[operating.ai_state, operating.cam_state, operating.threshold],
        outputs=[operating.ai_state, operating.ai_btn] + common_outputs,
        show_progress="hidden",
    )
    operating.cam_btn.click(
        fn=toggle_camera,
        inputs=[operating.cam_state, operating.ai_state, operating.threshold],
        outputs=[operating.cam_state, operating.cam_btn] + common_outputs,
        show_progress="hidden",
    )
    operating.threshold.change(
        fn=apply_threshold,
        inputs=[operating.ai_state, operating.cam_state, operating.threshold],
        outputs=[operating.threshold_head] + common_outputs,
        show_progress="hidden",
    )
    operating.reset_log_button.click(
        fn=reset_recent_log,
        inputs=None,
        outputs=[operating.recent_html],
        show_progress="hidden",
    )
    operating.view_all_button.click(
        fn=lambda: "Data",
        inputs=None,
        outputs=[nav],
        show_progress="hidden",
    )


def wire_data_logs_page(data_logs: Any) -> None:
    data_logs.class_filter.change(fn=filter_detection_events, inputs=[data_logs.class_filter], outputs=[data_logs.detection_table], show_progress="hidden")
    data_logs.export_button.click(
        fn=export_logs_csv,
        inputs=None,
        outputs=[data_logs.export_file, data_logs.export_banner],
        show_progress='hidden',
    )


def wire_statistics_page(statistics: Any) -> None:
    statistics.source.change(
        fn=build_statistics_figure,
        inputs=[statistics.source, statistics.chart_type],
        outputs=[statistics.main_plot],
        show_progress="hidden",
    )
    statistics.chart_type.change(
        fn=lambda chart, source: build_statistics_figure(source, chart),
        inputs=[statistics.chart_type, statistics.source],
        outputs=[statistics.main_plot],
        show_progress="hidden",
    )


def wire_debugging_page(debugging: Any) -> None:
    for test_id, button in debugging.test_buttons.items():
        button.click(
            fn=lambda state, test_id=test_id: run_single_test(state, test_id),
            inputs=[debugging.test_state],
            outputs=[
                debugging.test_state,
                debugging.test_headers[test_id],
                debugging.test_outputs[test_id],
                debugging.summary_output,
                debugging.progress_output,
            ],
            show_progress="hidden",
        )
    interleaved = [x for tid in TEST_IDS for x in (debugging.test_headers[tid], debugging.test_outputs[tid])]
    debugging.run_all_button.click(
        fn=run_all_tests, inputs=[debugging.test_state],
        outputs=[debugging.test_state, *interleaved, debugging.summary_output, debugging.progress_output],
        show_progress="hidden",
    )
    debugging.reset_button.click(
        fn=reset_tests, inputs=None,
        outputs=[debugging.test_state, *interleaved, debugging.summary_output, debugging.progress_output],
        show_progress="hidden",
    )


def wire_callbacks(layout: Any) -> None:
    layout.nav.change(
        fn=page_updates,
        inputs=[layout.nav],
        outputs=[layout.header_icon, layout.header_title, layout.header_subtitle, *layout.page_columns],
        show_progress="hidden",
    )
    layout.timer.tick(fn=current_clock, inputs=None, outputs=[layout.clock], show_progress="hidden")
    layout.timer.tick(
        fn=live_operating,
        inputs=[
            layout.nav,
            layout.operating.ai_state,
            layout.operating.cam_state,
            layout.operating.threshold,
        ],
        outputs=[
            layout.operating.camera_output,
            layout.operating.camera_status,
            layout.operating.detection_count,
            layout.operating.fps_output,
            layout.operating.mission_duration,
            layout.operating.recent_html,
        ],
        show_progress="hidden",
    )
    wire_operating_page(layout.operating, layout.nav)
    wire_data_logs_page(layout.data_logs)
    wire_statistics_page(layout.statistics)
    wire_debugging_page(layout.debugging)
