# `models` — AI models for the dashboard

One file per model (YOLO, MediaPipe, …). IDs and loading live in **`registry.py`** only.

## Files

| File | Purpose |
|------|---------|
| `registry.py` | **`MODEL_*` IDs** + **`build_models()`** — edit this to add a model |
| `base.py` | `InferenceResult` (image + JSON payload + status text) |
| `yolo_detector.py` | Drone detection (`best.pt`) |
| `pose_detector.py` | MediaPipe pose |

## Add a new model

1. Copy [`students/template_model.py`](../students/template_model.py) into `models/my_model.py`.
2. In **`registry.py`**: add `MODEL_MY = "my_model"`, append to `MODEL_IDS`, and add a line in `build_models()`.
3. Add a Gradio tab in `ui/model_section.py` and a run method in `ui/inference_handlers.py`.

## Run contract

Every model should implement:

- `run(frame_rgb, **kwargs) -> InferenceResult`
- `close()` (optional, called on app exit)
