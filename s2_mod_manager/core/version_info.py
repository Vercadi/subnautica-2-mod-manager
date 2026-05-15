from __future__ import annotations

import json
from pathlib import Path

from ..models.app_paths import S2GameVersion


def read_game_version(root: Path | None) -> S2GameVersion:
    if root is None:
        return S2GameVersion()
    return parse_game_version_files(root / "version.json", root / "version.txt")


def parse_game_version_files(version_json: Path, version_txt: Path | None = None) -> S2GameVersion:
    data: dict = {}
    raw_txt = ""

    text = _read_text_flexible(version_json) if version_json.is_file() else ""
    if text:
        try:
            parsed = json.loads(text)
            data = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            data = {}

    if version_txt and version_txt.is_file():
        raw_txt = _read_text_flexible(version_txt).strip()

    return S2GameVersion(
        changelist=str(data.get("changelist") or _first_token(raw_txt)),
        build_number=str(data.get("build_number") or ""),
        build_label=str(data.get("build_server_label") or ""),
        timestamp=str(data.get("timestamp") or _second_token(raw_txt)),
        branch=str(data.get("branch") or ""),
        raw_version_txt=raw_txt,
    )


def _first_token(value: str) -> str:
    parts = value.split()
    return parts[0] if parts else ""


def _second_token(value: str) -> str:
    parts = value.split()
    return parts[1] if len(parts) > 1 else ""


def _read_text_flexible(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return path.read_text(encoding=encoding)
        except (OSError, UnicodeDecodeError):
            continue
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
