from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models.app_paths import S2AppPaths


@dataclass(frozen=True)
class FolderTarget:
    label: str
    path: Path | None


def game_mods_folder_target(paths: S2AppPaths) -> FolderTarget:
    """Best single game-side mods folder for the current install layout."""
    candidates = [
        FolderTarget("UE4SS Mods", paths.ue4ss_mods),
        FolderTarget("Pak Mods", paths.mods_paks),
        FolderTarget("LogicMods", paths.logic_mods),
        FolderTarget("Paks", paths.content_paks),
    ]
    for candidate in candidates:
        if candidate.path is not None and candidate.path.exists():
            return candidate
    for candidate in candidates:
        if candidate.path is not None:
            return candidate
    return FolderTarget("Mods", None)
