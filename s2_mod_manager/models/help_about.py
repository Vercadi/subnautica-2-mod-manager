from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FolderShortcut:
    label: str
    path: Path | None
    available: bool = False

    @property
    def status_text(self) -> str:
        if self.available and self.path:
            return str(self.path)
        return "not available"


@dataclass(frozen=True)
class HelpAboutView:
    app_name: str
    app_version: str
    build_metadata: str
    safety_text: str
    archive_support_text: str
    support_report: str
    github_url: str
    releases_url: str
    nexus_url: str
    issues_url: str
    patreon_url: str = ""
    kofi_url: str = ""
    shortcuts: list[FolderShortcut] = field(default_factory=list)

    @property
    def summary_text(self) -> str:
        return f"Help/About: {self.app_name} {self.app_version}; {len(self.shortcuts)} folder shortcut(s)."
