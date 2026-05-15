from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppDirs:
    root_dir: Path
    data_dir: Path
    backup_dir: Path
    log_dir: Path
    assets_dir: Path
    frozen: bool = False

    @property
    def library_dir(self) -> Path:
        return self.data_dir / "library"

    @property
    def library_sources_dir(self) -> Path:
        return self.library_dir / "sources"

    @property
    def runtime_dirs(self) -> tuple[Path, ...]:
        return (
            self.data_dir,
            self.backup_dir,
            self.log_dir,
            self.library_dir,
            self.library_sources_dir,
        )


def resolve_app_dirs(
    *,
    frozen: bool | None = None,
    executable: Path | None = None,
    meipass: Path | None = None,
    source_root: Path | None = None,
    localappdata: Path | None = None,
) -> AppDirs:
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if is_frozen:
        base_root = localappdata or Path(os.environ.get("LOCALAPPDATA", Path.home()))
        base = Path(base_root) / "Subnautica2ModManager"
        executable_path = Path(executable) if executable else Path(sys.executable).resolve()
        bundle_root = Path(meipass) if meipass else Path(getattr(sys, "_MEIPASS", executable_path.parent))
        assets_dir = bundle_root / "assets"
    else:
        base = Path(source_root) if source_root else Path(__file__).resolve().parents[2]
        assets_dir = base / "assets"

    data_dir = base / "data"
    backup_dir = base / "backups"
    return AppDirs(
        root_dir=base,
        data_dir=data_dir,
        backup_dir=backup_dir,
        log_dir=data_dir / "logs",
        assets_dir=assets_dir,
        frozen=is_frozen,
    )


def ensure_app_dirs(dirs: AppDirs) -> None:
    for path in dirs.runtime_dirs:
        path.mkdir(parents=True, exist_ok=True)
    if not dirs.frozen:
        dirs.assets_dir.mkdir(parents=True, exist_ok=True)
