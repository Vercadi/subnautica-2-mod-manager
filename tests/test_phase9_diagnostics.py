from __future__ import annotations

from pathlib import Path

from s2_mod_manager.core.diagnostics import collect_diagnostics, read_log_excerpt, redact_path
from s2_mod_manager.core.discovery import normalize_install_path
from s2_mod_manager.core.library_store import LibraryStore
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.core.profile_store import ProfileStore
from s2_mod_manager.models.app_paths import S2AppPaths, S2GameVersion, SteamAppManifest
from s2_mod_manager.models.deployment import DeploymentPlan
from s2_mod_manager.models.library import LibraryComponent, LibrarySource
from s2_mod_manager.models.manifest import BackupRecord, InstallRecord, STATUS_COMPLETED
from s2_mod_manager.models.profile import VANILLA_PROFILE_ID
from s2_mod_manager.models.recovery import RecoverySummary


def test_redact_path_hides_user_profile_prefix() -> None:
    home = Path("C:/Users/Alice")
    path = Path("C:/Users/Alice/Documents/Subnautica2/Mods/file.zip")

    redacted = redact_path(path, home=home)

    assert "Alice" not in redacted
    assert "C:\\Users" not in redacted
    assert redacted.endswith(r"Documents\Subnautica2\Mods\file.zip")
    assert redacted.startswith("<USER_HOME>")


def test_redact_path_preserves_useful_tail_for_non_home_paths() -> None:
    path = Path("F:/SteamLibrary/steamapps/common/Subnautica2/Subnautica2/Content/Paks")

    redacted = redact_path(path, home=Path("C:/Users/Alice"))

    assert redacted.endswith(r"Subnautica2\Subnautica2\Content\Paks")


def test_diagnostics_report_generation(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    data_dir = tmp_path / "data"
    library = LibraryStore(data_dir)
    library.state.sources.append(_source(tmp_path))
    library.state.components.append(_component())
    profiles = ProfileStore(data_dir)
    profile = profiles.create_profile("Main")
    profiles.add_component(profile.profile_id, "component", library.list_components())
    manifest = ManifestStore(data_dir)
    manifest.add_or_update(_install(tmp_path, paths))
    log = data_dir / "logs" / "app.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("ready\n", encoding="utf-8")

    report = collect_diagnostics(
        paths=paths,
        data_dir=data_dir,
        library_store=library,
        profile_store=profiles,
        manifest_store=manifest,
        deployment_plan=DeploymentPlan("profile", "Main", paths.client_root),
        recovery_summary=RecoverySummary(install_count=1, deployed_file_count=1, backup_count=1, completed_count=1),
        log_path=log,
        home=tmp_path / "Users" / "Alice",
    )

    text = report.support_report_text()
    assert "Subnautica 2 Mod Manager Support Report" in text
    assert "Library Sources: 1" in text
    assert "Library Components: 1" in text
    assert "Profiles: 2" in text
    assert "Active Loadout Entries: 1" in text
    assert "Manifest Installs: 1" in text
    assert "Backups: 1" in text
    assert "ready" in text


def test_archive_support_reporting(tmp_path: Path) -> None:
    report = collect_diagnostics(
        paths=_paths(tmp_path),
        data_dir=tmp_path / "data",
        library_store=LibraryStore(tmp_path / "data"),
        profile_store=ProfileStore(tmp_path / "data"),
        manifest_store=ManifestStore(tmp_path / "data"),
        deployment_plan=None,
        recovery_summary=RecoverySummary(),
        log_path=None,
    )

    assert ".zip" in report.archive_support
    assert ".7z" in report.archive_support
    assert ".rar" in report.archive_support
    assert report.archive_support[".zip"] is True


def test_recovery_library_profile_counts(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    library = LibraryStore(data_dir)
    library.state.sources.append(_source(tmp_path))
    library.state.components.append(_component())
    profiles = ProfileStore(data_dir)
    profile = profiles.create_profile("Main")
    profiles.add_component(profile.profile_id, "component", library.list_components())
    manifest = ManifestStore(data_dir)
    manifest.add_or_update(_install(tmp_path, _paths(tmp_path)))

    report = collect_diagnostics(
        paths=_paths(tmp_path),
        data_dir=data_dir,
        library_store=library,
        profile_store=profiles,
        manifest_store=manifest,
        deployment_plan=None,
        recovery_summary=RecoverySummary(install_count=1, deployed_file_count=1, backup_count=1, completed_count=1),
        log_path=None,
    )

    assert report.library_source_count == 1
    assert report.library_component_count == 1
    assert report.profile_count == 2
    assert report.active_loadout_count == 1
    assert report.manifest_install_count == 1
    assert report.backup_count == 1


def test_log_excerpt_is_truncated_and_redacted(tmp_path: Path) -> None:
    home = Path("C:/Users/Alice")
    log = tmp_path / "app.log"
    lines = [f"line {index}" for index in range(30)]
    lines.append(f"path {home}\\Documents\\secret.txt")
    log.write_text("\n".join(lines), encoding="utf-8")

    excerpt = read_log_excerpt(log, line_limit=5, home=home)

    assert len(excerpt) == 5
    assert excerpt[0] == "line 26"
    assert "Alice" not in "\n".join(excerpt)
    assert "<USER_HOME>" in excerpt[-1]


def test_support_report_does_not_expose_save_or_home_paths(tmp_path: Path) -> None:
    home = Path("C:/Users/Alice")
    root = home / "Games" / "Subnautica2"
    paths = S2AppPaths(client_root=root)
    log = tmp_path / "app.log"
    log.write_text(f"save {root}\\Subnautica2\\Saved\\SaveGames\\slot\n", encoding="utf-8")

    report = collect_diagnostics(
        paths=paths,
        data_dir=home / "AppData" / "Local" / "Subnautica2ModManager",
        library_store=LibraryStore(tmp_path / "data"),
        profile_store=ProfileStore(tmp_path / "data"),
        manifest_store=ManifestStore(tmp_path / "data"),
        deployment_plan=None,
        recovery_summary=RecoverySummary(),
        log_path=log,
        home=home,
    )

    text = report.support_report_text()
    assert "Alice" not in text
    assert "C:\\Users" not in text
    assert "SaveGames" not in text
    assert "slot" not in text


def test_diagnostics_report_includes_gamepass_experimental_layout(tmp_path: Path) -> None:
    paths = _gamepass_paths(tmp_path)

    report = collect_diagnostics(
        paths=paths,
        data_dir=tmp_path / "data",
        library_store=LibraryStore(tmp_path / "data"),
        profile_store=ProfileStore(tmp_path / "data"),
        manifest_store=ManifestStore(tmp_path / "data"),
        deployment_plan=None,
        recovery_summary=RecoverySummary(),
        log_path=None,
        home=tmp_path / "Users" / "Alice",
    )

    text = report.support_report_text()
    assert report.install_variant == "Game Pass WinGDK (experimental)"
    assert "WinGDK" in text
    assert "UE4SS Runtime Root" in text
    assert "experimental" in text.casefold()
    assert "UE4SS Target Folder" in text
    assert "WinGDK\\ue4ss\\Mods" in text


def _paths(tmp_path: Path) -> S2AppPaths:
    root = tmp_path / "SteamLibrary" / "steamapps" / "common" / "Subnautica2"
    win64 = root / "Subnautica2" / "Binaries" / "Win64"
    win64.mkdir(parents=True, exist_ok=True)
    (win64 / "dwmapi.dll").write_bytes(b"runtime")
    manifest = SteamAppManifest(
        appid="1962700",
        buildid="123",
        manifest_path=tmp_path / "SteamLibrary" / "steamapps" / "appmanifest_1962700.acf",
    )
    return S2AppPaths(
        client_root=root,
        client_manifest=manifest,
        game_version=S2GameVersion(build_number="34", changelist="113109"),
    )


def _gamepass_paths(tmp_path: Path) -> S2AppPaths:
    root = tmp_path / "XboxGames" / "Subnautica 2"
    project = root / "Content" / "Subnautica2"
    wingdk = project / "Binaries" / "WinGDK"
    wingdk.mkdir(parents=True, exist_ok=True)
    (project / "Content" / "Paks").mkdir(parents=True, exist_ok=True)
    (wingdk / "Subnautica2-WinGDK-Shipping.exe").write_bytes(b"shipping")
    layout = normalize_install_path(wingdk)
    assert layout is not None
    return S2AppPaths(client_root=layout.client_root, install_layout=layout)


def _source(tmp_path: Path) -> LibrarySource:
    return LibrarySource(
        source_id="source",
        source_kind="folder",
        display_name="Source",
        original_path=tmp_path / "Mods" / "Source",
        managed_path=tmp_path / "data" / "library" / "sources" / "source",
        source_hash="hash",
        component_ids=["component"],
    )


def _component() -> LibraryComponent:
    return LibraryComponent(
        component_id="component",
        source_id="source",
        display_name="Component",
        component_type="pak_bundle",
        install_kind="standard_mod",
        file_count=1,
    )


def _install(tmp_path: Path, paths: S2AppPaths) -> InstallRecord:
    target = paths.mods_paks / "Managed_P.pak"
    backup_path = tmp_path / "backups" / "Managed_P.pak"
    backup = BackupRecord("backup", target, backup_path, "component")
    record = InstallRecord(
        install_id="install",
        profile_id=VANILLA_PROFILE_ID,
        profile_name="Vanilla",
        target_root=paths.client_root,
        status=STATUS_COMPLETED,
        backups=[backup],
    )
    return record
