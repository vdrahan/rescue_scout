from __future__ import annotations

import base64
import html
import time
from datetime import datetime
from typing import Any

import gradio as gr
import plotly.graph_objects as go

from .constants import (
    ASSET_LOGO,
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

try:  # works when launched from frontend/ (python app.py) or in Docker
    from services import api_client
    from services.config import AUTO_START_DETECTION
except ModuleNotFoundError:  # when launched as a package (frontend.app)
    from frontend.services import api_client
    from frontend.services.config import AUTO_START_DETECTION


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


_ALERT_WINDOW_SECONDS = 30


def _recent_dangerous(sensor_name: str) -> float | None:
    """Return sensor value if a dangerous reading exists within the alert window, else None."""
    try:
        rows = api_client.sensor_readings(sensor_name=sensor_name, dangerous_only=True, limit=1)
        if not rows:
            return None
        age = (datetime.now() - datetime.fromisoformat(rows[0]["reading_time"])).total_seconds()
        if age > _ALERT_WINDOW_SECONDS:
            return None
        return float(rows[0]["value"])
    except Exception:  # noqa: BLE001
        return None


def gas_banner_html() -> str:
    """Single status banner: safe info when all clear, warning when gas/temp danger."""
    gas_alert = _recent_dangerous("gas")
    temp_alert = _recent_dangerous("temperature")

    # Alert states
    if gas_alert is not None or temp_alert is not None:
        if gas_alert is not None and temp_alert is not None:
            content = (
                f"<strong>Gas Detected</strong> — {gas_alert:.0f} ppm"
                f" &nbsp;|&nbsp; "
                f"<strong>High Temperature</strong> — {temp_alert:.0f}°C"
            )
            icon = "⚠️"
            extra_class = ""
        elif gas_alert is not None:
            content = f"<strong>Gas Detected</strong> — MQ-2 reads {gas_alert:.0f} ppm. Ventilate immediately."
            icon = "⚠️"
            extra_class = ""
        else:
            content = f"<strong>High Temperature</strong> — DHT11 reads {temp_alert:.0f}°C. Area may be unsafe."
            icon = "🌡️"
            extra_class = " temp-warning-banner"
        return f"""<div id="warning-banner-inner" class="gas-warning-banner{extra_class}">
  <span class="gas-warning-icon">{icon}</span>
  <span class="gas-warning-text">{content}</span>
</div>"""

    # Safe state — fetch live readings to show current values
    gas_str = "N/A"
    temp_str = "N/A"
    try:
        hw = api_client.hardware_status() or {}
        gas_val = hw.get("gas", {}).get("ppm")
        temp_val = hw.get("climate", {}).get("temperature")
        if gas_val is not None:
            gas_str = f"{float(gas_val):.0f} ppm"
        if temp_val is not None:
            temp_str = f"{float(temp_val):.0f}°C"
    except Exception:  # noqa: BLE001
        pass

    return f"""<div id="warning-banner-inner" class="area-safe-banner">
  <span class="gas-warning-icon">✅</span>
  <span class="gas-warning-text">
    <strong>Area Safe</strong> &nbsp;—&nbsp; Gas: {gas_str} &nbsp;|&nbsp; Temperature: {temp_str}
  </span>
</div>"""


def page_updates(page: str) -> tuple[Any, ...]:
    selected = page if page in PAGE_DETAILS else DEFAULT_PAGE
    details = PAGE_DETAILS[selected]
    visibility = [gr.update(visible=(key == selected)) for key in PAGE_RENDER_ORDER]
    return header_icon_html(selected), f"### {PAGE_UI_LABELS[selected]}", details["subtitle"], *visibility


def metric_html(label: str, value: str, note: str, color: str = ORANGE) -> str:
    font_size = "18px" if len(value) > 10 else "30px"
    return (
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value' style='color:{color};font-size:{font_size}'>{value}</div>"
        f"<div class='metric-note'>{note}</div>"
    )


def badge_row(*labels: str) -> str:
    return "<div class='badge-row'>" + "".join(f"<span class='badge'>{label}</span>" for label in labels) + "</div>"


def threshold_head_html(value: float) -> str:
    v = int(value)
    pct = f"{v}%"
    oninput = (
        "this.style.setProperty('--p',this.value+'%');"
        "var d=this.parentElement.querySelector('.thr-val');"
        "if(d)d.textContent=this.value+'%'"
    )
    onchange = (
        "(function(v){"
        "var n=document.querySelector('#thr-value input[type=number]');"
        "if(n){n.value=v;"
        "n.dispatchEvent(new Event('input',{bubbles:true}));"
        "n.dispatchEvent(new Event('change',{bubbles:true}))}"
        "})(this.value)"
    )
    return (
        "<div class='thr-card'>"
        "<div class='thr-head'>"
        f"<span class='thr-label'>Confidence Threshold</span>"
        f"<span class='thr-val'>{pct}</span>"
        "</div>"
        f"<input type='range' class='thr-range' min='0' max='100' step='5' value='{v}'"
        f" style='--p:{pct}'"
        f" oninput=\"{oninput}\""
        f" onchange=\"{onchange}\""
        " />"
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
    cam_id = _camera_id(camera_mode)
    latest = api_client.detection_latest()
    status = api_client.station_status()

    if latest is None and status is None:
        return (
            None,
            camera_status_html("📡 Station Offline — Check Connection", "error"),
            0, 0, "Station unavailable",
            recent_detections_html([], "Station unavailable"),
        )

    camera_info = _camera_info(cam_id, status)
    frame = api_client.camera_frame(cam_id)

    if camera_info.get("status") == "error":
        cam_status = camera_status_html("🔄 Camera Reconnecting — Showing last frame", "warning")
    elif frame is None:
        cam_status = camera_status_html("⏳ No Frame Available — Waiting for signal...", "warning")
    else:
        active_camera = (status or {}).get("cameras", {}).get("active", cam_id)
        cam_status = camera_status_html(f"✅ Camera Live — {_camera_name(active_camera)}", "ok")

    recent = _latest_recent_rows(latest or {})
    detection_count = len((latest or {}).get("detections") or [])
    fps = round(float((latest or {}).get("fps") or 0), 1)
    duration = _format_uptime((status or {}).get("uptime_seconds"))
    return frame, cam_status, detection_count, fps, duration, recent_detections_html(recent)


def live_operating(page: str, ai_enabled: bool, camera_mode: str, threshold: float) -> tuple[Any, ...]:
    """Timer-driven refresh; only hits the backend while on the Operating page."""
    if page != "Operating":
        return tuple(gr.update() for _ in range(6))
    return operating_update(ai_enabled, camera_mode, threshold)


def live_camera_frame(page: str, camera_mode: str) -> Any:
    """Fast camera-only refresh — single HTTP call, no stats overhead."""
    if page != "Operating":
        return gr.update()
    cam_id = _camera_id(camera_mode)
    return api_client.camera_frame(cam_id)


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


_SCREEN_LABELS = {0: "LCD: System Status", 1: "LCD: Last Detection", 2: "LCD: Statistics", 3: "LCD: Gas Status"}

def cycle_lcd_screen() -> str:
    result = api_client.cycle_lcd_screen()
    if result is None:
        return "LCD: unavailable"
    return _SCREEN_LABELS.get(result.get("screen", 0), "LCD: ok")


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
    ppm = float(value) if value is not None else 0.0
    reading = "unknown" if value is None else f"{ppm:.0f} ppm"
    if ppm >= 250:
        level = "Critical"
    elif ppm >= 200:
        level = "Warning"
    else:
        level = "Normal"
    return [
        time_part[:8] or dt[:19],
        reading,
        level,
        str(r.get("message") or ""),
    ]


def gas_alert_rows() -> list[list[str]]:
    rows = api_client.sensor_readings(sensor_name="gas", dangerous_only=True, limit=50)
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        return [_status_row(result.message, GAS_ALERT_COLUMNS)]
    return [_format_gas_row(r) for r in rows]


def _rows_to_html(headers: list[str], rows: list[list[str]]) -> str:
    import html as _html
    ths = "".join(f"<th>{_html.escape(h)}</th>" for h in headers)
    trs = "".join(
        "<tr>" + "".join(f"<td>{_html.escape(str(c))}</td>" for c in row) + "</tr>"
        for row in rows
    )
    return (
        "<div class='log-table-wrap'>"
        f"<table class='log-table'><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>"
        "</div>"
    )


def detection_events_html(class_filter: str) -> str:
    from .constants import DETECTION_HEADERS
    return _rows_to_html(DETECTION_HEADERS, filter_detection_events(class_filter))


def system_events_html() -> str:
    from .constants import SYSTEM_EVENT_HEADERS
    return _rows_to_html(SYSTEM_EVENT_HEADERS, system_event_rows())


def gas_alerts_html() -> str:
    from .constants import GAS_ALERT_HEADERS
    return _rows_to_html(GAS_ALERT_HEADERS, gas_alert_rows())


def gas_kpi_card_html() -> str:
    """Return just the Gas Alerts metric_html string — single COUNT query, no pagination cap."""
    count = api_client.sensor_readings_count(sensor_name="gas", dangerous_only=True)
    if count is None:
        return metric_html("Gas Alerts", "—", "Danger readings", YELLOW)
    value = str(count) if count else "No data yet"
    return metric_html("Gas Alerts", value, "Danger readings", YELLOW)


def data_kpi_cards() -> list[tuple[str, str, str, str]]:
    """Returns first 2 KPI cards (static). Gas Alerts card is built by gas_kpi_card_html()."""
    stats = api_client.detection_stats()
    latest = api_client.detections(limit=1)

    if any(value is None for value in (stats, latest)):
        return [
            ("Total Detections", "Backend unavailable", "Data API", RED),
            ("Last Detection", "Backend unavailable", "Data API", RED),
        ]

    total = int(stats.get("total") or 0)
    last = latest[0] if latest else None
    return [
        ("Total Detections", str(total) if total else "No data yet", "Saved records", ORANGE),
        ("Last Detection", _canonical_class(last["class_name"]) if last else "No data yet",
         str(last.get("detection_time", ""))[:19] if last else "No saved detection", PURPLE),
    ]


def export_detections_csv(class_filter: str):
    import csv
    import tempfile

    from .constants import DETECTION_HEADERS
    rows = filter_detection_events(class_filter)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", prefix="detection_events_"
    )
    csv.writer(tmp).writerows([DETECTION_HEADERS] + rows)
    tmp.close()
    return gr.update(value=tmp.name, visible=True)


def export_gas_csv():
    import csv
    import tempfile

    from .constants import GAS_ALERT_HEADERS
    rows = gas_alert_rows()
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", prefix="gas_alerts_"
    )
    csv.writer(tmp).writerows([GAS_ALERT_HEADERS] + rows)
    tmp.close()
    return gr.update(value=tmp.name, visible=True)


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
                [float(r.get("max_value") or 0) for r in rows], "Gas ppm", YELLOW, 250, "")

    if data_source == "Temperature":
        rows = api_client.stat_sensor_over_time("temperature", "minute")
        result = api_client.service_result(rows, "Backend unavailable")
        if not result.available or not result.has_data:
            return [], [], "°C", "#f97316", 50, result.message
        return ([_fmt_bucket(r["bucket"]) for r in rows],
                [float(r.get("avg_value") or 0) for r in rows], "°C", "#f97316", 50, "")

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
    if kind == "temperature":
        fig = build_statistics_figure("Temperature", "Line")
        fig.update_layout(title_text="Temperature Sensor Readings", height=280)
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


# Throttle: rebuild chart data from DB at most once per interval
_CHART_INTERVAL = 5.0
_gas_fig_cache: go.Figure | None = None
_dist_fig_cache: go.Figure | None = None
_gas_fig_last_rebuild: float = 0.0
_dist_fig_last_rebuild: float = 0.0

_STATS_INTERVAL = 15.0
_stats_fig_last_rebuild: float = 0.0


def _build_gas_history_figure() -> go.Figure:
    rows = api_client.stat_sensor_over_time("gas", "minute")
    result = api_client.service_result(rows, "Backend unavailable")
    if not result.available or not result.has_data:
        fig = _empty_figure("Gas Sensor History", result.message)
        fig.update_layout(height=280, showlegend=False)
        return fig
    times = [_fmt_bucket(r["bucket"]) for r in rows]
    values = [float(r.get("max_value") or 0) for r in rows]
    fig = _base_figure("Gas Sensor History")
    fig.add_bar(x=times, y=values, marker_color=YELLOW, name="Peak ppm")
    if times:
        fig.add_scatter(x=times, y=[200] * len(times), mode="lines",
                        line={"color": "#f59e0b", "dash": "dot"}, name="Warning")
        fig.add_scatter(x=times, y=[250] * len(times), mode="lines",
                        line={"color": RED, "dash": "dot"}, name="Danger")
    fig.update_layout(height=280)
    fig.update_yaxes(title_text="ppm (peak)", title_font={"size": 14}, tickfont={"size": 13})
    return fig


def gas_history_figure() -> go.Figure:
    global _gas_fig_cache, _gas_fig_last_rebuild
    now = time.time()
    if now - _gas_fig_last_rebuild >= _CHART_INTERVAL:
        _gas_fig_last_rebuild = now
        _gas_fig_cache = _build_gas_history_figure()
    fig = _gas_fig_cache or _build_gas_history_figure()
    # Unique meta forces Gradio to always send a WebSocket update to the browser
    fig.update_layout(meta={"ts": now})
    return fig


def _build_class_distribution_figure() -> go.Figure:
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


def class_distribution_figure() -> go.Figure:
    global _dist_fig_cache, _dist_fig_last_rebuild
    now = time.time()
    if now - _dist_fig_last_rebuild >= _CHART_INTERVAL:
        _dist_fig_last_rebuild = now
        _dist_fig_cache = _build_class_distribution_figure()
    fig = _dist_fig_cache or _build_class_distribution_figure()
    fig.update_layout(meta={"ts": now})
    return fig

def statistics_status(data_source: str, chart_type: str) -> str:
    return f"Showing **{data_source}** as a **{chart_type}** chart from the data API."


def _refresh_statistics_tick(nav: str, stat_source: str, chart_type: str) -> tuple:
    global _stats_fig_last_rebuild
    no = gr.update()
    if nav != "Statistics":
        return no, no, no, no, no
    now = time.time()
    if now - _stats_fig_last_rebuild < _STATS_INTERVAL:
        return no, no, no, no, no
    _stats_fig_last_rebuild = now
    return (
        build_statistics_figure(stat_source, chart_type),
        overview_figure("detections"),
        overview_figure("gas"),
        overview_figure("classes"),
        overview_figure("temperature"),
    )


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
    "rgb_module":       "🎛",
    "rgb_status":       "🌈",
    "camera_servo":     "🔧",
}


def test_header_html(test: dict, status: str) -> str:
    icon = _TEST_ICONS.get(test["id"], "🔧")
    icon_bg = test["accent"] + "20"
    if status == "passed":
        badge = "<span class='ts-passed' style='color:#10b981;font-size:15px;font-weight:700'>✓</span>"
    elif status == "failed":
        badge = "<span class='ts-failed' style='color:#ef4444;font-size:15px;font-weight:700'>✗</span>"
    elif status == "skipped":
        badge = "<span class='ts-skipped' style='color:#f59e0b;font-size:15px;font-weight:700'>!</span>"
    else:
        badge = "<span class='ts-none'></span>"
    return (
        f"<div style='display:flex;align-items:center;gap:9px'>"
        f"<div style='width:32px;height:32px;border-radius:8px;background:{icon_bg};"
        f"display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0'>{icon}</div>"
        f"<span style='font-size:13px;font-weight:700;color:#1e293b;flex:1'>{test['name']}</span>"
        f"{badge}</div>"
    )


def test_rows_html(test: dict, status: str, detail: str = "") -> str:
    rows = ""
    safe_detail = html.escape(detail) if detail else ""
    for label, expected in test["checks"]:
        if status == "not_tested":
            actual = "<span style='color:#94a3b8;font-size:11px'>not tested</span>"
        elif status == "passed":
            actual = (
                f"<span style='color:#10b981;font-size:11px;font-weight:600'>{expected} ✓</span>"
            )
        elif status == "skipped":
            actual = "<span style='color:#f59e0b;font-size:11px;font-weight:600'>Skipped !</span>"
        else:
            actual = "<span style='color:#ef4444;font-size:11px;font-weight:600'>Error ✗</span>"
        rows += (
            f"<div style='display:flex;align-items:center;padding:4px 0;border-bottom:1px solid #f3f4f6'>"
            f"<span style='font-size:11px;color:#64748b;flex:1'>{label}</span>"
            f"{actual}</div>"
        )
    if safe_detail and status in {"failed", "skipped"}:
        rows += (
            "<div style='margin-top:6px;padding:6px 8px;border-radius:6px;"
            "background:#fef2f2;border:1px solid #fecaca;color:#991b1b;"
            f"font-size:11px;line-height:1.35'>{safe_detail}</div>"
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
        pct, ok_count, fail_count = 0, 0, 0
        status_label, ring_color = "No Tests Run", "#94a3b8"
        issues = []
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

    # Bigger ring: 110px diameter
    r, circ = 46, 289.0
    offset = circ * (1 - pct / 100)
    svg = (
        f'<svg width="110" height="110" viewBox="0 0 110 110">'
        f'<circle cx="55" cy="55" r="{r}" fill="none" stroke="#e5e7eb" stroke-width="9"/>'
        f'<circle cx="55" cy="55" r="{r}" fill="none" stroke="{ring_color}" stroke-width="9"'
        f' stroke-dasharray="{circ}" stroke-dashoffset="{offset:.1f}"'
        f' stroke-linecap="round" transform="rotate(-90 55 55)"/>'
        f'<text x="55" y="62" text-anchor="middle" font-size="20" font-weight="800"'
        f' fill="{ring_color}">{pct}%</text></svg>'
    )
    if all_not_tested:
        ok_badge = (
            "<span style='background:#f1f5f9;color:#64748b;border-radius:999px;"
            "font-size:11px;font-weight:600;padding:3px 10px'>Run tests to see results</span>"
        )
        fail_badge = ""
    else:
        ok_badge = (
            f"<span style='background:#d1fae5;color:#065f46;border-radius:999px;"
            f"font-size:11px;font-weight:600;padding:3px 10px'>{ok_count} passed</span>"
        )
        fail_badge = (
            f"<span style='background:#fee2e2;color:#991b1b;border-radius:999px;"
            f"font-size:11px;font-weight:600;padding:3px 10px'>{fail_count} failed</span>"
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

    # Layout: title → status label → ring → badges (all centred, stacked vertically)
    return (
        f"<div style='background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;"
        f"padding:16px 12px;box-shadow:0 1px 2px rgba(15,23,42,0.04);text-align:center'>"
        f"<div style='font-size:13px;font-weight:800;color:#94a3b8;letter-spacing:0.06em;"
        f"text-transform:uppercase;margin-bottom:4px'>Diagnostic Summary</div>"
        f"<div style='font-size:16px;font-weight:800;color:#1e293b;margin-bottom:12px'>"
        f"{status_label}</div>"
        f"<div style='display:flex;justify-content:center;margin-bottom:12px'>{svg}</div>"
        f"<div style='display:flex;justify-content:center;gap:8px;flex-wrap:wrap'>"
        f"{ok_badge} {fail_badge}</div>"
        f"{('<div style=\"margin-top:14px;text-align:left\">' + issues_html + '</div>') if issues_html else ''}"
        f"</div>"
    )


def diagnostic_progress(state: dict[str, str] | None) -> str:
    state = state or initial_test_state()
    passed = sum(1 for value in state.values() if value == "passed")
    completed = sum(1 for value in state.values() if value != "not_tested")
    return f"### Component Tests\n{completed}/{len(TEST_IDS)} run - {passed} passed"


def _component_status(test_id: str) -> str:
    """Run a real station hardware self-test."""
    status, _detail = _component_result(test_id)
    return status


def _component_result(test_id: str) -> tuple[str, str]:
    result = api_client.test_component(test_id)
    if result is None:
        return "failed", "Station hardware API unavailable"
    status = str(result.get("status") or "failed")
    if status not in {"passed", "failed", "skipped"}:
        status = "failed"
    return status, str(result.get("detail") or "")


def run_single_test(state: dict[str, str] | None, test_id: str) -> tuple[Any, ...]:
    next_state = dict(state or initial_test_state())
    status, detail = _component_result(test_id)
    next_state[test_id] = status
    t = TEST_LOOKUP[test_id]
    return (
        next_state,
        test_header_html(t, status),
        test_rows_html(t, status, detail),
        diagnostic_summary_html(next_state),
        diagnostic_progress(next_state),
    )


def run_all_tests(state: dict[str, str] | None) -> tuple[Any, ...]:
    next_state: dict[str, str] = {}
    pairs: list[str] = []
    for tid in TEST_IDS:
        status, detail = _component_result(tid)
        next_state[tid] = status
        t = TEST_LOOKUP[tid]
        pairs.append(test_header_html(t, status))
        pairs.append(test_rows_html(t, status, detail))
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
    data_logs.class_filter.change(fn=detection_events_html, inputs=[data_logs.class_filter], outputs=[data_logs.detection_table], show_progress="hidden")
    data_logs.detection_export_button.click(fn=export_detections_csv, inputs=[data_logs.class_filter], outputs=[data_logs.detection_export_file], show_progress="hidden")
    data_logs.gas_export_button.click(fn=export_gas_csv, inputs=None, outputs=[data_logs.gas_export_file], show_progress="hidden")
    # Refresh gas table and gas KPI when class filter changes (user is actively on the page)
    data_logs.class_filter.change(fn=gas_alerts_html, inputs=None, outputs=[data_logs.gas_table], show_progress="hidden")
    data_logs.class_filter.change(fn=gas_kpi_card_html, inputs=None, outputs=[data_logs.gas_kpi], show_progress="hidden")


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


def restart_frontend() -> str:
    import os
    import threading
    threading.Timer(2.0, lambda: os._exit(0)).start()
    return (
        "<div style='background:#1e3a5f;border:1px solid #3b82f6;border-radius:8px;"
        "padding:10px 14px;color:#93c5fd;font-size:12px;'>"
        "Frontend restarting in ~2 seconds. Refresh the page in about 10 seconds."
        "</div>"
    )


def reboot_pi() -> str:
    result = api_client.reboot_pi()
    if result is None:
        return (
            "<div style='background:#7c2d12;border:1px solid #ea580c;border-radius:8px;"
            "padding:10px 14px;color:#fca5a5;font-size:12px;'>"
            "Failed to reach the station backend. Is it running?"
            "</div>"
        )
    return (
        "<div style='background:#1e3a5f;border:1px solid #3b82f6;border-radius:8px;"
        "padding:10px 14px;color:#93c5fd;font-size:12px;'>"
        "Raspberry Pi is rebooting. All services will be unavailable for ~60 seconds."
        "</div>"
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
    debugging.restart_frontend_btn.click(
        fn=restart_frontend,
        inputs=None,
        outputs=[debugging.system_control_status],
        show_progress="hidden",
    )
    debugging.reboot_pi_btn.click(
        fn=reboot_pi,
        inputs=None,
        outputs=[debugging.system_control_status],
        show_progress="hidden",
    )


def wire_callbacks(layout: Any) -> None:
    def _load_page_content(nav: str, stat_source: str, chart_type: str) -> tuple[Any, ...]:
        no = gr.update()
        if nav == "Data":
            return (
                detection_events_html("All classes"), gas_alerts_html(), gas_kpi_card_html(),
                no, no, no, no, no, no,
            )
        if nav == "Statistics":
            return (
                no, no, no,
                build_statistics_figure(stat_source, chart_type), no,
                overview_figure("detections"), overview_figure("gas"),
                overview_figure("classes"), overview_figure("temperature"),
            )
        if nav == "Debugging":
            return no, no, no, no, diagnostic_summary_html(None), no, no, no, no
        return no, no, no, no, no, no, no, no, no

    layout.nav.change(
        fn=page_updates,
        inputs=[layout.nav],
        outputs=[layout.header_icon, layout.header_title, layout.header_subtitle, *layout.page_columns],
        show_progress="hidden",
    ).then(
        fn=_load_page_content,
        inputs=[layout.nav, layout.statistics.source, layout.statistics.chart_type],
        outputs=[
            layout.data_logs.detection_table,
            layout.data_logs.gas_table,
            layout.data_logs.gas_kpi,
            layout.statistics.main_plot,
            layout.debugging.summary_output,
            layout.statistics.overview_detections,
            layout.statistics.overview_gas,
            layout.statistics.overview_classes,
            layout.statistics.overview_temperature,
        ],
        show_progress="hidden",
        concurrency_limit=None,
    )
    layout.timer.tick(fn=current_clock, inputs=None, outputs=[layout.clock], show_progress="hidden")
    layout.timer.tick(fn=gas_banner_html, inputs=None, outputs=[layout.gas_banner], show_progress="hidden")
    layout.camera_timer.tick(
        fn=live_camera_frame,
        inputs=[layout.nav, layout.operating.cam_state],
        outputs=[layout.operating.camera_output],
        show_progress="hidden",
    )
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
    layout.lcd_button.click(
        fn=cycle_lcd_screen,
        inputs=None,
        outputs=[layout.lcd_status],
        show_progress="hidden",
    )
    wire_operating_page(layout.operating, layout.nav)
    wire_data_logs_page(layout.data_logs)
    wire_statistics_page(layout.statistics)
    wire_debugging_page(layout.debugging)

    def _refresh_gas_kpi(nav: str) -> Any:
        if nav != "Data":
            return gr.update()
        return gas_kpi_card_html()

    layout.timer.tick(
        fn=_refresh_gas_kpi,
        inputs=[layout.nav],
        outputs=[layout.data_logs.gas_kpi],
        show_progress="hidden",
    )

    def _refresh_gas_table(nav: str) -> Any:
        if nav != "Data":
            return gr.update()
        return gas_alerts_html()

    layout.timer.tick(
        fn=_refresh_gas_table,
        inputs=[layout.nav],
        outputs=[layout.data_logs.gas_table],
        show_progress="hidden",
    )

    def _refresh_gas_history_tick(nav: str) -> Any:
        if nav != "Data":
            return gr.update()
        return gas_history_figure()

    def _refresh_class_dist_tick(nav: str) -> Any:
        if nav != "Data":
            return gr.update()
        return class_distribution_figure()

    layout.timer.tick(
        fn=_refresh_gas_history_tick,
        inputs=[layout.nav],
        outputs=[layout.data_logs.gas_history_plot],
        show_progress="hidden",
    )

    layout.timer.tick(
        fn=_refresh_class_dist_tick,
        inputs=[layout.nav],
        outputs=[layout.data_logs.class_dist_plot],
        show_progress="hidden",
    )

    layout.timer.tick(
        fn=_refresh_statistics_tick,
        inputs=[layout.nav, layout.statistics.source, layout.statistics.chart_type],
        outputs=[
            layout.statistics.main_plot,
            layout.statistics.overview_detections,
            layout.statistics.overview_gas,
            layout.statistics.overview_classes,
            layout.statistics.overview_temperature,
        ],
        show_progress="hidden",
    )


