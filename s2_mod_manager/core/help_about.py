from __future__ import annotations

import json
from pathlib import Path

from .. import __app_name__, __version__
from ..models.app_paths import S2AppPaths
from ..models.help_about import FolderShortcut, HelpAboutView
from ..models.settings_view import SettingsSafetyState
from .archive_handler import archive_support_status
from .project_links import GITHUB_URL, ISSUES_URL, KOFI_URL, NEXUS_URL, PATREON_URL, RELEASES_URL


def build_help_about_view(
    *,
    paths: S2AppPaths,
    data_dir: Path,
    library_dir: Path,
    backup_dir: Path,
    log_dir: Path,
    docs_dir: Path,
    support_report: str,
    release_metadata_path: Path | None = None,
) -> HelpAboutView:
    return HelpAboutView(
        app_name=__app_name__,
        app_version=__version__,
        build_metadata=_metadata_summary(release_metadata_path),
        safety_text=SettingsSafetyState().text,
        archive_support_text=_archive_support_text(),
        support_report=support_report,
        github_url=GITHUB_URL,
        releases_url=RELEASES_URL,
        nexus_url=NEXUS_URL,
        issues_url=ISSUES_URL,
        patreon_url=PATREON_URL,
        kofi_url=KOFI_URL,
        shortcuts=[
            _shortcut("Game Install", paths.client_root),
            _shortcut("Mods Inbox", paths.archive_inbox_dir),
            _shortcut("Manager Data", data_dir),
            _shortcut("Library", library_dir),
            _shortcut("Backups", backup_dir),
            _shortcut("Logs", log_dir),
            _shortcut("Docs", docs_dir),
        ],
    )


def _shortcut(label: str, path: Path | None) -> FolderShortcut:
    return FolderShortcut(label=label, path=path, available=bool(path and path.exists()))


def _archive_support_text() -> str:
    return ", ".join(
        f"{suffix}: {'available' if available else 'missing'}"
        for suffix, available in sorted(archive_support_status().items())
    )


def _metadata_summary(path: Path | None) -> str:
    if path is None or not path.is_file():
        return "Release metadata not found; source mode or unpackaged build."
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "Release metadata unreadable."
    version = data.get("version") or __version__
    built_at = data.get("built_at") or data.get("generated_at") or ""
    return " / ".join(str(value) for value in (version, built_at) if value)
