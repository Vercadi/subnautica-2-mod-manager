from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath


SOURCE_ARCHIVE = "archive"
SOURCE_FOLDER = "folder"
SOURCE_LOCAL_FILES = "local_files"

COMPONENT_PAK_BUNDLE = "pak_bundle"
COMPONENT_UE4SS_RUNTIME = "ue4ss_runtime"
COMPONENT_UE4SS_MOD = "ue4ss_mod"
COMPONENT_LOOSE_OVERLAY = "loose_overlay"
COMPONENT_MIXED = "mixed"
COMPONENT_UNKNOWN = "unknown"

INSTALL_KIND_STANDARD = "standard_mod"
INSTALL_KIND_UE4SS_RUNTIME = "ue4ss_runtime"
INSTALL_KIND_UE4SS_MOD = "ue4ss_mod"
INSTALL_KIND_LOOSE_OVERLAY = "loose_overlay"

UNREAL_ASSET_SUFFIXES = {".pak", ".ucas", ".utoc"}
SUPPORTED_ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar"}


@dataclass(frozen=True)
class ScanEntry:
    path: str
    is_dir: bool = False
    size: int = 0

    @property
    def pure_path(self) -> PurePosixPath:
        return PurePosixPath(self.path.replace("\\", "/"))

    @property
    def name(self) -> str:
        return self.pure_path.name

    @property
    def suffix(self) -> str:
        return self.pure_path.suffix.casefold()

    @property
    def stem(self) -> str:
        return self.pure_path.stem

    @property
    def is_file(self) -> bool:
        return not self.is_dir

    @property
    def is_unreal_asset(self) -> bool:
        return self.suffix in UNREAL_ASSET_SUFFIXES

    @property
    def is_pak(self) -> bool:
        return self.suffix == ".pak"

    @property
    def is_companion(self) -> bool:
        return self.suffix in {".ucas", ".utoc"}

    def to_dict(self) -> dict:
        return {"path": self.path, "is_dir": self.is_dir, "size": self.size}

    @classmethod
    def from_dict(cls, data: dict) -> "ScanEntry":
        return cls(
            path=str(data.get("path") or ""),
            is_dir=bool(data.get("is_dir", False)),
            size=int(data.get("size") or 0),
        )


@dataclass(frozen=True)
class ComponentFile:
    source_path: str
    role: str = "file"
    target_hint: str = ""
    size: int = 0

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "role": self.role,
            "target_hint": self.target_hint,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentFile":
        return cls(
            source_path=str(data.get("source_path") or ""),
            role=str(data.get("role") or "file"),
            target_hint=str(data.get("target_hint") or ""),
            size=int(data.get("size") or 0),
        )


@dataclass
class ScannedComponent:
    component_id: str
    display_name: str
    component_type: str
    install_kind: str
    files: list[ComponentFile] = field(default_factory=list)
    badges: list[str] = field(default_factory=list)
    target_hint: str = ""
    dependency_warnings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    selected_variant: str = ""

    @property
    def file_count(self) -> int:
        return len(self.files)

    def to_dict(self) -> dict:
        return {
            "component_id": self.component_id,
            "display_name": self.display_name,
            "component_type": self.component_type,
            "install_kind": self.install_kind,
            "files": [file.to_dict() for file in self.files],
            "badges": list(self.badges),
            "target_hint": self.target_hint,
            "dependency_warnings": list(self.dependency_warnings),
            "warnings": list(self.warnings),
            "selected_variant": self.selected_variant,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScannedComponent":
        return cls(
            component_id=str(data.get("component_id") or ""),
            display_name=str(data.get("display_name") or ""),
            component_type=str(data.get("component_type") or ""),
            install_kind=str(data.get("install_kind") or ""),
            files=[ComponentFile.from_dict(item) for item in data.get("files", []) if isinstance(item, dict)],
            badges=[str(value) for value in data.get("badges", []) if value],
            target_hint=str(data.get("target_hint") or ""),
            dependency_warnings=[str(value) for value in data.get("dependency_warnings", []) if value],
            warnings=[str(value) for value in data.get("warnings", []) if value],
            selected_variant=str(data.get("selected_variant") or ""),
        )


@dataclass
class ScanResult:
    source_path: str
    source_kind: str
    display_name: str
    source_hash: str = ""
    source_paths: list[str] = field(default_factory=list)
    components: list[ScannedComponent] = field(default_factory=list)
    entries: list[ScanEntry] = field(default_factory=list)
    unsupported_files: list[str] = field(default_factory=list)
    unsafe_entries: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    ambiguous: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def component_count(self) -> int:
        return len(self.components)

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "source_kind": self.source_kind,
            "display_name": self.display_name,
            "source_hash": self.source_hash,
            "source_paths": list(self.source_paths),
            "components": [component.to_dict() for component in self.components],
            "entries": [entry.to_dict() for entry in self.entries],
            "unsupported_files": list(self.unsupported_files),
            "unsafe_entries": list(self.unsafe_entries),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "ambiguous": self.ambiguous,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScanResult":
        return cls(
            source_path=str(data.get("source_path") or ""),
            source_kind=str(data.get("source_kind") or ""),
            display_name=str(data.get("display_name") or ""),
            source_hash=str(data.get("source_hash") or ""),
            source_paths=[str(value) for value in data.get("source_paths", []) if value],
            components=[ScannedComponent.from_dict(item) for item in data.get("components", []) if isinstance(item, dict)],
            entries=[ScanEntry.from_dict(item) for item in data.get("entries", []) if isinstance(item, dict)],
            unsupported_files=[str(value) for value in data.get("unsupported_files", []) if value],
            unsafe_entries=[str(value) for value in data.get("unsafe_entries", []) if value],
            warnings=[str(value) for value in data.get("warnings", []) if value],
            errors=[str(value) for value in data.get("errors", []) if value],
            ambiguous=bool(data.get("ambiguous", False)),
        )
