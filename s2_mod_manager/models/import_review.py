from __future__ import annotations

from dataclasses import dataclass, field

from .archive_info import ScanResult


@dataclass(frozen=True)
class ImportComponentReview:
    component_id: str
    display_name: str
    component_type: str
    install_kind: str
    badges: list[str] = field(default_factory=list)
    file_count: int = 0
    target_hint: str = ""
    warnings: list[str] = field(default_factory=list)
    review_policy_text: str = ""
    selected: bool = True

    @property
    def status_text(self) -> str:
        bits = [self.component_type.replace("_", " ")]
        if self.file_count:
            bits.append(f"{self.file_count} file(s)")
        if self.target_hint:
            bits.append(self.target_hint)
        if self.review_policy_text:
            bits.append("review required")
        return " | ".join(bits)


@dataclass(frozen=True)
class ImportSourceReview:
    source_key: str
    display_name: str
    source_path: str
    source_kind: str
    source_hash: str = ""
    already_imported: bool = False
    importable: bool = False
    ambiguous: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    unsupported_files: list[str] = field(default_factory=list)
    unsafe_entries: list[str] = field(default_factory=list)
    components: list[ImportComponentReview] = field(default_factory=list)
    selected: bool = True

    @property
    def issue_count(self) -> int:
        return len(self.warnings) + len(self.errors) + len(self.unsupported_files) + len(self.unsafe_entries)

    @property
    def status_text(self) -> str:
        if self.already_imported:
            return "Already imported"
        if not self.importable:
            return "Not importable"
        if self.ambiguous:
            return "Review required"
        if self.issue_count:
            return f"{self.issue_count} issue(s)"
        return "Ready"


@dataclass(frozen=True)
class ImportReview:
    sources: list[ImportSourceReview] = field(default_factory=list)
    scans: list[ScanResult] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def component_count(self) -> int:
        return sum(len(source.components) for source in self.sources)

    @property
    def importable_source_count(self) -> int:
        return sum(1 for source in self.sources if source.importable and not source.already_imported)

    @property
    def selected_component_count(self) -> int:
        return sum(
            1
            for source in self.sources
            if source.selected and source.importable and not source.already_imported
            for component in source.components
            if component.selected
        )

    @property
    def warning_count(self) -> int:
        return sum(source.issue_count for source in self.sources)

    @property
    def summary_text(self) -> str:
        return (
            f"{self.source_count} source(s), {self.component_count} component(s), "
            f"{self.importable_source_count} importable, {self.warning_count} issue(s)"
        )


@dataclass(frozen=True)
class ImportSelection:
    selected_sources: dict[str, set[str]] = field(default_factory=dict)

    def component_ids_for_source(self, source_key: str) -> set[str]:
        return set(self.selected_sources.get(source_key, set()))
