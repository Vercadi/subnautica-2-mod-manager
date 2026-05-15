from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .app_paths import S2AppPaths


@dataclass
class AppRuntimeState:
    paths: S2AppPaths
    settings_path: Path
    discovery_messages: list[str] = field(default_factory=list)

    @property
    def install_detected(self) -> bool:
        return self.paths.client_root is not None
