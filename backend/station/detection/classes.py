"""Canonical SAR detection classes and their rescue priority."""

from __future__ import annotations

# Order matters: this is also the assumed model class index order.
CLASSES: tuple[str, ...] = (
    "standing_person",
    "sitting_person",
    "crawling_person",
    "lying_person",
    "partially_visible_person",
)

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

PRIORITY: dict[str, str] = {
    "lying_person": HIGH,
    "crawling_person": HIGH,
    "sitting_person": MEDIUM,
    "partially_visible_person": MEDIUM,
    "standing_person": LOW,
}

# Old/alternate spellings that may still appear in data → canonical name.
_ALIASES: dict[str, str] = {
    "partially_hidden": "partially_visible_person",
    "partially_hidden_person": "partially_visible_person",
    "partially_visible": "partially_visible_person",
}


def normalize(class_name: str) -> str:
    """Map a possibly-legacy class name to its canonical form."""
    key = class_name.strip().lower().replace(" ", "_")
    return _ALIASES.get(key, key)


def priority_for(class_name: str) -> str:
    return PRIORITY.get(normalize(class_name), LOW)
