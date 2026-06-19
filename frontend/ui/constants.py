from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PD_IMAGE_DIR = PROJECT_ROOT / "PD_Images"
ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
ASSET_THUMBNAIL = ASSET_DIR / "sar_design_thumbnail.png"
ASSET_LOGO = ASSET_DIR / "Logo.png"

APP_TITLE = "RC SAR Ground Station"
DEFAULT_PAGE = "About"

ORANGE = "#f05a24"
BLUE = "#3b82f6"
GREEN = "#10b981"
RED = "#ef4444"
YELLOW = "#f59e0b"
PURPLE = "#8b5cf6"

PAGE_KEYS = [
    "About",
    "Operating",
    "Data",
    "Statistics",
    "Debugging",
]

PAGE_RENDER_ORDER = [
    "Operating",
    "About",
    "Data",
    "Statistics",
    "Debugging",
]

PAGE_TAB_IDS = {
    "About": "onboarding",
    "Operating": "operating",
    "Data": "data_logs",
    "Statistics": "statistics",
    "Debugging": "debugging",
}

PAGE_DETAILS = {
    "About": {
        "icon": "DOC",
        "title": "About",
        "subtitle": "Guides, setup instructions and manuals for operators.",
    },
    "Operating": {
        "icon": "CAM",
        "title": "Operating",
        "subtitle": "Live camera feed with real-time YOLOv26 person detection.",
    },
    "Data": {
        "icon": "DB",
        "title": "Data",
        "subtitle": "Detection history, gas alerts and statistics.",
    },
    "Statistics": {
        "icon": "CHT",
        "title": "Statistics",
        "subtitle": "Interactive Plotly charts for detections, confidence, gas and performance.",
    },
    "Debugging": {
        "icon": "BUG",
        "title": "Debugging",
        "subtitle": "Test sensors, actuators and system components.",
    },
}

PAGE_UI_LABELS = {
    "About": "📘 About",
    "Operating": "📹 Operating",
    "Data": "🗄️ Data",
    "Statistics": "📊 Statistics",
    "Debugging": "🐞 Debugging",
}

DETECTION_HEADERS = ["ID", "Class", "Confidence", "Date", "Time", "Priority"]
SYSTEM_EVENT_HEADERS = ["Time", "Component", "Message", "Status"]
GAS_ALERT_HEADERS = ["Time", "Reading", "Level", "Action"]

CLASS_GALLERY = [
    (str(ASSET_DIR / "Lying_person.png"), "lying_person - high priority"),
    (str(ASSET_DIR / "Crawling Person.png"), "crawling_person - high priority"),
    (str(ASSET_DIR / "Sitting person.png"), "sitting_person - medium priority"),
    (str(ASSET_DIR / "Partially_visible_person.png"), "partially_visible_person - medium priority"),
    (str(ASSET_DIR / "Stanting Person.png"), "standing_person - low priority"),
]

TEST_GROUPS = [
    (
        "Visual",
        GREEN,
        [
            {"id": "fpv_camera", "name": "FPV Camera", "accent": GREEN, "checks": [("RTSP Stream", "Connected"), ("Frame Rate", ">= 25 fps"), ("Latency", "< 200 ms")]},
            {"id": "detection_camera", "name": "Detection Camera", "accent": GREEN, "checks": [("RTSP Stream", "Connected"), ("Frame Rate", ">= 25 fps"), ("Resolution", "1280 x 720")]},
            {"id": "touchscreen", "name": "Touchscreen", "accent": PURPLE, "checks": [("Driver", "Loaded"), ("Touch Events", "Detected"), ("Response Time", "< 30 ms")]},
            {"id": "lcd_display", "name": "LCD Display", "accent": BLUE, "checks": [("I2C Address", "0x27"), ("Message", "HARDWARE TEST"), ("Backlight", "On")]},
        ],
    ),
    (
        "Sensors",
        PURPLE,
        [
            {"id": "gas_sensor", "name": "Gas Sensor MQ-2", "accent": PURPLE, "checks": [("ADC", "ADS1115 A0"), ("Current Reading", "< 250 ppm"), ("I2C Address", "0x48")]},
            {"id": "temp_humidity", "name": "Temp & Humidity (DHT11)", "accent": BLUE, "checks": [("Temperature", "10-50 C"), ("Humidity", "20-90%"), ("Data Pin", "GPIO 25")]},
        ],
    ),
    (
        "Actuators",
        YELLOW,
        [
            {"id": "detection_led", "name": "FPV Feed LED", "accent": RED, "checks": [("GPIO Pin", "GPIO 17"), ("State Change", "ON/OFF"), ("Response Time", "< 20 ms")]},
            {"id": "buzzer", "name": "Buzzer", "accent": YELLOW, "checks": [("GPIO Pin", "GPIO 5"), ("Pulse Pattern", "3 beeps"), ("Volume", "Audible")]},
            {"id": "system_led", "name": "Detection Feed LED", "accent": GREEN, "checks": [("GPIO Pin", "GPIO 23"), ("State Change", "ON/OFF"), ("Brightness", "Stable")]},
            {"id": "rgb_module", "name": "RGB Module", "accent": PURPLE, "checks": [("GPIO Pins", "26 / 16 / 6"), ("Color Cycle", "R/G/B"), ("Mode", "Digital")]},
            {"id": "rgb_status", "name": "System Status LED", "accent": BLUE, "checks": [("GPIO Pins", "22 / 24 / 27"), ("Color Cycle", "G/R/B/Y"), ("Mode", "PWM")]},
        ],
    ),
]

TEST_IDS = [test["id"] for _, _, tests in TEST_GROUPS for test in tests]
TEST_LOOKUP = {test["id"]: test for _, _, tests in TEST_GROUPS for test in tests}

CUSTOM_CSS = """
/* ─────────────────────────────────────────────────────
   RC SAR Ground Station — Design Tokens & Layout
   Target: 1024 × 600 px  Raspberry Pi 7-inch touchscreen
   Single source of truth: no duplicate selector blocks.
   ───────────────────────────────────────────────────── */

/* 1. DESIGN TOKENS */
:root {
  /* Brand */
  --sar-orange: #f05a24;
  --sar-orange-dark: #e8500a;
  --sar-orange-soft: #fff3ee;
  --sar-orange-border: #fed7c2;
  /* Semantic state */
  --sar-blue: #3b82f6;
  --sar-blue-soft: #eff6ff;
  --sar-blue-border: #bfdbfe;
  --sar-green: #10b981;
  --sar-green-soft: #ecfdf5;
  --sar-green-border: #a7f3d0;
  --sar-purple: #8b5cf6;
  --sar-purple-soft: #f5f3ff;
  --sar-purple-border: #ddd6fe;
  --sar-yellow: #f59e0b;
  --sar-yellow-soft: #fffbeb;
  --sar-yellow-border: #fde68a;
  --sar-red: #ef4444;
  --sar-red-soft: #fef2f2;
  --sar-red-border: #fecaca;
  /* Neutral */
  --sar-bg: #f6f7fb;
  --sar-surface: #ffffff;
  --sar-surface-soft: #f9fafb;
  --sar-border: #e5e7eb;
  --sar-border-strong: #d1d5db;
  --sar-text: #0f172a;
  --sar-text-muted: #64748b;
  --sar-text-soft: #94a3b8;
  /* Radii */
  --sar-radius-sm: 8px;
  --sar-radius-md: 12px;
  --sar-radius-lg: 16px;
  /* Shadow */
  --sar-shadow-card: 0 1px 2px rgba(15, 23, 42, 0.04);
  /* Layout — single source of truth for sidebar width */
  --sidebar-w: 188px;
}

/* 2. GRADIO THEME OVERRIDES */
.gradio-container {
  --body-background-fill: var(--sar-bg) !important;
  --block-background-fill: var(--sar-surface) !important;
  --block-border-color: var(--sar-border) !important;
  --input-background-fill: var(--sar-surface) !important;
  --input-border-color: var(--sar-border) !important;
  --button-primary-background-fill: var(--sar-orange) !important;
  --button-primary-background-fill-hover: var(--sar-orange-dark) !important;
  --button-primary-border-color: var(--sar-orange) !important;
  --button-primary-text-color: #ffffff !important;
  --button-secondary-background-fill: var(--sar-surface) !important;
  --button-secondary-background-fill-hover: var(--sar-surface-soft) !important;
  --button-secondary-border-color: var(--sar-border) !important;
  --button-secondary-text-color: var(--sar-text) !important;
}

/* 3. BASE */
* { box-sizing: border-box; }

body, .gradio-container {
  margin: 0 !important;
  padding: 0 !important;
  min-height: 100vh !important;
  max-width: none !important;
  background: var(--sar-bg) !important;
  color: var(--sar-text) !important;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
  font-size: 15px !important;
  line-height: 1.45 !important;
}

footer { display: none !important; }

/* 4. APP SHELL */
#app-shell {
  min-height: 100vh;
  gap: 0 !important;
  align-items: stretch;
  overflow: visible;
}
#app-shell > .form,
#main-area > .form,
#page-stack > .form {
  background: transparent !important;
  border: 0 !important;
}

/* 5. SIDEBAR — fixed so it never scrolls away */
#sidebar {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: var(--sidebar-w) !important;
  min-width: var(--sidebar-w) !important;
  max-width: var(--sidebar-w) !important;
  height: 100vh !important;
  z-index: 50 !important;
  padding: 10px 8px !important;
  background: var(--sar-surface) !important;
  border-right: 1px solid var(--sar-border) !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* 6. MAIN AREA — offset equal to sidebar width so content is never under it */
#main-area {
  margin-left: var(--sidebar-w) !important;
  min-height: 100vh;
  overflow: visible;
  padding: 0 !important;
  background: var(--sar-bg);
}

/* 7. TOP HEADER */
#top-header {
  position: sticky;
  top: 0;
  z-index: 20;
  min-height: 54px !important;
  padding: 6px 12px !important;
  background: var(--sar-surface);
  border-bottom: 1px solid var(--sar-border);
  align-items: center;
  gap: 4px !important;
}
#top-header .header-title { padding-left: 0 !important; }
#top-header .header-title h3 {
  color: var(--sar-text) !important;
  font-size: 22px !important;
  line-height: 1.1 !important;
  margin-top: 0 !important;
  margin-bottom: 2px !important;
}
#top-header .header-subtitle p {
  color: var(--sar-text-muted) !important;
  font-size: 13px !important;
  margin: 0 !important;
}
/* Hide the decorative DOC/CAM icon box — title moves to the left naturally */
#header-icon { display: none !important; min-width: 0 !important; width: 0 !important; overflow: hidden !important; padding: 0 !important; }
/* Hide the LCD status line, keep the button */
.lcd-status { display: none !important; }

#top-header button {
  border-radius: 8px !important;
  background: var(--sar-surface-soft) !important;
  color: var(--sar-text) !important;
  border: 1px solid var(--sar-border) !important;
  min-height: 44px !important;
  padding: 0 14px !important;
  font-size: 14px !important;
}

/* 8. PAGE STACK */
#page-stack { padding: 10px 14px 16px !important; gap: 10px !important; }
#page-tabs [role="tablist"], #page-tabs .tab-nav { display: none !important; }
.page-pane { gap: 10px !important; }

/* 9. LOGO */
.logo-card {
  padding: 4px 4px 8px !important;
  border-bottom: 1px solid var(--sar-border);
  margin-bottom: 8px;
}
.logo-img {
  width: 100px;
  height: auto;
  object-fit: contain;
  display: block;
  margin: 0 auto 4px;
}
.logo-mark {
  width: 54px;
  height: 54px;
  margin: 0 auto 4px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: var(--sar-orange);
  border: 1px solid var(--sar-orange-border);
  background: var(--sar-orange-soft);
  font-weight: 800;
  font-size: 16px;
}
.logo-title {
  margin: 0;
  text-align: center;
  font-size: 12px !important;
  font-weight: 800;
  color: var(--sar-text) !important;
}

/* 10. NAVIGATION */
.nav-radio .wrap, .nav-radio fieldset {
  display: flex !important;
  flex-direction: column !important;
  gap: 4px !important;
  border: 0 !important;
  padding: 0 !important;
  background: transparent !important;
}
.nav-radio label {
  border-radius: 8px !important;
  border: 1px solid transparent !important;
  padding: 9px 10px !important;
  min-height: 48px !important;
  font-size: 14px !important;
  line-height: 1.2 !important;
  width: 100% !important;
  color: var(--sar-text) !important;
  background: transparent !important;
}
.nav-radio label:has(input:checked),
#sidebar .wrap label:has(input:checked) {
  background: var(--sar-orange-soft) !important;
  border-color: var(--sar-orange-border) !important;
  color: var(--sar-orange-dark) !important;
  font-weight: 800 !important;
}
#sidebar .wrap label input { accent-color: var(--sar-orange) !important; }

/* 11. SIDEBAR STATUS */
.sidebar-status {
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--sar-border);
  font-size: 12px;
}
.status-line {
  display: flex;
  gap: 8px;
  align-items: center;
  min-height: 22px;
  color: #4b5563;
  font-size: 12px;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  display: inline-block;
  box-shadow: 0 0 5px currentColor;
}
.clock-line p { color: var(--sar-text-muted) !important; font-size: 12px !important; }

/* 12. HEADER COMPONENTS */
.header-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: var(--sar-blue);
  border: 1px solid var(--sar-blue-border);
  background: var(--sar-blue-soft);
  font-weight: 800;
  font-size: 10px;
}
.header-title h3, .header-title p,
.compact-md h1, .compact-md h2, .compact-md h3, .compact-md p {
  margin-top: 0 !important;
  margin-bottom: 4px !important;
}
.header-subtitle p { color: var(--sar-text-muted); font-size: 13px; margin: 0 !important; }
.lcd-status textarea { min-height: 30px !important; font-size: 12px !important; }

/* 13. CARDS */
.app-card, .metric-card, .test-card, .camera-panel,
.about-display-card, .about-faq-item {
  background: var(--sar-surface) !important;
  border: 1px solid var(--sar-border) !important;
  border-radius: var(--sar-radius-lg) !important;
  box-shadow: var(--sar-shadow-card) !important;
}
.app-card { padding: 12px !important; }
.metric-card { min-height: 90px; padding: 12px !important; }
.control-card {
  background: var(--sar-surface) !important;
  border: 1px solid var(--sar-border) !important;
  border-radius: var(--sar-radius-md) !important;
  box-shadow: var(--sar-shadow-card) !important;
  padding: 8px 12px !important;
}
.welcome-card {
  background: linear-gradient(135deg, var(--sar-orange-soft), #fffaf7) !important;
  border-color: var(--sar-orange-border) !important;
}

/* 14. METRICS */
.metric-label { color: var(--sar-text-muted); font-size: 13px; font-weight: 700; }
.metric-value { margin: 3px 0; color: var(--sar-orange); font-size: 30px; font-weight: 800; line-height: 1; }
.metric-note { color: var(--sar-text-muted); font-size: 13px; }
.stat-number input, .stat-number textarea { font-weight: 800 !important; color: var(--sar-orange) !important; }

/* KPI row — equal width AND equal height for all three cards */
.kpi-row { flex-wrap: nowrap !important; align-items: stretch !important; }
.kpi-row > .form { display: flex !important; flex: 1 1 0 !important; min-width: 0 !important; align-items: stretch !important; }
.kpi-row .metric-card {
  flex: 1 1 0 !important;
  min-width: 0 !important;
  width: 100% !important;
  height: auto !important;
  min-height: 90px !important;
  align-self: stretch !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
}
.kpi-row .metric-card > .form { width: 100% !important; height: 100% !important; }
.kpi-row .metric-card .block,
.kpi-row .metric-card .wrap,
.kpi-row .metric-card .compact-md {
  width: 100% !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}

/* 15. BADGES */
.badge-row { display: flex; flex-wrap: wrap; gap: 5px; }
.badge {
  display: inline-flex;
  min-height: 22px;
  align-items: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 800;
  border: 1px solid var(--sar-orange-border);
  color: var(--sar-orange);
  background: var(--sar-orange-soft);
}

/* 16. CAMERA */
.camera-image img {
  border-radius: 10px !important;
  border: 2px solid var(--sar-orange) !important;
  object-fit: cover !important;
}
.camera-image .image-container {
  border: 2px solid var(--sar-orange) !important;
  background: #111827 !important;
  border-radius: 10px !important;
}

/* 17. TABLES */
.compact-table table { font-size: 12px !important; }
.compact-table th, .compact-table td { padding: 5px 7px !important; }

/* 18. CONTROLS (operating page) — 3 compact operator control cards */
.control-card label, .control-card span { font-size: 13px !important; }

/* One row, three equal-height control cards */
.op-controls-row {
  gap: 10px !important;
  align-items: stretch !important;
  flex-wrap: nowrap !important;
  margin-bottom: 8px !important;
}
.op-control-cell {
  gap: 6px !important;
  min-width: 0 !important;
}
/* Neutralise Gradio's inner block chrome so each card reads as one clean surface */
.op-control-cell .block {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}
.op-control-label {
  display: block !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  color: var(--sar-text-muted) !important;
  letter-spacing: 0.01em !important;
  line-height: 1.2 !important;
}
/* Toggle buttons (elem_classes land directly on the <button>) */
.op-toggle-btn { width: 100% !important; }
.control-card button.op-toggle-btn {
  min-height: 44px !important;
  height: 44px !important;
  font-size: 14px !important;
  font-weight: 700 !important;
  letter-spacing: 0.01em !important;
  border-radius: 8px !important;
}

/* Confidence Threshold card — label + live value over a compact slider */
.op-threshold-head {
  display: flex !important;
  align-items: baseline !important;
  justify-content: space-between !important;
  gap: 8px !important;
}
.op-threshold-value {
  font-size: 16px !important;
  font-weight: 800 !important;
  color: var(--sar-orange) !important;
  line-height: 1 !important;
}
/* Hide Gradio's built-in slider head (label + number box + reset);
   the card's own head already shows "Confidence Threshold" and the live value.
   The range input keeps its aria-label, so it stays screen-reader accessible. */
.op-threshold .head { display: none !important; }

/* Slider gray — exact class from Gradio Svelte template: slider_input_container.svelte-8epfm4 */
#op-threshold-slider .slider_input_container,
.op-threshold .slider_input_container {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
/* Also strip .wrap and .tab-like-container backgrounds */
#op-threshold-slider .wrap,
#op-threshold-slider .tab-like-container,
.op-threshold .wrap,
.op-threshold .tab-like-container {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
/* Strip the block-level padded wrapper */
#op-threshold-slider,
#op-threshold-slider.block,
#op-threshold-slider.block.padded {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}

/* AI Detection — ON state: .op-ai-btn is on wrapper div, button.primary is the inner element */
.op-ai-btn button.primary,
.op-ai-btn button[class*="primary"] {
  background: #d1fae5 !important;
  color: #065f46 !important;
  border: 1.5px solid #10b981 !important;
  box-shadow: none !important;
}
.op-ai-btn button.primary:hover { background: #a7f3d0 !important; border-color: #059669 !important; }
/* AI Detection — OFF state */
.op-ai-btn button.secondary,
.op-ai-btn button[class*="secondary"],
.op-ai-btn button:not([class*="primary"]) {
  background: #fef2f2 !important;
  color: #991b1b !important;
  border: 1.5px solid #fca5a5 !important;
  box-shadow: none !important;
}
.op-ai-btn button.secondary:hover,
.op-ai-btn button:not([class*="primary"]):hover { background: #fee2e2 !important; border-color: #ef4444 !important; }

/* Camera mode button — neutral, distinct from AI toggle */
button.op-cam-btn {
  background: var(--sar-surface) !important;
  color: var(--sar-text) !important;
  border: 1.5px solid var(--sar-border-strong) !important;
  box-shadow: none !important;
}
button.op-cam-btn:hover { background: var(--sar-surface-soft) !important; border-color: var(--sar-text-muted) !important; }

/* Camera fullwidth — no internal gaps */
.camera-fullwidth,
.camera-fullwidth > div,
.camera-fullwidth .wrap { width: 100% !important; padding: 0 !important; }
.camera-fullwidth .image-container {
  border-radius: 10px !important;
  width: 100% !important;
}
.op-camera-status-wrap,
.op-camera-status-wrap .block,
.op-camera-status-wrap .wrap {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}
.op-camera-status {
  margin-top: 6px;
  min-height: 34px;
  display: flex;
  align-items: center;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 13px;
  font-weight: 700;
  border: 1px solid var(--sar-border);
  background: var(--sar-surface-soft);
  color: var(--sar-text-muted);
}
.op-camera-status-ok {
  background: var(--sar-green-soft);
  border-color: var(--sar-green-border);
  color: #065f46;
}
.op-camera-status-warning {
  background: var(--sar-yellow-soft);
  border-color: var(--sar-yellow-border);
  color: #92400e;
}
.op-camera-status-error {
  background: var(--sar-red-soft);
  border-color: var(--sar-red-border);
  color: #991b1b;
}

/* Stats row section titles (plain HTML h3, no Gradio markdown wrapper) */
.op-section-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--sar-text);
  line-height: 1.2;
}
.op-stats-row { margin-top: 8px !important; }

/* Strip gray from Live Stats and Recent card interiors */
.op-stats-row .app-card {
  --block-background-fill: transparent;
  --block-border-color: transparent;
  --block-border-width: 0px;
  --panel-background-fill: transparent;
  --panel-border-color: transparent;
}
.op-stats-row .app-card > .form,
.op-stats-row .app-card .form,
.op-stats-row .app-card .block.gradio-html,
.op-stats-row .app-card .block.gradio-row,
.op-stats-row .app-card .block.gradio-column,
.op-stats-row .app-card .block.gradio-dataframe > .wrap,
.op-stats-row .app-card .block.padded {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
/* Compact Recent card: kill gap between title and table */
.op-stats-row .app-card > .form {
  gap: 4px !important;
}
.op-stats-row .app-card .block.gradio-html {
  padding: 0 !important;
  margin: 0 !important;
}
.op-stats-row .op-section-title {
  margin: 0 0 2px !important;
}
/* Recent card — collapse all spacing between title and table */
.recent-card > .form {
  gap: 2px !important;
  padding: 8px !important;
}
.recent-card .block {
  min-height: 0 !important;
  height: auto !important;
  padding: 0 !important;
  margin: 0 !important;
}
.recent-card .block.gradio-html {
  min-height: 0 !important;
  height: auto !important;
  padding: 0 !important;
  margin: 0 !important;
}
.recent-card .block.gradio-dataframe {
  padding: 0 !important;
  margin: 0 !important;
}
.recent-card .block.gradio-dataframe > .wrap {
  padding: 0 !important;
  margin: 0 !important;
}

/* Recent outer column — strip Gradio gray */
.recent-outer-col.block,
.recent-outer-col {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}
/* recent-group uses app-card chrome; override padding + add overflow clip */
.op-stats-row .recent-group.app-card {
  padding: 0 !important;
  overflow: hidden !important;
}
/* rh-card is content only — app-card outer div provides the card chrome */
.recent-group .rh-card {
  background: transparent !important;
  border: 0 !important;
  border-radius: 0 !important;
  overflow: visible !important;
}
/* Buttons row — card footer */
.recent-group .recent-btn-row,
.recent-group .block.gradio-row.recent-btn-row {
  border-top: 1px solid #f3f4f6 !important;
  padding: 8px 12px !important;
  margin-top: 0 !important;
  min-height: 0 !important;
}
.rh-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  font-size: 13px;
}
.rh-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px 8px;
  font-weight: 700;
  font-size: 15px;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
}
.rh-table {
  width: 100%;
  border-collapse: collapse;
}
.rh-table thead th {
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6b7280;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
}
.rh-table tbody td {
  padding: 7px 10px;
  border-bottom: 1px solid #f3f4f6;
  color: #374151;
}
.rh-table tbody tr:last-child td { border-bottom: 0; }
.rh-cls { font-family: monospace; color: #1d4ed8 !important; }
.rh-time { color: #6b7280 !important; }
.rh-pri {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.rh-pri-high   { background: #fef2f2; color: #b91c1c; }
.rh-pri-medium { background: #fffbeb; color: #b45309; }
.rh-pri-low    { background: #f0fdf4; color: #15803d; }
.rh-empty { text-align: center; color: #9ca3af; padding: 20px; }

/* 19. BUTTONS */
.control-card button, .app-card button,
#top-header button, .metric-card button {
  min-height: 44px !important;
  font-size: 14px !important;
  padding: 0 14px !important;
  transition: background 120ms ease-out, color 120ms ease-out, border-color 120ms ease-out, box-shadow 120ms ease-out !important;
}
button.primary, .primary button {
  background: var(--sar-orange) !important;
  border-color: var(--sar-orange) !important;
}

/* 20. PLOTS */
.plot-card { min-height: 240px; }
.plot-card, .plot-card > div {
  background: var(--sar-surface) !important;
  border-radius: var(--sar-radius-md) !important;
}
/* Kill harsh chart frames — card supplies the only (subtle) border */
.plot-card, .plot-card > div, .plot-card .block, .plot-card .gradio-plot,
.plot-card .js-plotly-plot, .plot-card .plot-container, .plot-card .svg-container {
  border: 0 !important;
  box-shadow: none !important;
}
/* Two equal chart cards, no leftover empty space */
.data-chart-row { gap: 10px !important; }
.plot-cell { padding: 8px !important; }

/* 20b. DATA & LOGS — Stored Logs card */
.logs-card { display: flex !important; flex-direction: column !important; gap: 4px !important; }
.logs-card > div { background: transparent !important; }
.logs-header { align-items: center !important; gap: 8px !important; }
.logs-title { display: flex !important; flex-direction: column !important; gap: 1px !important; }
.logs-title-main { font-size: 16px !important; font-weight: 800 !important; color: var(--sar-text) !important; line-height: 1.15 !important; }
.logs-title-sub { font-size: 12px !important; color: var(--sar-text-muted) !important; }
.logs-export-col { display: flex !important; align-items: center !important; justify-content: flex-end !important; }
.logs-card .logs-export-col button {
  background: var(--sar-orange) !important;
  border: 1px solid var(--sar-orange) !important;
  color: #ffffff !important;
  min-height: 40px !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
}
.logs-card .logs-export-col button:hover { background: var(--sar-orange-dark) !important; border-color: var(--sar-orange-dark) !important; }
/* Class filter — sits above accordion panels */
.logs-filter-col-top.block,
.logs-filter-col-top { background: transparent !important; border: 0 !important; box-shadow: none !important; padding: 2px 0 6px !important; min-height: 0 !important; }
.logs-filter, .logs-filter > div, .logs-filter .block,
.logs-filter .label-wrap, .logs-filter label {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}
.logs-filter .label-wrap span, .logs-filter label span { color: var(--sar-text-muted) !important; font-weight: 600 !important; }
/* Dropdown input itself: light, bordered, readable */
.logs-filter .wrap, .logs-filter .secondary-wrap,
.logs-filter input, .logs-filter .container {
  background: var(--sar-surface) !important;
  color: var(--sar-text) !important;
  border: 1px solid var(--sar-border) !important;
  border-radius: 8px !important;
}
.logs-filter input { border: 0 !important; }
/* Accordion panels for tables */
.logs-accordion {
  background: var(--sar-surface) !important;
  border: 1px solid var(--sar-border) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  margin-bottom: 4px !important;
}
.logs-accordion .label-wrap,
.logs-accordion button.label-wrap {
  font-size: 13px !important;
  font-weight: 700 !important;
  color: var(--sar-text) !important;
  background: var(--sar-surface-soft) !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
  border: 0 !important;
  box-shadow: none !important;
}
.logs-accordion .wrap-outer,
.logs-accordion .wrap,
.logs-accordion .gap {
  background: var(--sar-surface) !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 8px 0 0 !important;
}
.logs-accordion .form,
.logs-accordion .block.gradio-column {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}
/* Strip Gradio's gray container around table */
.logs-card .compact-table, .logs-card .compact-table > div {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.logs-card .compact-table table { border: 1px solid var(--sar-border) !important; border-radius: 8px !important; overflow: hidden !important; }

/* HTML log tables (replaces gr.Dataframe to avoid Svelte 5 renderer freeze) */
.log-table-container { background: transparent !important; border: 0 !important; box-shadow: none !important; padding: 0 !important; }
.log-table-wrap { overflow-x: auto; width: 100%; }
.log-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.log-table th { background: var(--sar-surface-soft); color: var(--sar-text); font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; padding: 6px 8px; border-bottom: 2px solid var(--sar-border); text-align: left; white-space: nowrap; }
.log-table td { padding: 5px 8px; border-bottom: 1px solid var(--sar-border); color: var(--sar-text); vertical-align: middle; }
.log-table tbody tr:last-child td { border-bottom: 0; }
.log-table tbody tr:hover { background: var(--sar-surface-soft); }

/* Warning banner — full-width, appears between header and page content */
#gas-banner,
#gas-banner.block,
#gas-banner > .wrap {
  padding: 0 !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.gas-warning-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 14px;
  padding: 10px 14px;
  background: #fff1f2;
  border: 1.5px solid #fca5a5;
  border-radius: 10px;
  color: #991b1b;
  font-size: 13px;
  font-weight: 600;
  animation: gas-pulse 1.5s ease-in-out infinite;
}
.gas-warning-icon { font-size: 20px; flex-shrink: 0; }
.gas-warning-text strong { color: #7f1d1d; }
@keyframes gas-pulse {
  0%, 100% { border-color: #fca5a5; background: #fff1f2; }
  50%       { border-color: #ef4444; background: #fee2e2; }
}
/* Area safe banner — green */
.area-safe-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 14px;
  padding: 8px 14px;
  background: #f0fdf4;
  border: 1.5px solid #86efac;
  border-radius: 10px;
  color: #166534;
  font-size: 13px;
  font-weight: 600;
}
.area-safe-banner .gas-warning-text strong { color: #14532d; }

/* Temperature warning banner — amber/orange to distinguish from gas red */
.temp-warning-banner {
  background: #fffbeb !important;
  border-color: #fcd34d !important;
  color: #92400e !important;
  animation: temp-pulse 1.5s ease-in-out infinite;
}
.temp-warning-banner .gas-warning-text strong { color: #78350f; }
@keyframes temp-pulse {
  0%, 100% { border-color: #fcd34d; background: #fffbeb; }
  50%       { border-color: #f59e0b; background: #fef3c7; }
}

/* Export notice banner — temporary, compact, warning style */
.export-banner-wrap { padding: 0 !important; background: transparent !important; border: 0 !important; }
.export-banner {
  background: var(--sar-orange-soft);
  color: var(--sar-orange-dark);
  border: 1px solid var(--sar-orange-border);
  border-radius: 8px;
  padding: 7px 10px;
  font-size: 12px;
  font-weight: 600;
}

/* 21. DEBUG — test card v2 */
.debug-grid { gap: 10px !important; }

/* Accordion container — white card */
.debug-accordion {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 10px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important;
  overflow: hidden !important;
  margin-bottom: 10px !important;
}

/* Accordion header button */
.debug-accordion .label-wrap,
.debug-accordion button.label-wrap {
  border: 0 !important;
  border-radius: 0 !important;
  font-size: 12px !important;
  font-weight: 800 !important;
  letter-spacing: 0.06em !important;
  text-transform: uppercase !important;
  padding: 9px 14px !important;
  width: 100% !important;
  box-shadow: none !important;
}

/* Per-group: tinted bg + colored text + left accent border */
#debug-acc-visual   .label-wrap { background: #ecfdf5 !important; color: #059669 !important; border-left: 3px solid #10b981 !important; }
#debug-acc-sensors  .label-wrap { background: #f5f3ff !important; color: #7c3aed !important; border-left: 3px solid #8b5cf6 !important; }
#debug-acc-actuators .label-wrap { background: #fffbeb !important; color: #d97706 !important; border-left: 3px solid #f59e0b !important; }
#debug-acc-visual   .label-wrap svg { color: #059669 !important; }
#debug-acc-sensors  .label-wrap svg { color: #7c3aed !important; }
#debug-acc-actuators .label-wrap svg { color: #d97706 !important; }

/* Accordion inner content — white, strip gray */
.debug-accordion .wrap-outer,
.debug-accordion .wrap,
.debug-accordion .gap {
  background: #ffffff !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 10px !important;
}
.debug-accordion .form,
.debug-accordion .block.gradio-row,
.debug-accordion .block.gradio-column {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  --block-background-fill: transparent;
  --block-border-color: transparent;
  --block-border-width: 0px;
  --panel-background-fill: transparent;
  --panel-border-color: transparent;
}

/* Override Gradio's CSS custom properties for all blocks inside the card.
   Gradio's .form and .block use var(--block-background-fill) for their gray bg;
   setting it to transparent here cascades to every child. */
.test-card-v2 {
  background: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 10px !important;
  padding: 10px 12px !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04) !important;
  --block-background-fill: transparent;
  --block-border-color: transparent;
  --block-border-width: 0px;
  --block-radius: 0px;
  --block-shadow: none;
  --block-padding: 0px;
  --block-label-background-fill: transparent;
  --block-label-border-color: transparent;
  --block-label-border-width: 0px;
  --panel-background-fill: transparent;
  --panel-border-color: transparent;
  --panel-border-width: 0px;
}
.test-card-v2:has(.ts-passed) {
  background: #f0fdf4 !important;
  border-color: #86efac !important;
}
.test-card-v2:has(.ts-failed) {
  background: #fef2f2 !important;
  border-color: #fca5a5 !important;
}

/* Force vertical stacking inside test cards */
.test-card-v2 > .form {
  display: flex !important;
  flex-direction: column !important;
  gap: 0 !important;
  width: 100% !important;
}

/* Belt-and-suspenders: also zero out backgrounds explicitly */
.test-card-v2 .form,
.test-card-v2 .block,
.test-card-v2 .wrap,
.test-card-v2 .gradio-row,
.test-card-v2 > .form > .block {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* Button sits below the rows, full width */
.tcv2-btn {
  margin-top: 10px !important;
  width: 100% !important;
  order: 99 !important;
}
.tcv2-btn button {
  background: #ffffff !important;
  background-color: #ffffff !important;
  color: var(--sar-text-muted) !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 6px !important;
  font-size: 12px !important;
  min-height: 28px !important;
  height: 28px !important;
  padding: 0 10px !important;
  box-shadow: none !important;
  width: 100% !important;
}

/* 22. STATUS NOTICES */
.notice-info {
  border: 1px solid var(--sar-border);
  color: var(--sar-text);
  background: var(--sar-surface-soft);
  border-radius: 8px;
  padding: 7px 10px;
}
.notice-ok {
  border: 1px solid var(--sar-green-border);
  color: #047857;
  background: var(--sar-green-soft);
  border-radius: 8px;
  padding: 7px 10px;
}
.notice-warn {
  border: 1px solid var(--sar-yellow-border);
  color: #92400e;
  background: var(--sar-yellow-soft);
  border-radius: 8px;
  padding: 7px 10px;
}

/* 23. ABOUT PAGE */
.about-page {
  gap: 12px !important;
  color: var(--sar-text) !important;
  overflow-x: hidden !important;
}
.about-page .app-card,
.about-page .metric-card,
.about-page .about-card,
.about-page .about-step-card,
.about-page .about-workflow-card {
  background: var(--sar-surface) !important;
  border: 1px solid var(--sar-border) !important;
  border-radius: var(--sar-radius-lg) !important;
  box-shadow: var(--sar-shadow-card) !important;
}
.about-page .welcome-card {
  background: linear-gradient(135deg, var(--sar-orange-soft), #fffaf7) !important;
  border-color: var(--sar-orange-border) !important;
}
.about-page .prose,
.about-page .markdown,
.about-page .md,
.about-page .gradio-html,
.about-page .block,
.about-page .wrap,
.about-page fieldset {
  background: transparent !important;
  box-shadow: none !important;
}
.about-page .block,
.about-page .wrap,
.about-page fieldset,
.about-page .image-container,
.about-page .gallery,
.about-page .thumbnail-item {
  border-color: var(--sar-border) !important;
}
.about-page h2, .about-page h3, .about-page h4, .about-page strong {
  color: var(--sar-text) !important;
}
.about-page p, .about-page li, .about-page small, .about-page em {
  color: var(--sar-text-muted) !important;
}
.about-page .welcome-card p, .about-page .welcome-card li {
  color: var(--sar-text) !important;
}
.about-step-number {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-weight: 800;
  margin-bottom: 6px;
}
.about-led-row {
  display: grid;
  grid-template-columns: 16px minmax(140px, 0.8fr) 1fr;
  gap: 10px;
  align-items: center;
  min-height: 38px;
  border-bottom: 1px solid #eef2f7;
  font-size: 13px;
}
.about-led-row span {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  box-shadow: 0 0 7px currentColor;
}
.about-led-row em { font-style: normal; }
.about-classes-section { overflow-x: hidden !important; }
.about-class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  width: 100%;
  overflow-x: hidden;
}
.about-class-card {
  min-width: 0;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid color-mix(in srgb, var(--class-color) 34%, var(--sar-border));
  border-radius: 12px;
  box-shadow: var(--sar-shadow-card);
  display: flex;
  flex-direction: column;
}
.about-class-image {
  height: 165px;
  padding: 0;
  background: #111827;
  border-bottom: 1px solid #0d1117;
  overflow: hidden;
  flex: 0 0 auto;
}
.about-class-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 55%;
  display: block;
}
.about-class-placeholder { color: var(--sar-text-soft); font-size: 12px; }
.about-class-body {
  padding: 10px 12px 12px;
  position: relative;
  z-index: 1;
  background: #ffffff;
  min-height: 90px;
}
.about-class-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.about-class-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: var(--class-color);
}
.about-priority {
  border-radius: 6px;
  padding: 2px 6px;
  background: color-mix(in srgb, var(--class-color) 14%, white);
  color: var(--class-color);
  font-size: 11px;
  font-weight: 800;
}
.about-class-card h4 {
  margin: 0 0 4px;
  font-family: Consolas, ui-monospace, monospace;
  font-size: 13px;
}
.about-class-card p { margin: 0; font-size: 12px; line-height: 1.4; }
.about-search-flow {
  display: grid;
  grid-template-columns: repeat(20, minmax(0, 1fr));
  gap: 8px;
  align-items: stretch;
  overflow-x: hidden;
}
.about-flow-arrow {
  display: grid;
  place-items: center;
  grid-column: span 1;
  color: var(--sar-text-soft);
  font-size: 16px;
  font-weight: 800;
}
.about-flow-step { grid-column: span 2; }
.about-flow-step {
  min-height: 70px;
  border: 1px solid color-mix(in srgb, var(--flow-color) 28%, var(--sar-border));
  background: color-mix(in srgb, var(--flow-color) 8%, white);
  border-radius: 10px;
  padding: 8px;
  text-align: center;
}
.about-flow-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--flow-color);
  color: #fff;
}
.about-flow-icon svg { display: block; }
.about-flow-step strong, .about-flow-step small { display: block; }
.about-flow-step strong { margin-top: 5px; font-size: 11px; }
.about-flow-step small { margin-top: 3px; font-size: 11px; }
.about-display-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.about-display-card {
  background: var(--sar-surface);
  border: 1px solid var(--sar-border);
  border-radius: var(--sar-radius-lg);
  box-shadow: var(--sar-shadow-card);
  padding: 10px;
}
.about-display-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.about-display-chip {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: var(--sar-text);
  background: var(--sar-surface-soft);
  border: 1px solid var(--sar-border);
}
.about-display-chip-blue { color: var(--sar-blue); background: var(--sar-blue-soft); border-color: var(--sar-blue-border); }
.about-display-chip-green { color: var(--sar-green); background: var(--sar-green-soft); border-color: var(--sar-green-border); }
.about-display-chip-orange { color: var(--sar-orange); background: var(--sar-orange-soft); border-color: var(--sar-orange-border); }
.about-display-chip-purple { color: var(--sar-purple); background: var(--sar-purple-soft); border-color: var(--sar-purple-border); }
.about-display-chip-red { color: var(--sar-red); background: var(--sar-red-soft); border-color: var(--sar-red-border); }
.about-display-caption {
  color: var(--sar-text-muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.about-lcd-shell {
  border-radius: 10px;
  padding: 8px;
  background: #d4edda;
  border: 1px solid #a3cfaa;
}
.about-lcd-screen {
  position: relative;
  min-height: 96px;
  border-radius: 8px;
  padding: 10px 12px;
  background: #eaf4eb;
  color: #1a3320;
  border: 1px solid #81c784;
  font-family: "Courier New", Consolas, monospace;
}
.about-lcd-dots { display: inline-flex; gap: 4px; margin-bottom: 8px; }
.about-lcd-dots i {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #e57373;
  display: inline-block;
}
.about-lcd-dots i:nth-child(2) { background: #ffb74d; }
.about-lcd-dots i:nth-child(3) { background: #66bb6a; }
.about-lcd-screen pre { margin: 0; white-space: pre-line; font-size: 12px; line-height: 1.45; color: #1a3320; }
.about-display-card p { margin: 8px 2px 0; font-size: 12px; line-height: 1.45; color: var(--sar-text-muted); }
.about-checklist .wrap,
.about-checklist fieldset,
.about-checklist .checkbox-group {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
}
.about-checklist label {
  display: flex !important;
  width: 100% !important;
  min-height: 36px !important;
  align-items: center !important;
  gap: 10px !important;
  padding: 6px 0 !important;
  border-bottom: 1px solid #eef2f7 !important;
  color: var(--sar-text) !important;
  background: transparent !important;
}
.about-checklist input[type="checkbox"] {
  width: 18px !important;
  height: 18px !important;
  accent-color: var(--sar-green) !important;
}
.about-critical {
  border: 1px solid var(--sar-red-border);
  color: #991b1b;
  background: var(--sar-red-soft);
  border-radius: 8px;
  padding: 7px 10px;
}
.about-info-callout {
  background: var(--sar-orange-soft);
  color: var(--sar-orange-dark);
  border: 1px solid var(--sar-orange-border);
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  margin: 6px 0 2px;
}
.about-faq-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.about-faq-item {
  background: var(--sar-surface);
  border: 1px solid var(--sar-border);
  border-radius: var(--sar-radius-lg);
  box-shadow: var(--sar-shadow-card);
  padding: 10px 12px;
}
.about-faq-head { margin-bottom: 6px; }
.about-faq-chip {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: var(--sar-text);
  background: var(--sar-surface-soft);
  border: 1px solid var(--sar-border);
}
.about-faq-chip-blue { color: var(--sar-blue); background: var(--sar-blue-soft); border-color: var(--sar-blue-border); }
.about-faq-chip-green { color: var(--sar-green); background: var(--sar-green-soft); border-color: var(--sar-green-border); }
.about-faq-chip-orange { color: var(--sar-orange); background: var(--sar-orange-soft); border-color: var(--sar-orange-border); }
.about-faq-chip-purple { color: var(--sar-purple); background: var(--sar-purple-soft); border-color: var(--sar-purple-border); }
.about-faq-item p { margin: 0; font-size: 12px; line-height: 1.45; color: var(--sar-text-muted); }

/* About: strip transparent Gradio wrappers */
.about-page .form,
.about-page .block.padded,
.about-page .block.gradio-markdown,
.about-page .block.gradio-html,
.about-page .block.gradio-checkboxgroup,
.about-page .block:has(.prose),
.about-page .block:has(.gradio-html),
.about-page .wrap:not(.nav-radio .wrap),
.about-page fieldset {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.about-page .app-card > div,
.about-page .welcome-card > div,
.about-page .about-card > div { background: transparent !important; }
.about-page .welcome-card .metric-card,
.about-page .about-step-card,
.about-page .about-workflow-card {
  background: var(--sar-surface) !important;
  border: 1px solid var(--sar-border) !important;
}
.about-page .about-display-card,
.about-page .about-faq-item {
  background: var(--sar-surface) !important;
  border: 1px solid var(--sar-border) !important;
  border-radius: var(--sar-radius-lg) !important;
  box-shadow: var(--sar-shadow-card) !important;
}
.about-page textarea, .about-page input[type="text"] {
  background: var(--sar-surface) !important;
  color: var(--sar-text) !important;
}
.about-checklist-card { width: 100% !important; }
.about-checklist,
.about-checklist .wrap,
.about-checklist fieldset,
.about-checklist .checkbox-group,
.about-checklist .checkbox-group > div,
.about-checklist .wrap > div {
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: stretch !important;
  gap: 0 !important;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}
.about-checklist label,
.about-checklist .label-wrap {
  width: 100% !important;
  justify-content: flex-start !important;
  text-align: left !important;
  border-radius: 0 !important;
  box-shadow: none !important;
}
.about-checklist label span,
.about-checklist .label-wrap span {
  color: var(--sar-text) !important;
  text-align: left !important;
  white-space: normal !important;
}

/* 24. RESPONSIVE — About page grids only */
@media (max-width: 1100px) {
  .about-search-flow { grid-template-columns: repeat(16, minmax(0, 1fr)); }
  .about-display-grid, .about-faq-grid { grid-template-columns: repeat(1, minmax(0, 1fr)); }
}

/* Diagnostic Summary — pin to top of its column and strip wrapper chrome */
#diag-summary-col {
  align-self: flex-start !important;
  position: sticky;
  top: 8px;
}
#diag-summary-html,
#diag-summary-html.block,
#diag-summary-html > .wrap,
#diag-summary-col > .form,
#diag-summary-col .block {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* System Controls — strip Gradio grey from wrappers only (not buttons themselves) */
#sys-ctrl-cards, #sys-ctrl-cards.block, #sys-ctrl-cards > .wrap,
#sys-ctrl-btns, #sys-ctrl-btns.block, #sys-ctrl-btns > .form,
#sys-ctrl-btns > .form > .block,
#btn-restart-frontend.block, #btn-reboot-pi.block,
#sys-ctrl-status, #sys-ctrl-status.block, #sys-ctrl-status > .wrap {
  background: transparent !important;
  background-color: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  --block-background-fill: transparent;
  --block-border-color: transparent;
  --block-border-width: 0px;
}
#sys-ctrl-btns { gap: 12px !important; margin-top: 4px !important; }
#sys-ctrl-status { min-height: 0 !important; }

/* Buttons — explicit orange colour so nothing can override */
#btn-restart-frontend button,
#btn-reboot-pi button {
  background: var(--sar-orange) !important;
  background-color: var(--sar-orange) !important;
  border-color: var(--sar-orange-dark) !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  font-weight: 700 !important;
}
#btn-restart-frontend button:hover,
#btn-reboot-pi button:hover {
  background: var(--sar-orange-dark) !important;
  background-color: var(--sar-orange-dark) !important;
}

/* System Controls card visuals */
.sc-section { margin: 14px 0 0; }
.sc-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.sc-title {
  font-size: 15px;
  font-weight: 800;
  color: var(--sar-text);
}
.sc-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
.sc-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.sc-card {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid;
}
.sc-card-orange {
  background: var(--sar-orange-soft);
  border-color: var(--sar-orange-border);
}
.sc-card-red {
  background: var(--sar-red-soft);
  border-color: var(--sar-red-border);
}
.sc-icon { font-size: 20px; flex-shrink: 0; margin-top: 1px; }
.sc-card-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--sar-text);
  margin-bottom: 3px;
}
.sc-card-desc {
  font-size: 11px;
  line-height: 1.5;
  color: var(--sar-text-muted);
}
"""
