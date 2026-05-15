from __future__ import annotations

from pathlib import Path

from ..models.app_paths import S2AppPaths
from ..models.preferences import UserPreferences
from ..utils.json_io import read_json, write_json

SETTINGS_SCHEMA_VERSION = 1


def load_settings(settings_path: Path) -> S2AppPaths:
    data = read_json(settings_path)
    paths = S2AppPaths.from_dict(data.get("paths") if isinstance(data.get("paths"), dict) else data)
    return paths


def load_preferences(settings_path: Path) -> UserPreferences:
    data = read_json(settings_path)
    preferences = data.get("preferences") if isinstance(data.get("preferences"), dict) else {}
    return UserPreferences.from_dict(preferences)


def save_settings(settings_path: Path, paths: S2AppPaths, preferences: UserPreferences | None = None) -> None:
    current = read_json(settings_path)
    prefs = preferences or UserPreferences.from_dict(
        current.get("preferences") if isinstance(current.get("preferences"), dict) else {}
    )
    payload = {
        "schema_version": SETTINGS_SCHEMA_VERSION,
        "paths": paths.to_dict(),
        "preferences": prefs.to_dict(),
    }
    if current == payload:
        return
    write_json(settings_path, payload)


def save_preferences(settings_path: Path, preferences: UserPreferences) -> None:
    data = read_json(settings_path)
    paths = S2AppPaths.from_dict(data.get("paths") if isinstance(data.get("paths"), dict) else data)
    save_settings(settings_path, paths, preferences=preferences)
