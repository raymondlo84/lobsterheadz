# 🦞 LobsterHeadz

Face-tracking webcam app that overlays two bouncy lobster images on people's heads in real-time.

![Demo](docs/demo.gif)

> Put lobsters on people's heads. That's it. That's the app.

## Features

- Real-time face detection and tracking via MediaPipe Face Mesh
- 2 lobster overlays per detected face (side-by-side), up to 5 faces
- Transparent PNG overlay with proper alpha blending
- Subtle bounce animation on the lobsters
- 1920×1080 @ 30fps via MJPEG pixel format
- Custom overlay images and camera options
- Resolves paths relative to script directory (no broken `~` paths)

## Install

### Prerequisites

- Python 3.9+
- A webcam (any OpenCV-compatible camera)
- Linux (tested on Ubuntu/Jetson), should work on macOS/Windows too

### Setup

```bash
# Clone the repo
git clone https://github.com/raymondlo84/lobsterheadz.git
cd lobsterheadz

# Install dependencies
pip3 install -r requirements.txt
```

## Run

```bash
# Default camera, bundled lobster overlay
python3 lobstercam.py

# Custom camera index
python3 lobstercam.py --camera 1

# Custom overlay image (transparent PNG, preferably 256×256+)
python3 lobstercam.py --image /path/to/my-overlay.png

# Custom resolution
python3 lobstercam.py --width 1280 --height 720 --fps 24

# Combine options
python3 lobstercam.py --camera 2 --image overlays/cat.png --width 1920 --height 1080
```

Press **Q** in the camera window to quit.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--camera` | `0` | Camera device index |
| `--image` | bundled overlay | Path to overlay PNG image |
| `--width` | `1920` | Camera resolution width |
| `--height` | `1080` | Camera resolution height |
| `--fps` | `30` | Camera frame rate |

## Custom Overlays

Any transparent PNG works as an overlay. Tips:

- **256×256** is the default size — scales automatically based on detected face size
- Use a PNG with **alpha channel** (transparent background) for best results
- The image is centered and placed above the detected head
- You can create custom overlays with any image editor — GIFs, cartoon animals, hats, whatever

## How It Works

1. Opens webcam at specified resolution (default 1920×1080) via MJPEG for full 30fps
2. Uses MediaPipe Face Mesh to detect up to 5 faces simultaneously
3. Estimates head position from eyebrow landmarks (forehead midpoint, extrapolated upward)
4. Places two overlay images side-by-side on each detected head
5. Bounce animation adds a subtle vertical oscillation
6. Face size determines lobster scale — closer faces get bigger lobsters

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mediapipe` | 0.10.18 | Face mesh detection |
| `opencv-python` | 4.9.0.80 | Video capture & image processing |

## License

MIT — do whatever you want with it. Just don't blame me when you look ridiculous.
