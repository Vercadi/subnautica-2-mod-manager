# Subnautica 2 Mod Manager

Planning repo for a Windows desktop mod manager for Subnautica 2.

The manager will be built at the same practical depth as the existing Windrose and Conan managers: game-specific path discovery, drag-and-drop mod import, managed archive storage, profiles/loadouts, preview-before-apply deployment, uninstall/restore workflows, diagnostics, and a polished custom UI.

## Current Status

Phase 21 first Nexus release-candidate artifact prep is complete on top of the completed Phase 20 clean-machine validation:

- Python package scaffold exists.
- `app.py` launches a CustomTkinter shell.
- Source-mode data, backup, asset, and log directories are resolved.
- Logging is initialized under `data/logs/`.
- The first static UI shell follows the draft layout with placeholder mod data.
- Phase 2 install discovery is wired:
  - Steam appmanifest discovery for app id `1962700`
  - S2 root validation
  - `version.json` / `version.txt` parsing
  - source-mode `data/settings.json` persistence
- Phase 3 scan/import foundation is wired:
  - `.zip`, `.7z`, and optional `.rar` archive reader abstraction
  - folder scanner
  - pak bundle grouping with `.ucas` / `.utoc` companions
  - UE4SS runtime and UE4SS mod detection
  - unsafe path rejection
  - read-only startup scan summary for `..\Mods`
  - manager-owned library copy API under `data/library`
- Phase 4 Installed Mods / Library workflow is wired:
  - explicit `Scan Mods Inbox`, `Import Selected`, and `Import All` actions
  - persisted manager library state in `data/library_state.json`
  - startup loads imported library components before inbox candidates
  - source rows, component rows, warning rows, unsupported source rows, and target hints
  - right inspector displays real scanned/library component metadata
- Phase 5 profile/loadout workflow is wired:
  - persistent `data/profiles.json`
  - protected permanent `Vanilla` profile
  - active profile selection
  - create, save-as, rename, and delete for non-Vanilla profiles
  - add/remove imported library components to/from the active profile
  - enable/disable and reorder active profile entries
  - bottom load-order chip strip driven by the active profile
  - profile warnings for missing components, UE4SS runtime requirements, and review-needed components
- Phase 6 dry-run deployment preview is wired:
  - active-profile target planning without game writes
  - pak, UE4SS runtime, and UE4SS mod target mapping
  - disabled-entry skips
  - missing source/component errors
  - target conflict and overwrite detection
  - loose overlay review blocking
  - inspector Preview tab and console `Preview Apply` output
- Phase 7 guarded apply engine is wired:
  - `data/install_manifest.json` persistence
  - overwrite backups under `backups/installs`
  - guarded installer that refuses dry-run, blocked, and non-test writes by default
  - fake test install marker support through `.s2mm_fake_install`
  - folder and archive-member source copying
  - partial-failure records remain in the manifest
- Phase 8 recovery workflow is wired:
  - manifest-driven selected uninstall and uninstall-all services
  - backup restore helpers for overwritten originals
  - missing deployed files are tolerated during uninstall
  - unknown files are left untouched and only reported
  - restore-vanilla preview reports managed and unknown files in `~mods` / `ue4ss\Mods`
  - quarantine preview candidates are modeled but not executed
  - recovery summary is shown in the console and inspector preview
- Phase 9 diagnostics/support report is wired:
  - S2 path/build and Steam manifest status
  - archive support status for `.zip`, `.7z`, and `.rar`
  - library, profile, loadout, manifest, backup, deployment, and recovery counts
  - UE4SS runtime state
  - redacted last-log excerpt
  - support report generation without upload
- Phase 10 draft-fidelity polish is wired:
  - darker underwater glass shell, tighter command/profile/action controls, and stronger cyan HUD treatment
  - long labels, source headers, load-order chips, and inspector values clamp or wrap for the 1280x760 minimum
  - empty library/inbox states are explicit instead of fake installed content
- Phase 11 import review UX is wired:
  - drop-zone file/folder browse fallback plus native file-drop hook when available
  - selected `.pak/.ucas/.utoc` companion files are grouped before import
  - scan results dialog shows sources, components, file counts, warnings, unsupported files, unsafe paths, ambiguity, and target hints
  - selected source/component imports copy only into `data/library`
  - duplicate source hashes reuse the existing library source and can merge newly selected components
- Phase 12 guarded Apply Profile UI is wired:
  - `Apply Preview` opens a confirmation dialog with profile, target, managed apply state, blocked state, planned files, skips, warnings, errors, and backup counts
  - real detected S2 installs can apply non-blocked managed plans through the guarded installer
  - fake test installs marked with `.s2mm_fake_install` can still execute clearly labeled test applies
  - apply results refresh manifest/recovery summaries and report completed/refused/failed state
- Phase 13 Recovery / Backups UI is wired:
  - console header opens a recovery dialog
  - install records show status, profile, target root, deployed files, backups, warnings, and errors
  - uninstall selected/all remove or restore only manifest-tracked managed files
  - restore-vanilla and quarantine candidates are preview-only; unknown files are reported, not deleted
- Phase 14 Settings UI is wired:
  - top command bar opens Settings
  - manual S2 path selection validates before saving
  - Auto Detect reruns discovery and persists detected state
  - Mods inbox path updates persist and trigger candidate rescans
  - data/library/backup paths are visible read-only until migration exists
  - archive support, UI scale placeholder, and safety indicators are shown
- Phase 15 packaging/first-run hardening is wired:
  - PyInstaller one-folder spec and portable build script
  - release metadata generation
  - source/frozen data, logs, backups, and library directory setup
  - missing/corrupt settings recovery messages
  - packaging, privacy, and changelog docs
- Phase 16 real sample validation is wired:
  - real `..\Mods` inbox scan was audited against the real detected S2 install in dry-run mode
  - wrapped UE4SS mod archives keep their inner mod folder and sibling Lua/config files together
  - import/profile/deployment/recovery/settings flows were validated without game writes
  - validation notes are captured in `docs\phase16-real-sample-validation.md`
- Phase 17 release-candidate fake-install hardening is wired:
  - real sample mods were imported, applied, backed up, uninstalled, and recovery-previewed against a fake `.s2mm_fake_install` target
  - `SN2P`-style loose root overlays remain blocked and review-required
  - restore-vanilla preview excludes uninstalled manifest records from current managed ownership
  - RC validation notes and Nexus blockers are captured in `docs\phase17-rc-fake-install-validation.md`
- Phase 18 Nexus release UX and policy hardening is wired:
  - review-required loose root overlays have consistent policy text in import, library, profile, apply preview, settings, diagnostics, and first-run surfaces
  - Nexus quickstart, supported shapes, safety limitations, troubleshooting, known issues, and support-report guidance are documented
  - `SN2P`-style root overlays remain blocked from automatic apply pending explicit target policy
- Phase 19 Windrose/Conan/UE4SS parity polish is wired:
  - dialogs use a shared centered placement helper with transient/grab behavior and screen clamping
  - command bar `Updates` uses GitHub Releases plumbing with manual checks and optional startup checks off by default
  - Help / About / Support exposes version/build metadata, support report copy/save actions, project links, and folder shortcuts
  - persistent bounded `data/activity_log.json` records startup, settings, scan/import, profile, preview/apply, recovery, support, and update events
  - Needs Attention summarizes missing install state, archive support gaps, scan warnings, review-required overlays, profile warnings, apply issues, recovery issues, and update availability
  - UE4SS native/core mod names get protected warnings, and root `scripts/` / `dlls/` mod archives surface wrapping hints
- Phase 20 clean-machine release validation is captured:
  - frozen portable launch was validated with isolated temp app data
  - required package contents, docs, icons/assets, and release metadata were checked
  - real sample mods were imported, profile-planned, test-applied, recovered, and uninstalled against a fake S2 install
  - final manual Nexus upload checks are listed in `docs\release-checklist.md`
- Phase 21 release-candidate packaging is wired:
  - Nexus release notes are captured in `docs\release-notes-v0.1.0.md`
  - release zip and SHA256 generation are scripted through `scripts\package_release.ps1`
  - package-content regression checks guard against shipping local data, logs, caches, or sample mod inbox content
- Phase 22 RC1 QA fixes are wired:
  - left navigation opens real Profiles, Recovery, Diagnostics, Activity, and Help/Support surfaces
  - the main shell now prioritizes a full-height compact mod list with profile/import controls moved into a side command rail
  - the whole mod-list panel participates in drag/drop import when native TkDND is available
  - UE4SS activation policy toggles are exposed for `enabled.txt`, `mods.json`, and `mods.txt`; guarded apply plans now generate those activation-file writes/deletes with manifest tracking
  - imported duplicates are hidden from inbox candidates, and duplicate import attempts are skipped
  - row toggles, warning details, row menus, and checkbox-based batch profile removal are functional for editable profiles
  - profile-safe On All, Off All, and Clear bulk actions are available
  - noncritical popup preferences persist in `settings.json`; critical safety confirmations remain always-on
  - Patreon and Ko-fi support links are configured for Vercadi
- Release apply/recovery is plug-and-play for supported managed mod shapes; loose overlays remain blocked.

## Nexus Release Quickstart

1. Extract the portable build outside the Subnautica 2 game folder.
2. Start the app and confirm the detected install in Settings.
3. Add `.zip`, `.7z`, pak bundles, or UE4SS folders through the Mods inbox, Browse, or Drop Zone.
4. Import sources into the manager library.
5. Create a non-Vanilla profile and add imported components.
6. Use Apply Preview to inspect exact planned targets, then apply the profile when the plan is ready.

Supported shapes: pak bundles with `.ucas`/`.utoc` companions, UE4SS runtime archives, UE4SS mods under `ue4ss\Mods\<ModName>`, wrapped UE4SS mod folders, `.zip`, `.7z`, and locally supported `.rar`.

Review-required shapes: loose root overlays such as `dxgi.dll`, root `.ini` files, and arbitrary files targeting unmanaged game-root paths. These are blocked from automatic apply because they can affect game launch or leave unmanaged files behind.

Support reports are local text only. Include the report text, mod filename, active profile, action clicked, and visible warning/error. Do not include saves or personal account paths.

Verified local target during planning:

- Install root example: `<SteamLibrary>\steamapps\common\Subnautica2`
- Steam app id: `1962700`
- Game executable: `Subnautica2.exe`
- Shipping executable: `Subnautica2\Binaries\Win64\Subnautica2-Win64-Shipping.exe`
- Pak folder: `Subnautica2\Content\Paks`
- UE4SS target folder: `Subnautica2\Binaries\Win64`
- Local sample mod inbox: `Mods\`

## Planning Docs

- [research.md](research.md) - findings from Windrose, Conan, the local S2 install, and sample mods.
- [design.md](design.md) - product design, UX flows, screens, and expected behavior.
- [theme.md](theme.md) - Subnautica-inspired visual system, tokens, component styling, and optional asset prompts.
- [technical-spec.md](technical-spec.md) - architecture, data model, path mapping, import classification, and safety rules.
- [implementation-plan.md](implementation-plan.md) - phased build plan and acceptance criteria.
- [PACKAGING.md](PACKAGING.md) - portable build instructions, first-run behavior, and reset notes.
- [PRIVACY.md](PRIVACY.md) - local-data and support-report privacy notes.
- [CHANGELOG.md](CHANGELOG.md) - release change notes.
- [docs/phase16-real-sample-validation.md](docs/phase16-real-sample-validation.md) - real sample mod validation report.
- [docs/phase17-rc-fake-install-validation.md](docs/phase17-rc-fake-install-validation.md) - fake-install RC validation report.
- [docs/nexus-release-guide.md](docs/nexus-release-guide.md) - Nexus quickstart, safety limits, troubleshooting, and support workflow.

## Source-Mode Layout Target

```text
S2 Mod Manager/
  Mods/
  Mod Manager/
    app.py
    s2_mod_manager/
      core/
      models/
      ui/
      utils/
    tests/
    assets/
    docs/
```

`..\Mods\` is treated as the local import inbox beside the app project. The Git repo lives in `Mod Manager/`.

## Running From Source

```powershell
pip install -r requirements.txt
python app.py
```

## Smoke Checks

```powershell
python -m compileall app.py s2_mod_manager tests
python -m pytest -q
```

## Portable Build

```powershell
.\scripts\build_portable.ps1 -Clean
```
