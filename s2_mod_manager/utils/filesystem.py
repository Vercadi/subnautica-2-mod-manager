from __future__ import annotations

from pathlib import Path


def safe_is_dir(path: Path | None) -> bool:
    if path is None:
        return False
    try:
        return Path(path).is_dir()
    except OSError:
        return False


def safe_is_file(path: Path | None) -> bool:
    if path is None:
        return False
    try:
        return Path(path).is_file()
    except OSError:
        return False
