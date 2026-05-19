from __future__ import annotations

import argparse
import os
import tempfile
import zipfile
from pathlib import Path


def make_release_zip(source_dir: Path, output_zip: Path, *, root_name: str) -> None:
    source_dir = source_dir.resolve()
    output_zip = output_zip.resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source_dir}")

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip", dir=output_zip.parent) as temp:
        temp_path = Path(temp.name)

    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            _write_directory_entry(archive, f"{root_name}/")
            directories: set[str] = {f"{root_name}/"}
            for path in sorted(source_dir.rglob("*"), key=lambda item: item.relative_to(source_dir).as_posix().casefold()):
                rel = path.relative_to(source_dir)
                arcname = f"{root_name}/{rel.as_posix()}"
                if path.is_dir():
                    if not arcname.endswith("/"):
                        arcname += "/"
                    if arcname not in directories:
                        _write_directory_entry(archive, arcname)
                        directories.add(arcname)
                    continue

                parent = str(Path(arcname).parent).replace("\\", "/")
                if parent and parent != ".":
                    current = ""
                    for part in parent.split("/"):
                        current = f"{current}{part}/"
                        if current not in directories:
                            _write_directory_entry(archive, current)
                            directories.add(current)
                _write_file_entry(archive, path, arcname)
        os.replace(temp_path, output_zip)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _write_directory_entry(archive: zipfile.ZipFile, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname)
    info.create_system = 3
    info.external_attr = 0o755 << 16
    archive.writestr(info, b"")


def _write_file_entry(archive: zipfile.ZipFile, source: Path, arcname: str) -> None:
    stat = source.stat()
    info = zipfile.ZipInfo(arcname)
    info.create_system = 3
    info.date_time = _zip_date_time(stat.st_mtime)
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    with source.open("rb") as handle:
        archive.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _zip_date_time(timestamp: float) -> tuple[int, int, int, int, int, int]:
    import time

    year, month, day, hour, minute, second, *_ = time.localtime(timestamp)
    return max(year, 1980), month, day, hour, minute, second


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a portable release zip with explicit directory entries.")
    parser.add_argument("--source", required=True, help="Portable dist folder to zip.")
    parser.add_argument("--output", required=True, help="Output zip path.")
    parser.add_argument("--root-name", default="Subnautica2ModManager", help="Root directory name inside the zip.")
    args = parser.parse_args()
    make_release_zip(Path(args.source), Path(args.output), root_name=args.root_name)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
