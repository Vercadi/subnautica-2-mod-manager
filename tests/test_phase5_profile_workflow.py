from __future__ import annotations

from pathlib import Path

import pytest

from s2_mod_manager.core.profile_store import ProfileStore
from s2_mod_manager.core.profile_workflow import build_loadout_warnings, loadout_chips
from s2_mod_manager.models.archive_info import COMPONENT_PAK_BUNDLE, COMPONENT_UE4SS_MOD, COMPONENT_UE4SS_RUNTIME
from s2_mod_manager.models.library import LibraryComponent
from s2_mod_manager.models.profile import LoadoutEntry, VANILLA_PROFILE_ID


def test_profile_persistence_roundtrip(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Exploration")
    store.add_component(profile.profile_id, "pak_lights", [_component("pak_lights", "Lights")])

    reloaded = ProfileStore(tmp_path / "data")

    assert reloaded.active_profile().name == "Exploration"
    assert reloaded.active_profile().entries[0].component_id == "pak_lights"


def test_vanilla_profile_is_protected(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")

    assert store.active_profile().profile_id == VANILLA_PROFILE_ID
    with pytest.raises(ValueError):
        store.rename_profile(VANILLA_PROFILE_ID, "Renamed")
    with pytest.raises(ValueError):
        store.delete_profile(VANILLA_PROFILE_ID)
    with pytest.raises(ValueError):
        store.add_component(VANILLA_PROFILE_ID, "pak_lights", [_component("pak_lights", "Lights")])


def test_add_remove_enable_disable(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")
    component = _component("pak_lights", "Lights")

    assert store.add_component(profile.profile_id, component.component_id, [component])
    assert not store.add_component(profile.profile_id, component.component_id, [component])
    assert store.set_component_enabled(profile.profile_id, component.component_id, False)
    assert not store.active_profile().entries[0].enabled
    assert store.set_component_enabled(profile.profile_id, component.component_id, True)
    assert store.remove_component(profile.profile_id, component.component_id)
    assert not store.active_profile().entries


def test_reorder_helpers(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")
    components = [_component("a", "A"), _component("b", "B"), _component("c", "C")]
    for component in components:
        store.add_component(profile.profile_id, component.component_id, components)

    assert store.move_component(profile.profile_id, "c", -2)

    assert [entry.component_id for entry in store.active_profile().ordered_entries()] == ["c", "a", "b"]
    assert [entry.order for entry in store.active_profile().ordered_entries()] == [0, 1, 2]


def test_duplicate_rename_delete_non_vanilla(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    source = store.create_profile("Main")
    store.add_component(source.profile_id, "pak_lights", [_component("pak_lights", "Lights")])

    duplicate = store.duplicate_profile(source.profile_id, "Dive Night")
    renamed = store.rename_profile(duplicate.profile_id, "Deep Dive")
    store.delete_profile(source.profile_id)

    assert renamed.name == "Deep Dive"
    assert store.active_profile().profile_id == duplicate.profile_id
    assert store.get_profile(source.profile_id) is None
    assert len(store.active_profile().entries) == 1


def test_loadout_entries_must_be_imported_components(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")

    with pytest.raises(ValueError):
        store.add_component(profile.profile_id, "missing", [])


def test_warning_generation_for_missing_runtime_and_review(tmp_path: Path) -> None:
    profile = ProfileStore(tmp_path / "data").create_profile("Main")
    profile.entries = [
        LoadoutEntry("ue4ss_mod", "HUD", enabled=True, order=0),
        LoadoutEntry("missing", "Missing Mod", enabled=True, order=1),
    ]
    components = [
        _component(
            "ue4ss_mod",
            "HUD",
            component_type=COMPONENT_UE4SS_MOD,
            warnings=["Ambiguous multi-component source; review before adding to a profile."],
        )
    ]

    warnings = build_loadout_warnings(profile, components, ue4ss_runtime_installed=False)
    messages = [warning.message for warning in warnings]

    assert any("UE4SS runtime" in message for message in messages)
    assert any("Import/add a UE4SS Runtime package" in message for message in messages)
    assert any("Ambiguous" in message for message in messages)
    assert any("missing from the imported library" in message for message in messages)


def test_warning_generation_allows_runtime_in_profile_or_install(tmp_path: Path) -> None:
    profile = ProfileStore(tmp_path / "data").create_profile("Main")
    profile.entries = [
        LoadoutEntry("runtime", "UE4SS Runtime", enabled=True, order=0),
        LoadoutEntry("ue4ss_mod", "HUD", enabled=True, order=1),
    ]
    components = [
        _component("runtime", "UE4SS Runtime", component_type=COMPONENT_UE4SS_RUNTIME),
        _component("ue4ss_mod", "HUD", component_type=COMPONENT_UE4SS_MOD),
    ]

    assert not build_loadout_warnings(profile, components, ue4ss_runtime_installed=False)

    install_runtime_profile = ProfileStore(tmp_path / "other-data").create_profile("Main")
    install_runtime_profile.entries = [LoadoutEntry("ue4ss_mod", "HUD", enabled=True, order=0)]
    assert not build_loadout_warnings(install_runtime_profile, components[1:], ue4ss_runtime_installed=True)


def test_chip_strip_state(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")
    components = [_component("a", "A"), _component("b", "B")]
    for component in components:
        store.add_component(profile.profile_id, component.component_id, components)
    store.set_component_enabled(profile.profile_id, "b", False)

    chips = loadout_chips(store.active_profile(), components)

    assert [chip.label for chip in chips] == ["A", "B"]
    assert [chip.enabled for chip in chips] == [True, False]


def _component(
    component_id: str,
    name: str,
    *,
    component_type: str = COMPONENT_PAK_BUNDLE,
    warnings: list[str] | None = None,
) -> LibraryComponent:
    return LibraryComponent(
        component_id=component_id,
        source_id=f"src_{component_id}",
        display_name=name,
        component_type=component_type,
        install_kind="standard_mod",
        badges=["Pak"],
        target_hint=r"Subnautica2\Content\Paks\~mods",
        file_count=1,
        warnings=warnings or [],
    )
