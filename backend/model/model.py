from pathlib import Path
import os

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp|max_delay;0|fflags;nobuffer|flags;low_delay"

import cv2
import torch
from ultralytics import YOLO
import PIL.Image as Image
import gradio as gr


model_path = Path(__file__).parent
backend_path = model_path.parent
model_name = "rescue_person_detection_yolo26n"


def get_path_from_env(name, default_path):
    value = os.getenv(name)
    if value:
        return Path(value).expanduser()
    return Path(default_path)


data_yaml = get_path_from_env("DATA_YAML", backend_path / "data" / "data.yaml")
start_model = os.getenv("START_MODEL_PATH", "yolo26n.pt")
trained_model = get_path_from_env(
    "MODEL_PATH",
    backend_path / "model" / "runs" / "detect" / model_name / "weights" / "best.pt"
)

default_rtsp_url = os.getenv("RTSP_CAMERA_1_URL", "rtsp://Stickk:12345678@172.20.10.6:554/stream1")
auto_train_model = os.getenv("AUTO_TRAIN_MODEL", "false").lower() in {"1", "true", "yes", "on"}

device = 0 if torch.cuda.is_available() else "cpu"
use_half = torch.cuda.is_available()
camera_img_size = 320
model = None


def get_model():
    print("CUDA available:", torch.cuda.is_available())

    if torch.cuda.is_available():
        print("Using GPU:", torch.cuda.get_device_name(0))
    else:
        print("Using CPU")

    if trained_model.exists():
        print("Trained model found. Loading it...")
        return YOLO(str(trained_model))

    if not auto_train_model:
        print("Trained model not found. Loading starter model from Ultralytics.")
        return YOLO(str(start_model))

    print("Trained model not found. Training new model...")

    if not data_yaml.exists():
        raise FileNotFoundError(f"DATA_YAML does not exist: {data_yaml}")

    yolo_model = YOLO(str(start_model))
    yolo_model.train(
        data=data_yaml,
        epochs=30,
        imgsz=640,
        batch=8,
        patience=6,
        device=device,
        workers=2,
        cache=False,
        plots=True,
        verbose=True,
        pretrained=True,
        optimizer="auto",
        cos_lr=True,
        close_mosaic=5,
        amp=True,
        project=backend_path / "runs" / "detect",
        name=model_name,
        exist_ok=True
    )

    yolo_model = YOLO(str(trained_model))
    yolo_model.val(data=data_yaml, device=device)
    yolo_model.export(format="onnx")

    return yolo_model


def predict_image(img, conf_threshold, iou_threshold):
    results = model.predict(
        source=img,
        conf=conf_threshold,
        iou=iou_threshold,
        show_labels=True,
        show_conf=True,
        imgsz=640,
        device=device
    )

    for r in results:
        im_array = r.plot()
        im = Image.fromarray(im_array[..., ::-1])

    return im


def predict_camera(camera_url, conf_threshold, iou_threshold):
    camera = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not camera.isOpened():
        yield None, "Camera could not be opened. Check RTSP URL."
        return

    while True:
        for i in range(10):
            camera.grab()

        success, frame = camera.retrieve()

        if not success:
            yield None, "Camera stream stopped or frame could not be read."
            break

        results = model.predict(
            source=frame,
            conf=conf_threshold,
            iou=iou_threshold,
            show_labels=True,
            show_conf=True,
            imgsz=camera_img_size,
            agnostic_nms=True,
            device=device,
            half=use_half,
            max_det=20,
            verbose=False
        )

        for r in results:
            im_array = r.plot()
            im = Image.fromarray(im_array[..., ::-1])

        yield im, "Camera is running with low latency mode"

    camera.release()


def main():
    global model
    model = get_model()

    with gr.Blocks() as iface:
        gr.Markdown("# Search and Rescue YOLOv26n Demo")

        with gr.Tab("Image"):
            image_input = gr.Image(type="pil", label="Upload Image")
            image_conf = gr.Slider(minimum=0, maximum=1, value=0.25, label="Confidence threshold")
            image_iou = gr.Slider(minimum=0, maximum=1, value=0.45, label="IoU threshold")
            image_button = gr.Button("Predict Image")
            image_output = gr.Image(type="pil", label="Result")

            image_button.click(
                fn=predict_image,
                inputs=[image_input, image_conf, image_iou],
                outputs=image_output
            )

        with gr.Tab("RTSP Camera"):
            camera_url = gr.Textbox(value=default_rtsp_url, label="RTSP URL")
            camera_conf = gr.Slider(minimum=0, maximum=1, value=0.25, label="Confidence threshold")
            camera_iou = gr.Slider(minimum=0, maximum=1, value=0.45, label="IoU threshold")
            camera_button = gr.Button("Start RTSP Camera")
            camera_output = gr.Image(type="pil", label="Live Camera")
            camera_status = gr.Textbox(label="Status")

            camera_button.click(
                fn=predict_camera,
                inputs=[camera_url, camera_conf, camera_iou],
                outputs=[camera_output, camera_status]
            )

    iface.launch(
        theme=gr.themes.Monochrome(),
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
    )


if __name__ == "__main__":
    main()
