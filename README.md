# Posture Monitor Pro

Local posture tracking application with a modern interface and built-in compliance requirements.

## ⚠️ Disclaimer

Posture Monitor Pro **is not a medical device** and does not provide any diagnosis, treatment, or medical advice. It is simply an assistive tool intended to raise the user's awareness of their posture.

The metrics and alerts displayed are indicative and may be inaccurate. They are in no way a substitute for the advice of a qualified healthcare professional. If you experience pain, discomfort, or any health issue, consult a doctor or a healthcare professional.

Use of this application is the sole responsibility of the user, who is free to use it or not. The authors accept no liability for decisions made or consequences resulting from its use.

## Quick start

### Recommended modern application
```bash
python launch.py
```

Then open `http://localhost:5173`.

### Alternative modes
```bash
python launch.py --backend-only
python launch.py --frontend-only
```

## Architecture

- `frontend/`: modern Vue 3 + Vite interface
- `backend/`: local FastAPI + WebSocket API
- `launch.py`: single launcher for backend + frontend
- `reglementation.md`: compliance tracking for Europe / North America

## Key features

- real-time posture monitoring
- simpler-to-use local web interface
- explicit consent before use
- minimum age verification
- export and deletion of user data
- audit logs and data retention
- English / French support

## Built-in compliance

- GDPR: consent, right of access, deletion, retention
- ePrivacy: no third-party trackers added
- BIPA / biometrics: explicit consent before processing
- CCPA/CPRA: data export and deletion
- COPPA: age verification
- PIPEDA: local privacy-first approach

## Important files

- `backend/app.py`: API and WebSocket endpoints
- `backend/config.py`: retention and compliance rules
- `backend/models.py`: data models and audit
- `frontend/src/pages/PostureMonitor.vue`: main monitoring screen
- `frontend/src/pages/PrivacyCenter.vue`: user rights management

## Installation

### Python
```bash
pip install -r requirements.txt
```

Python 3.12 is now supported via the modern MediaPipe Tasks backend.
Python 3.11 remains the most stable path to stay close to the legacy backend and older integrations.

### Stable Python 3.11 setup
```powershell
./setup_py311.ps1
```

This script prepares a `.venv311` environment if Python 3.11 is installed locally.

### Node.js
Node.js 18+ is required for the frontend.

On first launch, `launch.py` automatically installs the frontend dependencies if needed.

## Notes

- processing stays local by default
- raw video frames must not be stored persistently
- on Python 3.12, the `pose_landmarker_full.task` model is downloaded automatically into `.cache/` on first start
- the `/health` endpoint indicates whether the posture analyzer is available

See also `backend/README.md`, `frontend/README.md`, and `reglementation.md`.

