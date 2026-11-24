---
name: lobsterheadz
description: Face-tracking webcam app that puts bouncing lobsters on heads and lobster claws on hands in real time; run lobstercam.py (1080p30 MJPEG, MediaPipe).
---

# LobsterCam 2 🦞

> Description: Face tracking app that overlays lobster images on people's heads and lobster claws on their hands — now at 1080p30 via MJPEG.

Face tracking app that overlays lobster images on people's heads and lobster claws on their hands — now at 1080p30 via MJPEG.

## Features
- Real-time face detection and tracking via MediaPipe
- Real-time hand detection and tracking via MediaPipe Hands
- 2 lobster overlays per detected face (side-by-side, ~5 max)
- Lobster claw overlay on every detected hand (~4 max)
- Transparent PNG overlays with proper alpha blending
- Bounce animation on the lobsters
- 1920×1080 @ 30fps via MJPEG pixel format
- Path resolution relative to script directory (no broken `~` paths)

## Usage

### Install dependencies
```bash
pip3 install -r requirements.txt
```

### Run
```bash
python3 lobstercam.py
```

The camera feed opens in a window. Detected faces get two lobsters on their heads. Press **Q** to quit.

### Custom camera or image
```bash
# Use camera index 1 instead of 0
python3 lobstercam.py --camera 1

# Use a different overlay image
python3 lobstercam.py --image /path/to/my-overlay.png

# Use a different claw overlay, or disable hand tracking
python3 lobstercam.py --claw-image /path/to/my-claw.png
python3 lobstercam.py --no-claws
```

## Dependencies
- `mediapipe==0.10.18` (face mesh detection)
- `opencv-python==4.9.0.80` (video processing)

## How It Works
1. Opens webcam at 1920×1080 @ 30fps using MJPEG pixel format
2. Uses MediaPipe Face Mesh to detect up to 5 faces
3. Uses MediaPipe Hands to detect up to 4 hands
4. Estimates head position from eyebrow landmarks (forehead midpoint extrapolated upward)
5. Estimates hand position from wrist + middle-finger-base landmarks (palm center)
6. Overlays 2 lobster PNG images on each head and 1 lobster claw on each hand, with proper transparency
7. Bounce animation adds a subtle vertical oscillation
6. Press **Q** to quit

## Files
- `SKILL.md` — this file
- `lobstercam.py` — main application
- `SKILL.md` — skill description/instructions (frontmatter + usage)
- `lobstercam.py` — main application
- `lobster_overlay.png` — lobster overlay image (transparent PNG, 256×256)
- `lobster_claw.png` — lobster claw overlay for hands (transparent PNG, 256×256)
- `requirements.txt` — pinned dependencies

## Known Fix (fixed upstream, 2026-11-12)

`main()` once opened the camera without applying MJPG or the `--width/--height/--fps`
flags, so it fell back to 640×480. Fixed upstream (commit 721da6a) by setting
`MJPG` + width/height/fps right after `cv2.VideoCapture`.
