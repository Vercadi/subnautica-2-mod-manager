from __future__ import annotations

from pathlib import Path

from ..models.archive_info import ScanResult
from ..utils.json_io import read_json, write_json
from .archive_inspector import scan_source


class ScanCache:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "scan_cache.json"
        self.data = read_json(self.path)

    def scan_source(self, path: Path) -> ScanResult:
        key = _cache_key(path)
        cached = self.data.get(key)
        if isinstance(cached, dict):
            try:
                return ScanResult.from_dict(cached)
            except Exception:
                pass
        result = scan_source(path)
        self.data[key] = result.to_dict()
        write_json(self.path, self.data)
        return result

    def scan_inbox(self, inbox_dir: Path | None) -> list[ScanResult]:
        if inbox_dir is None or not inbox_dir.is_dir():
            return []
        return [
            self.scan_source(path)
            for path in sorted(inbox_dir.iterdir(), key=lambda item: item.name.casefold())
            if path.name.casefold() != "readme.md" and (path.is_file() or path.is_dir())
        ]


def _cache_key(path: Path) -> str:
    try:
        stat = path.stat()
        if path.is_dir():
            latest = max((child.stat().st_mtime_ns for child in path.rglob("*") if child.is_file()), default=stat.st_mtime_ns)
            count = sum(1 for child in path.rglob("*") if child.is_file())
            return f"dir:{path.resolve()}:{latest}:{count}"
        return f"file:{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}"
    except OSError:
        return f"missing:{path}"
