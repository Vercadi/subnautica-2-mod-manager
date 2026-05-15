from __future__ import annotations

from pathlib import Path

from ..models.manifest import InstallRecord, ManifestState
from ..utils.json_io import read_json, write_json


class ManifestStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.manifest_path = data_dir / "install_manifest.json"
        self.state = ManifestState.from_dict(read_json(self.manifest_path))

    def list_installs(self) -> list[InstallRecord]:
        return list(self.state.installs)

    def add_or_update(self, record: InstallRecord) -> None:
        for index, existing in enumerate(self.state.installs):
            if existing.install_id == record.install_id:
                self.state.installs[index] = record
                self.save()
                return
        self.state.installs.append(record)
        self.save()

    def save(self) -> None:
        write_json(self.manifest_path, self.state.to_dict())
