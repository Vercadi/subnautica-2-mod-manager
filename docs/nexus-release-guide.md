# Nexus Release Guide

This guide is written for users downloading a portable Nexus build.

## Quickstart

1. Extract the portable build to a normal folder outside the game install.
2. Start `Subnautica2ModManager.exe`.
3. Open Settings and confirm the detected Subnautica 2 install path.
4. Put mod archives, pak bundles, or UE4SS folders in the configured Mods inbox, or use Browse/Drop in the app.
5. Use Scan/Import to copy sources into the manager library.
6. Create or select a non-Vanilla profile.
7. Add imported components to the profile.
8. Use Apply Preview, review the exact file actions, then apply the profile when the plan is ready.

Supported managed mods can be installed to the detected game folder through Apply Preview. Blocked/review-required files are refused. Recovery removes or restores only files recorded in `install_manifest.json`.

## Supported Mod Shapes

- Pak bundles: `.pak` with optional `.ucas` and `.utoc` companions.
- UE4SS runtime archives with runtime files for `Subnautica2\Binaries\Win64`.
- UE4SS mods under `ue4ss\Mods\<ModName>`.
- UE4SS mods wrapped as `<ModName>\Scripts\main.lua` plus sibling files.
- Full-path UE4SS archives with `Subnautica2\Binaries\Win64\ue4ss\Mods\<ModName>`.
- `.zip` and `.7z` archives. `.rar` is supported only when the local runtime can open it.

## Review-Required Shapes

Loose root overlays are intentionally blocked from automatic apply. Examples:

- `dxgi.dll`
- `dwmapi.dll` when not part of a recognized UE4SS runtime package
- root `.ini` files
- arbitrary files targeting the game root or unmanaged folders

These files can affect game launch, conflict with other loaders, or leave unmanaged files behind. Keep them imported for reference and follow the mod author's manual instructions only if you understand the target paths and have your own backup.

## Safety Limitations

- The manager does not delete saves.
- Restore-vanilla is preview-only.
- Quarantine is preview-only.
- Unknown files are reported, not deleted.
- Managed uninstall removes or restores only files recorded in `install_manifest.json`.
- Loose root overlays and arbitrary unmanaged files are blocked from automatic apply.

## Troubleshooting

- Install not detected: open Settings, choose the Subnautica 2 root, and verify it contains `Subnautica2.exe`.
- Archive will not scan: confirm it is `.zip`, `.7z`, or locally supported `.rar`.
- UE4SS mod warning: add a UE4SS runtime package to the same profile or install runtime manually.
- Apply is blocked: inspect the Apply Preview errors and blocked file actions. Loose root overlays are blocked by policy.
- Import appears duplicated: duplicate source hashes reuse the existing manager library copy.

## Windows Security / Antivirus Notes

The portable executable is built with PyInstaller and is not code-signed yet. Some antivirus products can flag unsigned Python bundles heuristically. Verify that the download came from the official Nexus/GitHub release, compare any published hashes when available, and report the exact detection name if you see one. The app does not require administrator rights.

## Support Report Workflow

Diagnostics are local text only. The app does not upload reports.

When reporting an issue, include:

- The generated support report text.
- The mod archive filename.
- The active profile name.
- The action you clicked.
- The visible error or warning text.

Do not include save folders, personal account paths, or private files. The support report redacts home paths and omits save paths by design.

## Known Issues

- `SN2P`-style root overlays are blocked until an explicit target policy exists.
- Runtime packages with bundled `ue4ss\Mods` content are treated as one runtime payload.
- Nexus metadata is not parsed from filenames yet.
- A final manual clean-machine launch check is still required before each public upload.
