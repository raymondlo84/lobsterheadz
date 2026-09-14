#!/usr/bin/env python3
"""Face tracking app that puts a lobster image on people's heads. 🦞"""

import cv2
import mediapipe as mp
import math
import numpy as np
import os
import argparse

mp_face = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils

# Resolve the lobster overlay path relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOBSTER_PATH = os.path.join(SCRIPT_DIR, "lobster_overlay.png")
lobster_img = cv2.imread(LOBSTER_PATH, cv2.IMREAD_UNCHANGED)

if lobster_img is None:
    print(f"Error: Could not load lobster image from {LOBSTER_PATH}")
    lobster_img = np.zeros((100, 100, 4), dtype=np.uint8)  # Fallback
    lobster_img[:, :, 3] = 255  # Fully transparent
else:
    # Convert to RGBA if needed
    if len(lobster_img.shape) == 2:
        lobster_img = cv2.cvtColor(lobster_img, cv2.COLOR_GRAY2RGBA)
    elif lobster_img.shape[2] == 3:
        lobster_img = cv2.cvtColor(lobster_img, cv2.COLOR_BGR2RGBA)
    lobster_img[lobster_img[:, :, 3] == 0] = [255, 255, 255, 0]  # Make transparent areas white


def estimate_top_of_head(face_landmarks, w, h):
    """Estimate the top of the head position using face mesh landmarks."""
    lm = face_landmarks.landmark

    # Eyebrow landmarks
    left_eyebrow = (lm[105].x, lm[105].y)
    right_eyebrow = (lm[334].x, lm[334].y)

    # Midpoint between eyebrows (forehead center)
    forehead_x = (left_eyebrow[0] + right_eyebrow[0]) / 2
    forehead_y = (left_eyebrow[1] + right_eyebrow[1]) / 2

    # Distance between eyebrows (proxy for face width)
    brow_distance = math.sqrt(
        (right_eyebrow[0] - left_eyebrow[0]) ** 2 +
        (right_eyebrow[1] - left_eyebrow[1]) ** 2
    )

    # Extrapolate upward from forehead to estimate top of head
    head_height_factor = 1.8
    top_x = forehead_x
    top_y = forehead_y - brow_distance * head_height_factor

    # Clamp to image bounds
    top_x = max(0.01, min(0.99, top_x))
    top_y = max(0.01, min(0.99, top_y))

    # Convert to pixel coordinates
    pixel_x = int(top_x * w)
    pixel_y = int(top_y * h)

    return pixel_x, pixel_y, brow_distance


def estimate_face_size(face_landmarks):
    """Estimate face size for scaling the lobster."""
    lm = face_landmarks.landmark
    left_x = min(lm[i].x for i in range(len(lm)))
    right_x = max(lm[i].x for i in range(len(lm)))
    top_y = min(lm[i].y for i in range(len(lm)))
    bottom_y = max(lm[i].y for i in range(len(lm)))
    width = right_x - left_x
    height = bottom_y - top_y
    return width, height


def overlay_image_with_transparency(frame, overlay, x, y, scale=1.0):
    """Overlay an image with transparency onto the frame."""
    h, w = overlay.shape[:2]
    new_h, new_w = int(h * scale), int(w * scale)

    # Resize overlay
    resized_overlay = cv2.resize(overlay, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Calculate position on frame
    overlay_x1 = x - new_w // 2
    overlay_y1 = y - new_h // 2

    # Calculate overlap region
    x1 = max(0, overlay_x1)
    y1 = max(0, overlay_y1)
    x2 = min(frame.shape[1], overlay_x1 + new_w)
    y2 = min(frame.shape[0], overlay_y1 + new_h)

    # No overlap
    if x2 <= x1 or y2 <= y1:
        return

    # Get frame ROI
    frame_roi = frame[y1:y2, x1:x2]

    # Get corresponding overlay ROI
    overlay_roi_x = max(0, -overlay_x1)
    overlay_roi_y = max(0, -overlay_y1)
    overlay_roi = resized_overlay[overlay_roi_y:overlay_roi_y + (y2 - y1),
                                   overlay_roi_x:overlay_roi_x + (x2 - x1)]

    # Handle transparency
    if overlay_roi.shape[2] == 4:
        alpha = overlay_roi[:, :, 3].astype(np.float32) / 255.0
        alpha_expanded = np.stack([alpha] * 3, axis=-1)
        overlay_rgb = overlay_roi[:, :, :3].astype(np.float32)
        frame_rgb = frame_roi.astype(np.float32)
        blended = overlay_rgb * alpha_expanded + frame_rgb * (1 - alpha_expanded)
        frame_roi[:] = blended.astype(np.uint8)
    else:
        frame_roi[:] = overlay_roi


def draw_lobster_on_head(frame, face_landmarks, h, w, time_offset):
    """Draw TWO lobster images on top of the person's head."""
    px, py, brow_dist = estimate_top_of_head(face_landmarks, w, h)

    # Scale lobster based on face size
    face_width, face_height = estimate_face_size(face_landmarks)
    scale = max(0.3, min(1.5, face_width * 2))

    # Add a subtle bounce animation
    bounce = math.sin(time_offset * 3.0) * 5
    lobster_y = int(py + bounce)

    # Offset between the two lobsters (side by side)
    offset_x = int(brow_dist * w * 0.6)

    # Overlay both lobster images
    overlay_image_with_transparency(frame, lobster_img, px - offset_x, lobster_y, scale)
    overlay_image_with_transparency(frame, lobster_img, px + offset_x, lobster_y, scale)


def parse_args():
    parser = argparse.ArgumentParser(description="LobsterHeadz 🦞 - Put lobsters on people's heads")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--image", type=str, default=None, help="Path to overlay image (overrides default)")
    parser.add_argument("--width", type=int, default=1920, help="Camera width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Camera height (default: 1080)")
    parser.add_argument("--fps", type=int, default=30, help="Camera FPS (default: 30)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Use the user-specified image, or fall back to the bundled one
    lobster_path = args.image if args.image else LOBSTER_PATH
    lobster_img = cv2.imread(lobster_path, cv2.IMREAD_UNCHANGED)
    if lobster_img is None:
        print(f"Error: Could not load lobster image from {lobster_path}")
        lobster_img = np.zeros((100, 100, 4), dtype=np.uint8)
        lobster_img[:, :, 3] = 255
    else:
        if len(lobster_img.shape) == 2:
            lobster_img = cv2.cvtColor(lobster_img, cv2.COLOR_GRAY2RGBA)
        elif lobster_img.shape[2] == 3:
            lobster_img = cv2.cvtColor(lobster_img, cv2.COLOR_BGR2RGBA)
        lobster_img[lobster_img[:, :, 3] == 0] = [255, 255, 255, 0]

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Error: Could not open camera device {args.camera}.")
        return

    # Use MJPEG to get full 1080p30 — the camera only hits 30fps in MJPEG mode
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, args.fps)
    print(f"Camera {args.camera}: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}@{cap.get(cv2.CAP_PROP_FPS)}fps")
    print(f"Overlay: {lobster_path} ({lobster_img.shape[1]}x{lobster_img.shape[0]})")

    face_mesh = mp_face.FaceMesh(
        static_image_mode=False,
        max_num_faces=5,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    start_time = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame.shape[:2]

            # Track elapsed time for animations
            if start_time is None:
                start_time = cv2.getTickCount()
            elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()

            # Process face mesh
            results = face_mesh.process(rgb)

            # Draw lobsters on all detected faces
            if results and results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # Lobster on head
                    draw_lobster_on_head(frame, face_landmarks, h, w, elapsed)

            # Title
            face_count = len(results.multi_face_landmarks) if results and results.multi_face_landmarks else 0
            cv2.putText(frame, f"Lobster Headz 🦞 ({face_count})", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 255), 2)

            cv2.imshow("Lobster Headz", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        face_mesh.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
