from __future__ import annotations

import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..models.archive_info import SUPPORTED_ARCHIVE_SUFFIXES


@dataclass(frozen=True)
class ArchiveEntryInfo:
    filename: str
    is_dir: bool
    file_size: int = 0


@runtime_checkable
class ArchiveReader(Protocol):
    def list_entries(self) -> list[ArchiveEntryInfo]: ...
    def read_file(self, entry_path: str) -> bytes: ...
    def close(self) -> None: ...


class ZipArchiveReader:
    def __init__(self, path: Path):
        self._archive = zipfile.ZipFile(path, "r")

    def list_entries(self) -> list[ArchiveEntryInfo]:
        return [
            ArchiveEntryInfo(info.filename.replace("\\", "/"), info.is_dir(), info.file_size)
            for info in self._archive.infolist()
        ]

    def read_file(self, entry_path: str) -> bytes:
        return self._archive.read(entry_path)

    def close(self) -> None:
        self._archive.close()


class SevenZipArchiveReader:
    def __init__(self, path: Path):
        import py7zr

        self._archive = py7zr.SevenZipFile(path, "r")
        self._entries: list[ArchiveEntryInfo] | None = None
        self._tmpdir_obj: tempfile.TemporaryDirectory | None = None
        self._tmpdir: Path | None = None

    def list_entries(self) -> list[ArchiveEntryInfo]:
        if self._entries is None:
            self._entries = [
                ArchiveEntryInfo(
                    entry.filename.replace("\\", "/"),
                    bool(entry.is_directory),
                    int(getattr(entry, "uncompressed", 0) or 0),
                )
                for entry in self._archive.list()
            ]
        return self._entries

    def read_file(self, entry_path: str) -> bytes:
        self._ensure_extracted()
        assert self._tmpdir is not None
        for candidate in (entry_path, entry_path.replace("/", "\\")):
            full = self._tmpdir / candidate
            if full.is_file():
                return full.read_bytes()
        raise KeyError(f"Entry not found in extracted 7z: {entry_path}")

    def close(self) -> None:
        try:
            self._archive.close()
        finally:
            if self._tmpdir_obj is not None:
                self._tmpdir_obj.cleanup()
                self._tmpdir_obj = None
                self._tmpdir = None

    def _ensure_extracted(self) -> None:
        if self._tmpdir is not None:
            return
        self._tmpdir_obj = tempfile.TemporaryDirectory(prefix="s2mm_7z_")
        self._tmpdir = Path(self._tmpdir_obj.name)
        self._archive.extractall(path=str(self._tmpdir))


class RarArchiveReader:
    def __init__(self, path: Path):
        import rarfile

        self._archive = rarfile.RarFile(str(path), "r")

    def list_entries(self) -> list[ArchiveEntryInfo]:
        return [
            ArchiveEntryInfo(info.filename.replace("\\", "/"), info.is_dir(), info.file_size)
            for info in self._archive.infolist()
        ]

    def read_file(self, entry_path: str) -> bytes:
        return self._archive.read(entry_path)

    def close(self) -> None:
        self._archive.close()


def open_archive(path: Path) -> ArchiveReader:
    suffix = path.suffix.casefold()
    if suffix == ".zip":
        return ZipArchiveReader(path)
    if suffix == ".7z":
        return SevenZipArchiveReader(path)
    if suffix == ".rar":
        return RarArchiveReader(path)
    raise ValueError(f"Unsupported archive format: {suffix}")


def is_supported_archive(path: Path) -> bool:
    return path.suffix.casefold() in SUPPORTED_ARCHIVE_SUFFIXES


def archive_support_status() -> dict[str, bool]:
    status = {".zip": True, ".7z": False, ".rar": False}
    try:
        import py7zr  # noqa: F401

        status[".7z"] = True
    except Exception:
        status[".7z"] = False
    try:
        import rarfile  # noqa: F401

        status[".rar"] = True
    except Exception:
        status[".rar"] = False
    return status
