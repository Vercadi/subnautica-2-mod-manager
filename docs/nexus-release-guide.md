# Nexus Release Guide

This guide is written for users downloading a portable Nexus build.

## Quickstart

1. Extract the portable build to a normal folder outside the game install.
2. Start `Subnautica2ModManager.exe`.
3. Open Settings and confirm the detected Subnautica 2 install path.
4. Drag/drop a mod onto the mod list, or use Install From File / Install Folder.
5. In the import review, use Import & Enable for supported mods. Import Only is still available if you want to review first.
6. Toggle mods on/off in the mod list. If Vanilla is active, the manager creates or selects `Default Modded`.
7. Use Preview & Apply Profile, review the exact file actions, then apply the profile when the plan is ready.

Supported managed mods can be installed to the detected game folder through Preview & Apply Profile. Blocked/review-required files are refused. Recovery removes or restores only files recorded in `install_manifest.json`.

## Storefront / Install Layout Support

- Steam is the tested path and is auto-detected from Steam libraries.
- Epic/manual installs are supported when manual path selection points to a normal Win64 Unreal layout. The root wrapper `Subnautica2.exe` is no longer required for non-Steam manual validation if the shipping exe and pak folder are present.
- Game Pass WinGDK is experimental. The manager can recognize the user-reported layout `Content\Subnautica2\Binaries\WinGDK`. Game Pass UE4SS base/runtime packages are treated as Content-root payloads, while standard Lua mods target `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods`. This path is less tested and individual mods may still crash if they are not compatible with Game Pass/WinGDK.

Manual path selection accepts the outer install folder, the inner `Subnautica2` project folder, `Subnautica2\Binaries\Win64`, the Game Pass `Content` folder, `Content\Subnautica2`, or `Content\Subnautica2\Binaries\WinGDK`.

## Supported Mod Shapes

- Pak bundles: `.pak` with optional `.ucas` and `.utoc` companions.
- Patch pak bundles ending in `_P` are installed to `Subnautica2\Content\Paks\~mods`.
- UE4SS Blueprint/logic pak bundles without `_P`, such as SeaSprint, are installed to `Subnautica2\Content\Paks\LogicMods`.
- UE4SS runtime archives with runtime files for the detected layout (`Win64` for Steam/Epic, experimental Game Pass Content root for WinGDK).
- UE4SS mods under `ue4ss\Mods\<ModName>` (`Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods` on Game Pass).
- UE4SS mods wrapped as `<ModName>\Scripts\main.lua` plus sibling files.
- Full-path UE4SS archives with `Subnautica2\Binaries\Win64\ue4ss\Mods\<ModName>` or `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods\<ModName>`.
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

- Install not detected: open Settings and choose the outer install folder, inner `Subnautica2` folder, binaries folder, or Game Pass `Content` folder. Steam/Epic-style installs need a shipping exe plus `Content\Paks`; Game Pass needs `Content\Subnautica2\Binaries\WinGDK` plus its pak folder.
- Epic install not accepted: select the folder that contains the inner `Subnautica2` project folder, or select `Subnautica2\Binaries\Win64` directly.
- Game Pass install warning: WinGDK support is experimental. UE4SS mods target `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods`; if the game crashes after loading a save, test one mod at a time because some day-one mods may be incompatible even when the folder target is correct.
- Archive will not scan: confirm it is `.zip`, `.7z`, or locally supported `.rar`.
- UE4SS mod warning: drag/drop or Install From File the UE4SS package, import it as **UE4SS Runtime**, add it to the same profile, or install UE4SS manually first.
- Pak installed to the wrong folder in older builds: update to `0.1.1`, then open Preview & Apply again. Existing imported SeaSprint-style pak entries are migrated from `~mods` to `LogicMods` automatically.
- Apply is blocked: inspect the Preview & Apply errors and blocked file actions. Loose root overlays are blocked by policy.
- Import appears duplicated: duplicate source hashes reuse the existing manager library copy.

## FAQ

**Does it work with Epic?**
Epic/manual Win64 installs are supported in `0.1.1` if the game folder exposes the normal Unreal layout. Use Settings -> Browse Install and select the outer install folder, inner `Subnautica2` folder, or `Subnautica2\Binaries\Win64`.

**Does it work with Game Pass?**
Game Pass support is experimental in `0.1.1`. The manager detects `Content\Subnautica2\Binaries\WinGDK` and maps UE4SS mods to `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods`, but crashes can still be caused by individual mods that are not compatible with Game Pass/WinGDK.

**What should I send if Epic or Game Pass still fails?**
Open Help / About / Support and generate a support report. Include the report, the exact folder you selected, the mod filename, and the visible warning/error. Do not include save folders or personal files.

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
