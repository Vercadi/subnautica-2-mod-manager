from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..models.deployment import ACTION_BLOCKED, ACTION_CREATE, ACTION_DELETE, ACTION_OVERWRITE, DeploymentFileAction, DeploymentPlan
from ..models.manifest import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_REFUSED,
    STATUS_STARTED,
    DeployedFileRecord,
    InstallRecord,
)
from .archive_handler import open_archive
from .backup_store import BackupStore
from .manifest_store import ManifestStore


@dataclass(frozen=True)
class InstallResult:
    ok: bool
    record: InstallRecord


class Installer:
    def __init__(self, *, manifest_store: ManifestStore, backup_store: BackupStore):
        self.manifest_store = manifest_store
        self.backup_store = backup_store

    def apply(self, plan: DeploymentPlan, *, allow_real_apply: bool = False) -> InstallResult:
        record = InstallRecord(
            install_id=f"install_{uuid.uuid4().hex[:12]}",
            profile_id=plan.profile_id,
            profile_name=plan.profile_name,
            target_root=plan.target_root,
            status=STATUS_STARTED,
            warnings=list(plan.warnings),
        )
        self.manifest_store.add_or_update(record)

        refusal = _refusal_reason(plan, allow_real_apply=allow_real_apply)
        if refusal:
            record.errors.append(refusal)
            record.finish(STATUS_REFUSED)
            self.manifest_store.add_or_update(record)
            return InstallResult(False, record)

        executable_actions = [
            action
            for action in plan.actions
            if action.action in {ACTION_CREATE, ACTION_OVERWRITE, ACTION_DELETE}
        ]
        for action in executable_actions:
            try:
                deployed = self._execute_action(record, action)
            except Exception as exc:
                record.errors.append(f"{action.component_name}: {exc}")
                record.finish(STATUS_FAILED)
                self.manifest_store.add_or_update(record)
                return InstallResult(False, record)
            record.deployed_files.append(deployed)
            self.manifest_store.add_or_update(record)

        record.finish(STATUS_COMPLETED)
        self.manifest_store.add_or_update(record)
        return InstallResult(True, record)

    def _execute_action(self, record: InstallRecord, action: DeploymentFileAction) -> DeployedFileRecord:
        if action.target_path is None:
            raise FileNotFoundError("planned action has no target path")
        if action.action == ACTION_DELETE:
            backup = self.backup_store.backup_existing(
                action.target_path,
                install_id=record.install_id,
                component_id=action.component_id,
                target_root=record.target_root,
            )
            if backup is not None:
                record.backups.append(backup)
                self.manifest_store.add_or_update(record)
            if action.target_path.exists():
                action.target_path.unlink()
            return DeployedFileRecord(
                component_id=action.component_id,
                component_name=action.component_name,
                source_path=None,
                source_member=action.source_member,
                target_path=action.target_path,
                action=action.action,
                backup_id=backup.backup_id if backup else "",
            )
        source_bytes = _action_source_bytes(action)
        backup = self.backup_store.backup_existing(
            action.target_path,
            install_id=record.install_id,
            component_id=action.component_id,
            target_root=record.target_root,
        )
        if backup is not None:
            record.backups.append(backup)
            self.manifest_store.add_or_update(record)
        action.target_path.parent.mkdir(parents=True, exist_ok=True)
        action.target_path.write_bytes(source_bytes)
        return DeployedFileRecord(
            component_id=action.component_id,
            component_name=action.component_name,
            source_path=action.source_path,
            source_member=action.source_member,
            target_path=action.target_path,
            action=action.action,
            backup_id=backup.backup_id if backup else "",
        )


def _refusal_reason(plan: DeploymentPlan, *, allow_real_apply: bool) -> str:
    if plan.blocked:
        return "Refusing to apply a blocked deployment plan."
    if plan.dry_run:
        return "Refusing to apply a dry-run deployment plan."
    if plan.target_root is None:
        return "Refusing to apply without a target root."
    if not allow_real_apply and not is_fake_test_install(plan.target_root):
        return "Refusing to write to a non-test install without allow_real_apply=True."
    if any(action.action == ACTION_BLOCKED for action in plan.actions):
        return "Refusing to apply blocked file actions."
    return ""


def _action_source_bytes(action: DeploymentFileAction) -> bytes:
    if action.generated_content or (action.source_path is None and action.source_member.startswith("generated:")):
        return action.generated_content.encode("utf-8")
    if action.source_path is None:
        raise FileNotFoundError("planned action has no source path")
    return _read_source_bytes(action.source_path, action.source_member)


def is_fake_test_install(root: Path | None) -> bool:
    return bool(root and (root / ".s2mm_fake_install").is_file())


def _read_source_bytes(source_path: Path, source_member: str) -> bytes:
    if source_path.is_dir():
        member_path = _safe_member_path(source_path, source_member)
        if not member_path.is_file():
            raise FileNotFoundError(f"source member not found: {source_member}")
        return member_path.read_bytes()
    if source_path.is_file():
        reader = open_archive(source_path)
        try:
            return reader.read_file(source_member)
        finally:
            reader.close()
    raise FileNotFoundError(f"source path not found: {source_path}")


def _safe_member_path(root: Path, member: str) -> Path:
    parts = PurePosixPath(member.replace("\\", "/")).parts
    if not parts or ".." in parts:
        raise FileNotFoundError(f"unsafe source member: {member}")
    candidate = (root / Path(*parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise FileNotFoundError(f"unsafe source member: {member}") from exc
    return candidate
