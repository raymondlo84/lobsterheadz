#!/usr/bin/env python3
"""Face and hand tracking app that puts a lobster on people's heads and a lobster claw on their hands. 🦞"""

import cv2
import mediapipe as mp
import math
import numpy as np
import os
import argparse

mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Resolve overlay paths relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOBSTER_PATH = os.path.join(SCRIPT_DIR, "lobster_overlay.png")
CLAW_PATH = os.path.join(SCRIPT_DIR, "lobster_claw.png")


def load_rgba(path):
    """Load an overlay image as RGBA. Returns a transparent fallback on failure."""
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Error: Could not load overlay image from {path}")
        img = np.zeros((100, 100, 4), dtype=np.uint8)
        img[:, :, 3] = 0  # Fully transparent
    else:
        # Convert to RGBA if needed
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
        elif img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        img[img[:, :, 3] == 0] = [255, 255, 255, 0]  # Make transparent areas white
    return img


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


def estimate_hand_center(hand_landmarks, w, h):
    """Estimate the center of a hand and its length in pixels."""
    lm = hand_landmarks.landmark
    wrist = (lm[0].x, lm[0].y)        # wrist
    mid_mcp = (lm[9].x, lm[9].y)      # middle finger base (palm center)
    mid_tip = (lm[15].x, lm[15].y)    # middle finger tip

    # Center between wrist and palm
    center_x = (wrist[0] + mid_mcp[0]) / 2
    center_y = (wrist[1] + mid_mcp[1]) / 2

    # Hand length: wrist -> middle-finger tip, in pixels
    dx = (mid_tip[0] - wrist[0]) * w
    dy = (mid_tip[1] - wrist[1]) * h
    hand_len_px = math.sqrt(dx * dx + dy * dy)

    # Clamp to image bounds, then convert to pixel coordinates
    center_x = max(0.01, min(0.99, center_x))
    center_y = max(0.01, min(0.99, center_y))
    pixel_x = int(center_x * w)
    pixel_y = int(center_y * h)

    return pixel_x, pixel_y, hand_len_px


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


def draw_lobster_on_head(frame, face_landmarks, h, w, time_offset, overlay):
    """Draw TWO lobster images on top of the person's head."""
    px, py, brow_dist = estimate_top_of_head(face_landmarks, w, h)

    # Scale lobster based on face size (1.25x for a chunkier look)
    face_width, face_height = estimate_face_size(face_landmarks)
    scale = max(0.3, min(1.5, face_width * 2)) * 1.25

    # Add a subtle bounce animation
    bounce = math.sin(time_offset * 3.0) * 5
    lobster_y = int(py + bounce)

    # Offset between the two lobsters (side by side)
    offset_x = int(brow_dist * w * 0.6)

    # Overlay both lobster images
    overlay_image_with_transparency(frame, overlay, px - offset_x, lobster_y, scale)
    overlay_image_with_transparency(frame, overlay, px + offset_x, lobster_y, scale)


def draw_claw_on_hand(frame, hand_landmarks, h, w, time_offset, overlay, hand_index=0):
    """Draw a lobster claw on the detected hand, oriented along the fingers."""
    px, py, hand_len_px = estimate_hand_center(hand_landmarks, w, h)

    # Scale the claw to roughly cover the whole hand: the asset is
    # 256px tall, so render it at ~1.2x the measured hand length.
    scale = max(0.5, min(2.2, 1.2 * hand_len_px / 256.0))

    # Subtle bounce animation, phase-shifted per hand
    bounce = math.sin((time_offset + hand_index * 0.7) * 3.0) * 5
    claw_y = int(py + bounce)

    # Rotate the claw so its pincer points along the hand's finger
    # direction (wrist -> middle-finger tip) instead of staying upright.
    lm = hand_landmarks.landmark
    wrist = lm[0]
    mid_tip = lm[15]
    hand_angle = math.degrees(math.atan2(mid_tip.y - wrist.y, mid_tip.x - wrist.x))
    # The asset's pincer points up (image angle -90 deg); positive OpenCV
    # angles rotate counter-clockwise on screen, hence the sign flip.
    rotation = -90.0 - hand_angle

    resized = cv2.resize(overlay, (int(overlay.shape[1] * scale), int(overlay.shape[0] * scale)),
                         interpolation=cv2.INTER_AREA)
    ch, cw = resized.shape[:2]
    m = cv2.getRotationMatrix2D((cw / 2, ch / 2), rotation, 1.0)
    rotated = cv2.warpAffine(resized, m, (cw, ch), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

    overlay_image_with_transparency(frame, rotated, px, claw_y, 1.0)


def parse_args():
    parser = argparse.ArgumentParser(description="LobsterHeadz 🦞 - Put lobsters on people's heads and claws on their hands")
    parser.add_argument("--camera", type=str, default="/dev/video0", help="Camera device index or path (default: /dev/video0)")
    parser.add_argument("--image", type=str, default=None, help="Path to overlay image (overrides default)")
    parser.add_argument("--claw-image", type=str, default=None, help="Path to claw overlay image (overrides bundled lobster_claw.png)")
    parser.add_argument("--no-claws", action="store_true", help="Disable hand tracking and claw overlay")
    parser.add_argument("--width", type=int, default=1920, help="Camera width (default: 1920)")
    parser.add_argument("--height", type=int, default=1080, help="Camera height (default: 1080)")
    parser.add_argument("--fps", type=int, default=30, help="Camera FPS (default: 30)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Use the user-specified images, or fall back to the bundled ones
    lobster_path = args.image if args.image else LOBSTER_PATH
    lobster_img = load_rgba(lobster_path)
    claw_path = args.claw_image if args.claw_image else CLAW_PATH
    claw_img = None if args.no_claws else load_rgba(claw_path)

    # Try the specified camera first, fall back to /dev/video2 if it fails
    cap = cv2.VideoCapture(args.camera, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"Warning: Could not open {args.camera}, trying /dev/video2")
        cap = cv2.VideoCapture('/dev/video2', cv2.CAP_V4L2)
        if not cap.isOpened():
            print("Error: Could not open camera /dev/video2.")
            return
        args.camera = '/dev/video2'

    # Set MJPG + requested resolution (must be done right after open; the
    # driver only exposes 1080p30 in MJPG mode, not raw YUV)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, args.fps)

    print(f"Camera {args.camera}: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}@{cap.get(cv2.CAP_PROP_FPS)}fps")
    print(f"Overlay: {lobster_path} ({lobster_img.shape[1]}x{lobster_img.shape[0]})")
    if claw_img is not None:
        print(f"Claw overlay: {claw_path} ({claw_img.shape[1]}x{claw_img.shape[0]})")

    face_mesh = mp_face.FaceMesh(
        static_image_mode=False,
        max_num_faces=5,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    hand_tracker = None
    if claw_img is not None:
        hand_tracker = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=4,
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
                    draw_lobster_on_head(frame, face_landmarks, h, w, elapsed, lobster_img)

            # Draw claws on all detected hands
            hand_count = 0
            if hand_tracker is not None:
                hand_results = hand_tracker.process(rgb)
                if hand_results and hand_results.multi_hand_landmarks:
                    for i, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                        draw_claw_on_hand(frame, hand_landmarks, h, w, elapsed, claw_img, i)
                        hand_count += 1

            # Title
            face_count = len(results.multi_face_landmarks) if results and results.multi_face_landmarks else 0
            cv2.putText(frame, f"Lobster Headz (~^..^~) ({face_count} heads, {hand_count} hands)", (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 255), 2)

            cv2.imshow("Lobster Headz", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        face_mesh.close()
        if hand_tracker is not None:
            hand_tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
