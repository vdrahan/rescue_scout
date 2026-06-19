"""Frame helpers built on Pillow + numpy only (no OpenCV).

Used by the mock camera, the mock detector and the JPEG frame endpoint so the
whole pipeline works without cv2 installed.
"""

from __future__ import annotations

import io
from datetime import datetime

import numpy as np
from PIL import Image, ImageDraw

# Priority -> RGB box colour
_PRIORITY_COLOR = {
    "HIGH": (239, 68, 68),
    "MEDIUM": (139, 92, 246),
    "LOW": (59, 130, 246),
}
_ACCENT = (240, 90, 36)  # SAR orange


def new_scene(width: int, height: int, title: str, subtitle: str = "") -> np.ndarray:
    """A dark gradient + grid scene with a header — stand-in camera frame."""
    img = Image.new("RGB", (width, height), (16, 23, 34))
    draw = ImageDraw.Draw(img)

    # vertical gradient
    for y in range(0, height, 2):
        shade = int(16 + (y / height) * 22)
        draw.line((0, y, width, y), fill=(shade, shade + 8, shade + 14))
    # grid
    for x in range(0, width, 48):
        draw.line((x, 0, x, height), fill=(26, 35, 47))
    for y in range(0, height, 48):
        draw.line((0, y, width, y), fill=(26, 35, 47))

    draw.rectangle((0, 0, width - 1, height - 1), outline=_ACCENT, width=3)
    draw.text((16, 14), title, fill=(226, 232, 240))
    if subtitle:
        draw.text((16, 30), subtitle, fill=(148, 163, 184))
    draw.text((width - 86, height - 22),
              datetime.now().strftime("%H:%M:%S"), fill=(226, 232, 240))
    return np.asarray(img, dtype=np.uint8)


def annotate(frame: np.ndarray, detections) -> np.ndarray:
    """Draw bounding boxes + labels for an iterable of Detection objects."""
    img = Image.fromarray(frame.copy())
    draw = ImageDraw.Draw(img)
    for det in detections:
        color = _PRIORITY_COLOR.get(det.priority, _ACCENT)
        x1, y1, x2, y2 = det.bbox
        draw.rectangle((x1, y1, x2, y2), outline=color, width=3)
        label = f"{det.class_name} {int(det.confidence * 100)}%"
        draw.rectangle((x1, max(0, y1 - 16), x1 + 8 + 6 * len(label), y1), fill=color)
        draw.text((x1 + 4, max(0, y1 - 14)), label, fill=(255, 255, 255))
    return np.asarray(img, dtype=np.uint8)


def to_jpeg(frame: np.ndarray, quality: int = 80, max_width: int | None = None) -> bytes:
    # Downscale wide frames before encoding. On the Pi, JPEG-encoding a 1920x1080
    # frame costs ~45 ms (caps the feed at ~16 fps), and PIL's resize() adds another
    # ~40 ms — so we decimate with a cheap numpy stride (~1 ms) instead. Aliasing is
    # irrelevant for the FPV navigation feed; the win is a ~3x faster, lighter stream.
    if max_width and frame.shape[1] > max_width:
        step = (frame.shape[1] + max_width - 1) // max_width  # ceil → result ≤ max_width
        frame = np.ascontiguousarray(frame[::step, ::step])
    buf = io.BytesIO()
    Image.fromarray(frame).save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def placeholder(width: int, height: int, message: str) -> np.ndarray:
    img = Image.new("RGB", (width, height), (17, 24, 39))
    draw = ImageDraw.Draw(img)
    draw.text((width // 2 - 4 * len(message), height // 2), message, fill=(156, 163, 175))
    return np.asarray(img, dtype=np.uint8)
