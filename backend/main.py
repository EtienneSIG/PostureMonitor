"""
PostureMonitor — FastAPI backend
================================
• Serves the built SvelteKit frontend as static files
• Exposes a WebSocket at /ws for real-time posture updates
• Streams an MJPEG video feed at /video_feed
• Exposes a small REST API under /api/*
• Runs a system-tray icon (pystray) for background operation
"""

import asyncio
import json
import logging
import os
import signal
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from camera import CameraManager
from posture_alerts import PostureAlerter
from tray import PostureTray

# ── logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("posture.main")

# ── constants ─────────────────────────────────────────────────────────────────

HOST = "127.0.0.1"
PORT = 8000
DASHBOARD_URL = f"http://{HOST}:{PORT}"
STATIC_DIR = Path(__file__).parent / "static"

# ── app state ─────────────────────────────────────────────────────────────────

app = FastAPI(title="PostureMonitor", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", DASHBOARD_URL],
    allow_methods=["*"],
    allow_headers=["*"],
)

alerter = PostureAlerter()
camera = CameraManager(alerter)
monitoring_active = False

# broadcast queue — camera thread pushes; WS handler fans out to all clients
broadcast_queue: asyncio.Queue = asyncio.Queue(maxsize=5)
connected_clients: Set[WebSocket] = set()
_loop: asyncio.AbstractEventLoop | None = None

app_settings: dict = {
    "sensitivity": "low",
    "language": "en",
    "notifications_enabled": True,
    "alert_cooldown": 30,
}

# ── lifecycle ─────────────────────────────────────────────────────────────────


@app.on_event("startup")
async def _startup() -> None:
    global _loop, monitoring_active
    _loop = asyncio.get_running_loop()
    camera.set_event_loop(_loop, broadcast_queue)
    # Start monitoring immediately
    monitoring_active = True
    camera.start()
    # Fan-out task
    _loop.create_task(_broadcaster())
    log.info("PostureMonitor backend started — %s", DASHBOARD_URL)


@app.on_event("shutdown")
async def _shutdown() -> None:
    camera.stop()
    alerter.cleanup()
    log.info("Backend shut down cleanly")


# ── broadcaster task ──────────────────────────────────────────────────────────


async def _broadcaster() -> None:
    """Dequeue posture results and fan out to every connected WebSocket."""
    while True:
        result = await broadcast_queue.get()
        if not connected_clients:
            continue
        payload = json.dumps({"type": "posture_update", **result})
        dead: Set[WebSocket] = set()
        for ws in set(connected_clients):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        connected_clients.difference_update(dead)


# ── WebSocket ─────────────────────────────────────────────────────────────────


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    connected_clients.add(ws)
    log.info("WS client connected (%d total)", len(connected_clients))

    # Send current state immediately
    await ws.send_text(
        json.dumps(
            {
                "type": "state",
                "monitoring": monitoring_active,
                "settings": app_settings,
            }
        )
    )

    try:
        while True:
            raw = await ws.receive_text()
            await _handle_ws_message(ws, json.loads(raw))
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        connected_clients.discard(ws)
        log.info("WS client disconnected (%d total)", len(connected_clients))


async def _handle_ws_message(ws: WebSocket, msg: dict) -> None:
    global monitoring_active
    t = msg.get("type")

    if t == "get_state":
        await ws.send_text(
            json.dumps(
                {"type": "state", "monitoring": monitoring_active, "settings": app_settings}
            )
        )

    elif t == "start":
        if not monitoring_active:
            monitoring_active = True
            camera.start()
            tray.set_monitoring(True)

    elif t == "stop":
        if monitoring_active:
            monitoring_active = False
            camera.stop()
            tray.set_monitoring(False)

    elif t == "calibrate":
        camera.calibrate()

    elif t == "settings_update":
        new_settings: dict = msg.get("settings", {})
        _apply_settings(new_settings)
        await ws.send_text(json.dumps({"type": "settings_ack", "settings": app_settings}))


def _apply_settings(new: dict) -> None:
    if "sensitivity" in new:
        app_settings["sensitivity"] = new["sensitivity"]
        camera.set_sensitivity(new["sensitivity"])
    if "language" in new:
        app_settings["language"] = new["language"]
        camera.analyzer.set_translator_language(new["language"])
    if "notifications_enabled" in new:
        app_settings["notifications_enabled"] = new["notifications_enabled"]
        alerter.enabled = new["notifications_enabled"]
    if "alert_cooldown" in new:
        app_settings["alert_cooldown"] = new["alert_cooldown"]
        alerter.set_cooldown(new["alert_cooldown"])


# ── REST API ──────────────────────────────────────────────────────────────────


@app.get("/api/status")
def api_status() -> dict:
    result = camera.get_latest_result() or {}
    return {
        "monitoring": monitoring_active,
        "posture": result,
        "settings": app_settings,
    }


@app.post("/api/calibrate")
def api_calibrate() -> dict:
    camera.calibrate()
    return {"ok": True}


@app.post("/api/settings")
async def api_settings(body: dict) -> dict:
    _apply_settings(body)
    return {"ok": True, "settings": app_settings}


# ── MJPEG video feed ──────────────────────────────────────────────────────────


async def _mjpeg_generator():
    while True:
        frame = camera.get_jpeg_frame()
        if frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
        await asyncio.sleep(0.05)  # ~20 FPS max


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        _mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# ── Static SvelteKit frontend ─────────────────────────────────────────────────

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    @app.get("/")
    def _no_build():
        return Response(
            content=(
                "<h1>PostureMonitor</h1>"
                "<p>Frontend not built yet. Run <code>cd frontend && yarn build</code></p>"
            ),
            media_type="text/html",
        )


# ── system tray ───────────────────────────────────────────────────────────────

tray = PostureTray(
    dashboard_url=DASHBOARD_URL,
    on_start=lambda: None,   # patched after app init
    on_stop=lambda: None,
    on_calibrate=lambda: camera.calibrate(),
    on_quit=lambda: os.kill(os.getpid(), signal.SIGTERM),
)


# ── entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    log.info("Starting PostureMonitor v2 …")

    # Patch tray callbacks now that camera/monitoring state are defined
    tray._on_start = lambda: camera.start()
    tray._on_stop = lambda: camera.stop()
    tray.start()

    # Open browser after a short delay
    threading.Timer(1.5, lambda: webbrowser.open(DASHBOARD_URL)).start()

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
