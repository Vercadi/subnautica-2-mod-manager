# Phase 17 RC Fake Install Validation

Validation date: 2026-05-15

Scope:

- Used the real sample inbox at `<ProjectRoot>\..\Mods`.
- Created temporary fake Subnautica 2 installs with the expected executable, shipping executable, `Content\Paks`, version file, save folder, and `.s2mm_fake_install` marker.
- Did not write to the real detected install at `<SteamLibrary>\steamapps\common\Subnautica2`.

## Real Sample End-to-End Result

All real sample sources imported into a temporary manager library. The all-samples profile remained blocked because `SN2P` is a loose root overlay:

- Blocked actions: 2
- Blocked targets: `dxgi.dll`, `snsnp_settings.ini`
- Apply result: refused before any writes

The safe sample profile excluded loose overlay components and executed against the fake test install:

- Deployment actions: 36
- Creates: 35
- Overwrites: 1
- Backups: 1
- Apply status: completed
- Recovery preview before uninstall: 36 managed files, 0 unknown files
- Uninstall result: 35 removed, 1 restored, 0 missing, 0 errors
- Recovery preview after uninstall: 0 managed files, 1 unknown file
- Restored unknown file: pre-existing `InfiniteOxygen_P.pak`
- Save file check: fake save remained untouched

Verified target families:

- Pak bundles deploy to `Subnautica2\Content\Paks\~mods`.
- UE4SS runtime deploys to `Subnautica2\Binaries\Win64`.
- UE4SS mods deploy to `Subnautica2\Binaries\Win64\ue4ss\Mods\<ModName>`.
- Wrapped UE4SS sibling files deploy under the detected mod folder.
- Loose root overlays remain blocked and review-required.

## Fixes From This Pass

- Recovery restore-vanilla preview no longer treats uninstalled manifest records as managed ownership.
- Missing/non-existing manifest targets are not shown as currently managed restore-preview files.
- Restored pre-existing files now appear as unknown files after uninstall, which better matches actual ownership.

## New Regression Coverage

- Real-sample-shaped fake install apply, manifest, backup, uninstall, and restore preview.
- Blocked `SN2P`-style loose overlay refusal before writes.
- Non-test install guard refusal with real-sample-shaped safe components.
- Restore preview state after uninstall.

## Remaining Nexus Release Blockers

- Decide how to message or support `SN2P` root-overlay installs. It is intentionally blocked today.
- Do one packaged portable build on a clean machine or VM.
- Add final release icon/name/version metadata review if needed.
- Perform user-facing UX pass on import/apply/recovery dialogs with the actual Nexus sample set.
- Prepare Nexus description, install instructions, safety limitations, and troubleshooting notes.
