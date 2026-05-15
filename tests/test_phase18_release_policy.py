from __future__ import annotations

import zipfile
from pathlib import Path

from s2_mod_manager.core.apply_workflow import build_apply_preview
from s2_mod_manager.core.archive_inspector import inspect_archive
from s2_mod_manager.core.deployment_planner import build_deployment_plan
from s2_mod_manager.core.diagnostics import collect_diagnostics
from s2_mod_manager.core.first_run import prepare_first_run_state
from s2_mod_manager.core.import_review import build_import_review
from s2_mod_manager.core.library_store import LibraryStore
from s2_mod_manager.core.library_workflow import build_library_view_state
from s2_mod_manager.core.profile_store import ProfileStore
from s2_mod_manager.core.review_policy import (
    is_review_required_component,
    loose_overlay_policy,
    review_required_warning,
)
from s2_mod_manager.core.manifest_store import ManifestStore
from s2_mod_manager.models.app_paths import S2AppPaths
from s2_mod_manager.models.archive_info import COMPONENT_LOOSE_OVERLAY, INSTALL_KIND_LOOSE_OVERLAY
from s2_mod_manager.models.deployment import ACTION_BLOCKED
from s2_mod_manager.models.library import LibraryComponent, LibraryComponentFile, LibrarySource
from s2_mod_manager.models.profile import LoadoutEntry, ModProfile
from s2_mod_manager.models.recovery import RecoverySummary
from s2_mod_manager.core.app_dirs import AppDirs


def test_loose_overlay_policy_text_names_targets_and_user_action() -> None:
    policy = loose_overlay_policy(target_hints=["dxgi.dll", "snsnp_settings.ini"])

    assert policy.policy_id == "loose_overlay_review_required"
    assert "loose root overlay" in policy.title
    assert "dxgi.dll" in policy.text
    assert "blocked" in policy.text.casefold()
    assert "mod author's install instructions" in policy.text
    assert is_review_required_component(COMPONENT_LOOSE_OVERLAY, INSTALL_KIND_LOOSE_OVERLAY)
    assert "Loose overlay files require explicit review" in review_required_warning(target_hints=["dxgi.dll"])


def test_import_review_and_library_surface_loose_overlay_policy(tmp_path: Path) -> None:
    archive = _archive(tmp_path / "SN2P.zip", {"dxgi.dll": b"dll", "snsnp_settings.ini": b"settings"})

    review = build_import_review([archive])
    component = review.sources[0].components[0]
    store = LibraryStore(tmp_path / "data")
    store.import_scan(inspect_archive(archive))
    view = build_library_view_state(store, [])
    item = view.library_items[0]

    assert component.review_policy_text
    assert "dxgi.dll" in component.review_policy_text
    assert "review required" in component.status_text
    assert item.review_policy_text
    assert "blocked" in item.warning.casefold()
    assert "Review-required loose overlays" in item.description


def test_blocked_apply_preview_has_actionable_loose_overlay_policy(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    source = _source(tmp_path)
    component = _loose_component(source.source_id)
    profile = ModProfile(
        profile_id="profile",
        name="Release Profile",
        entries=[LoadoutEntry(component.component_id, component.display_name, enabled=True, order=0)],
    )

    plan = build_deployment_plan(
        profile,
        sources=[source],
        components=[component],
        paths=paths,
        dry_run=False,
        real_apply_enabled=True,
    )
    preview = build_apply_preview(plan)

    assert plan.blocked
    assert plan.actions[0].action == ACTION_BLOCKED
    assert preview.review_required_count == 2
    assert "loose root overlay" in preview.review_policy_text.casefold()
    assert "dxgi.dll" in preview.review_policy_text
    assert "manual review" in preview.disabled_reason
    assert not preview.allow_apply


def test_first_run_messages_explain_release_safety_and_support_reports(tmp_path: Path) -> None:
    dirs = AppDirs(
        root_dir=tmp_path,
        data_dir=tmp_path / "data",
        backup_dir=tmp_path / "backups",
        log_dir=tmp_path / "data" / "logs",
        assets_dir=tmp_path / "assets",
    )

    messages = prepare_first_run_state(dirs, dirs.data_dir / "settings.json")
    text = "\n".join(messages)

    assert "Apply Preview writes only non-blocked managed files" in text
    assert "Loose root overlays" in text
    assert "Support reports are local text only" in text


def test_diagnostics_support_report_release_guidance_is_redacted(tmp_path: Path) -> None:
    home = Path("C:/Users/Alice")
    log = tmp_path / "app.log"
    log.write_text("blocked dxgi.dll for review\n", encoding="utf-8")
    data_dir = home / "AppData" / "Local" / "Subnautica2ModManager"

    report = collect_diagnostics(
        paths=S2AppPaths(client_root=home / "Games" / "Subnautica2"),
        data_dir=data_dir,
        library_store=LibraryStore(tmp_path / "data"),
        profile_store=ProfileStore(tmp_path / "data"),
        manifest_store=ManifestStore(tmp_path / "data"),
        deployment_plan=None,
        recovery_summary=RecoverySummary(),
        log_path=log,
        home=home,
    )
    text = report.support_report_text()

    assert "Safety:" in text
    assert "Support Workflow:" in text
    assert "mod archive name" in text
    assert "Do not paste save folders" in text
    assert "Alice" not in text
    assert "C:\\Users" not in text


def _archive(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return path


def _paths(tmp_path: Path) -> S2AppPaths:
    root = tmp_path / "Subnautica2"
    root.mkdir()
    (root / ".s2mm_fake_install").write_text("test-only", encoding="utf-8")
    (root / "Subnautica2" / "Content" / "Paks").mkdir(parents=True)
    (root / "Subnautica2" / "Binaries" / "Win64").mkdir(parents=True)
    return S2AppPaths(client_root=root)


def _source(tmp_path: Path) -> LibrarySource:
    managed = tmp_path / "data" / "library" / "sources" / "src_loose"
    managed.mkdir(parents=True)
    (managed / "dxgi.dll").write_bytes(b"dll")
    (managed / "snsnp_settings.ini").write_bytes(b"settings")
    return LibrarySource(
        source_id="src_loose",
        source_kind="folder",
        display_name="SN2P",
        original_path=tmp_path / "SN2P",
        managed_path=managed,
        source_hash="hash",
        component_ids=["loose"],
    )


def _loose_component(source_id: str) -> LibraryComponent:
    return LibraryComponent(
        component_id="loose",
        source_id=source_id,
        display_name="SN2P Loose Files",
        component_type=COMPONENT_LOOSE_OVERLAY,
        install_kind=INSTALL_KIND_LOOSE_OVERLAY,
        file_count=2,
        files=[
            LibraryComponentFile("dxgi.dll", role="loose", target_hint="dxgi.dll"),
            LibraryComponentFile("snsnp_settings.ini", role="loose", target_hint="snsnp_settings.ini"),
        ],
    )
