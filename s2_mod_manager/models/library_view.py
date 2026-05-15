from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScanSummary:
    source_count: int = 0
    component_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    ambiguous_count: int = 0
    imported_source_count: int = 0
    candidate_source_count: int = 0

    @property
    def text(self) -> str:
        return (
            f"{self.source_count} source(s), {self.component_count} component(s), "
            f"{self.warning_count + self.error_count} warning/error item(s)"
        )


@dataclass(frozen=True)
class LibraryDisplayItem:
    item_id: str
    display_name: str
    version_label: str
    description: str
    badges: list[str] = field(default_factory=list)
    status: str = ""
    enabled: bool = False
    warning: str = ""
    accent: str = "#38D6D6"
    state: str = "candidate"
    source_name: str = ""
    source_path: str = ""
    managed_path: str = ""
    component_id: str = ""
    source_id: str = ""
    component_type: str = ""
    install_kind: str = ""
    target_hint: str = ""
    file_count: int = 0
    files: list[str] = field(default_factory=list)
    dependency_warnings: list[str] = field(default_factory=list)
    source_warnings: list[str] = field(default_factory=list)
    review_policy_text: str = ""


@dataclass(frozen=True)
class LibraryViewState:
    library_items: list[LibraryDisplayItem] = field(default_factory=list)
    candidate_items: list[LibraryDisplayItem] = field(default_factory=list)
    summary: ScanSummary = field(default_factory=ScanSummary)

    @property
    def all_items(self) -> list[LibraryDisplayItem]:
        return list(self.library_items) + list(self.candidate_items)
