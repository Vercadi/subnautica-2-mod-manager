from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_STARTED = "started"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_REFUSED = "refused"
STATUS_UNINSTALLED = "uninstalled"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _path_to_str(path: Path | None) -> str:
    return str(path) if path else ""


def _path_from_str(value: str | None) -> Path | None:
    return Path(value) if value else None


@dataclass
class BackupRecord:
    backup_id: str
    original_path: Path
    backup_path: Path
    component_id: str
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "original_path": _path_to_str(self.original_path),
            "backup_path": _path_to_str(self.backup_path),
            "component_id": self.component_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupRecord":
        return cls(
            backup_id=str(data.get("backup_id") or ""),
            original_path=Path(str(data.get("original_path") or "")),
            backup_path=Path(str(data.get("backup_path") or "")),
            component_id=str(data.get("component_id") or ""),
            created_at=str(data.get("created_at") or utc_now_iso()),
        )


@dataclass
class DeployedFileRecord:
    component_id: str
    component_name: str
    source_path: Path | None
    source_member: str
    target_path: Path
    action: str
    backup_id: str = ""
    deployed_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "source_path": _path_to_str(self.source_path),
            "source_member": self.source_member,
            "target_path": _path_to_str(self.target_path),
            "action": self.action,
            "backup_id": self.backup_id,
            "deployed_at": self.deployed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeployedFileRecord":
        target_path = _path_from_str(data.get("target_path"))
        return cls(
            component_id=str(data.get("component_id") or ""),
            component_name=str(data.get("component_name") or ""),
            source_path=_path_from_str(data.get("source_path")),
            source_member=str(data.get("source_member") or ""),
            target_path=target_path or Path(),
            action=str(data.get("action") or ""),
            backup_id=str(data.get("backup_id") or ""),
            deployed_at=str(data.get("deployed_at") or utc_now_iso()),
        )


@dataclass
class InstallRecord:
    install_id: str
    profile_id: str
    profile_name: str
    target_root: Path | None
    status: str = STATUS_STARTED
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str = ""
    deployed_files: list[DeployedFileRecord] = field(default_factory=list)
    backups: list[BackupRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def finish(self, status: str) -> None:
        self.status = status
        self.finished_at = utc_now_iso()

    def to_dict(self) -> dict[str, Any]:
        return {
            "install_id": self.install_id,
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "target_root": _path_to_str(self.target_root),
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "deployed_files": [record.to_dict() for record in self.deployed_files],
            "backups": [record.to_dict() for record in self.backups],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstallRecord":
        return cls(
            install_id=str(data.get("install_id") or ""),
            profile_id=str(data.get("profile_id") or ""),
            profile_name=str(data.get("profile_name") or ""),
            target_root=_path_from_str(data.get("target_root")),
            status=str(data.get("status") or STATUS_STARTED),
            started_at=str(data.get("started_at") or utc_now_iso()),
            finished_at=str(data.get("finished_at") or ""),
            deployed_files=[
                DeployedFileRecord.from_dict(item)
                for item in data.get("deployed_files", [])
                if isinstance(item, dict)
            ],
            backups=[
                BackupRecord.from_dict(item)
                for item in data.get("backups", [])
                if isinstance(item, dict)
            ],
            errors=[str(value) for value in data.get("errors", []) if value],
            warnings=[str(value) for value in data.get("warnings", []) if value],
        )


@dataclass
class ManifestState:
    installs: list[InstallRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"installs": [record.to_dict() for record in self.installs]}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ManifestState":
        if not isinstance(data, dict):
            return cls()
        return cls(
            installs=[
                InstallRecord.from_dict(item)
                for item in data.get("installs", [])
                if isinstance(item, dict)
            ]
        )
