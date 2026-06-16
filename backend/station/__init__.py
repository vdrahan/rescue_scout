"""RC SAR station service — realtime detection, camera and hardware brain.

Runs the YOLOv26 detection worker, camera sources and hardware (GPIO/sensors)
behind a small FastAPI app. Everything works in a dependency-light *mock* mode so
the whole system runs on a laptop without torch, OpenCV or Raspberry Pi libraries.
"""

__version__ = "0.1.0"
