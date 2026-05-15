from __future__ import annotations

import time
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import ImageGrab


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = ROOT / "screenshots"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from s2_mod_manager.ui.app_window import AppWindow  # noqa: E402


def _update(app: AppWindow, delay: float = 0.25) -> None:
    app.update_idletasks()
    app.update()
    time.sleep(delay)
    app.update_idletasks()
    app.update()


def _capture(widget, path: Path) -> None:
    top = widget.winfo_toplevel()
    try:
        top.lift()
        top.attributes("-topmost", True)
        top.focus_force()
    except Exception:
        pass
    _update(top)
    x = widget.winfo_rootx()
    y = widget.winfo_rooty()
    width = max(widget.winfo_width(), 1)
    height = max(widget.winfo_height(), 1)
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
    image.save(path)
    try:
        top.attributes("-topmost", False)
    except Exception:
        pass


def _toplevels(app: AppWindow) -> list[ctk.CTkToplevel]:
    return [child for child in app.winfo_children() if isinstance(child, ctk.CTkToplevel) and child.winfo_exists()]


def _capture_dialog(app: AppWindow, name: str, opener, before_capture=None) -> None:
    before = {str(window) for window in _toplevels(app)}
    opener()
    _update(app, delay=0.35)
    candidates = [window for window in _toplevels(app) if str(window) not in before]
    if not candidates:
        candidates = _toplevels(app)
    if not candidates:
        return
    dialog = candidates[-1]
    if before_capture is not None:
        before_capture(dialog)
        _update(app, delay=0.2)
    _capture(dialog, SCREENSHOTS_DIR / f"{name}.png")
    try:
        dialog.grab_release()
    except Exception:
        pass
    dialog.destroy()
    _update(app, delay=0.1)


def _first_sample_source() -> Path | None:
    inbox = ROOT.parent / "Mods"
    if not inbox.is_dir():
        return None
    for pattern in ("*.zip", "*.7z", "*.rar", "*.pak", "*.ucas", "*.utoc"):
        matches = sorted(inbox.glob(pattern))
        if matches:
            return matches[0]
    folders = [path for path in sorted(inbox.iterdir()) if path.is_dir()]
    return folders[0] if folders else None


def _prepare_console(app: AppWindow) -> None:
    app.status_log.clear()
    app._console_write("Release candidate visual QA.")
    app._console_write("Safety gates active: Apply Preview installs managed files only; loose overlays remain blocked.")
    app._console_write("Loose root overlays remain review-required and blocked from automatic apply.")


def _scroll_settings_to_popup_policy(dialog) -> None:
    body = getattr(dialog, "body", None)
    canvas = getattr(body, "_parent_canvas", None)
    if canvas is not None:
        canvas.yview_moveto(0.48)


def main() -> None:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    app = AppWindow()
    try:
        _prepare_console(app)
        for width, height in ((1280, 760), (1500, 900)):
            app.geometry(f"{width}x{height}+40+40")
            _update(app, delay=0.35)
            _capture(app, SCREENSHOTS_DIR / f"main-shell-{width}x{height}.png")

        _capture_dialog(app, "settings", app.open_settings_dialog)
        _capture_dialog(app, "settings-popup-policy", app.open_settings_dialog, before_capture=_scroll_settings_to_popup_policy)
        _capture_dialog(app, "help-about-support", app.open_help_dialog)
        _capture_dialog(app, "activity", app.open_activity_dialog)
        _capture_dialog(app, "recovery", app.open_recovery_dialog)
        _capture_dialog(app, "apply-preview", app.preview_deployment)

        sample = _first_sample_source()
        if sample is not None:
            _capture_dialog(app, "import-review", lambda: app.open_import_review([sample]))
    finally:
        app.destroy()


if __name__ == "__main__":
    main()
