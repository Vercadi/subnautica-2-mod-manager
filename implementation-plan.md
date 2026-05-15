# Implementation Plan

## Goal

Build a Subnautica 2 mod manager at the same engineering level as the Windrose and Conan managers, while keeping the feature set specific to S2:

- local client install management
- pak bundle support
- UE4SS runtime and mod support
- drag-and-drop import
- manager-owned archive/library storage
- profiles/loadouts
- preview-first apply/uninstall
- backup and restore
- polished Subnautica-inspired UI

## Port Strategy

Use Windrose as the base for Unreal archive deployment and UE4SS handling. Use Conan as the base for managed local library, active profiles, selected uninstall, and profile-driven UX.

Do not copy game-specific features that do not exist for S2:

- Conan Workshop/SteamCMD
- Conan modlist.txt generation
- Conan dedicated server workflow
- Windrose hosted server workflow
- Windrose server config/RCON/WindrosePlus logic

## Phase 0: Repo And Planning

Deliverables:

- Initialize Git repository.
- Add `.gitignore`.
- Add planning docs:
  - `research.md`
  - `design.md`
  - `theme.md`
  - `technical-spec.md`
  - `implementation-plan.md`
- Keep `Mods/` as local import inbox, ignored by Git.

Acceptance:

- Repo can show clean tracked planning files.
- Sample local archives are not accidentally tracked.

## Phase 1: Application Skeleton

Deliverables:

- `requirements.txt`
- `app.py`
- `s2_mod_manager/__init__.py`
- app directory resolver for source vs packaged mode
- logging service
- basic CustomTkinter root window
- `UiTokens` and first `Abyssal HUD` token pass
- draft-aligned shell:
  - full-window background image layer
  - cyan bordered main console shell
  - top command bar
  - left navigation rail
  - center content area
  - right inspector area
  - bottom console/load-order strip
- tabs/views created lazily:
  - Installed Mods
  - Loadout
  - Profiles
  - Backups
  - Mod Browser
  - Settings
  - Diagnostics

Acceptance:

- `python app.py` opens the shell.
- Data/log directories are created.
- UI does not use stock CTk blue defaults beyond initial bootstrapping.
- The first screen resembles the supplied draft's layout even before real mod data is wired in.
- Tests can import package modules.

## Phase 2: Discovery And Settings

Deliverables:

- `S2AppPaths` model.
- Steam library discovery.
- `appmanifest_1962700.acf` parser/reuse.
- Manual path validation.
- `settings.json` persistence.
- Dashboard path/build status.
- Launch/open-folder helpers.

Acceptance:

- Detects a Steam install such as `<SteamLibrary>\steamapps\common\Subnautica2`.
- Validates required exe and pak paths.
- Reads `version.json`, `version.txt`, and Steam build id when available.
- Manual path entry rejects invalid roots with useful messages.

Tests:

- manifest parsing
- root validation
- derived path generation
- settings roundtrip

## Phase 3: Archive And Folder Import

Deliverables:

- archive reader for `.zip` and `.7z`
- optional `.rar` support detection
- folder scanner
- archive inspector
- UE4SS runtime detector
- UE4SS mod detector
- pak bundle grouping
- unsafe path rejection
- scan results model
- local library store
- import into manager-owned storage

Acceptance:

- Sample UE4SS runtime zip classifies correctly.
- Sample SN2ModSettings zip maps as UE4SS mod.
- Sample Infinite Oxygen zip maps as pak bundle with companions.
- Sample Hide HUD 7z can be inspected through py7zr once dependencies are installed.
- Import does not write to the game folder.

Tests:

- zip scan
- 7z scan
- pak companion grouping
- UE4SS runtime shape
- UE4SS mod full-prefix stripping
- duplicate source hash reuse
- invalid traversal rejection

## Phase 4: Installed Mods UI And Drag-Drop

Deliverables:

- Installed Mods view with draft-aligned center list.
- Drop zone at the top of the center workspace.
- Explicit Scan Mods Inbox action.
- Import Selected and Import All actions.
- Multi-file import workflow through scanned inbox sources.
- Folder import.
- Source/component list.
- Candidate-vs-imported state.
- Manager-owned source copy into `data/library`.
- Persistent `data/library_state.json`.
- Filters and status chips.
- Context menu actions.
- Right inspector tabs:
  - Overview
  - Files
  - Dependencies
  - Changelog
- Bottom console output panel.

Acceptance:

- Scanning mixed inbox files produces a scan summary.
- Unsupported files are listed but do not block valid imports.
- Imported sources are visible after restart.
- Component rows reserve fixed action/badge space and do not jump.
- Selecting a row updates the right inspector.
- Console output shows scan/import messages.
- Apply/install actions stay disabled until Phase 6.

Tests:

- library persistence
- duplicate import behavior
- scan summary counts
- imported-vs-candidate state

Deferred polish:

- Native drag/drop through tkinterdnd2.
- Context menu actions.
- Inline row selection and richer multi-select behavior.

## Phase 5: Profiles And Loadout

Deliverables:

- `ProfileStore`.
- Permanent `Vanilla` profile.
- active loadout state.
- Initial loadout controls in the Installed Mods shell.
- Ordered enabled components.
- bottom load-order chip strip in the Installed Mods shell.
- Add/remove/reorder/enable/disable.
- Save, save as, duplicate, rename, delete.
- Profile diff renderer.
- Missing/dependency warnings.

Acceptance:

- Users can build a named profile from imported components.
- Vanilla profile remains protected.
- Profiles persist across restart.
- UE4SS mods warn when runtime is absent from install or profile.
- Reordering updates the bottom chip strip.
- Apply/install actions stay disabled until Phase 6.

Tests:

- profile roundtrip
- protected Vanilla behavior
- reorder helpers
- diff output
- profile warning generation

Deferred polish:

- Dedicated full Loadout tab.
- Dedicated Profiles tab.
- Profile diff renderer.
- Native drag reorder.

## Phase 6: Deployment Planner And Apply Preview

Deliverables:

- `DeploymentPlan` model.
- target mapping:
  - pak bundles to `Content\Paks\~mods`
  - UE4SS runtime to `Binaries\Win64`
  - UE4SS mods to `Binaries\Win64\ue4ss\Mods`
  - loose overlays only after review
- conflict detection.
- inspector/console preview.
- overwrite detection.
- disabled-entry skip detection.
- missing source/component detection.
- missing UE4SS runtime warning.
- dry-run mode with real writes disabled.

Acceptance:

- Previewing a profile shows exact target paths before writing.
- Preview maps `~mods` without creating it.
- Existing targets are marked as overwrites.
- Loose overlays are blocked behind review.
- Target conflicts are errors.
- Dry-run preview is available before real writes.
- Real apply remains disabled by default.

Tests:

- plan target mapping
- disabled entries skipped
- missing library source handling
- missing UE4SS runtime warning
- loose overlay review blocking
- conflict detection
- overwrite detection
- dry-run preview output

Completed in Phase 7 apply foundation:

- Real file copy apply.
- Backup-before-overwrite execution.
- Install manifest persistence.
- Partial failure recovery.

## Phase 7: Guarded Apply Foundation

Deliverables:

- guarded apply execution.
- `ManifestStore`.
- `InstallRecord` model.
- backup helper for overwrites.
- fake test install marker support.
- partial failure manifest records.

Acceptance:

- Apply executes only non-blocked, non-dry-run plans.
- Apply refuses non-test installs unless `allow_real_apply=True`.
- Apply creates target directories and copies planned files.
- Apply backs up overwrites before copy.
- Manifest records completed, refused, and failed installs.

Tests:

- create targets in fake install
- overwrite backup creation
- manifest write/read
- blocked plan refusal
- missing source refusal
- partial failure manifest behavior
- no writes when `allow_real_apply` is false

## Phase 8: Uninstall, Restore, And Recovery

Deliverables:

- uninstall selected.
- uninstall all managed.
- restore overwritten originals.
- restore vanilla preview.
- quarantine preview model.
- recovery summary.
- recovery/activity timeline.
- backup browser.

Acceptance:

- Uninstall removes only manifest-tracked files.
- Uninstall restores backups for overwritten originals.
- Missing deployed files are tolerated.
- Unknown files are left untouched.
- Restore vanilla preview does not touch saves.
- Unknown files are only quarantine candidates through explicit preview.
- Read-only recovery summary is visible in the UI.

Tests:

- selected uninstall
- uninstall all
- restore backup
- unknown files untouched
- missing deployed files tolerated
- failed partial install uninstallability
- quarantine preview generation
- restore vanilla preview
- no save deletion

## Phase 9: Diagnostics And Support

Deliverables:

- diagnostics tab.
- redacted support report.
- archive support status.
- dependency status for py7zr/rarfile/UnRAR.
- last log excerpt.
- copy/export diagnostics.
- path/build and Steam manifest status.
- library/profile/loadout/deployment/recovery counts.
- UE4SS runtime state.

Acceptance:

- Diagnostics do not expose secrets.
- Report includes S2 build, paths, UE4SS state, library counts, backup counts, and last operation.
- Save paths are omitted from support reports.
- User home/profile path prefixes are redacted.

Tests:

- redaction
- support report generation
- archive support reporting
- recovery/library/profile counts
- log excerpt truncation
- save path omission

## Phase 10: Draft Fidelity And Theme Polish

Deliverables:

- Replace default CTk blue usage with `Abyssal HUD` tokens.
- underwater background asset integration.
- simulated glass panels with dark fills and cyan borders.
- Navigation rail and top command bar polish.
- O2/System Health gauge drawn with canvas.
- optional depth/radar HUD if it does not crowd the app.
- Drop-zone sonar style.
- Mod row thumbnails and badges.
- Right inspector visual polish.
- Bottom console/load-order strip polish.
- Preview modal polish.
- Icon asset pass.
- App icon.

Acceptance:

- UI reads as a Subnautica-specific tool.
- The app is recognizably close to the supplied draft.
- Text fits at compact/default/large UI sizes.
- No controls overlap at minimum window size.
- Primary workflows are usable without reading documentation.
- Static background and HUD drawings do not make scrolling/import operations sluggish.

Manual verification:

- First run at 1280x760.
- Default run at 1500x900.
- Large UI size.
- Mixed valid/invalid drag/drop.
- Long mod filenames.

## Phase 10.5: UE4SS Quality Pass

Deliverables:

- UE4SS enable-state policy:
  - `enabled.txt`
  - optional `mods.json`
  - optional `mods.txt`
- Protected native UE4SS mod warnings.
- Root `scripts/main.lua` and `dlls/main.dll` archive-shape tests.
- Root `scripts/` zip wrapping into a stable mod folder name.
- Optional read-only `scripts/config.lua` detection in the inspector.

Acceptance:

- UE4SS deployment previews show which enable-state files would be written.
- Native/core UE4SS mods are visible only with warnings.
- Root-script UE4SS archives classify and deploy predictably.
- `config.lua` is reported when present without editing arbitrary Lua.

## Phase 11: Packaging And Release Prep

Deliverables:

- PyInstaller spec.
- build script.
- portable smoke test checklist.
- privacy policy.
- changelog.
- Nexus/GitHub release notes draft.

Acceptance:

- Built app launches outside the repo.
- Packaged app writes to `%LOCALAPPDATA%\Subnautica2ModManager`.
- Source-mode tests pass.
- Smoke test applies and uninstalls a harmless fixture mod in a temporary fake S2 install.

## First Implementation Sequence

1. Scaffold package, requirements, app shell, logging, and UI tokens.
2. Build the draft-aligned static shell with placeholder data.
3. Implement S2 path model and discovery.
4. Add tests for local S2 path validation using fake fixtures.
5. Port archive reader and inspector concepts.
6. Implement S2-specific framework detector and target mapping.
7. Build library store and importer.
8. Wire real imported components into the Installed Mods list and inspector.
9. Add profiles/loadout and bottom chip strip.
10. Add preview/apply/manifest/backup.
11. Add uninstall all and restore vanilla.
12. Polish theme, assets, and package.

## Risk Register

### S2 Modding Conventions May Shift

Mitigation:

- Keep path mapping centralized.
- Store game build with profile/apply records.
- Make warnings non-blocking unless paths are invalid.

### UE4SS Archive Shapes Vary

Mitigation:

- Support common path prefixes.
- Add review dialog for ambiguous scans.
- Keep detector test fixtures based on real sample archives.

### Users May Drop Folders Instead Of Archives

Mitigation:

- Treat folders as first-class import sources.
- Copy to manager-owned storage before applying.
- Preserve relative paths in scan results.

### Uninstall Can Be Risky

Mitigation:

- Only auto-remove manifest-tracked paths.
- Restore overwritten backups.
- Quarantine unknown files instead of deleting.
- Require preview for uninstall all and restore vanilla.

### Visual Polish Could Delay Core Safety

Mitigation:

- Implement the draft layout and tokens from day one with placeholder content.
- Keep bitmap/asset polish in Phase 9.
- Keep the UI operational before decorative refinements.

### Custom Glass And Titlebar Effects May Be Expensive

Mitigation:

- Simulate glass with dark opaque colors instead of real blur.
- Use standard Windows chrome or a minimal custom header until the app behavior is stable.
- Draw gauges/radar in canvas and keep animation optional.
