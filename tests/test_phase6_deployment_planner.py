from __future__ import annotations

from pathlib import Path

from s2_mod_manager.core.deployment_planner import build_deployment_plan
from s2_mod_manager.core.discovery import normalize_install_path
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.archive_info import (
    COMPONENT_LOOSE_OVERLAY,
    COMPONENT_PAK_BUNDLE,
    COMPONENT_UE4SS_MOD,
    COMPONENT_UE4SS_RUNTIME,
    INSTALL_KIND_LOOSE_OVERLAY,
    INSTALL_KIND_STANDARD,
    INSTALL_KIND_UE4SS_MOD,
    INSTALL_KIND_UE4SS_RUNTIME,
)
from s2_mod_manager.models.deployment import ACTION_BLOCKED, ACTION_CREATE, ACTION_DELETE, ACTION_OVERWRITE
from s2_mod_manager.models.library import LibraryComponent, LibraryComponentFile, LibrarySource
from s2_mod_manager.models.profile import LoadoutEntry, ModProfile


def test_target_mapping_for_pak_runtime_and_ue4ss_mod(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["Mod/Mod_P.pak", "UE4SS.dll", "Hud/Scripts/main.lua"])
    components = [
        _component("pak", "Pak Mod", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
            _file("Mod/Mod_P.pak", "Mod_P.pak"),
        ]),
        _component("runtime", "Runtime", source.source_id, COMPONENT_UE4SS_RUNTIME, INSTALL_KIND_UE4SS_RUNTIME, [
            _file("UE4SS.dll", "UE4SS.dll"),
        ]),
        _component("ue4ss", "HUD", source.source_id, COMPONENT_UE4SS_MOD, INSTALL_KIND_UE4SS_MOD, [
            _file("Hud/Scripts/main.lua", "Hud/Scripts/main.lua"),
        ]),
    ]
    profile = _profile([component.component_id for component in components])

    plan = build_deployment_plan(profile, sources=[source], components=components, paths=paths)
    targets = {action.component_id: action.target_path for action in plan.actions}

    assert targets["pak"] == paths.mods_paks / "Mod_P.pak"
    assert targets["runtime"] == paths.win64 / "UE4SS.dll"
    assert targets["ue4ss"] == paths.ue4ss_mods / "Hud" / "Scripts" / "main.lua"
    assert not plan.errors


def test_gamepass_layout_maps_runtime_to_content_and_ue4ss_mods_to_wingdk_targets(tmp_path: Path) -> None:
    paths = _gamepass_paths(tmp_path)
    source = _source(tmp_path, files=["Mod/Mod_P.pak", "ue4ss/UE4SS.dll", "dwmapi.dll", "Hud/Scripts/main.lua"])
    components = [
        _component("pak", "Pak Mod", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
            _file("Mod/Mod_P.pak", "Mod_P.pak"),
        ]),
        _component("runtime", "Runtime", source.source_id, COMPONENT_UE4SS_RUNTIME, INSTALL_KIND_UE4SS_RUNTIME, [
            _file("ue4ss/UE4SS.dll", "ue4ss/UE4SS.dll"),
            _file("dwmapi.dll", "dwmapi.dll"),
        ]),
        _component("ue4ss", "HUD", source.source_id, COMPONENT_UE4SS_MOD, INSTALL_KIND_UE4SS_MOD, [
            _file("Hud/Scripts/main.lua", "Hud/Scripts/main.lua"),
        ]),
    ]

    plan = build_deployment_plan(_profile([component.component_id for component in components]), sources=[source], components=components, paths=paths)
    targets = {action.component_id: action.target_path for action in plan.actions}

    assert targets["pak"] == paths.content_paks / "~mods" / "Mod_P.pak"
    runtime_targets = {action.target_path for action in plan.actions if action.component_id == "runtime"}
    assert runtime_targets == {
        paths.gamepass_content_root / "ue4ss" / "UE4SS.dll",
        paths.gamepass_content_root / "dwmapi.dll",
    }
    assert targets["ue4ss"] == paths.binaries_dir / "ue4ss" / "Mods" / "Hud" / "Scripts" / "main.lua"
    assert "WinGDK" in str(targets["ue4ss"])
    assert any("experimental" in warning.casefold() for warning in plan.warnings)


def test_gamepass_explicit_wingdk_runtime_target_is_preserved(tmp_path: Path) -> None:
    paths = _gamepass_paths(tmp_path)
    source = _source(
        tmp_path,
        files=[
            "Content/Subnautica2/Binaries/WinGDK/ue4ss/UE4SS.dll",
            "Content/Subnautica2/Binaries/WinGDK/dwmapi.dll",
        ],
    )
    component = _component(
        "runtime",
        "Game Pass Runtime",
        source.source_id,
        COMPONENT_UE4SS_RUNTIME,
        INSTALL_KIND_UE4SS_RUNTIME,
        [
            _file(
                "Content/Subnautica2/Binaries/WinGDK/ue4ss/UE4SS.dll",
                "Subnautica2/Binaries/WinGDK/ue4ss/UE4SS.dll",
            ),
            _file(
                "Content/Subnautica2/Binaries/WinGDK/dwmapi.dll",
                "Subnautica2/Binaries/WinGDK/dwmapi.dll",
            ),
        ],
    )

    plan = build_deployment_plan(_profile([component.component_id]), sources=[source], components=[component], paths=paths)

    assert {action.target_path for action in plan.actions} == {
        paths.gamepass_content_root / "Subnautica2" / "Binaries" / "WinGDK" / "ue4ss" / "UE4SS.dll",
        paths.gamepass_content_root / "Subnautica2" / "Binaries" / "WinGDK" / "dwmapi.dll",
    }


def test_logicmods_pak_bundle_maps_under_content_paks_logicmods(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["SeaSprint/SeaSprint.pak", "SeaSprint/SeaSprint.ucas"])
    component = _component("logic", "SeaSprint", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
        _file("SeaSprint/SeaSprint.pak", "LogicMods/SeaSprint.pak"),
        _file("SeaSprint/SeaSprint.ucas", "LogicMods/SeaSprint.ucas"),
    ])

    plan = build_deployment_plan(_profile(["logic"]), sources=[source], components=[component], paths=paths)
    targets = sorted(action.target_path for action in plan.actions)

    assert targets == [
        paths.content_paks / "LogicMods" / "SeaSprint.pak",
        paths.content_paks / "LogicMods" / "SeaSprint.ucas",
    ]
    assert not plan.errors


def test_disabled_entries_are_skipped(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["Mod/Mod_P.pak"])
    component = _component("pak", "Pak Mod", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
        _file("Mod/Mod_P.pak", "Mod_P.pak"),
    ])
    profile = _profile(["pak"], enabled=False)

    plan = build_deployment_plan(profile, sources=[source], components=[component], paths=paths)

    assert not plan.actions
    assert plan.skips[0].reason == "disabled in active profile"


def test_missing_library_source_is_an_error(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    component = _component("pak", "Pak Mod", "missing_source", COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
        _file("Mod/Mod_P.pak", "Mod_P.pak"),
    ])

    plan = build_deployment_plan(_profile(["pak"]), sources=[], components=[component], paths=paths)

    assert any("missing its library source" in error for error in plan.errors)


def test_missing_profile_component_is_an_error(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    plan = build_deployment_plan(_profile(["missing"]), sources=[], components=[], paths=paths)

    assert any("missing from the imported library" in error for error in plan.errors)


def test_missing_managed_source_file_is_an_error(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["Other/Other_P.pak"])
    component = _component("pak", "Pak Mod", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
        _file("Mod/Mod_P.pak", "Mod_P.pak"),
    ])

    plan = build_deployment_plan(_profile(["pak"]), sources=[source], components=[component], paths=paths)

    assert any("source file is missing" in error for error in plan.errors)


def test_missing_ue4ss_runtime_warns(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["Hud/Scripts/main.lua"])
    component = _component("ue4ss", "HUD", source.source_id, COMPONENT_UE4SS_MOD, INSTALL_KIND_UE4SS_MOD, [
        _file("Hud/Scripts/main.lua", "Hud/Scripts/main.lua"),
    ])

    plan = build_deployment_plan(
        _profile(["ue4ss"]),
        sources=[source],
        components=[component],
        paths=paths,
        ue4ss_runtime_installed=False,
    )

    assert any("UE4SS runtime" in warning for warning in plan.warnings)
    assert any("Import/add a UE4SS Runtime package" in warning for warning in plan.warnings)


def test_loose_overlay_is_review_blocked(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["Subnautica2/Config/Game.ini"])
    component = _component(
        "loose",
        "Loose Overlay",
        source.source_id,
        COMPONENT_LOOSE_OVERLAY,
        INSTALL_KIND_LOOSE_OVERLAY,
        [_file("Subnautica2/Config/Game.ini", "Subnautica2/Config/Game.ini")],
        warnings=["Loose overlay files require explicit review before deployment."],
    )

    plan = build_deployment_plan(_profile(["loose"]), sources=[source], components=[component], paths=paths)

    assert plan.blocked
    assert plan.actions[0].action == ACTION_BLOCKED
    assert any("manual review" in error for error in plan.errors)


def test_target_conflicts_are_detected(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["A/Same_P.pak", "B/Same_P.pak"])
    components = [
        _component("a", "A", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
            _file("A/Same_P.pak", "Same_P.pak"),
        ]),
        _component("b", "B", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
            _file("B/Same_P.pak", "Same_P.pak"),
        ]),
    ]

    plan = build_deployment_plan(_profile(["a", "b"]), sources=[source], components=components, paths=paths)

    assert any("Target conflict" in error for error in plan.errors)


def test_existing_target_overwrite_is_detected(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    target = paths.mods_paks / "Mod_P.pak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"existing")
    source = _source(tmp_path, files=["Mod/Mod_P.pak"])
    component = _component("pak", "Pak Mod", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
        _file("Mod/Mod_P.pak", "Mod_P.pak"),
    ])

    plan = build_deployment_plan(_profile(["pak"]), sources=[source], components=[component], paths=paths)

    assert plan.actions[0].action == ACTION_OVERWRITE
    assert any("overwrite existing target" in warning for warning in plan.warnings)


def test_unsafe_paths_are_errors(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["Mod/Mod_P.pak"])
    component = _component("pak", "Pak Mod", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
        _file("../evil.pak", "Mod_P.pak"),
    ])

    plan = build_deployment_plan(_profile(["pak"]), sources=[source], components=[component], paths=paths)

    assert any("unsafe source path" in error for error in plan.errors)


def test_dry_run_preview_output_keeps_real_apply_disabled(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["Mod/Mod_P.pak"])
    component = _component("pak", "Pak Mod", source.source_id, COMPONENT_PAK_BUNDLE, INSTALL_KIND_STANDARD, [
        _file("Mod/Mod_P.pak", "Mod_P.pak"),
    ])

    plan = build_deployment_plan(
        _profile(["pak"]),
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=True,
        real_apply_enabled=True,
    )

    preview = plan.preview_text()
    assert "Mode: dry-run" in preview
    assert "Real apply: disabled" in preview
    assert "create:" in preview
    assert plan.actions[0].action == ACTION_CREATE


def test_ue4ss_enabled_txt_policy_generates_marker_and_skips_source_marker(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path, files=["HUD/enabled.txt", "HUD/Scripts/main.lua"])
    component = _component("ue4ss", "HUD", source.source_id, COMPONENT_UE4SS_MOD, INSTALL_KIND_UE4SS_MOD, [
        _file("HUD/enabled.txt", "HUD/enabled.txt"),
        _file("HUD/Scripts/main.lua", "HUD/Scripts/main.lua"),
    ])

    plan = build_deployment_plan(
        _profile(["ue4ss"]),
        sources=[source],
        components=[component],
        paths=paths,
        ue4ss_activation_policy={"ue4ss_write_enabled_txt": True},
    )

    assert not any(action.source_member == "HUD/enabled.txt" for action in plan.actions)
    marker = next(action for action in plan.actions if action.target_path == paths.ue4ss_mods / "HUD" / "enabled.txt")
    assert marker.action == ACTION_CREATE
    assert marker.generated_content == ""


def test_ue4ss_enabled_txt_policy_deletes_disabled_existing_marker(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    marker = paths.ue4ss_mods / "HUD" / "enabled.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("", encoding="utf-8")
    source = _source(tmp_path, files=["HUD/Scripts/main.lua"])
    component = _component("ue4ss", "HUD", source.source_id, COMPONENT_UE4SS_MOD, INSTALL_KIND_UE4SS_MOD, [
        _file("HUD/Scripts/main.lua", "HUD/Scripts/main.lua"),
    ])
    profile = ModProfile(
        profile_id="profile_test",
        name="Test Profile",
        entries=[LoadoutEntry(component_id="ue4ss", display_name="HUD", enabled=False, order=0)],
    )

    plan = build_deployment_plan(
        profile,
        sources=[source],
        components=[component],
        paths=paths,
        ue4ss_activation_policy={"ue4ss_write_enabled_txt": True},
    )

    delete = next(action for action in plan.actions if action.action == ACTION_DELETE)
    assert delete.target_path == marker
    assert delete.reason.startswith("remove enabled.txt")


def test_ue4ss_central_activation_files_are_generated_from_profile(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    paths.ue4ss_mods.mkdir(parents=True, exist_ok=True)
    (paths.ue4ss_mods / "mods.txt").write_text(
        "ConsoleCommandsMod : 1\nKeybinds : 1\n",
        encoding="utf-8",
    )
    (paths.ue4ss_mods / "mods.json").write_text(
        '[{"mod_name":"ConsoleCommandsMod","mod_enabled":true}]\n',
        encoding="utf-8",
    )
    source = _source(tmp_path, files=["HUD/Scripts/main.lua", "Scan/Scripts/main.lua"])
    components = [
        _component("hud", "HUD", source.source_id, COMPONENT_UE4SS_MOD, INSTALL_KIND_UE4SS_MOD, [
            _file("HUD/Scripts/main.lua", "HUD/Scripts/main.lua"),
        ]),
        _component("scan", "Scan", source.source_id, COMPONENT_UE4SS_MOD, INSTALL_KIND_UE4SS_MOD, [
            _file("Scan/Scripts/main.lua", "Scan/Scripts/main.lua"),
        ]),
    ]
    profile = ModProfile(
        profile_id="profile_test",
        name="Test Profile",
        entries=[
            LoadoutEntry(component_id="hud", display_name="HUD", enabled=True, order=0),
            LoadoutEntry(component_id="scan", display_name="Scan", enabled=False, order=1),
        ],
    )

    plan = build_deployment_plan(
        profile,
        sources=[source],
        components=components,
        paths=paths,
        ue4ss_activation_policy={"ue4ss_write_mods_txt": True, "ue4ss_write_mods_json": True},
    )

    mods_txt = next(action for action in plan.actions if action.target_path == paths.ue4ss_mods / "mods.txt")
    assert "ConsoleCommandsMod : 1" in mods_txt.generated_content
    assert "HUD : 1" in mods_txt.generated_content
    assert "Scan : 0" in mods_txt.generated_content
    assert mods_txt.generated_content.index("HUD : 1") < mods_txt.generated_content.index("Keybinds : 1")
    mods_json = next(action for action in plan.actions if action.target_path == paths.ue4ss_mods / "mods.json")
    assert '"mod_name": "HUD"' in mods_json.generated_content
    assert '"mod_enabled": false' in mods_json.generated_content


def _paths(tmp_path: Path) -> S2AppPaths:
    root = tmp_path / "Subnautica2Install"
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True)
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True)
    return S2AppPaths(client_root=root)


def _gamepass_paths(tmp_path: Path) -> S2AppPaths:
    root = tmp_path / "XboxGames" / "Subnautica 2"
    project = root / "Content" / "Subnautica2"
    (project / "Content" / "Paks").mkdir(parents=True)
    wingdk = project / "Binaries" / "WinGDK"
    wingdk.mkdir(parents=True)
    (wingdk / "Subnautica2-WinGDK-Shipping.exe").write_bytes(b"shipping")
    layout = normalize_install_path(project / "Binaries" / "WinGDK")
    assert layout is not None
    return S2AppPaths(client_root=layout.client_root, install_layout=layout)


def _source(tmp_path: Path, *, files: list[str]) -> LibrarySource:
    managed = tmp_path / "data" / "library" / "sources" / "src_test"
    for rel in files:
        path = managed / Path(*rel.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"source")
    return LibrarySource(
        source_id="src_test",
        source_kind="folder",
        display_name="Source",
        original_path=tmp_path / "source",
        managed_path=managed,
        source_hash="hash",
    )


def _component(
    component_id: str,
    name: str,
    source_id: str,
    component_type: str,
    install_kind: str,
    files: list[LibraryComponentFile],
    *,
    warnings: list[str] | None = None,
) -> LibraryComponent:
    return LibraryComponent(
        component_id=component_id,
        source_id=source_id,
        display_name=name,
        component_type=component_type,
        install_kind=install_kind,
        target_hint="",
        file_count=len(files),
        files=files,
        warnings=warnings or [],
    )


def _file(source_path: str, target_hint: str) -> LibraryComponentFile:
    return LibraryComponentFile(source_path=source_path, target_hint=target_hint, role="file", size=6)


def _profile(component_ids: list[str], *, enabled: bool = True) -> ModProfile:
    return ModProfile(
        profile_id="profile_test",
        name="Test Profile",
        entries=[
            LoadoutEntry(component_id=component_id, display_name=component_id, enabled=enabled, order=index)
            for index, component_id in enumerate(component_ids)
        ],
    )
