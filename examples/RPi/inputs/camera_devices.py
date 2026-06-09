from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

V4L_BY_ID = Path("/dev/v4l/by-id")
V4L_SYS = Path("/sys/class/video4linux")
CAP_VIDEO_CAPTURE = 0x00000001


@dataclass(frozen=True)
class CameraDevice:
    """One V4L2 capture device students can select in config."""

    label: str
    """Human-readable name (from sysfs or by-id basename)."""

    open_path: str
    """Pass this to OpenCV VideoCapture (stable by-id path or /dev/videoN)."""

    device_node: str
    """Resolved node, e.g. /dev/video8."""

    config_value: str
    """Short string to paste into config.py `camera_device`."""

    index: int | None = None
    """Numeric index if parsed from /dev/videoN."""


def _video_index(name: str) -> int | None:
    match = re.search(r"video-index(\d+)", name)
    return int(match.group(1)) if match else None


def _is_capture_device(video_name: str) -> bool:
    caps_path = V4L_SYS / video_name / "device_caps"
    if not caps_path.exists():
        caps_path = V4L_SYS / video_name / "capabilities"
    if not caps_path.exists():
        return True
    try:
        caps = int(caps_path.read_text().strip(), 0)
    except ValueError:
        return True
    return bool(caps & CAP_VIDEO_CAPTURE)


def _read_sysfs_name(video_name: str) -> str:
    name_path = V4L_SYS / video_name / "name"
    if name_path.exists():
        return name_path.read_text().strip()
    return video_name


def _parse_video_node(node: Path) -> CameraDevice | None:
    match = re.search(r"video(\d+)$", node.name)
    if match is None:
        return None
    video_name = f"video{match.group(1)}"
    if not _is_capture_device(video_name):
        return None
    label = _read_sysfs_name(video_name)
    idx = int(match.group(1))
    return CameraDevice(
        label=label,
        open_path=str(node),
        device_node=str(node),
        config_value=str(node),
        index=idx,
    )


def _parse_by_id_link(link: Path) -> CameraDevice | None:
    name = link.name
    idx = _video_index(name)
    if idx is not None and idx != 0:
        return None
    if "video-index" in name and idx is None:
        return None

    try:
        resolved = link.resolve()
    except OSError:
        return None
    if not resolved.name.startswith("video"):
        return None

    video_name = resolved.name
    if not _is_capture_device(video_name):
        return None

    label = _read_sysfs_name(video_name)
    # Prefer a short by-id substring for config (stable across reboots).
    config_value = name if name.startswith("usb-") or name.startswith("platform-") else name
    return CameraDevice(
        label=label,
        open_path=str(link),
        device_node=str(resolved),
        config_value=config_value,
        index=int(video_name.replace("video", "")),
    )


def list_cameras() -> list[CameraDevice]:
    """Enumerate capture cameras (Linux / Raspberry Pi)."""
    if sys.platform == "win32":
        return _list_cameras_windows()

    found: dict[str, CameraDevice] = {}

    if V4L_BY_ID.is_dir():
        for link in sorted(V4L_BY_ID.iterdir()):
            if not link.is_symlink():
                continue
            cam = _parse_by_id_link(link)
            if cam is not None:
                found[cam.device_node] = cam

    for i in range(64):
        node = Path(f"/dev/video{i}")
        if not node.exists():
            continue
        cam = _parse_video_node(node)
        if cam is not None and cam.device_node not in found:
            found[cam.device_node] = cam

    return sorted(found.values(), key=lambda c: (c.index is None, c.index or 0))


def _list_cameras_windows() -> list[CameraDevice]:
    """Fallback: probe indices 0–9 with OpenCV (laptop dev without V4L2)."""
    try:
        import cv2
    except ImportError:
        return []

    found: list[CameraDevice] = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if not cap.isOpened():
            continue
        cap.release()
        found.append(
            CameraDevice(
                label=f"Camera index {i}",
                open_path=str(i),
                device_node=f"index:{i}",
                config_value=str(i),
                index=i,
            )
        )
    return found


def find_camera(query: str) -> CameraDevice | None:
    """Match by full path, by-id name substring, sysfs label, or numeric index."""
    query = query.strip()
    if not query:
        return None

    cameras = list_cameras()
    if not cameras:
        return None

    if query.startswith("/dev/"):
        for cam in cameras:
            if cam.open_path == query or cam.device_node == query:
                return cam
        return None

    if query.isdigit():
        idx = int(query)
        for cam in cameras:
            if cam.index == idx:
                return cam

    q = query.lower()
    for cam in cameras:
        if q in cam.config_value.lower() or q in cam.label.lower() or q in cam.open_path.lower():
            return cam
    return None


def resolve_camera_source(camera_device: str = "", camera_index: int | None = 8) -> str | int:
    """
    What to pass to cv2.VideoCapture.

    - If `camera_device` is set: stable by-id path or substring match.
    - Else: numeric `camera_index` (legacy).
    """
    device = camera_device.strip()
    if device:
        match = find_camera(device)
        if match is None:
            raise ValueError(
                f"No camera matching {device!r}. Run: python list_cameras.py"
            )
        print(f"[USB] Using camera {match.label!r} -> {match.open_path}")
        return match.open_path

    if camera_index is not None:
        print(f"[USB] Using camera index {camera_index} (set camera_device to avoid fixed index)")
        return camera_index

    raise ValueError("Set camera_device or camera_index in config.py")
