from __future__ import annotations

from pathlib import Path, PurePosixPath


PAK_FOLDER_PATCH = "~mods"
PAK_FOLDER_LOGIC = "LogicMods"


def pak_target_folder(relative_path: str) -> str:
    path = PurePosixPath(str(relative_path or "").replace("\\", "/"))
    parts = path.parts
    for part in parts:
        lowered = part.casefold()
        if lowered == "logicmods":
            return PAK_FOLDER_LOGIC
        if lowered in {"~mods", "mods"}:
            return PAK_FOLDER_PATCH
    if _is_patch_pak(path.name):
        return PAK_FOLDER_PATCH
    return PAK_FOLDER_LOGIC


def pak_file_target_hint(relative_path: str) -> str:
    path = PurePosixPath(str(relative_path or "").replace("\\", "/"))
    folder = pak_target_folder(str(path))
    return str(PurePosixPath(folder, path.name))


def pak_component_target_hint(relative_path: str) -> str:
    folder = pak_target_folder(relative_path)
    return rf"Subnautica2\Content\Paks\{folder}"


def pak_target_path(content_paks: Path | None, target_hint: str, source_path: str = "") -> Path | None:
    if content_paks is None:
        return None
    hint = target_hint or source_path
    rel = PurePosixPath(pak_file_target_hint(hint))
    return content_paks / Path(*rel.parts)


def _is_patch_pak(name: str) -> bool:
    stem = PurePosixPath(str(name or "")).stem.casefold()
    return stem.endswith("_p")
