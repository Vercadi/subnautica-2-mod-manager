from __future__ import annotations

import json
from pathlib import Path

from .app_dirs import AppDirs, ensure_app_dirs


def prepare_first_run_state(dirs: AppDirs, settings_path: Path) -> list[str]:
    messages: list[str] = []
    ensure_app_dirs(dirs)
    messages.append(f"Runtime directories ready: {dirs.data_dir}")
    messages.append(f"Library directory ready: {dirs.library_dir}")
    messages.append(f"Backup directory ready: {dirs.backup_dir}")
    messages.append("Release safety: Apply writes only non-blocked manager-tracked files and records every install in the manifest.")
    messages.append("Recovery removes only manifest-tracked managed files; unknown files are reported, not deleted.")
    messages.append("Loose root overlays such as loader DLL/config drops are review-required and blocked from automatic apply.")

    if not settings_path.exists():
        messages.append(f"Settings file will be created: {settings_path}")
    elif _settings_json_valid(settings_path):
        messages.append(f"Settings file loaded: {settings_path}")
    else:
        messages.append(f"Settings file is unreadable and will be regenerated: {settings_path}")

    if not (dirs.assets_dir / "background.png").is_file():
        messages.append("Background asset not found; procedural underwater background is active.")
    messages.append("Support reports are local text only; personal home and save paths are redacted or omitted.")
    return messages


def _settings_json_valid(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return True
