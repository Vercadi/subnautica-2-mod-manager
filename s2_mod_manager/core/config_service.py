from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from ..models.config_file import (
    CONFIG_EDIT_SIZE_LIMIT,
    CONFIG_PREVIEW_SIZE_LIMIT,
    EDITABLE_CONFIG_EXTENSIONS,
    ConfigEditResult,
    ConfigFileInfo,
)
from ..models.manifest import STATUS_UNINSTALLED, InstallRecord
from .archive_handler import open_archive
from .backup_store import BackupStore
from .manifest_store import ManifestStore


class ConfigService:
    """Config editor for manager-installed files only."""

    def __init__(self, manifest_store: ManifestStore, backup_store: BackupStore):
        self.manifest_store = manifest_store
        self.backup_store = backup_store

    def list_component_configs(self, component_id: str) -> list[ConfigFileInfo]:
        if not component_id:
            return []
        configs: list[ConfigFileInfo] = []
        seen: set[Path] = set()
        for record in self._active_records():
            for deployed in record.deployed_files:
                if deployed.component_id != component_id or deployed.action == "delete":
                    continue
                target = deployed.target_path
                if not target or target in seen or not target.is_file():
                    continue
                seen.add(target)
                suffix = target.suffix.casefold()
                if suffix not in EDITABLE_CONFIG_EXTENSIONS:
                    continue
                size = _safe_size(target)
                editable = size <= CONFIG_EDIT_SIZE_LIMIT
                reason = "" if editable else "File is too large for the built-in editor; use Open Folder."
                configs.append(
                    ConfigFileInfo(
                        component_id=deployed.component_id,
                        component_name=deployed.component_name,
                        relative_path=_relative_display(target, record.target_root),
                        installed_path=target,
                        source_path=deployed.source_path,
                        source_member=deployed.source_member,
                        extension=suffix,
                        size_bytes=size,
                        editable=editable,
                        reason=reason,
                        has_backup=bool(deployed.backup_id),
                    )
                )
        return sorted(configs, key=lambda item: item.relative_path.casefold())

    def read_config(self, info: ConfigFileInfo) -> tuple[bool, str]:
        if not info.installed_path.is_file():
            return False, "Installed config file was not found."
        if info.size_bytes > CONFIG_PREVIEW_SIZE_LIMIT:
            return False, "Config file is too large to preview safely."
        try:
            return True, info.installed_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return False, f"Could not read config: {exc}"

    def save_config(self, info: ConfigFileInfo, text: str) -> ConfigEditResult:
        if not info.editable:
            return ConfigEditResult(False, info.reason or "Config file is not editable.")
        if not info.installed_path.is_file():
            return ConfigEditResult(False, "Installed config file was not found.")
        encoded = text.encode("utf-8")
        if len(encoded) > CONFIG_EDIT_SIZE_LIMIT:
            return ConfigEditResult(False, "Edited config is too large for the built-in editor.")
        json_error = _json_validation_error(info, text)
        if json_error:
            return ConfigEditResult(False, json_error)
        backup_id = ""
        try:
            backup = self.backup_store.backup_existing(
                info.installed_path,
                install_id="config_edit",
                component_id=info.component_id,
                target_root=_target_root_for(info, self._active_records()),
            )
            if backup is not None:
                backup_id = backup.backup_id
            info.installed_path.write_text(text, encoding="utf-8", newline="")
        except OSError as exc:
            return ConfigEditResult(False, f"Could not save config: {exc}")
        return ConfigEditResult(True, "Saved to installed mod config.", backup_id=backup_id)

    def restore_original(self, info: ConfigFileInfo) -> ConfigEditResult:
        if info.source_path is None or not info.source_member:
            return ConfigEditResult(False, "Original imported config source is not available.")
        try:
            original = _read_source_bytes(info.source_path, info.source_member)
        except Exception as exc:
            return ConfigEditResult(False, f"Could not read imported original: {exc}")
        backup_id = ""
        try:
            backup = self.backup_store.backup_existing(
                info.installed_path,
                install_id="config_restore",
                component_id=info.component_id,
                target_root=_target_root_for(info, self._active_records()),
            )
            if backup is not None:
                backup_id = backup.backup_id
            info.installed_path.parent.mkdir(parents=True, exist_ok=True)
            info.installed_path.write_bytes(original)
        except OSError as exc:
            return ConfigEditResult(False, f"Could not restore original config: {exc}")
        return ConfigEditResult(True, "Restored original config from manager library.", backup_id=backup_id)

    def _active_records(self) -> list[InstallRecord]:
        return [record for record in self.manifest_store.list_installs() if record.status != STATUS_UNINSTALLED]


def _json_validation_error(info: ConfigFileInfo, text: str) -> str:
    if info.extension != ".json":
        return ""
    try:
        json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        return f"JSON is invalid: line {exc.lineno}, column {exc.colno}: {exc.msg}"
    return ""


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _relative_display(path: Path, target_root: Path | None) -> str:
    if target_root is not None:
        try:
            return path.resolve().relative_to(target_root.resolve()).as_posix()
        except (OSError, ValueError):
            pass
    return path.name


def _target_root_for(info: ConfigFileInfo, records: list[InstallRecord]) -> Path | None:
    for record in records:
        for deployed in record.deployed_files:
            if deployed.target_path == info.installed_path:
                return record.target_root
    return None


def _read_source_bytes(source_path: Path, source_member: str) -> bytes:
    if source_path.is_dir():
        member_path = _safe_member_path(source_path, source_member)
        return member_path.read_bytes()
    reader = open_archive(source_path)
    try:
        return reader.read_file(source_member)
    finally:
        reader.close()


def _safe_member_path(root: Path, member: str) -> Path:
    parts = PurePosixPath(member.replace("\\", "/")).parts
    if not parts or ".." in parts:
        raise FileNotFoundError(f"unsafe source member: {member}")
    candidate = (root / Path(*parts)).resolve()
    candidate.relative_to(root.resolve())
    if not candidate.is_file():
        raise FileNotFoundError(f"source member not found: {member}")
    return candidate
