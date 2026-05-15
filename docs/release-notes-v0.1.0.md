# Subnautica 2 Mod Manager v0.1.0 RC1

First Nexus release candidate for the Subnautica 2 Mod Manager portable Windows build.

## Safety Notes

- Real apply for supported managed mods is available through Apply Preview for the detected Subnautica 2 install.
- Apply Preview refuses blocked/review-required plans before any game-folder write.
- Destructive recovery is limited to managed uninstall/restore actions for files recorded in `install_manifest.json`.
- Fake installs marked with `.s2mm_fake_install` can still be used for test-only validation.
- Restore-vanilla and quarantine flows are preview/report surfaces only.
- The app does not delete saves and recovery uses only its own install manifest.

## Supported Mod Shapes

- Pak bundles: `.pak` with optional `.ucas` and `.utoc` companions.
- UE4SS runtime archives/folders targeting `Subnautica2\Binaries\Win64`.
- UE4SS Lua/C++ mods under `ue4ss\Mods\<ModName>`.
- Wrapped UE4SS mod folders with `Scripts\main.lua` or `DLLs\main.dll`.
- UE4SS activation-file preview/apply for `enabled.txt`, `mods.txt`, and `mods.json` through the guarded profile apply flow.
- Archives: `.zip`, `.7z`, and `.rar` when local RAR support is available.
- Direct folders and selected loose pak companion files through Browse or Drop Zone.

## Review-Required Shapes

- Loose game-root overlays such as `dxgi.dll`, root `.ini` files, loader DLLs, or arbitrary unmanaged files.
- SN2P-style root overlays remain blocked from automatic apply until a dedicated safe policy is implemented.
- Ambiguous multi-component archives may need manual review before being added to a profile.

## Known Limitations

- No automatic download/install for updates; update checks only report GitHub release availability.
- No Nexus metadata parsing, dependency resolution, or one-click Nexus integration yet.
- UE4SS activation-file writes remain guarded by Apply Preview, backups, and manifests.
- No migration UI for moving an existing manager data/library/backups folder.

## Support Report

Use Help / About / Support, then copy or save the local support report. Include:

- The report text.
- The mod filename or archive name.
- The active profile name.
- The action clicked.
- The visible warning or error text.

Support reports redact user-home paths. Do not include saves, personal account folders, or unrelated logs.

## Windows Security Note

This is an unsigned PyInstaller portable build. Some antivirus tools may flag unsigned Python apps heuristically. The app does not require administrator rights and should be extracted outside the game folder.
