from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from s2_mod_manager import __app_name__, __version__
from s2_mod_manager.core.app_dirs import ensure_app_dirs, resolve_app_dirs
from s2_mod_manager.core.first_run import prepare_first_run_state
from s2_mod_manager.core.release_metadata import build_release_metadata, write_release_metadata
from s2_mod_manager.core.settings_store import load_settings, save_settings
from s2_mod_manager.models.app_paths import S2AppPaths


def test_source_app_dirs_create_runtime_and_assets_dirs(tmp_path: Path) -> None:
    dirs = resolve_app_dirs(frozen=False, source_root=tmp_path)

    ensure_app_dirs(dirs)

    assert dirs.root_dir == tmp_path
    assert dirs.data_dir.is_dir()
    assert dirs.log_dir.is_dir()
    assert dirs.backup_dir.is_dir()
    assert dirs.library_dir.is_dir()
    assert dirs.library_sources_dir.is_dir()
    assert dirs.assets_dir.is_dir()


def test_frozen_app_dirs_use_localappdata_and_bundle_assets(tmp_path: Path) -> None:
    localappdata = tmp_path / "LocalAppData"
    bundle = tmp_path / "Bundle"
    dirs = resolve_app_dirs(
        frozen=True,
        executable=bundle / "Subnautica2ModManager.exe",
        meipass=bundle / "_internal",
        localappdata=localappdata,
    )

    ensure_app_dirs(dirs)

    assert dirs.frozen
    assert dirs.root_dir == localappdata / "Subnautica2ModManager"
    assert dirs.assets_dir == bundle / "_internal" / "assets"
    assert dirs.data_dir.is_dir()
    assert dirs.library_sources_dir.is_dir()
    assert not dirs.assets_dir.exists()


def test_first_run_reports_missing_and_corrupt_settings(tmp_path: Path) -> None:
    dirs = resolve_app_dirs(frozen=False, source_root=tmp_path)
    settings = dirs.data_dir / "settings.json"

    missing_messages = prepare_first_run_state(dirs, settings)
    settings.write_text("{not-json", encoding="utf-8")
    corrupt_messages = prepare_first_run_state(dirs, settings)

    assert any("will be created" in message for message in missing_messages)
    assert any("will be regenerated" in message for message in corrupt_messages)
    assert dirs.library_dir.is_dir()


def test_corrupt_settings_loads_defaults_and_can_be_rewritten(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text("{not-json", encoding="utf-8")

    loaded = load_settings(settings)
    save_settings(settings, S2AppPaths(archive_inbox_dir=tmp_path / "Mods"))
    reloaded = load_settings(settings)

    assert loaded.client_root is None
    assert reloaded.archive_inbox_dir == tmp_path / "Mods"


def test_release_metadata_generation(tmp_path: Path) -> None:
    output = tmp_path / "release-metadata.json"

    metadata = write_release_metadata(output)
    parsed = json.loads(output.read_text(encoding="utf-8"))

    assert metadata["app_name"] == __app_name__
    assert parsed["version"] == __version__
    assert parsed["safety_defaults"]["real_apply"] == "enabled_for_non_blocked_preview_apply_plans"
    assert parsed["safety_defaults"]["destructive_recovery"] == "manifest_tracked_managed_files_only"


def test_static_release_metadata_tracks_package_identity() -> None:
    metadata = build_release_metadata()

    assert metadata["app_name"] == __app_name__
    assert metadata["version"] == __version__
    assert metadata["package_kind"] == "portable-pyinstaller"


def test_pyinstaller_spec_and_build_script_include_assets_and_metadata() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = (root / "Subnautica2ModManager.spec").read_text(encoding="utf-8")
    script = (root / "scripts" / "build_portable.ps1").read_text(encoding="utf-8")

    assert "assets" in spec
    assert "tkinterdnd2" in spec
    assert "release-metadata.json" in script
    assert "write_release_metadata" in script
    assert "PyInstaller" in script


def test_icon_assets_are_present_and_readable() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "assets" / "app_icon_source.png"
    masked = root / "assets" / "app_icon.png"
    icon = root / "assets" / "app.ico"

    assert source.is_file()
    assert masked.is_file()
    assert icon.is_file()
    with Image.open(masked) as image:
        assert image.size == (2048, 2048)
        assert image.mode == "RGBA"
    with Image.open(icon) as image:
        assert image.size == (256, 256)
