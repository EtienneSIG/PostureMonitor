"""
Camera capture thread — grabs frames from the webcam, runs posture analysis,
and pushes results to a shared asyncio queue consumed by the WebSocket handler.
"""

import asyncio
import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np

from posture_analyzer import PostureAnalyzer
from posture_alerts import PostureAlerter

log = logging.getLogger(__name__)


def _derive_status(analysis: dict) -> tuple[str, str]:
    """Map raw analysis dict → (status, message) strings."""
    if not analysis.get("landmarks"):
        return "no_detection", "Position yourself in the camera view"

    issues = analysis.get("issues", [])
    n = len(issues)

    if n == 0:
        return "good", "Good posture 🟢"
    elif n == 1:
        return "fair", issues[0]
    else:
        return "poor", f"{n} issues detected"


class CameraManager:
    """
    Runs in a daemon thread.  Provides:
      - get_latest_result()  → dict | None
      - get_jpeg_frame()     → bytes | None  (for MJPEG streaming)
      - calibrate()          → captures next frame and calibrates thresholds
    """

    def __init__(self, alerter: PostureAlerter) -> None:
        self._analyzer = PostureAnalyzer()
        # Use the shared alerter so there is exactly one notification source
        self._analyzer.alerter = alerter

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None

        self._result_lock = threading.Lock()
        self._latest_result: Optional[dict] = None

        self._jpeg_lock = threading.Lock()
        self._latest_jpeg: Optional[bytes] = None

        self._calibrate_next = False

        # async event loop + queue injected from main.py
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_queue: Optional[asyncio.Queue] = None

    # ── public API ────────────────────────────────────────────────────────────

    def set_event_loop(
        self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue
    ) -> None:
        self._loop = loop
        self._async_queue = queue

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="camera")
        self._thread.start()
        log.info("Camera thread started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None
        log.info("Camera thread stopped")

    def set_sensitivity(self, level: str) -> None:
        self._analyzer.set_sensitivity(level)

    def calibrate(self) -> None:
        """Request calibration on the next available frame."""
        self._calibrate_next = True

    def get_latest_result(self) -> Optional[dict]:
        with self._result_lock:
            return dict(self._latest_result) if self._latest_result else None

    def get_jpeg_frame(self) -> Optional[bytes]:
        with self._jpeg_lock:
            return self._latest_jpeg

    @property
    def analyzer(self) -> PostureAnalyzer:
        return self._analyzer

    # ── background thread ────────────────────────────────────────────────────

    def _run(self) -> None:
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            log.warning("No camera found — running in headless mode")
            self._cap = None
            self._push_result(
                {
                    "status": "no_detection",
                    "confidence": 0,
                    "issues": [],
                    "message": "No camera found",
                    "timestamp": int(time.time() * 1000),
                }
            )
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        mp_drawing = self._analyzer.mp_drawing
        mp_pose = self._analyzer.mp_pose

        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            try:
                analysis = self._analyzer.analyze_posture(frame)
            except Exception as exc:
                log.debug("Analysis error: %s", exc)
                time.sleep(0.05)
                continue

            # Calibration requested?
            if self._calibrate_next:
                self._calibrate_next = False
                self._analyzer.calibrate_good_posture(frame)

            # Draw skeleton overlay
            annotated = frame.copy()
            if analysis.get("landmarks"):
                mp_drawing.draw_landmarks(
                    annotated,
                    analysis["landmarks"],
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(80, 200, 120), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(80, 200, 120), thickness=2),
                )

            # Encode annotated frame as JPEG for the video feed
            _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
            with self._jpeg_lock:
                self._latest_jpeg = buf.tobytes()

            status, message = _derive_status(analysis)
            result = {
                "status": status,
                "confidence": round(float(analysis.get("confidence", 0)) * 100, 1),
                "issues": analysis.get("issues", []),
                "message": message,
                "timestamp": int(time.time() * 1000),
            }
            self._push_result(result)

            time.sleep(0.1)  # ~10 FPS analysis

        if self._cap:
            self._cap.release()
            self._cap = None

    def _push_result(self, result: dict) -> None:
        with self._result_lock:
            self._latest_result = result
        # Forward to async queue (non-blocking, drop stale frames)
        if self._loop and self._async_queue:
            try:
                self._loop.call_soon_threadsafe(
                    self._async_queue.put_nowait, result
                )
            except asyncio.QueueFull:
                pass

