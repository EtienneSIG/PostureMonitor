# 🧍 PostureMonitor v2

A **lightweight, modern posture-monitoring app** that runs quietly in the background while you work or attend meetings, and alerts you via desktop notifications when your posture needs correction.

Built with **SvelteKit + Tailwind CSS** (frontend) and **Python FastAPI** (backend), with **MediaPipe** for real-time pose detection.

---

## ✨ What's new in v2

| Feature | v1 (Tkinter/OpenCV window) | v2 (SvelteKit + FastAPI) |
|---------|----------------------------|--------------------------|
| Interface | Desktop OpenCV window | Modern web dashboard |
| Background running | ❌ Window must stay open | ✅ System-tray icon |
| Notifications | Pygame audio beeps | OS desktop notifications |
| Settings | Keyboard shortcuts | Click-to-configure UI |
| Architecture | Monolithic Python | FastAPI + SvelteKit |
| Bundle size | Heavy (pygame, tkinter) | Lean (no GUI frameworks) |

---

## 🚀 Quick start

### Prerequisites
- **Python 3.10+** and **pip**
- **Node.js 18+** and **yarn** (`npm install -g yarn`)
- A webcam

### macOS / Linux
```bash
./start.sh
```

### Windows
```bat
start.bat
```

Both scripts will:
1. Build the SvelteKit frontend (only on first run or when files change)
2. Install Python dependencies if missing
3. Launch the FastAPI backend at `http://127.0.0.1:8000`
4. Open your browser automatically
5. Add a system-tray icon for background control

---

## 🛠️ Development setup (hot-reload)

Open the **VS Code workspace** (`PostureMonitor.code-workspace`) then run two tasks in parallel:

**Terminal 1 — Backend**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Terminal 2 — Frontend dev server** (hot-reload on save)
```bash
cd frontend
yarn install
yarn dev          # proxies /api and /ws to port 8000
```

Open `http://localhost:5173` for the hot-reloading UI.

---

## 📦 Project structure

```
PostureMonitor/
├── backend/
│   ├── main.py              # FastAPI server + system-tray entry point
│   ├── camera.py            # Camera capture & MediaPipe analysis thread
│   ├── tray.py              # pystray system-tray icon
│   ├── posture_analyzer.py  # Core pose analysis (MediaPipe)
│   ├── posture_alerts.py    # OS desktop notifications (plyer)
│   ├── posture_translator.py# EN / FR translations
│   ├── requirements.txt
│   └── static/              # Built SvelteKit output (git-ignored)
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte
│   │   │   ├── +layout.ts   # prerender = true, ssr = false
│   │   │   └── +page.svelte # Main dashboard
│   │   └── lib/
│   │       ├── stores.svelte.ts  # Reactive state (Svelte 5 runes)
│   │       ├── websocket.ts      # Auto-reconnecting WS client
│   │       └── components/
│   │           ├── StatusCard.svelte
│   │           ├── HistoryBar.svelte
│   │           ├── SettingsPanel.svelte
│   │           └── VideoFeed.svelte
│   ├── vite.config.ts
│   └── package.json
├── PostureMonitor.code-workspace
├── start.sh / start.bat
└── .gitignore
```

---

## 🖥️ System tray

Once running, a coloured dot appears in your system tray:
- 🟢 Good posture
- 🟡 Fair posture
- 🔴 Poor posture
- ⚫ No detection / monitoring paused

**Right-click** the icon for:
- 📊 Open Dashboard
- ▶ / ⏸ Start / Pause monitoring
- 📐 Calibrate
- ❌ Quit

---

## ⚙️ REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Current posture status + settings |
| POST | `/api/calibrate` | Trigger calibration |
| POST | `/api/settings` | Update settings (`sensitivity`, `language`, etc.) |
| GET | `/video_feed` | MJPEG camera stream |
| WS | `/ws` | Real-time posture events |

---

## 🧩 WebSocket protocol

**Server → Client**
```json
{ "type": "posture_update", "status": "good|fair|poor|no_detection",
  "confidence": 87.4, "issues": ["Forward head posture"],
  "message": "Adjust your neck", "timestamp": 1718000000000 }
```

**Client → Server**
```json
{ "type": "start" | "stop" | "calibrate" | "settings_update" | "get_state" }
```

---

## 🌍 Languages
Switch between **English** and **Français** in the Settings panel. All posture issue messages and UI labels update instantly.

