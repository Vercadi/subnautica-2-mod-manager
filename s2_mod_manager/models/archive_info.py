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


@dataclass(frozen=True)
class ComponentFile:
    source_path: str
    role: str = "file"
    target_hint: str = ""
    size: int = 0


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
