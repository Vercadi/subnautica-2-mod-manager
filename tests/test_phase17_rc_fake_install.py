from __future__ import annotations

import zipfile
from pathlib import Path

from s2_mod_manager.core.archive_inspector import scan_inbox
from s2_mod_manager.core.backup_store import BackupStore
from s2_mod_manager.core.deployment_planner import build_deployment_plan
from s2_mod_manager.core.installer import Installer
from s2_mod_manager.core.library_store import LibraryStore
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.core.profile_store import ProfileStore
from s2_mod_manager.core.recovery_service import RecoveryService
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.archive_info import COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED
from s2_mod_manager.models.manifest import STATUS_COMPLETED, STATUS_REFUSED, STATUS_UNINSTALLED


def test_real_sample_shaped_fake_install_apply_uninstall_and_restore_preview(tmp_path: Path) -> None:
    inbox = _sample_inbox(tmp_path)
    paths = _fake_install(tmp_path, fake=True)
    preexisting = paths.mods_paks / "InfiniteOxygen_P.pak"
    preexisting.parent.mkdir(parents=True, exist_ok=True)
    preexisting.write_bytes(b"old pak")
    save = paths.save_games / "slot0001" / "save.dat"
    save.parent.mkdir(parents=True, exist_ok=True)
    save.write_bytes(b"save")
    library = _import_samples(tmp_path, inbox)
    safe_components = [
        component
        for component in library.list_components()
        if component.component_type not in {COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED}
    ]
    profile = _profile_with_components(tmp_path, "RC Safe Samples", safe_components, library.list_components())
    plan = build_deployment_plan(
        profile,
        sources=library.list_sources(),
        components=library.list_components(),
        paths=paths,
        ue4ss_runtime_installed=False,
        dry_run=False,
        real_apply_enabled=True,
    )

    manifest = ManifestStore(tmp_path / "data")
    result = Installer(manifest_store=manifest, backup_store=BackupStore(tmp_path / "backups")).apply(plan)

    assert result.ok
    assert result.record.status == STATUS_COMPLETED
    assert len(result.record.deployed_files) == 18
    assert len(result.record.backups) == 1
    assert preexisting.read_bytes() != b"old pak"
    assert (paths.mods_paks / "SeaSprint.pak").is_file()
    assert (paths.ue4ss_root / "UE4SS.dll").is_file()
    assert (paths.ue4ss_mods / "HUDToggle" / "Scripts" / "main.lua").is_file()
    assert (paths.ue4ss_mods / "ScannerSpeedMod" / "original_durations.lua").is_file()
    assert (paths.ue4ss_mods / "SN2ModSettings" / "Scripts" / "SN2ModSettings.lua").is_file()

    recovery = RecoveryService(ManifestStore(tmp_path / "data"), BackupStore(tmp_path / "backups"))
    preview_before = recovery.restore_vanilla_preview(paths)
    assert len(preview_before.managed_files) == 18
    assert not preview_before.unknown_files

    uninstall = recovery.uninstall_all()
    reloaded = ManifestStore(tmp_path / "data").list_installs()[0]
    preview_after = RecoveryService(ManifestStore(tmp_path / "data")).restore_vanilla_preview(paths)

    assert uninstall.ok
    assert len(uninstall.removed_files) == 17
    assert uninstall.restored_files == [preexisting]
    assert reloaded.status == STATUS_UNINSTALLED
    assert preexisting.read_bytes() == b"old pak"
    assert save.read_bytes() == b"save"
    assert not (paths.mods_paks / "SeaSprint.pak").exists()
    assert not (paths.ue4ss_mods / "ScannerSpeedMod" / "original_durations.lua").exists()
    assert preview_after.managed_files == []
    assert preview_after.unknown_files == [preexisting]


def test_real_sample_shaped_profile_with_sn2p_is_blocked_and_refused(tmp_path: Path) -> None:
    inbox = _sample_inbox(tmp_path)
    paths = _fake_install(tmp_path, fake=True)
    library = _import_samples(tmp_path, inbox)
    profile = _profile_with_components(tmp_path, "RC All Samples", library.list_components(), library.list_components())
    plan = build_deployment_plan(
        profile,
        sources=library.list_sources(),
        components=library.list_components(),
        paths=paths,
        dry_run=False,
        real_apply_enabled=True,
    )

    result = Installer(
        manifest_store=ManifestStore(tmp_path / "blocked_data"),
        backup_store=BackupStore(tmp_path / "blocked_backups"),
    ).apply(plan)

    assert plan.blocked
    assert len(plan.blocked_actions) == 2
    assert any("SN2P" in error for error in plan.errors)
    assert not result.ok
    assert result.record.status == STATUS_REFUSED
    assert "blocked deployment plan" in result.record.errors[0]
    assert not (paths.client_root / "dxgi.dll").exists()
    assert not (paths.mods_paks / "SeaSprint.pak").exists()


def test_real_sample_shaped_non_test_install_refuses_writes(tmp_path: Path) -> None:
    inbox = _sample_inbox(tmp_path)
    paths = _fake_install(tmp_path, fake=False)
    library = _import_samples(tmp_path, inbox)
    safe_components = [
        component
        for component in library.list_components()
        if component.component_type not in {COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED}
    ]
    profile = _profile_with_components(tmp_path, "RC Non Test", safe_components, library.list_components())
    plan = build_deployment_plan(
        profile,
        sources=library.list_sources(),
        components=library.list_components(),
        paths=paths,
        dry_run=False,
    )

    result = Installer(
        manifest_store=ManifestStore(tmp_path / "real_guard_data"),
        backup_store=BackupStore(tmp_path / "real_guard_backups"),
    ).apply(plan, allow_real_apply=False)

    assert not result.ok
    assert result.record.status == STATUS_REFUSED
    assert "non-test install" in result.record.errors[0]
    assert not (paths.mods_paks / "InfiniteOxygen_P.pak").exists()
    assert not (paths.ue4ss_root / "UE4SS.dll").exists()


def test_real_sample_shaped_non_test_install_can_apply_safe_components_when_allowed(tmp_path: Path) -> None:
    inbox = _sample_inbox(tmp_path)
    paths = _fake_install(tmp_path, fake=False)
    library = _import_samples(tmp_path, inbox)
    safe_components = [
        component
        for component in library.list_components()
        if component.component_type not in {COMPONENT_LOOSE_OVERLAY, COMPONENT_MIXED}
    ]
    profile = _profile_with_components(tmp_path, "RC Real Managed", safe_components, library.list_components())
    plan = build_deployment_plan(
        profile,
        sources=library.list_sources(),
        components=library.list_components(),
        paths=paths,
        dry_run=False,
        real_apply_enabled=True,
        ue4ss_activation_policy={"ue4ss_write_enabled_txt": True},
    )

    result = Installer(
        manifest_store=ManifestStore(tmp_path / "real_apply_data"),
        backup_store=BackupStore(tmp_path / "real_apply_backups"),
    ).apply(plan, allow_real_apply=True)

    assert result.ok
    assert (paths.mods_paks / "InfiniteOxygen_P.pak").exists()
    assert (paths.ue4ss_root / "UE4SS.dll").exists()
    assert (paths.ue4ss_mods / "HUDToggle" / "enabled.txt").exists()
    assert not (paths.client_root / "dxgi.dll").exists()


def _sample_inbox(tmp_path: Path) -> Path:
    inbox = tmp_path / "Mods"
    inbox.mkdir()
    _write_zip(
        inbox / "Hide HUD.zip",
        {
            "ue4ss/mods/HUDToggle/enabled.txt": b"",
            "ue4ss/mods/HUDToggle/Scripts/main.lua": b"print('hide')",
        },
    )
    _write_zip(
        inbox / "Infinite Oxygen.zip",
        {
            "InfiniteOxygen/InfiniteOxygen_P.pak": b"pak",
            "InfiniteOxygen/InfiniteOxygen_P.ucas": b"ucas",
            "InfiniteOxygen/InfiniteOxygen_P.utoc": b"utoc",
        },
    )
    _write_zip(
        inbox / "ScannerSpeedMod.zip",
        {
            "ScannerSpeedMod/enabled.txt": b"",
            "ScannerSpeedMod/Scripts/main.lua": b"print('scan')",
            "ScannerSpeedMod/original_durations.lua": b"return {}",
        },
    )
    _write_zip(
        inbox / "SeaSprint.zip",
        {
            "SeaSprint/SeaSprint.pak": b"pak",
            "SeaSprint/SeaSprint.ucas": b"ucas",
            "SeaSprint/SeaSprint.utoc": b"utoc",
        },
    )
    _write_zip(
        inbox / "SN2ModSettings.zip",
        {
            "Subnautica2/Binaries/Win64/ue4ss/Mods/SN2ModSettings/enabled.txt": b"",
            "Subnautica2/Binaries/Win64/ue4ss/Mods/SN2ModSettings/Scripts/main.lua": b"print('settings')",
            "Subnautica2/Binaries/Win64/ue4ss/Mods/SN2ModSettings/Scripts/SN2ModSettings.lua": b"return {}",
        },
    )
    _write_zip(
        inbox / "SN2P.zip",
        {
            "dxgi.dll": b"loader",
            "snsnp_settings.ini": b"[settings]",
        },
    )
    _write_zip(
        inbox / "UE4SS SN2.zip",
        {
            "ue4ss/UE4SS.dll": b"runtime",
            "ue4ss/UE4SS-settings.ini": b"settings",
            "dwmapi.dll": b"proxy",
            "ue4ss/Mods/BPModLoaderMod/Scripts/main.lua": b"print('bp')",
        },
    )
    return inbox


def _fake_install(tmp_path: Path, *, fake: bool) -> S2AppPaths:
    root = tmp_path / ("FakeSubnautica2" if fake else "RealShapedSubnautica2")
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True)
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True)
    (root / "Subnautica2.exe").write_bytes(b"fake exe")
    (root / "Subnautica2" / "Binaries" / "Win64" / "Subnautica2-Win64-Shipping.exe").write_bytes(b"fake shipping")
    (root / "version.txt").write_text("Build: Phase17\nChangelist: 17\n", encoding="utf-8")
    if fake:
        (root / ".s2mm_fake_install").write_text("test-only", encoding="utf-8")
    return S2AppPaths(client_root=root)


def _import_samples(tmp_path: Path, inbox: Path) -> LibraryStore:
    library = LibraryStore(tmp_path / "data")
    scans = scan_inbox(inbox)
    assert len(scans) == 7
    for scan in scans:
        assert scan.ok
        library.import_scan(scan)
    assert len(library.list_sources()) == 7
    assert len(library.list_components()) == 7
    return library


def _profile_with_components(tmp_path: Path, name: str, components, all_components):
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile(name)
    for component in components:
        assert store.add_component(profile.profile_id, component.component_id, all_components)
    return store.get_profile(profile.profile_id)


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
