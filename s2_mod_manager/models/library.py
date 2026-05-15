from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .archive_info import ComponentFile, ScannedComponent


def _path_to_str(path: Path | None) -> str:
    return str(path) if path else ""


def _path_from_str(value: str | None) -> Path | None:
    return Path(value) if value else None


@dataclass
class LibrarySource:
    source_id: str
    source_kind: str
    display_name: str
    original_path: Path
    managed_path: Path
    source_hash: str = ""
    component_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_kind": self.source_kind,
            "display_name": self.display_name,
            "original_path": _path_to_str(self.original_path),
            "managed_path": _path_to_str(self.managed_path),
            "source_hash": self.source_hash,
            "component_ids": list(self.component_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LibrarySource":
        return cls(
            source_id=str(data.get("source_id") or ""),
            source_kind=str(data.get("source_kind") or ""),
            display_name=str(data.get("display_name") or ""),
            original_path=Path(str(data.get("original_path") or "")),
            managed_path=Path(str(data.get("managed_path") or "")),
            source_hash=str(data.get("source_hash") or ""),
            component_ids=[str(value) for value in data.get("component_ids", []) if value],
        )


@dataclass
class LibraryComponentFile:
    source_path: str
    role: str = "file"
    target_hint: str = ""
    size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "role": self.role,
            "target_hint": self.target_hint,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LibraryComponentFile":
        return cls(
            source_path=str(data.get("source_path") or ""),
            role=str(data.get("role") or "file"),
            target_hint=str(data.get("target_hint") or ""),
            size=int(data.get("size") or 0),
        )

    @classmethod
    def from_scan_file(cls, file: ComponentFile) -> "LibraryComponentFile":
        return cls(
            source_path=file.source_path,
            role=file.role,
            target_hint=file.target_hint,
            size=file.size,
        )


@dataclass
class LibraryComponent:
    component_id: str
    source_id: str
    display_name: str
    component_type: str
    install_kind: str
    badges: list[str] = field(default_factory=list)
    target_hint: str = ""
    file_count: int = 0
    files: list[LibraryComponentFile] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "source_id": self.source_id,
            "display_name": self.display_name,
            "component_type": self.component_type,
            "install_kind": self.install_kind,
            "badges": list(self.badges),
            "target_hint": self.target_hint,
            "file_count": self.file_count,
            "files": [file.to_dict() for file in self.files],
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LibraryComponent":
        return cls(
            component_id=str(data.get("component_id") or ""),
            source_id=str(data.get("source_id") or ""),
            display_name=str(data.get("display_name") or ""),
            component_type=str(data.get("component_type") or ""),
            install_kind=str(data.get("install_kind") or ""),
            badges=[str(value) for value in data.get("badges", []) if value],
            target_hint=str(data.get("target_hint") or ""),
            file_count=int(data.get("file_count") or 0),
            files=[
                LibraryComponentFile.from_dict(item)
                for item in data.get("files", [])
                if isinstance(item, dict)
            ],
            warnings=[str(value) for value in data.get("warnings", []) if value],
        )

    @classmethod
    def from_scan(cls, source_id: str, component: ScannedComponent) -> "LibraryComponent":
        return cls(
            component_id=component.component_id,
            source_id=source_id,
            display_name=component.display_name,
            component_type=component.component_type,
            install_kind=component.install_kind,
            badges=list(component.badges),
            target_hint=component.target_hint,
            file_count=component.file_count,
            files=[LibraryComponentFile.from_scan_file(file) for file in component.files],
            warnings=list(component.warnings) + list(component.dependency_warnings),
        )


@dataclass
class LibraryState:
    sources: list[LibrarySource] = field(default_factory=list)
    components: list[LibraryComponent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sources": [source.to_dict() for source in self.sources],
            "components": [component.to_dict() for component in self.components],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "LibraryState":
        if not isinstance(data, dict):
            return cls()
        return cls(
            sources=[
                LibrarySource.from_dict(item)
                for item in data.get("sources", [])
                if isinstance(item, dict)
            ],
            components=[
                LibraryComponent.from_dict(item)
                for item in data.get("components", [])
                if isinstance(item, dict)
            ],
        )
