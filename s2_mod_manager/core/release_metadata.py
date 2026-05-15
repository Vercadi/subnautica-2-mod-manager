from __future__ import annotations

import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .. import __app_name__, __version__
from ..utils.json_io import write_json


def build_release_metadata() -> dict[str, Any]:
    return {
        "app_name": __app_name__,
        "version": __version__,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "package_kind": "portable-pyinstaller",
        "safety_defaults": {
            "real_apply": "enabled_for_non_blocked_preview_apply_plans",
            "destructive_recovery": "manifest_tracked_managed_files_only",
            "restore_vanilla": "preview_only",
            "quarantine": "preview_only",
        },
    }


def write_release_metadata(path: Path) -> dict[str, Any]:
    metadata = build_release_metadata()
    write_json(path, metadata)
    return metadata
