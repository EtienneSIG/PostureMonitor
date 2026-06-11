#!/usr/bin/env python3
"""
Posture Monitor Pro - Desktop entry point.

Single-process launcher intended for the packaged (.exe) build:
- Stores the database and downloaded model in a user-writable folder.
- Starts the FastAPI backend, which also serves the built Vue frontend.
- Opens the default web browser on the app once the server is ready.

This is what PyInstaller bundles into PostureMonitorPro.exe.
"""

import os
import sys
import socket
import threading
import time
import webbrowser
from pathlib import Path


APP_NAME = "PostureMonitorPro"
DEFAULT_PORT = 8000


def get_user_data_dir() -> Path:
    """Return a per-user, writable directory for the database and model cache."""
    if sys.platform.startswith("win"):
        base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    data_dir = Path(base) / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def find_free_port(preferred: int) -> int:
    """Return the preferred port if free, otherwise an OS-assigned free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def configure_environment() -> None:
    """Set writable paths before the backend is imported."""
    data_dir = get_user_data_dir()
    model_dir = data_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "posture_monitor.db"
    # SQLAlchemy URL with forward slashes for cross-platform safety.
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    os.environ.setdefault("POSTURE_MODEL_DIR", str(model_dir))
    os.environ["RELOAD"] = "False"


def open_browser_when_ready(url: str, timeout_seconds: int = 30) -> None:
    """Poll the health endpoint, then open the browser once the server responds."""
    import urllib.request

    health_url = url.rstrip("/") + "/health"
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=2):
                break
        except Exception:
            time.sleep(0.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> None:
    configure_environment()

    port = find_free_port(DEFAULT_PORT)
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    # Import after environment is configured so config picks up our paths.
    import uvicorn
    from backend.app import app

    print("=" * 60)
    print("  Posture Monitor Pro")
    print("=" * 60)
    print(f"  Opening {url}")
    print("  Close this window to stop the application.")
    print("=" * 60)

    threading.Thread(target=open_browser_when_ready, args=(url,), daemon=True).start()

    uvicorn.run(app, host=host, port=port, reload=False, log_level="warning")


if __name__ == "__main__":
    main()
