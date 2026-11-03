import os
import socket
from pathlib import Path

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp|max_delay;0|fflags;nobuffer|flags;low_delay"

import cv2
import gradio as gr
import PIL.Image as Image
import torch
from ultralytics import YOLO

model_path = Path(__file__).parent
backend_path = model_path.parent
model_name = "rescue_person_detection_yolo26s"


def get_path_from_env(name, default_path):
    value = os.getenv(name)
    if value:
        return Path(value).expanduser()
    return Path(default_path)


def get_env_int(name, default):
    value = os.getenv(name)
    if value:
        return int(value)
    return default


def get_env_float(name, default):
    value = os.getenv(name)
    if value:
        return float(value)
    return default


runs_dir = backend_path / "model" / "runs" / "detect"
runs_dir.mkdir(parents=True, exist_ok=True)

data_yaml = get_path_from_env("DATA_YAML", backend_path / "data" / "data.yaml")
start_model = os.getenv("START_MODEL_PATH", "yolo26s.pt")
trained_model = get_path_from_env(
    "MODEL_PATH",
    runs_dir / model_name / "weights" / "best.pt"
)

default_rtsp_url = os.getenv("RTSP_CAMERA_1_URL", "")
auto_train_model = os.getenv("AUTO_TRAIN_MODEL", "false").lower() in {"1", "true", "yes", "on"}

device = 0 if torch.cuda.is_available() else "cpu"
use_half = torch.cuda.is_available()

TRAIN_EPOCHS   = get_env_int("TRAIN_EPOCHS",   120)
TRAIN_IMGSZ    = get_env_int("TRAIN_IMGSZ",    768)
TRAIN_BATCH    = get_env_int("TRAIN_BATCH",    2)
TRAIN_PATIENCE = get_env_int("TRAIN_PATIENCE", 25)
TRAIN_WORKERS  = get_env_int("TRAIN_WORKERS",  2)

camera_img_size = get_env_int("CAMERA_IMGSZ",  640)
image_img_size  = get_env_int("IMAGE_IMGSZ",   768)
default_conf    = get_env_float("DEFAULT_CONF", 0.12)
default_iou     = get_env_float("DEFAULT_IOU",  0.50)
max_det         = get_env_int("MAX_DET",        50)

model = None


def _train(yolo_model, imgsz, batch):
    yolo_model.train(
        data=str(data_yaml),
        epochs=TRAIN_EPOCHS,
        imgsz=imgsz,
        batch=batch,
        patience=TRAIN_PATIENCE,
        device=device,
        workers=TRAIN_WORKERS,
        cache="disk",
        plots=True,
        verbose=True,
        pretrained=True,
        optimizer="auto",
        cos_lr=True,
        close_mosaic=15,
        amp=True,

        degrees=5,
        translate=0.05,
        scale=0.30,
        shear=0.0,
        perspective=0.0003,
        flipud=0.0,
        fliplr=0.5,

        hsv_h=0.01,
        hsv_s=0.30,
        hsv_v=0.25,

        mixup=0.0,
        copy_paste=0.0,

        project=str(runs_dir),
        name=model_name,
        exist_ok=True,
    )


def get_model():
    print("=" * 56)
    print(f"CUDA available:  {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU:             {torch.cuda.get_device_name(0)}")
    else:
        print("Device:          CPU")
    print(f"data_yaml:       {data_yaml}")
    print(f"start_model:     {start_model}")
    print(f"trained_model:   {trained_model}")
    print(f"runs_dir:        {runs_dir}")
    print(f"train  imgsz={TRAIN_IMGSZ}  batch={TRAIN_BATCH}  epochs={TRAIN_EPOCHS}  patience={TRAIN_PATIENCE}")
    print(f"camera imgsz:    {camera_img_size}")
    print(f"image  imgsz:    {image_img_size}")
    print(f"default conf:    {default_conf}   iou: {default_iou}   max_det: {max_det}")

    if trained_model.exists():
        print("Status: trained model found — loading best.pt")
        print("=" * 56)
        return YOLO(str(trained_model))

    if not auto_train_model:
        print("Status: best.pt not found, AUTO_TRAIN_MODEL=false — loading starter model")
        print("=" * 56)
        return YOLO(str(start_model))

    print("Status: best.pt not found, AUTO_TRAIN_MODEL=true — starting training")
    print("=" * 56)

    if not data_yaml.exists():
        raise FileNotFoundError(f"DATA_YAML does not exist: {data_yaml}")

    used_imgsz = TRAIN_IMGSZ
    yolo_model = YOLO(str(start_model))

    try:
        _train(yolo_model, imgsz=TRAIN_IMGSZ, batch=TRAIN_BATCH)
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"CUDA OOM at imgsz={TRAIN_IMGSZ} — retrying with imgsz=640, batch=2")
            torch.cuda.empty_cache()
            yolo_model = YOLO(str(start_model))
            _train(yolo_model, imgsz=640, batch=2)
            used_imgsz = 640
        else:
            raise

    yolo_model = YOLO(str(trained_model))
    yolo_model.val(data=str(data_yaml), device=device, imgsz=used_imgsz, plots=True)
    yolo_model.export(format="onnx")

    return yolo_model


def predict_image(img, conf_threshold, iou_threshold):
    results = model.predict(
        source=img,
        conf=conf_threshold,
        iou=iou_threshold,
        show_labels=True,
        show_conf=True,
        imgsz=image_img_size,
        device=device,
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
        for _ in range(10):
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
            agnostic_nms=False,
            device=device,
            half=use_half,
            max_det=max_det,
            verbose=False,
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
        gr.Markdown("# Search and Rescue YOLOv26s Demo")

        with gr.Tab("Image"):
            image_input = gr.Image(type="pil", label="Upload Image")
            image_conf = gr.Slider(minimum=0, maximum=1, value=default_conf, label="Confidence threshold")
            image_iou  = gr.Slider(minimum=0, maximum=1, value=default_iou,  label="IoU threshold")
            image_button = gr.Button("Predict Image")
            image_output = gr.Image(type="pil", label="Result")

            image_button.click(
                fn=predict_image,
                inputs=[image_input, image_conf, image_iou],
                outputs=image_output,
            )

        with gr.Tab("RTSP Camera"):
            camera_url  = gr.Textbox(value=default_rtsp_url, label="RTSP URL")
            camera_conf = gr.Slider(minimum=0, maximum=1, value=default_conf, label="Confidence threshold")
            camera_iou  = gr.Slider(minimum=0, maximum=1, value=default_iou,  label="IoU threshold")
            camera_button = gr.Button("Start RTSP Camera")
            camera_output = gr.Image(type="pil", label="Live Camera")
            camera_status = gr.Textbox(label="Status")

            camera_button.click(
                fn=predict_camera,
                inputs=[camera_url, camera_conf, camera_iou],
                outputs=[camera_output, camera_status],
            )

    iface.launch(
        theme=gr.themes.Monochrome(),
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=find_free_port(),
        inbrowser=False,
    )

def find_free_port(default_port=7860):
    port = int(os.getenv("GRADIO_SERVER_PORT", default_port))
    host = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")

    for candidate in range(port, port + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
                return candidate
            except OSError:
                continue
    raise OSError(f"Cannot find empty port in range: {port}-{port + 9}")

    
    
    
if __name__ == "__main__":
    main()
