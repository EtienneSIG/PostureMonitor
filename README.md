# Posture Monitor Application

This application monitors your posture through your computer's camera and provides visual alerts when you need to correct your posture.

## Features

- Real-time posture detection using MediaPipe
- Visual alerts when poor posture is detected
- Customizable sensitivity settings
- Live camera feed with pose landmarks overlay

## Installation

1. Install Python 3.8 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python posture_monitor.py
```

### Controls
- **Space**: Toggle posture monitoring on/off
- **Esc**: Exit application
- **C**: Calibrate good posture (sit up straight and press C)
- **S**: Toggle sensitivity between Low/Medium/High

## How it works

The application uses MediaPipe to detect key body landmarks:
- Head position relative to shoulders
- Shoulder alignment
- Spine curvature

When poor posture is detected, you'll see:
- Red warning overlay on the video feed
- Text alert indicating posture issue
- Optional sound notification (if enabled)

## Tips for best results

- Ensure good lighting
- Position camera at eye level
- Sit approximately 2-3 feet from camera
- Calibrate your good posture when starting