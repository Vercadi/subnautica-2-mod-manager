from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

import pytest

from s2_mod_manager import __version__


ROOT = Path(__file__).resolve().parents[1]


def test_nexus_release_notes_cover_release_blockers() -> None:
    notes = (ROOT / "docs" / "release-notes-v0.1.0.md").read_text(encoding="utf-8")

    assert "real apply" in notes.lower()
    assert "destructive recovery" in notes.lower()
    assert "Supported Mod Shapes" in notes
    assert "Review-Required Shapes" in notes
    assert "SN2P" in notes
    assert "Support Report" in notes
    assert "PyInstaller" in notes


def test_package_release_script_generates_zip_and_hashes() -> None:
    script = (ROOT / "scripts" / "package_release.ps1").read_text(encoding="utf-8")

    assert "CreateFromDirectory" in script
    assert "Get-FileHash" in script
    assert "SHA256SUMS.txt" in script
    assert "release-metadata.json" in script
    assert "release-notes-v0.1.0.md" in script
    assert "forbidden local/build content" in script


def _latest_release_zip() -> Path | None:
    release_dir = ROOT / "dist" / "release"
    if not release_dir.exists():
        return None
    zips = sorted(release_dir.glob("Subnautica2ModManager-*-portable.zip"), key=lambda path: path.stat().st_mtime)
    return zips[-1] if zips else None


def test_release_zip_contents_are_clean_when_built() -> None:
    zip_path = _latest_release_zip()
    if zip_path is None:
        pytest.skip("release zip has not been built")

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        metadata_names = [name for name in names if name.endswith("/release-metadata.json")]
        if not metadata_names:
            pytest.skip("release zip is incomplete")
        metadata = json.loads(archive.read(metadata_names[0]).decode("utf-8"))
        if metadata.get("version") != __version__:
            pytest.skip("release zip is stale")

        required = {
            "Subnautica2ModManager/Subnautica2ModManager.exe",
            "Subnautica2ModManager/README.md",
            "Subnautica2ModManager/CHANGELOG.md",
            "Subnautica2ModManager/LICENSE",
            "Subnautica2ModManager/PRIVACY.md",
            "Subnautica2ModManager/PACKAGING.md",
            "Subnautica2ModManager/release-metadata.json",
            "Subnautica2ModManager/assets/app.ico",
            "Subnautica2ModManager/assets/app_icon.png",
            "Subnautica2ModManager/docs/nexus-release-guide.md",
            "Subnautica2ModManager/docs/release-checklist.md",
            "Subnautica2ModManager/docs/release-notes-v0.1.0.md",
        }
        assert required.issubset(set(names))

        forbidden_parts = {"build", "data", "backups", "logs", ".pytest_cache", "__pycache__", "Mods"}
        bad = []
        for name in names:
            parts = set(PurePosixPath(name).parts)
            if parts & forbidden_parts or name.endswith(".log"):
                bad.append(name)
        assert bad == []


def test_release_hashes_match_artifacts_when_built() -> None:
    zip_path = _latest_release_zip()
    sums_path = ROOT / "dist" / "release" / "SHA256SUMS.txt"
    exe_path = ROOT / "dist" / "Subnautica2ModManager" / "Subnautica2ModManager.exe"
    if zip_path is None or not sums_path.is_file() or not exe_path.is_file():
        pytest.skip("release artifacts have not been built")

    sums = sums_path.read_text(encoding="utf-8").lower()
    zip_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    exe_hash = hashlib.sha256(exe_path.read_bytes()).hexdigest()

    assert zip_hash in sums
    assert exe_hash in sums
    assert zip_path.name.lower() in sums
    assert "subnautica2modmanager/subnautica2modmanager.exe" in sums
