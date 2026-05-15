from __future__ import annotations

from pathlib import Path

from s2_mod_manager.core.discovery import (
    discover_all,
    find_app_manifest,
    root_from_manifest,
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
