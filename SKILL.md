---
name: lobsterheadz
description: Face-tracking webcam app that puts bouncing lobsters on heads and lobster claws on hands in real time; run lobstercam.py (1080p30 MJPEG, MediaPipe).
---

# LobsterHeadz 🦞

Face-tracking webcam app that overlays two bouncy lobsters on people's heads and a lobster claw on their hands — 1920×1080 @ 30fps via MJPEG.

## Features
- Real-time face detection and tracking via MediaPipe
- Real-time hand detection and tracking via MediaPipe Hands
- 2 lobster overlays per detected face (side-by-side, ~5 max)
- Lobster claw overlay on every detected hand (~4 max)
- Transparent PNG overlays with proper alpha blending
- Bounce animation on the lobsters and claws
- 1920×1080 @ 30fps via MJPEG pixel format
- Path resolution relative to script directory (no broken `~` paths)

## Usage

### Install dependencies
```bash
pip3 install -r requirements.txt
```

### Run
```bash
# Headless hosts: point DISPLAY at the screen you want
DISPLAY=:1 python3 lobstercam.py --width 1920 --height 1080
```

The camera feed opens in a window. Detected faces get two lobsters on their heads, and detected hands get a lobster claw that follows the hand's orientation. Press **Q** to quit.

### Custom camera and overlays
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
- `mediapipe==0.10.18` (face mesh + hand detection)
- `opencv-python==4.9.0.80` (video processing)

## How It Works
1. Opens webcam at 1920×1080 @ 30fps using MJPEG pixel format
2. Uses MediaPipe Face Mesh to detect up to 5 faces
3. Uses MediaPipe Hands to detect up to 4 hands
4. Estimates head position from eyebrow landmarks (forehead midpoint extrapolated upward)
5. Estimates hand position from wrist + middle-finger-base landmarks (palm center)
6. Overlays 2 lobster PNGs on each head and 1 claw on each hand with proper transparency; claws rotate to point along the hand's finger direction
7. Head lobsters scale with face width (1.25x for a chunkier look); claws scale to ~1.2x hand length so they cover the hand
8. Bounce animation adds a subtle vertical oscillation (phase-shifted per hand)
9. Press **Q** to quit

## Files
- `SKILL.md` — this file (skill description/instructions)
- `lobstercam.py` — main application
- `lobster_overlay.png` — lobster overlay for heads (transparent PNG, 256×256)
- `lobster_claw.png` — lobster claw overlay for hands (transparent PNG, 256×256)
- `requirements.txt` — pinned dependencies

## Known Fixes

- **Camera resolution (fixed upstream, commit 721da6a, 2026-11-12):** `main()` once opened the camera
  without applying MJPG or the `--width/--height/--fps` flags, so it fell back to 640×480.
  Fixed by setting `MJPG` + width/height/fps right after `cv2.VideoCapture`.
- **Custom overlays (fixed on the `hand-claws` branch):** `--image` was loaded into a local variable
  while the renderer read the module-level bundled image, so custom overlays never rendered; overlays
  are now passed explicitly. The error-fallback overlay was also opaque (alpha 255) instead of
  transparent.
