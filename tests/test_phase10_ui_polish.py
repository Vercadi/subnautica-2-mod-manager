from __future__ import annotations

from s2_mod_manager.ui.tabs.installed_mods_tab import _empty_selection
from s2_mod_manager.ui.ui_tokens import ui_tokens_for_size
from s2_mod_manager.ui.widgets.mod_row import PlaceholderMod, _fit_text, _row_badges, _thumbnail_label


def test_fit_text_middle_truncates_long_labels() -> None:
    label = "Extremely Long Subnautica 2 UE4SS Gameplay Overhaul With Pak Bundle Companions"

    fitted = _fit_text(label, 34)

    assert len(fitted) <= 34
    assert " ... " in fitted
    assert fitted.startswith("Extremely")
    assert fitted.endswith("Companions")


def test_row_badges_surface_profile_preview_state_without_overflow() -> None:
    tokens = ui_tokens_for_size("default")
    mod = PlaceholderMod(
        name="Very Long Mod",
        version="library",
        description="Imported component",
        badges=["UE4SS", "Pak", "Runtime", "Loose", "Extra"],
        status="Library",
        state="library",
        in_active_profile=True,
        profile_enabled=False,
        profile_order=2,
        deployment_status="2 create, 1 overwrite",
        warning="Review needed",
    )

    badges = _row_badges(mod, tokens)
    labels = [label for label, _color in badges]

    assert len(labels) <= 6
    assert "Loadout #3" in labels
    assert "Off" in labels
    assert labels[-1].startswith("+") or "Review" in labels


def test_thumbnail_label_matches_component_family() -> None:
    assert _thumbnail_label(PlaceholderMod("Pak", "", "", badges=["Pak"])) == "PAK"
    assert _thumbnail_label(PlaceholderMod("UE", "", "", badges=["UE4SS"])) == "UE"
    assert _thumbnail_label(PlaceholderMod("Runtime", "", "", badges=["UE4SS Runtime"])) == "CORE"


def test_minimum_window_budget_keeps_center_panel_usable() -> None:
    tokens = ui_tokens_for_size("default")
    shell_width = int(1280 * 0.92)
    fixed_width = tokens.nav_width + tokens.inspector_width + (tokens.panel_gap * 3) + 48
    center_budget = shell_width - fixed_width

    assert center_budget >= 500


def test_empty_selection_is_safe_for_inspector() -> None:
    empty = _empty_selection()

    assert empty.state == "empty"
    assert not empty.enabled
    assert "Scan" in empty.description
