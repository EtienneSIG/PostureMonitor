"""
System-tray icon for PostureMonitor.
Shows a coloured dot that reflects the current posture status and provides
a right-click context menu for common actions.
"""

import logging
import threading
import webbrowser
from typing import Callable, Optional

log = logging.getLogger(__name__)

try:
    import pystray
    from pystray import MenuItem as Item
    from PIL import Image, ImageDraw
    _PYSTRAY_OK = True
except ImportError:
    _PYSTRAY_OK = False
    log.warning("pystray / Pillow not available — system tray disabled")


# Palette: status → RGBA colour
_COLORS = {
    "good":         (34, 197, 94, 255),   # green-500
    "fair":         (245, 158, 11, 255),  # amber-500
    "poor":         (239, 68, 68, 255),   # red-500
    "no_detection": (100, 116, 139, 255), # slate-500
    "disabled":     (71,  85, 105, 255),  # slate-600
}


def _make_icon(color: tuple) -> "Image.Image":
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, 56, 56], fill=color)
    return img


class PostureTray:
    """Manages the system-tray icon lifecycle."""

    def __init__(
        self,
        dashboard_url: str,
        on_start: Callable,
        on_stop: Callable,
        on_calibrate: Callable,
        on_quit: Callable,
    ) -> None:
        self._url = dashboard_url
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_calibrate = on_calibrate
        self._on_quit = on_quit
        self._icon: Optional["pystray.Icon"] = None
        self._thread: Optional[threading.Thread] = None
        self._monitoring = False

    # ── public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        if not _PYSTRAY_OK:
            log.info("Tray unavailable — skipping")
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="tray")
        self._thread.start()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    def update_status(self, status: str) -> None:
        if not self._icon:
            return
        color = _COLORS.get(status, _COLORS["no_detection"])
        self._icon.icon = _make_icon(color)
        label = status.replace("_", " ").title()
        self._icon.title = f"PostureMonitor — {label}"

    def set_monitoring(self, active: bool) -> None:
        self._monitoring = active
        self._rebuild_menu()

    # ── internals ────────────────────────────────────────────────────────────

    def _run(self) -> None:
        icon_img = _make_icon(_COLORS["no_detection"])
        self._icon = pystray.Icon(
            name="PostureMonitor",
            icon=icon_img,
            title="PostureMonitor",
            menu=self._build_menu(),
        )
        self._icon.run()

    def _build_menu(self):
        toggle_label = "⏸ Pause Monitoring" if self._monitoring else "▶ Start Monitoring"
        return pystray.Menu(
            Item("📊 Open Dashboard", self._open_dashboard, default=True),
            Item(toggle_label, self._toggle_monitoring),
            Item("📐 Calibrate", lambda icon, item: self._on_calibrate()),
            pystray.Menu.SEPARATOR,
            Item("❌ Quit", self._quit),
        )

    def _rebuild_menu(self) -> None:
        if self._icon:
            self._icon.menu = self._build_menu()

    def _open_dashboard(self, icon=None, item=None) -> None:
        webbrowser.open(self._url)

    def _toggle_monitoring(self, icon=None, item=None) -> None:
        if self._monitoring:
            self._on_stop()
            self._monitoring = False
        else:
            self._on_start()
            self._monitoring = True
        self._rebuild_menu()

    def _quit(self, icon=None, item=None) -> None:
        self._on_quit()
        if self._icon:
            self._icon.stop()
