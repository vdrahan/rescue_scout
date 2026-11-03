from pathlib import Path
import shutil

import gradio as gr
from PIL import Image


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".tif",
    ".tiff",
}


def clean_path(path: str) -> str:
    cleaned = path.strip().strip('"').strip("'").strip()

    bracket_pairs = {
        "(": ")",
        "[": "]",
        "{": "}",
        "<": ">",
    }

    while len(cleaned) >= 2 and cleaned[0] in bracket_pairs and cleaned[-1] == bracket_pairs[cleaned[0]]:
        cleaned = cleaned[1:-1].strip().strip('"').strip("'").strip()

    return cleaned


def get_image_files(source_folder: str) -> list[Path]:
    source_path = Path(clean_path(source_folder))

    if not source_path.exists() or not source_path.is_dir():
        return []

    return sorted(
        file_path
        for file_path in source_path.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_current_image(source_folder: str, index: int = 0):
    files = get_image_files(source_folder)

    if not files:
        return None, "No images found in the source folder.", 0, ""

    index = max(0, min(index, len(files) - 1))
    current_file = files[index]
    status = f"{index + 1} / {len(files)}: {current_file.name}"

    return read_image(current_file), status, index, current_file.name


def move_current_file(source_folder: str, destination_folder: str, index: int):
    files = get_image_files(source_folder)

    if not files:
        return None, "No images left in the source folder.", 0, ""

    index = max(0, min(index, len(files) - 1))
    current_file = files[index]

    destination_path = Path(clean_path(destination_folder))
    if not str(destination_path):
        return read_image(current_file), "Please enter a destination folder.", index, current_file.name

    destination_path.mkdir(parents=True, exist_ok=True)

    target_file = destination_path / current_file.name
    if target_file.exists():
        target_file = make_unique_path(target_file)

    shutil.move(str(current_file), str(target_file))

    next_files = get_image_files(source_folder)
    if not next_files:
        return None, f"Moved {current_file.name}. No images left.", 0, ""

    next_index = min(index, len(next_files) - 1)
    next_file = next_files[next_index]
    status = f"Moved {current_file.name}. Next: {next_index + 1} / {len(next_files)}"

    return read_image(next_file), status, next_index, next_file.name


def read_image(file_path: Path):
    with Image.open(file_path) as img:
        return img.copy()


def make_unique_path(file_path: Path) -> Path:
    counter = 1
    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent

    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def remove_image(source_folder: str, remove_folder: str, index: int):
    return move_current_file(source_folder, remove_folder, index)


def keep_image(source_folder: str, keep_folder: str, index: int):
    return move_current_file(source_folder, keep_folder, index)


def next_image(source_folder: str, index: int):
    return load_current_image(source_folder, index + 1)


def previous_image(source_folder: str, index: int):
    return load_current_image(source_folder, index - 1)


with gr.Blocks(title="Frame Filter") as demo:
    gr.Markdown("# Frame Filter")

    current_index = gr.State(0)

    with gr.Row():
        source_folder = gr.Textbox(
            label="Source folder",
            placeholder=r"D:\path\to\extracted_frames",
        )
        remove_folder = gr.Textbox(
            label="Remove folder",
            placeholder=r"D:\path\to\removed_frames",
        )
        keep_folder = gr.Textbox(
            label="Keep folder",
            placeholder=r"D:\path\to\kept_frames",
        )

    with gr.Row():
        load_button = gr.Button("Load", variant="primary")
        previous_button = gr.Button("Previous")
        next_button = gr.Button("Next")

    image = gr.Image(label="Current image", type="pil", height=620)
    status = gr.Textbox(label="Status", interactive=False)
    filename = gr.Textbox(label="Current file", interactive=False)

    with gr.Row():
        remove_button = gr.Button("Remove", variant="stop")
        keep_button = gr.Button("Keep", variant="primary")

    load_button.click(
        fn=load_current_image,
        inputs=[source_folder, current_index],
        outputs=[image, status, current_index, filename],
    )

    previous_button.click(
        fn=previous_image,
        inputs=[source_folder, current_index],
        outputs=[image, status, current_index, filename],
    )

    next_button.click(
        fn=next_image,
        inputs=[source_folder, current_index],
        outputs=[image, status, current_index, filename],
    )

    remove_button.click(
        fn=remove_image,
        inputs=[source_folder, remove_folder, current_index],
        outputs=[image, status, current_index, filename],
    )

    keep_button.click(
        fn=keep_image,
        inputs=[source_folder, keep_folder, current_index],
        outputs=[image, status, current_index, filename],
    )


if __name__ == "__main__":
    demo.launch(inbrowser=False)

