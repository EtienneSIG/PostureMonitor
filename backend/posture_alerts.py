"""
Posture alert system using OS-native desktop notifications (plyer).
Replaces the previous pygame-based audio beeps.
"""

import time
import threading

try:
    from plyer import notification as _plyer_notify
    _PLYER_OK = True
except Exception:
    _PLYER_OK = False


class PostureAlerter:
    """Send OS desktop notifications when bad posture is detected."""

    def __init__(self):
        self.alerts_enabled: bool = True
        self.alert_cooldown: float = 30.0
        self._last_alert_time: float = 0.0
        self._lock = threading.Lock()

    # ── public properties ────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return self.alerts_enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.alerts_enabled = value

    def set_enabled(self, enabled: bool) -> None:
        self.alerts_enabled = enabled

    def set_cooldown(self, seconds: float) -> None:
        self.alert_cooldown = max(5.0, float(seconds))

    # ── core alert logic ─────────────────────────────────────────────────────

    def can_alert(self) -> bool:
        if not self.alerts_enabled:
            return False
        with self._lock:
            return time.time() - self._last_alert_time >= self.alert_cooldown

    def _mark_alerted(self) -> None:
        with self._lock:
            self._last_alert_time = time.time()

    def trigger_alert(self, analysis: dict) -> None:
        if not self.can_alert():
            return
        status = analysis.get("status", "unknown")
        issues = analysis.get("issues", [])
        message = analysis.get("message", "Check your posture")

        if status == "poor" or len(issues) > 1:
            title = "⚠️ Bad Posture Detected"
            body = message or "Multiple posture issues – please adjust."
        elif status in ("fair", "warning") or len(issues) == 1:
            title = "🔔 Posture Reminder"
            body = message or (issues[0] if issues else "Minor posture issue.")
        else:
            return

        self._notify(title, body)

    def alert_for_status(self, status: str, status_msg: str, issues: list) -> None:
        self.trigger_alert({"status": status, "issues": issues, "message": status_msg})

    # ── plyer wrapper ────────────────────────────────────────────────────────

    def _notify(self, title: str, body: str) -> None:
        self._mark_alerted()
        if _PLYER_OK:
            threading.Thread(
                target=self._send_plyer,
                args=(title, body),
                daemon=True,
            ).start()
        else:
            print(f"[PostureMonitor] {title}: {body}")

    @staticmethod
    def _send_plyer(title: str, body: str) -> None:
        try:
            _plyer_notify.notify(
                title=title,
                message=body,
                app_name="PostureMonitor",
                timeout=8,
            )
        except Exception as exc:
            print(f"[PostureMonitor] Notification error: {exc}")

    # ── helpers ──────────────────────────────────────────────────────────────

    def get_alert_config(self) -> dict:
        return {
            "enabled": self.alerts_enabled,
            "cooldown": self.alert_cooldown,
            "plyer_available": _PLYER_OK,
        }

    def play_alert(self, issue_type: str) -> None:
        """Called by PostureAnalyzer with a single issue string."""
        if not self.can_alert():
            return
        self._notify("⚠️ Posture Reminder", issue_type or "Adjust your posture")

    def cleanup(self) -> None:
        pass  # nothing to tear down
