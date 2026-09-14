# LobsterCam 2 🦞

> Description: Face tracking app that overlays lobster images on people's heads — now at 1080p30 via MJPEG.

Face tracking app that overlays lobster images on people's heads — now at 1080p30 via MJPEG.

## Features
- Real-time face detection and tracking via MediaPipe
- 2 lobster overlays per detected face (side-by-side, ~5 max)
- Transparent PNG overlay with proper alpha blending
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
```

## Dependencies
- `mediapipe==0.10.18` (face mesh detection)
- `opencv-python==4.9.0.80` (video processing)

## How It Works
1. Opens webcam at 1920×1080 @ 30fps using MJPEG pixel format
2. Uses MediaPipe Face Mesh to detect up to 5 faces
3. Estimates head position from eyebrow landmarks (forehead midpoint extrapolated upward)
4. Overlays 2 lobster PNG images on each head with proper transparency
5. Bounce animation adds a subtle vertical oscillation
6. Press **Q** to quit

## Files
- `SKILL.md` — this file
- `lobstercam.py` — main application
- `lobster_overlay.png` — lobster overlay image (transparent PNG, 256×256)
- `requirements.txt` — pinned dependencies
