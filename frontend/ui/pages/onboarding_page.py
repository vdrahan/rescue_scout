from __future__ import annotations

import base64
from dataclasses import dataclass
from html import escape
from pathlib import Path

import gradio as gr

from ..constants import BLUE, CLASS_GALLERY, GREEN, ORANGE, PURPLE, RED, YELLOW
from ..handlers import badge_row


@dataclass
class OnboardingPage:
    checklist: gr.CheckboxGroup


CLASS_DETAILS = {
    "lying_person": ("Injured / unconscious person", "HIGH", RED),
    "crawling_person": ("Person in distress, moving", "HIGH", ORANGE),
    "sitting_person": ("Unable to stand, resting", "MED", YELLOW),
    "partially_visible_person": ("Behind obstacle / cover", "MED", PURPLE),
    "standing_person": ("Visible and upright person", "LOW", GREEN),
}

_CLASS_IMG_POSITION = {
    "lying_person":     "center 65%",
    "crawling_person":  "center 55%",
    "sitting_person":   "center 60%",
    "partially_visible_person": "center 85%",
    "standing_person":  "center 45%",
}


CHECKLIST_TASKS = [
    "RC car is fully charged and powered on",
    "Base station is connected to power",
    "Both cameras mounted and secured",
    "RC car within WiFi range of base station",
    "LCD shows STATUS: ACTIVE",
    "Gradio interface loaded on touchscreen",
    "Gas sensor shows nominal reading (< 200 ppm)",
    "Test buzzer before deployment",
]


def _image_data_uri(path: str) -> str:
    image_path = Path(path)
    if not image_path.exists():
        return ""
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _step_card(number: int, title: str, body: str, note: str, color: str) -> None:
    with gr.Column(elem_classes=["metric-card", "about-step-card"]):
        gr.Markdown(
            f"<div class='about-step-number' style='color:{color};border-color:{color}33;background:{color}10'>{number}</div>"
            f"\n\n**{title}**\n\n{body}\n\n`{note}`",
            elem_classes=["compact-md"],
        )


def render_detection_class_cards() -> str:
    cards: list[str] = []
    for image_path, label in CLASS_GALLERY:
        class_name = label.split(" - ", 1)[0]
        body, priority, color = CLASS_DETAILS[class_name]
        pos = _CLASS_IMG_POSITION.get(class_name, "center 55%")
        image_src = _image_data_uri(image_path)
        image_html = (
            f'<img src="{image_src}" alt="{escape(class_name)} example" style="object-position:{pos}">'
            if image_src
            else '<div class="about-class-placeholder">Image unavailable</div>'
        )
        cards.append(
            f"""
            <article class="about-class-card" style="--class-color:{color}">
              <div class="about-class-image">{image_html}</div>
              <div class="about-class-body">
                <div class="about-class-meta">
                  <span class="about-class-dot"></span>
                  <span class="about-priority">{priority}</span>
                </div>
                <h4>{escape(class_name)}</h4>
                <p>{escape(body)}</p>
              </div>
            </article>
            """
        )
    return "<div class='about-class-grid'>" + "".join(cards) + "</div>"


def render_search_workflow() -> str:
    _icons = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.77.04"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m22 8-6 4 6 4V8z"/><rect width="14" height="12" x="2" y="6" rx="2" ry="2"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="6" x2="10" y1="12" y2="12"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="15" x2="15.01" y1="13" y2="13"/><line x1="18" x2="18.01" y1="11" y2="11"/><rect width="20" height="12" x="2" y="6" rx="2"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></svg>',
    ]
    steps = [
        ("Boot",         "Base station starts",  ORANGE),
        ("Camera Live",  "RTSP connected",        BLUE),
        ("AI On",        "Detection enabled",     PURPLE),
        ("Drive",        "Manual control",        GREEN),
        ("Detected",     "Box shown",             YELLOW),
        ("Alert",        "Buzzer + LED",          RED),
        ("Logged",       "Saved to database",     "#64748b"),
    ]
    items = []
    for index, ((title, note, color), icon) in enumerate(zip(steps, _icons)):
        items.append(
            f"""
            <div class="about-flow-step" style="--flow-color:{color}">
              <span class="about-flow-icon">{icon}</span>
              <strong>{escape(title)}</strong>
              <small>{escape(note)}</small>
            </div>
            """
        )
        if index < len(steps) - 1:
            items.append('<span class="about-flow-arrow">→</span>')
    return "<div class='about-search-flow'>" + "".join(items) + "</div>"


def render_led_rows() -> str:
    rows = [
        (RED,    "System Status LED",  "Red — System is not working"),
        (ORANGE, "System Status LED",  "Orange — System loading / booting"),
        (GREEN,  "System Status LED",  "Green — System is working"),
        (GREEN,  "FPV Feed LED",       "Green — FPV video feed is active / connected"),
        (GREEN,  "Detection Feed LED", "Green — Detection camera / feed is active / connected"),
        (RED,    "Detection LED",      "Red — Person detected / detection alert"),
    ]
    return "".join(
        f"<div class='about-led-row'><span style='background:{color};color:{color}'></span><strong>{label}</strong><em>{note}</em></div>"
        for color, label, note in rows
    )


def render_display_cards() -> str:
    screens = [
        {
            "title": "System Status",
            "tone": "blue",
            "screen": ["STATUS: ACTIVE", "VIDEO: CONNECTED"],
            "note": "Shows system and video connection state.",
        },
        {
            "title": "Last Detection",
            "tone": "green",
            "screen": ["LAST DETECTION", "CLASS: lying_person, TIME: 08:30:59"],
            "note": "Shows the last saved detection result.",
        },
        {
            "title": "Detection",
            "tone": "orange",
            "screen": ["PERSON DETECTION", "CLASS: lying_person, TIME: 12:30:59"],
            "note": "Shows the current active detection alert.",
        },
        {
            "title": "Detection Statistics",
            "tone": "purple",
            "screen": ["TOTAL DETECTIONS: 5", "Lying_person: 1"],
            "note": "Shows total detections and class count.",
        },
        {
            "title": "Gas",
            "tone": "red",
            "screen": ["GAS: 145 ppm - NORMAL", "AREA SAFE"],
            "note": "Shows gas sensor value and area safety state.",
        },
    ]
    cards = []
    for screen in screens:
        cards.append(
            f"""
            <article class="about-display-card">
              <div class="about-display-head">
                <span class="about-display-chip about-display-chip-{screen['tone']}">{escape(screen['title'])}</span>
                <span class="about-display-caption">LCD example</span>
              </div>
              <div class="about-lcd-shell">
                <div class="about-lcd-screen">
                  <span class="about-lcd-dots"><i></i><i></i><i></i></span>
                  <pre>{escape(chr(10).join(screen['screen']))}</pre>
                </div>
              </div>
              <p>{escape(screen['note'])}</p>
            </article>
            """
        )
    return "<div class='about-display-grid'>" + "".join(cards) + "</div>"


def render_faq_tips() -> str:
    faqs = [
        ("blue", "How do I switch camera feeds?", "Use the camera selector on the Operating page to move between FPV / Nav and Detection."),
        ("green", "What does the buzzer mean?", "It sounds when a person is detected or when gas levels need attention."),
        ("orange", "Where are detections stored?", "Detections are saved by the data API and shown on the Data page."),
        ("purple", "How do I adjust AI sensitivity?", "Use the threshold control on Operating to tune the detection sensitivity."),
    ]
    items = []
    for tone, question, answer in faqs:
        items.append(
            f"""
            <article class="about-faq-item">
              <div class="about-faq-head">
                <span class="about-faq-chip about-faq-chip-{tone}">{escape(question)}</span>
              </div>
              <p>{escape(answer)}</p>
            </article>
            """
        )
    return "<div class='about-faq-grid'>" + "".join(items) + "</div>"


def build_onboarding_page() -> OnboardingPage:
    with gr.Column(elem_classes=["about-page"]):
        with gr.Group(elem_classes=["app-card", "welcome-card", "about-card"]):
            gr.Markdown(
                "## 👋 Welcome to the RC SAR Ground Station!\n"
                "This guide explains how to operate the RC car search-and-rescue system. "
                "The base station runs AI detection, shows feedback alerts, and logs events for review.",
                elem_classes=["compact-md"],
            )
            gr.HTML(badge_row("YOLOv26", "Raspberry Pi", "Touchscreen", "Station API"))

        with gr.Group(elem_classes=["app-card", "about-card"]):
            gr.Markdown("### 1 - Quick Start - Connect & Begin", elem_classes=["compact-md"])
            with gr.Row():
                _step_card(1, "Power On Base Station", "Connect Raspberry Pi power. LEDs flash twice after boot.", "Green LED = OK", ORANGE)
                _step_card(2, "Connect RC Car Camera", "Turn on the car. The RTSP stream connects automatically.", "LCD shows VIDEO", BLUE)
                _step_card(3, "Read the Displays", "Check touchscreen and LCD. Both show current system status.", "DISPLAY cycles LCD", PURPLE)
                _step_card(4, "Enable AI & Start Ops", "Use Operating page controls to enable detection overlays.", "Orange LED = AI", GREEN)

        with gr.Group(elem_classes=["app-card", "about-card"]):
            gr.Markdown("### 2 - Example Search Workflow", elem_classes=["compact-md"])
            gr.HTML(render_search_workflow())

        with gr.Group(elem_classes=["app-card", "about-card"]):
            gr.Markdown("### 3 - Understand the Displays", elem_classes=["compact-md"])
            gr.Markdown(
                "The touchscreen shows the full Gradio dashboard while the LCD stays compact and readable at a glance. "
                "The orange notice below explains when the Info LCD button is used to cycle the physical screen."
            )
            gr.Markdown(
                "<div class='about-info-callout'><strong>Info LCD</strong> cycles the base station LCD through the status screens shown here.</div>",
                elem_classes=["compact-md"],
            )
            gr.HTML(render_display_cards())

        with gr.Group(elem_classes=["app-card", "about-card"]):
            gr.Markdown("### 4 - LEDs", elem_classes=["compact-md"])
            gr.Markdown(
                "Use the left navigation to switch pages. The shared header button is reserved for the physical LCD control.",
                elem_classes=["compact-md"],
            )
            gr.HTML(render_led_rows())

        with gr.Group(elem_classes=["app-card", "about-card", "about-classes-section"]):
            gr.Markdown("### 5 - Detection Classes", elem_classes=["compact-md"])
            gr.HTML(render_detection_class_cards())

        with gr.Group(elem_classes=["app-card", "about-card", "about-checklist-card"]):
            gr.Markdown("### 6 - Before You Begin - Checklist", elem_classes=["compact-md"])
            checklist = gr.CheckboxGroup(
                choices=[f"{index}. {task}" for index, task in enumerate(CHECKLIST_TASKS, start=1)],
                label="",
                show_label=False,
                elem_classes=["about-checklist"],
            )

        with gr.Group(elem_classes=["app-card", "about-card"]):
            gr.Markdown("### 7 - Gas Sensor Warnings", elem_classes=["compact-md"])
            gr.Markdown(
                "<div class='notice-info'><strong>MQ-2 on GPIO 18</strong> — Detects combustible gases and smoke.</div><br>"
                "<div class='notice-ok'>&lt; 200 ppm — Normal, safe to proceed</div><br>"
                "<div class='notice-warn'>200–250 ppm — Warning, use caution</div><br>"
                "<div class='about-critical'>&gt; 250 ppm — Critical, do not enter</div>"
            )

        with gr.Group(elem_classes=["app-card", "about-card", "about-faq-card"]):
            gr.Markdown("### 8 - FAQ & Tips", elem_classes=["compact-md"])
            gr.HTML(render_faq_tips())

    return OnboardingPage(checklist=checklist)
