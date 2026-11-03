import cv2
import os


def clean_path(path):
    return path.strip().strip('"').strip("'")


def extract_frames(video_path, output_folder, target_fps):
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)

    if video_fps <= 0:
        print("Error: Could not read video FPS.")
        cap.release()
        return

    frame_interval = int(round(video_fps / target_fps))

    if frame_interval < 1:
        frame_interval = 1

    frame_number = 0
    saved_frame_number = 0

    while True:
        success, frame = cap.read()

        if not success:
            break

        if frame_number % frame_interval == 0:
            frame_filename = os.path.join(
                output_folder,
                f"frame_{saved_frame_number:06d}.jpg"
            )
            cv2.imwrite(frame_filename, frame)
            saved_frame_number += 1

        frame_number += 1

    cap.release()

    print(f"Video FPS: {video_fps}")
    print(f"Extracted FPS: {target_fps}")
    print(f"Saved {saved_frame_number} frames to '{output_folder}'")


while True:
    video_path = clean_path(input("Enter the full path to the MP4 video: "))
    output_folder = clean_path(input("Enter the directory path where frames should be saved: "))
    target_fps = float(input("Enter frames per second to extract: ").strip())

    extract_frames(video_path, output_folder, target_fps)

    again = input("Do you want to process another video? Y/N: ").strip().upper()

    if again == "N":
        print("Stopping program.")
        break

    if again != "Y":
        print("Invalid input. Stopping program.")
        break