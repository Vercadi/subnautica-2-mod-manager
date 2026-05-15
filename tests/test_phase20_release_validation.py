from __future__ import annotations

import json
from pathlib import Path

import pytest

from s2_mod_manager import __version__


def test_release_checklist_documents_final_manual_checks() -> None:
    root = Path(__file__).resolve().parents[1]
    checklist = (root / "docs" / "release-checklist.md").read_text(encoding="utf-8")
    validation = (root / "docs" / "phase20-clean-release-validation.md").read_text(encoding="utf-8")

    assert "Clean Launch" in checklist
    assert "Fake-Install Execution" in checklist
    assert "real S2 install folders were not modified" in checklist
    assert "Windows security note" in checklist
    assert "36 file(s)" in validation
    assert "No real S2 install write" in validation


def test_release_docs_include_antivirus_and_support_guidance() -> None:
    root = Path(__file__).resolve().parents[1]
    nexus = (root / "docs" / "nexus-release-guide.md").read_text(encoding="utf-8")
    packaging = (root / "PACKAGING.md").read_text(encoding="utf-8")

    assert "PyInstaller" in nexus
    assert "administrator rights" in nexus
    assert "Support Report Workflow" in nexus
    assert "unsigned PyInstaller bundle" in packaging
    assert "docs\\release-checklist.md" in packaging


def test_portable_dist_contains_required_release_files_when_built() -> None:
    root = Path(__file__).resolve().parents[1]
    dist = root / "dist" / "Subnautica2ModManager"
    if not dist.exists():
        pytest.skip("portable dist has not been built")
    metadata_path = dist / "release-metadata.json"
    if not metadata_path.is_file():
        pytest.skip("portable dist is incomplete")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("version") != __version__:
        pytest.skip("portable dist is stale")

    required = [
        "Subnautica2ModManager.exe",
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "PRIVACY.md",
        "PACKAGING.md",
        "release-metadata.json",
        "assets/app.ico",
        "assets/app_icon.png",
        "docs/nexus-release-guide.md",
        "docs/release-checklist.md",
        "docs/phase20-clean-release-validation.md",
    ]
    for relative in required:
        assert (dist / relative).is_file(), relative
    assert (dist / "_internal").is_dir()
    assert metadata["version"] == __version__


def test_build_script_copies_docs_and_release_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    script = (root / "scripts" / "build_portable.ps1").read_text(encoding="utf-8")

    assert 'Copy-Item -LiteralPath ".\\docs"' in script
    assert "release-metadata.json" in script
    assert "write_release_metadata" in script
