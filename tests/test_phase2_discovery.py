from __future__ import annotations

from pathlib import Path

from s2_mod_manager.core.discovery import (
    discover_all,
    find_app_manifest,
    normalize_install_path,
    root_from_manifest,
    validate_install_path,
    validate_client_root,
)
from s2_mod_manager.core.settings_store import load_settings, save_settings
from s2_mod_manager.core.steam_manifest import parse_acf_text, read_app_manifest
from s2_mod_manager.core.version_info import parse_game_version_files
from s2_mod_manager.models.app_paths import S2AppPaths


def test_validate_client_root_accepts_s2_layout(tmp_path: Path) -> None:
    root = _fake_s2_install(tmp_path / "Subnautica2")
    assert validate_client_root(root)
    assert not validate_client_root(tmp_path / "missing")


def test_parse_and_read_steam_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "appmanifest_1962700.acf"
    manifest_path.write_text(_manifest_text(), encoding="utf-8")

    parsed = parse_acf_text(manifest_path.read_text(encoding="utf-8"))
    assert parsed["appid"] == "1962700"
    assert parsed["installdir"] == "Subnautica2"

    manifest = read_app_manifest(manifest_path, library_root=tmp_path.parent)
    assert manifest is not None
    assert manifest.appid == "1962700"
    assert manifest.buildid == "23165626"
    assert manifest.library_root == tmp_path.parent


def test_manifest_discovery_resolves_root(tmp_path: Path) -> None:
    steamapps = tmp_path / "steamapps"
    common = steamapps / "common"
    root = _fake_s2_install(common / "Subnautica2")
    manifest_path = steamapps / "appmanifest_1962700.acf"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(_manifest_text(), encoding="utf-8")

    manifest = find_app_manifest("1962700", [steamapps])
    assert manifest is not None
    assert root_from_manifest(manifest) == root


def test_discover_all_uses_known_valid_root(tmp_path: Path) -> None:
    root = _fake_s2_install(tmp_path / "Subnautica2")
    paths, messages = discover_all(extra_steamapps_dirs=[], known_client_root=root)
    assert paths.client_root == root
    assert paths.game_version.changelist == "113109"
    assert any("validated" in message.lower() for message in messages)


def test_manual_win64_layout_without_root_exe_validates_for_epic_style_install(tmp_path: Path) -> None:
    root = _fake_manual_win64_install(tmp_path / "Epic" / "Subnautica2", root_exe=False)

    validation = validate_install_path(root)

    assert validation.ok
    assert validation.layout is not None
    assert validation.layout.variant_label == "Manual/Epic Win64"
    assert validation.layout.shipping_exe == root / "Subnautica2" / "Binaries" / "Win64" / "Subnautica2-Win64-Shipping.exe"


def test_manual_path_normalizes_inner_project_and_win64_folder(tmp_path: Path) -> None:
    root = _fake_manual_win64_install(tmp_path / "Epic" / "Subnautica2", root_exe=False)

    inner = normalize_install_path(root / "Subnautica2")
    win64 = normalize_install_path(root / "Subnautica2" / "Binaries" / "Win64")

    assert inner is not None
    assert win64 is not None
    assert inner.client_root == root
    assert win64.client_root == root
    assert win64.binaries_dir.name == "Win64"


def test_gamepass_wingdk_layout_normalizes_project_and_binaries_folder(tmp_path: Path) -> None:
    root = _fake_gamepass_install(tmp_path / "XboxGames" / "Subnautica 2")

    project = normalize_install_path(root / "Content" / "Subnautica2")
    wingdk = normalize_install_path(root / "Content" / "Subnautica2" / "Binaries" / "WinGDK")

    assert project is not None
    assert wingdk is not None
    assert project.client_root == root
    assert wingdk.client_root == root
    assert wingdk.variant_label == "Game Pass WinGDK (experimental)"
    assert wingdk.gamepass_content_root == root / "Content"
    assert wingdk.ue4ss_runtime_root == root / "Content"
    assert wingdk.ue4ss_root == root / "Content" / "Subnautica2" / "Binaries" / "WinGDK" / "ue4ss"
    assert wingdk.ue4ss_mods == root / "Content" / "Subnautica2" / "Binaries" / "WinGDK" / "ue4ss" / "Mods"


def test_gamepass_content_folder_and_ue4ss_mods_folder_normalize_to_layout(tmp_path: Path) -> None:
    root = _fake_gamepass_install(tmp_path / "XboxGames" / "Subnautica 2")
    (root / "Content" / "ue4ss" / "Mods").mkdir(parents=True)

    content = normalize_install_path(root / "Content")
    mods = normalize_install_path(root / "Content" / "ue4ss" / "Mods")

    assert content is not None
    assert mods is not None
    assert content.client_root == root
    assert mods.client_root == root
    assert mods.ue4ss_mods == root / "Content" / "Subnautica2" / "Binaries" / "WinGDK" / "ue4ss" / "Mods"


def test_invalid_path_reports_missing_requirements_clearly(tmp_path: Path) -> None:
    selected = tmp_path / "NotS2"
    selected.mkdir()

    validation = validate_install_path(selected)

    assert not validation.ok
    assert "Missing expected layout item" in validation.message
    assert "Subnautica2/Binaries/Win64" in validation.message
    assert "Content/Subnautica2/Binaries/WinGDK" in validation.message


def test_version_parsing_reads_json_and_txt(tmp_path: Path) -> None:
    root = _fake_s2_install(tmp_path / "Subnautica2")
    version = parse_game_version_files(root / "version.json", root / "version.txt")
    assert version.changelist == "113109"
    assert version.build_number == "34"
    assert version.timestamp == "2026-05-10T04:15:22"
    assert "Build 34" in version.summary


def test_settings_roundtrip_preserves_paths_and_manifest(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    root = _fake_s2_install(tmp_path / "Subnautica2")
    paths = S2AppPaths(client_root=root, steamapps_dirs=[tmp_path / "steamapps"])

    save_settings(settings_path, paths)
    loaded = load_settings(settings_path)

    assert loaded.client_root == root
    assert loaded.steamapps_dirs == [tmp_path / "steamapps"]


def _fake_s2_install(root: Path) -> Path:
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True, exist_ok=True)
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True, exist_ok=True)
    (root / "Subnautica2.exe").write_bytes(b"exe")
    (root / "Subnautica2" / "Binaries" / "Win64" / "Subnautica2-Win64-Shipping.exe").write_bytes(b"shipping")
    (root / "version.json").write_text(
        """
{
  "branch": "//Project/SN2-Release-Hotfix-Live",
  "changelist": 113109,
  "build_number": 34,
  "build_server_label": "34_SHIPPING_RELEASEHOTFIXLIVE_CL-113109_B-13",
  "timestamp": "2026-05-10T04:15:22"
}
""".strip(),
        encoding="utf-8",
    )
    (root / "version.txt").write_text("113109 2026-05-10T04:15:22", encoding="utf-8")
    return root


def _fake_manual_win64_install(root: Path, *, root_exe: bool) -> Path:
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True, exist_ok=True)
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True, exist_ok=True)
    (root / "Subnautica2" / "Binaries" / "Win64" / "Subnautica2-Win64-Shipping.exe").write_bytes(b"shipping")
    if root_exe:
        (root / "Subnautica2.exe").write_bytes(b"exe")
    return root


def _fake_gamepass_install(root: Path) -> Path:
    project = root / "Content" / "Subnautica2"
    (project / "Binaries" / "WinGDK").mkdir(parents=True, exist_ok=True)
    (project / "Content" / "Paks").mkdir(parents=True, exist_ok=True)
    (project / "Binaries" / "WinGDK" / "Subnautica2-WinGDK-Shipping.exe").write_bytes(b"shipping")
    return root


def _manifest_text() -> str:
    return """
"AppState"
{
    "appid" "1962700"
    "name" "Subnautica 2"
    "installdir" "Subnautica2"
    "buildid" "23165626"
    "LastUpdated" "1778774947"
    "SizeOnDisk" "15671076247"
}
""".strip()
