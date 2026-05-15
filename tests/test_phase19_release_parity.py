from __future__ import annotations

import json
import urllib.error
import zipfile
from pathlib import Path

from s2_mod_manager.core.activity_log import ActivityLog
from s2_mod_manager.core.archive_inspector import inspect_archive
from s2_mod_manager.core.help_about import build_help_about_view
from s2_mod_manager.core.needs_attention import build_needs_attention
from s2_mod_manager.core.settings_store import load_preferences, load_settings, save_preferences, save_settings
from s2_mod_manager.core.settings_workflow import build_settings_view, update_auto_check_updates
from s2_mod_manager.core.update_checker import (
    ReleaseAsset,
    friendly_error,
    is_newer_version,
    pick_preferred_asset,
    release_info_from_api,
    version_parts,
)
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.deployment import DeploymentPlan
from s2_mod_manager.models.library import LibraryComponent, LibrarySource
from s2_mod_manager.models.preferences import UserPreferences
from s2_mod_manager.models.recovery import RecoverySummary
from s2_mod_manager.ui.window_utils import centered_placement


def test_centered_placement_is_parent_centered_and_screen_clamped() -> None:
    placement = centered_placement(
        parent_x=100,
        parent_y=80,
        parent_width=1000,
        parent_height=700,
        width=500,
        height=300,
        screen_width=1280,
        screen_height=760,
    )
    assert placement.geometry == "500x300+350+280"

    clamped = centered_placement(
        parent_x=1100,
        parent_y=700,
        parent_width=400,
        parent_height=300,
        width=600,
        height=400,
        screen_width=1280,
        screen_height=760,
    )
    assert clamped.x == 680
    assert clamped.y == 360


def test_update_checker_parses_versions_assets_and_errors() -> None:
    release = release_info_from_api(
        {
            "tag_name": "v0.2.1",
            "html_url": "https://example.test/releases/v0.2.1",
            "assets": [
                {"name": "hash.sha256", "browser_download_url": "https://example.test/hash", "size": 4},
                {"name": "portable.zip", "browser_download_url": "https://example.test/zip", "size": 12},
            ],
        }
    )

    assert release.version == "0.2.1"
    assert release.preferred_asset and release.preferred_asset.name == "portable.zip"
    assert version_parts("v0.1.0-phase18") == [0, 1, 0, 18]
    assert is_newer_version("v0.2.0", "0.1.9")
    assert not is_newer_version("0.1.0", "0.1.0-phase18")
    assert pick_preferred_asset([ReleaseAsset("build.sig", "x"), ReleaseAsset("build.7z", "y")]).name == "build.7z"
    assert "No GitHub release" in friendly_error(urllib.error.HTTPError("x", 404, "missing", None, None))


def test_update_preference_defaults_off_and_roundtrips_with_paths(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    paths = S2AppPaths(client_root=tmp_path / "Subnautica2")
    save_settings(settings, paths)

    assert load_preferences(settings).auto_check_updates is False

    prefs = update_auto_check_updates(settings, True)
    view = build_settings_view(
        load_settings(settings),
        data_dir=tmp_path / "data",
        library_dir=tmp_path / "data" / "library",
        backup_dir=tmp_path / "backups",
        preferences=prefs,
    )

    assert load_settings(settings).client_root == paths.client_root
    assert load_preferences(settings).auto_check_updates is True
    assert "startup_updates=on" in view.summary_text

    save_preferences(settings, UserPreferences(auto_check_updates=False))
    assert load_preferences(settings).auto_check_updates is False


def test_activity_log_persists_bounds_and_recovers_from_corrupt_json(tmp_path: Path) -> None:
    log = ActivityLog(tmp_path, limit=3)
    for index in range(5):
        log.append(action="event", result=str(index))

    loaded = ActivityLog(tmp_path, limit=3)
    assert loaded.count == 3
    assert [record.result for record in loaded.list_records()] == ["2", "3", "4"]

    (tmp_path / "activity_log.json").write_text("{not-json", encoding="utf-8")
    recovered = ActivityLog(tmp_path, limit=3)
    assert recovered.list_records() == []


def test_needs_attention_summarizes_actionable_release_state(tmp_path: Path) -> None:
    source = LibrarySource(
        source_id="source",
        source_kind="folder",
        display_name="Source",
        original_path=tmp_path / "Source",
        managed_path=tmp_path / "data" / "library" / "sources" / "source",
    )
    component = LibraryComponent(
        component_id="component",
        source_id="missing-source",
        display_name="Loose Overlay",
        component_type="loose_overlay",
        install_kind="loose_overlay",
    )
    plan = DeploymentPlan("profile", "Main", tmp_path / "Subnautica2")
    plan.errors.append("Target root is invalid.")

    summary = build_needs_attention(
        paths=S2AppPaths(),
        scans=[],
        library_sources=[source],
        library_components=[component],
        loadout_warnings=[],
        deployment_plan=plan,
        recovery_summary=RecoverySummary(failed_count=1),
    )
    text = summary.detail_text()

    assert "S2 install" in text
    assert "missing library source" in text
    assert "Target root is invalid" in text
    assert "Recovery" in text


def test_ue4ss_native_warning_and_root_scripts_wrapping(tmp_path: Path) -> None:
    native = _archive(tmp_path / "ConsoleCommands.zip", {"ConsoleCommands/scripts/main.lua": b"-- lua"})
    root_scripts = _archive(tmp_path / "RootLua.zip", {"scripts/main.lua": b"-- lua", "scripts/config.lua": b"return {}"})

    native_component = inspect_archive(native).components[0]
    root_component = inspect_archive(root_scripts).components[0]

    assert "Core" in native_component.badges
    assert any("Protected native UE4SS core mod" in warning for warning in native_component.warnings)
    assert root_component.files[0].target_hint.startswith("RootLua/")
    assert any("Root scripts/dlls archive shape" in warning for warning in root_component.warnings)


def test_help_about_view_models_links_shortcuts_and_report(tmp_path: Path) -> None:
    data = tmp_path / "data"
    library = data / "library"
    backups = tmp_path / "backups"
    logs = data / "logs"
    docs = tmp_path / "docs"
    for path in (data, library, backups, logs, docs):
        path.mkdir(parents=True)
    metadata = tmp_path / "release-metadata.json"
    metadata.write_text(json.dumps({"version": "0.1.0-phase19", "generated_at": "2026-05-15"}), encoding="utf-8")

    view = build_help_about_view(
        paths=S2AppPaths(client_root=tmp_path / "missing-game"),
        data_dir=data,
        library_dir=library,
        backup_dir=backups,
        log_dir=logs,
        docs_dir=docs,
        support_report="support report",
        release_metadata_path=metadata,
    )

    assert "0.1.0-phase19" in view.build_metadata
    assert "GitHub" not in view.summary_text
    assert view.github_url.startswith("https://github.com/")
    assert any(shortcut.label == "Library" and shortcut.available for shortcut in view.shortcuts)
    assert view.support_report == "support report"


def _archive(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return path
