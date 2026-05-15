from __future__ import annotations

from pathlib import Path

import pytest

from s2_mod_manager.core.help_about import build_help_about_view
from s2_mod_manager.core.import_review import build_import_review, import_review_selection, selection_from_review
from s2_mod_manager.core.library_store import LibraryStore
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.core.profile_actions import (
    DEFAULT_MODDED_PROFILE_NAME,
    enable_imported_sources,
    smart_toggle_component,
)
from s2_mod_manager.core.profile_store import ProfileStore
from s2_mod_manager.core.recovery_workflow import build_recovery_view, can_execute_recovery_action
from s2_mod_manager.core.settings_store import load_preferences, save_settings
from s2_mod_manager.core.settings_workflow import (
    build_settings_view,
    update_popup_policy,
    update_popup_preference,
    update_ue4ss_activation_preference,
)
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.archive_info import COMPONENT_LOOSE_OVERLAY, COMPONENT_UE4SS_MOD
from s2_mod_manager.models.library import LibraryComponent, LibraryComponentFile
from s2_mod_manager.ui.shell.navigation import NAV_ITEMS
from s2_mod_manager.ui.tabs.installed_mods_tab import preview_apply_action_state
from s2_mod_manager.ui.widgets.mod_row import PlaceholderMod, _row_action_hint


def test_navigation_items_are_actionable_release_surfaces() -> None:
    labels = [label for label, _icon in NAV_ITEMS]

    assert labels == [
        "Installed Mods",
        "Profiles",
        "Recovery",
        "Diagnostics",
        "Activity",
        "Help / Support",
    ]
    assert "Mod Browser" not in labels


def test_profile_store_bulk_and_top_bottom_helpers(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")
    components = [_component("a", "A"), _component("b", "B"), _component("c", "C")]
    for component in components:
        store.add_component(profile.profile_id, component.component_id, components)

    assert store.move_component_to_bottom(profile.profile_id, "a")
    assert [entry.component_id for entry in store.active_profile().ordered_entries()] == ["b", "c", "a"]
    assert store.move_component_to_top(profile.profile_id, "a")
    assert [entry.component_id for entry in store.active_profile().ordered_entries()] == ["a", "b", "c"]

    assert store.set_all_enabled(profile.profile_id, False) == 3
    assert [entry.enabled for entry in store.active_profile().ordered_entries()] == [False, False, False]
    assert store.set_all_enabled(profile.profile_id, True) == 3
    assert store.remove_all_components(profile.profile_id) == 3
    assert store.active_profile().entries == []


def test_bulk_helpers_keep_vanilla_protected(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")

    with pytest.raises(ValueError):
        store.set_all_enabled("vanilla", False)
    with pytest.raises(ValueError):
        store.remove_all_components("vanilla")


def test_popup_preferences_roundtrip_and_settings_text(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    save_settings(settings, S2AppPaths())

    prefs = update_popup_policy(settings, "Critical safety only")
    view = build_settings_view(
        S2AppPaths(),
        data_dir=tmp_path / "data",
        library_dir=tmp_path / "data" / "library",
        backup_dir=tmp_path / "backups",
        preferences=prefs,
    )

    loaded = load_preferences(settings)
    assert loaded.show_update_popups is False
    assert loaded.show_info_popups is False
    assert loaded.show_success_popups is False
    assert loaded.show_warning_popups is False
    assert load_preferences(settings).show_warning_popups is False
    assert view.popup_policy_label == "Critical safety only"
    assert "critical safety confirmations are always shown" in view.popup_text


def test_popup_policy_warning_mode_roundtrip(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    save_settings(settings, S2AppPaths())

    prefs = update_popup_policy(settings, "Warnings + critical only")

    assert prefs.show_update_popups is False
    assert prefs.show_info_popups is False
    assert prefs.show_success_popups is False
    assert prefs.show_warning_popups is True
    assert load_preferences(settings).popup_policy_label == "Warnings + critical only"


def test_invalid_popup_preference_is_rejected(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    save_settings(settings, S2AppPaths())

    with pytest.raises(ValueError):
        update_popup_preference(settings, "show_everything_forever", False)


def test_ue4ss_activation_preferences_roundtrip(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    save_settings(settings, S2AppPaths())

    prefs = update_ue4ss_activation_preference(settings, "ue4ss_write_mods_json", True)
    view = build_settings_view(
        S2AppPaths(),
        data_dir=tmp_path / "data",
        library_dir=tmp_path / "data" / "library",
        backup_dir=tmp_path / "backups",
        preferences=prefs,
    )

    loaded = load_preferences(settings)
    assert loaded.ue4ss_write_enabled_txt is True
    assert loaded.ue4ss_write_mods_json is True
    assert loaded.ue4ss_write_mods_txt is False
    assert "mods.json=on" in view.ue4ss_policy_text
    assert "writes stay guarded" in view.ue4ss_policy_text


def test_help_about_view_has_support_link_slots(tmp_path: Path) -> None:
    view = build_help_about_view(
        paths=S2AppPaths(),
        data_dir=tmp_path / "data",
        library_dir=tmp_path / "data" / "library",
        backup_dir=tmp_path / "backups",
        log_dir=tmp_path / "data" / "logs",
        docs_dir=tmp_path / "docs",
        support_report="support",
    )

    assert hasattr(view, "patreon_url")
    assert hasattr(view, "kofi_url")
    assert view.github_url.startswith("https://github.com/")
    assert view.nexus_url.startswith("https://www.nexusmods.com/")
    assert view.patreon_url == "https://www.patreon.com/c/Vercadi"
    assert view.kofi_url == "https://ko-fi.com/vercadi"


def test_row_action_hint_explains_disabled_switch_states() -> None:
    assert _row_action_hint(PlaceholderMod("Candidate", "", "", state="candidate_source"), can_toggle=False) == "import first"
    assert (
        _row_action_hint(PlaceholderMod("Library", "", "", state="library", component_id="lib"), can_toggle=True)
        == "toggle adds"
    )
    assert (
        _row_action_hint(
            PlaceholderMod("Vanilla", "", "", state="library", component_id="lib"),
            can_toggle=True,
            profile_protected=True,
        )
        == "enable creates profile"
    )
    assert _row_action_hint(
        PlaceholderMod("Profile", "", "", state="library", in_active_profile=True, profile_enabled=True),
        can_toggle=True,
    ) == "enabled"
    assert _row_action_hint(
        PlaceholderMod("Protected", "", "", state="library", in_active_profile=True),
        can_toggle=False,
    ) == "protected"


def test_smart_toggle_on_adds_and_enables_imported_component(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")
    component = _component("pak_lights", "Lights")

    result = smart_toggle_component(store, component.component_id, [component])

    assert result.ok
    assert result.changed_count == 1
    active = store.active_profile()
    assert active.profile_id == profile.profile_id
    assert [(entry.component_id, entry.enabled) for entry in active.entries] == [("pak_lights", True)]


def test_smart_toggle_off_disables_existing_profile_entry(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")
    component = _component("pak_lights", "Lights")
    store.add_component(profile.profile_id, component.component_id, [component])

    result = smart_toggle_component(store, component.component_id, [component])

    assert result.ok
    assert result.changed_count == 1
    assert store.active_profile().entries[0].enabled is False


def test_smart_toggle_from_vanilla_creates_default_modded_profile(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    component = _component("pak_lights", "Lights")

    result = smart_toggle_component(store, component.component_id, [component])

    assert result.ok
    assert result.created_profile
    assert store.active_profile().name == DEFAULT_MODDED_PROFILE_NAME
    assert store.active_profile().entries[0].component_id == component.component_id
    assert store.active_profile().entries[0].enabled is True


def test_preview_apply_primary_action_state() -> None:
    disabled = preview_apply_action_state(
        [PlaceholderMod("Imported", "", "", state="library", component_id="a")]
    )
    enabled = preview_apply_action_state(
        [
            PlaceholderMod(
                "Enabled",
                "",
                "",
                state="library",
                component_id="a",
                in_active_profile=True,
                profile_enabled=True,
            )
        ]
    )

    assert disabled == ("Preview & Apply Profile", False, "Enable at least one imported mod.")
    assert enabled == ("Preview & Apply Profile", True, "Review exact target paths before applying.")


def test_import_and_enable_imports_source_and_enables_components(tmp_path: Path) -> None:
    archive = tmp_path / "lights.zip"
    _write_zip(archive, {"Lights/Lights_P.pak": b"pak"})
    library = LibraryStore(tmp_path / "data")
    profile_store = ProfileStore(tmp_path / "data")
    review = build_import_review([archive])
    selection = selection_from_review(review)

    imported = import_review_selection(library, review, selection)
    result = enable_imported_sources(profile_store, imported, library.list_components())

    assert result.ok
    assert result.enabled_component_ids == [library.list_components()[0].component_id]
    assert profile_store.active_profile().name == DEFAULT_MODDED_PROFILE_NAME
    assert profile_store.active_profile().entries[0].enabled is True


def test_runtime_warning_text_is_user_guidance_in_profile_warning(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    profile = store.create_profile("Main")
    component = _component("ue_mod", "Lua Mod", component_type=COMPONENT_UE4SS_MOD)
    store.add_component(profile.profile_id, component.component_id, [component])

    from s2_mod_manager.core.profile_workflow import build_loadout_warnings

    warnings = build_loadout_warnings(store.active_profile(), [component], ue4ss_runtime_installed=False)

    assert any(
        "Requires UE4SS runtime. Import/add a UE4SS Runtime package to this profile, or install UE4SS manually first."
        in warning.message
        for warning in warnings
    )


def test_smart_toggle_does_not_bypass_review_required_loose_overlay(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "data")
    component = _component(
        "loose",
        "SN2P",
        component_type=COMPONENT_LOOSE_OVERLAY,
        install_kind="loose_overlay",
        files=[LibraryComponentFile("dxgi.dll", role="loose", target_hint="dxgi.dll")],
    )

    result = smart_toggle_component(store, component.component_id, [component])

    assert not result.ok
    assert "needs review" in result.message
    assert store.active_profile().name == "Vanilla"
    assert store.active_profile().entries == []


def test_recovery_without_manifest_records_has_no_uninstall_action(tmp_path: Path) -> None:
    paths = S2AppPaths(client_root=tmp_path / "RealSubnautica2")
    view = build_recovery_view(ManifestStore(tmp_path / "data"), paths)

    allowed, reason = can_execute_recovery_action(view, ["install"])

    assert not allowed
    assert "not uninstallable" in reason.casefold() or "no uninstallable" in reason.casefold()
    assert not view.action_state.allow_uninstall_all


def _component(
    component_id: str,
    name: str,
    *,
    component_type: str = "pak_bundle",
    install_kind: str = "standard_mod",
    files: list[LibraryComponentFile] | None = None,
) -> LibraryComponent:
    return LibraryComponent(
        component_id=component_id,
        source_id=f"src_{component_id}",
        display_name=name,
        component_type=component_type,
        install_kind=install_kind,
        badges=["Pak"],
        target_hint=r"Subnautica2\Content\Paks\~mods",
        file_count=len(files or []) or 1,
        files=files or [],
    )


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    import zipfile

    with zipfile.ZipFile(path, "w") as archive:
        for member, data in members.items():
            archive.writestr(member, data)
