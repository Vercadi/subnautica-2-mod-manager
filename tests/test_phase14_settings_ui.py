from __future__ import annotations

import zipfile
from pathlib import Path

from s2_mod_manager.core.archive_inspector import scan_inbox
from s2_mod_manager.core.settings_store import load_settings, save_settings
from s2_mod_manager.core.settings_workflow import (
    build_settings_view,
    settings_refresh_summary,
    update_inbox_path,
    update_manual_install_path,
)
from s2_mod_manager.models.app_paths import S2AppPaths


def test_settings_view_model_reports_paths_archive_support_and_safety(tmp_path: Path) -> None:
    root = _fake_s2_install(tmp_path / "Subnautica2")
    inbox = tmp_path / "Mods"
    inbox.mkdir()
    view = build_settings_view(
        S2AppPaths(client_root=root, archive_inbox_dir=inbox),
        data_dir=tmp_path / "data",
        library_dir=tmp_path / "data" / "library",
        backup_dir=tmp_path / "backups",
    )

    assert view.install_valid
    assert "Valid S2 install" in view.install_status_text
    assert ".zip: available" in view.archive_support_text
    assert "Real apply: enabled for non-blocked Preview & Apply plans" in view.safety.text
    assert "manifest-tracked managed files" in view.safety.text
    assert "preview-only" in view.safety.text


def test_invalid_manual_install_path_is_refused_without_corrupting_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    root = _fake_s2_install(tmp_path / "Subnautica2")
    current = S2AppPaths(client_root=root, archive_inbox_dir=tmp_path / "Mods")
    save_settings(settings_path, current)

    result = update_manual_install_path(
        settings_path,
        current,
        tmp_path / "not_s2",
        data_dir=tmp_path / "data",
        backup_dir=tmp_path / "backups",
    )
    loaded = load_settings(settings_path)

    assert not result.ok
    assert "Invalid Subnautica 2 install path refused" in result.message
    assert loaded.client_root == root


def test_valid_manual_install_path_persists(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    root = _fake_s2_install(tmp_path / "Subnautica2")
    current = S2AppPaths(archive_inbox_dir=tmp_path / "Mods")

    result = update_manual_install_path(
        settings_path,
        current,
        root,
        data_dir=tmp_path / "data",
        backup_dir=tmp_path / "backups",
    )
    loaded = load_settings(settings_path)

    assert result.ok
    assert loaded.client_root == root
    assert loaded.game_version.build_number == "34"


def test_inbox_path_update_persists_and_can_rescan(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    inbox = tmp_path / "New Mods"
    inbox.mkdir()
    _archive(inbox / "lights.zip", {"Lights/Lights_P.pak": b"pak"})
    current = S2AppPaths(client_root=_fake_s2_install(tmp_path / "Subnautica2"))

    result = update_inbox_path(
        settings_path,
        current,
        inbox,
        data_dir=tmp_path / "data",
        backup_dir=tmp_path / "backups",
    )
    scans = scan_inbox(result.paths.archive_inbox_dir)

    assert result.ok
    assert load_settings(settings_path).archive_inbox_dir == inbox
    assert len(scans) == 1
    assert scans[0].component_count == 1


def test_invalid_inbox_path_is_refused(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    inbox = tmp_path / "Mods"
    inbox.mkdir()
    current = S2AppPaths(archive_inbox_dir=inbox)
    save_settings(settings_path, current)

    result = update_inbox_path(
        settings_path,
        current,
        tmp_path / "missing",
        data_dir=tmp_path / "data",
        backup_dir=tmp_path / "backups",
    )

    assert not result.ok
    assert load_settings(settings_path).archive_inbox_dir == inbox


def test_settings_refresh_summary_text() -> None:
    result = type("Result", (), {"ok": True, "message": "Saved Mods inbox path", "discovery_messages": []})()

    text = settings_refresh_summary(result, 3)

    assert "Settings saved" in text
    assert "3 source(s)" in text


def _fake_s2_install(root: Path) -> Path:
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True, exist_ok=True)
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True, exist_ok=True)
    (root / "Subnautica2.exe").write_bytes(b"exe")
    (root / "Subnautica2" / "Binaries" / "Win64" / "Subnautica2-Win64-Shipping.exe").write_bytes(b"shipping")
    (root / "version.json").write_text(
        """
{
  "changelist": 113109,
  "build_number": 34,
  "timestamp": "2026-05-10T04:15:22"
}
""".strip(),
        encoding="utf-8",
    )
    return root


def _archive(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for member, data in members.items():
            archive.writestr(member, data)
    return path
