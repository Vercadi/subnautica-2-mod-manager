from __future__ import annotations

import os
from pathlib import Path

from .. import __version__
from ..models.app_paths import S2AppPaths
from ..models.deployment import DeploymentPlan
from ..models.diagnostics import DiagnosticsReport
from ..models.recovery import RecoverySummary
from .archive_handler import archive_support_status
from .library_store import LibraryStore
from .manifest_store import ManifestStore
from .profile_store import ProfileStore


def collect_diagnostics(
    *,
    paths: S2AppPaths,
    data_dir: Path,
    library_store: LibraryStore,
    profile_store: ProfileStore,
    manifest_store: ManifestStore,
    deployment_plan: DeploymentPlan | None,
    recovery_summary: RecoverySummary,
    log_path: Path | None,
    home: Path | None = None,
) -> DiagnosticsReport:
    profiles = profile_store.list_profiles()
    active = profile_store.active_profile()
    manifest_installs = manifest_store.list_installs()
    backup_count = sum(len(record.backups) for record in manifest_installs)
    return DiagnosticsReport(
        app_version=__version__,
        install_detected=paths.client_root is not None,
        install_root=redact_path(paths.client_root, home=home) if paths.client_root else "not configured",
        build_summary=paths.build_summary,
        steam_manifest_status=_manifest_status(paths),
        archive_support=archive_support_status(),
        library_source_count=len(library_store.list_sources()),
        library_component_count=len(library_store.list_components()),
        profile_count=len(profiles),
        active_profile_name=active.name,
        active_loadout_count=len(active.entries),
        deployment_summary=deployment_plan.summary_text if deployment_plan else "not available",
        recovery_summary=recovery_summary.text,
        manifest_install_count=len(manifest_installs),
        backup_count=backup_count,
        ue4ss_runtime_state=_ue4ss_runtime_state(paths),
        app_data_dir=redact_path(data_dir, home=home),
        log_excerpt=read_log_excerpt(log_path, line_limit=25, home=home),
    )


def redact_path(path: Path | str | None, *, home: Path | None = None, tail_parts: int = 4) -> str:
    if path is None:
        return ""
    raw = str(path)
    if not raw:
        return ""
    normalized = Path(raw)
    home = home or Path.home()
    home_text = str(home)
    lowered_raw = raw.casefold()
    lowered_home = home_text.casefold()
    if lowered_raw == lowered_home or lowered_raw.startswith(lowered_home.rstrip("\\/").casefold() + os.sep.casefold()):
        tail = _tail_after_prefix(raw, home_text)
        return _join_redacted("<USER_HOME>", tail)

    parts = _split_parts(raw)
    lowered_parts = [part.casefold() for part in parts]
    for marker in ("users", "documents and settings"):
        if marker in lowered_parts:
            index = lowered_parts.index(marker)
            tail = parts[index + 2 :]
            return _join_redacted("<USER_HOME>", tail)

    if len(parts) > tail_parts + 1:
        prefix = parts[0]
        tail = parts[-tail_parts:]
        return _join_redacted(prefix, tail)
    return raw


def read_log_excerpt(log_path: Path | None, *, line_limit: int = 25, home: Path | None = None) -> list[str]:
    if log_path is None or not log_path.is_file():
        return []
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return [_redact_text(line, home=home) for line in lines[-line_limit:]]


def _manifest_status(paths: S2AppPaths) -> str:
    manifest = paths.client_manifest
    if manifest is None:
        return "not found"
    bits = [f"appid={manifest.appid}"]
    if manifest.buildid:
        bits.append(f"buildid={manifest.buildid}")
    if manifest.manifest_path:
        bits.append(f"path={redact_path(manifest.manifest_path)}")
    return ", ".join(bits)


def _ue4ss_runtime_state(paths: S2AppPaths) -> str:
    win64 = paths.win64
    ue4ss_root = paths.ue4ss_root
    if win64 is None:
        return "install not configured"
    markers = [
        win64 / "UE4SS.dll",
        win64 / "dwmapi.dll",
        win64 / "xinput1_3.dll",
        ue4ss_root / "UE4SS.dll" if ue4ss_root else None,
    ]
    present = [path.name for path in markers if path is not None and path.exists()]
    if present:
        return "present: " + ", ".join(sorted(set(present)))
    return "not detected"


def _redact_text(text: str, *, home: Path | None) -> str:
    if "savegames" in text.casefold():
        return "[save path omitted]"
    home = home or Path.home()
    redacted = text.replace(str(home), "<USER_HOME>")
    parts = _split_parts(str(home))
    if len(parts) >= 2:
        marker = "\\".join(parts[-2:])
        redacted = redacted.replace(marker, "<USER_HOME>")
        redacted = redacted.replace(marker.replace("\\", "/"), "<USER_HOME>")
    return redacted


def _tail_after_prefix(value: str, prefix: str) -> list[str]:
    tail = value[len(prefix) :].lstrip("\\/")
    return _split_parts(tail)


def _split_parts(value: str) -> list[str]:
    value = value.replace("/", "\\")
    return [part for part in value.split("\\") if part]


def _join_redacted(prefix: str, tail: list[str]) -> str:
    if not tail:
        return prefix
    return prefix.rstrip("\\/") + "\\" + "\\".join(tail)
