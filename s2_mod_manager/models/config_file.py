from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


EDITABLE_CONFIG_EXTENSIONS = frozenset({".ini", ".json", ".txt", ".cfg", ".lua"})
CONFIG_PREVIEW_SIZE_LIMIT = 512 * 1024
CONFIG_EDIT_SIZE_LIMIT = 256 * 1024


@dataclass(frozen=True)
class ConfigFileInfo:
    component_id: str
    component_name: str
    relative_path: str
    installed_path: Path
    source_path: Path | None
    source_member: str
    extension: str
    size_bytes: int = 0
    editable: bool = True
    reason: str = ""
    has_backup: bool = False
    modified_by_manager: bool = False

    @property
    def display_name(self) -> str:
        return self.relative_path or self.installed_path.name


@dataclass(frozen=True)
class ConfigEditResult:
    ok: bool
    message: str
    backup_id: str = ""
    errors: list[str] = field(default_factory=list)
