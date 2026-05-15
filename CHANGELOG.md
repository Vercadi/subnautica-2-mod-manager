# Changelog

## 0.1.0-rc1

- Phase 22 UX wiring pass:
  - shared app-owned dialog icon/styling for settings, prompts, warnings, reports, and operational dialogs
  - clickable left navigation for profiles, recovery, diagnostics, activity, and support
  - main shell uses a full-height compact mod list with profile/import controls moved into a side command rail
  - full mod-list panel accepts drag/drop sources when native TkDND is available
  - UE4SS activation policy toggles for `enabled.txt`, `mods.json`, and `mods.txt` are persisted and generate guarded apply-preview actions with backup/manifest tracking
  - imported inbox duplicates are hidden from the candidate list and duplicate imports are skipped
  - row-local toggle/menu/warning actions for editable profiles, with checkbox selection for batch profile removal
  - profile-safe activate all, deactivate all, and clear profile actions
  - popup preferences for noncritical update/info/success/warning dialogs
  - Patreon/Ko-fi support links in Help/About
- Prepared the first Nexus release-candidate artifact flow with release notes, zip packaging, and SHA256 hash generation.
- Added package-content checks so the release zip excludes local data, logs, caches, and sample mod inbox content.
- Added Nexus-facing release notes for safety limits, supported shapes, review-required overlays, known limitations, and support reports.
- Enabled plug-and-play managed apply for non-blocked real install plans through Apply Preview.
- Enabled manifest-tracked managed uninstall/recovery for real installs; unknown files and saves are left alone.

## 0.1.0-phase20

- Ran clean-machine style frozen launch validation against the portable build with an isolated `LOCALAPPDATA`.
- Validated real sample mod import, profile planning, fake-install test apply, manifest/recovery summaries, uninstall-all, and no real S2 install writes.
- Added final Nexus release checklist and Phase 20 validation notes.
- Added package-content regression coverage for required portable files, docs, assets, and release metadata.
- Kept real apply and destructive recovery disabled for real installs by default.

## 0.1.0-phase19

- Added centered dialog/window placement utilities and applied them to the main review, apply, recovery, settings, help, activity, message, and profile-name dialogs.
- Added GitHub Releases update-check plumbing with robust version comparison, preferred asset selection, friendly errors, manual command-bar checks, and an optional startup-check preference that defaults off.
- Added Help / About / Support with app metadata, safety/archive status, project links, folder shortcuts, and copy/save support report actions.
- Added persistent bounded activity logging and a recent-events dialog.
- Added Needs Attention summaries for install, archive, scan, library, profile, apply, recovery, safety, and update states.
- Added UE4SS protected native/core mod warnings and root `scripts`/`dlls` archive wrapping hints.
- Kept real apply and destructive recovery disabled for real installs by default.

## 0.1.0-phase18

- Added centralized release policy text for review-required loose root overlays.
- Surfaced loose-overlay policy in import review, library rows, inspector text, profile warnings, apply preview, settings, diagnostics, and first-run messages.
- Added Nexus release guide with quickstart, supported shapes, review-required shapes, troubleshooting, known issues, and support-report workflow.
- Added Phase 18 regression coverage for policy text, blocked apply messaging, first-run wording, and support report guidance.
- Kept real apply and destructive recovery disabled for real installs by default.

## 0.1.0-phase17

- Validated real sample mods against a fake `.s2mm_fake_install` S2 install.
- Verified test-only apply, manifest records, overwrite backups, uninstall, restore preview, and save-file safety.
- Fixed restore-vanilla preview so uninstalled manifest records are not treated as currently managed files.
- Added RC fake-install regression coverage for sample-shaped pak, UE4SS runtime, UE4SS mod, and blocked loose-overlay sources.
- Kept `SN2P`-style loose root overlays blocked pending explicit manual review policy.
- Kept real apply and destructive recovery disabled for real installs by default.

## 0.1.0-phase16

- Validated the real sample mod inbox against the real detected S2 install in dry-run mode.
- Hardened wrapped UE4SS mod detection so sibling files stay with the detected mod folder.
- Added regression tests for wrapped and root-level UE4SS mod archive shapes.
- Added a Phase 16 real sample validation report.
- Kept real apply and destructive recovery disabled for real installs by default.

## 0.1.0-phase15

- Added portable PyInstaller build spec and build script.
- Added release metadata generation for packaged builds.
- Hardened source/frozen runtime directory creation.
- Added first-run settings recovery messages.
- Added Packaging and Privacy docs for release prep.
- Kept real apply and destructive recovery disabled for real installs by default.
