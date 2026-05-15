from __future__ import annotations

from s2_mod_manager import __app_name__, __version__
from s2_mod_manager.core.app_dirs import resolve_app_dirs
from s2_mod_manager.ui.tabs.installed_mods_tab import PLACEHOLDER_MODS
from s2_mod_manager.ui.ui_tokens import ui_tokens_for_size


def test_app_metadata_present() -> None:
    assert __app_name__ == "Subnautica 2 Mod Manager"
    assert __version__


def test_app_dirs_resolve_to_repo_in_source_mode() -> None:
    dirs = resolve_app_dirs()
    assert dirs.root_dir.name == "Mod Manager"
    assert dirs.data_dir.name == "data"
    assert dirs.backup_dir.name == "backups"


def test_ui_tokens_have_draft_shell_dimensions() -> None:
    tokens = ui_tokens_for_size("default")
    assert tokens.nav_width >= 200
    assert tokens.inspector_width >= 380
    assert tokens.bottom_strip_height >= 140
    assert tokens.colors.shell_border.startswith("#")


def test_placeholder_mods_seed_static_shell() -> None:
    assert len(PLACEHOLDER_MODS) >= 5
    assert PLACEHOLDER_MODS[0].badges
