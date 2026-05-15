# Subnautica 2 Mod Manager v0.1.0

Initial public portable Windows release.

## Highlights

- Import UE4SS and pak mods from files, folders, `.zip`, and `.7z`.
- Organize imported mods into profiles.
- Enable or disable profile entries.
- Preview every planned install action before writing to the game folder.
- Apply supported managed mods after confirmation.
- Track installed files in `install_manifest.json`.
- Uninstall managed files later through Recovery / Backups.
- Generate diagnostics and redacted support reports.

## Supported Mod Shapes

- Pak bundles with `.pak`, `.ucas`, and `.utoc` companions.
- UE4SS runtime archives/folders.
- UE4SS Lua mods using `Scripts\main.lua`.
- UE4SS C++ mods using `dlls\main.dll`.
- Wrapped UE4SS mod folders.
- Zip and 7z archives.
- Direct folders containing supported mod structures.

## Review-Required Shapes

- Loose game-root overlays.
- SN2P-style root overlays.
- Root loader DLLs or root `.ini` files.
- Ambiguous archives containing multiple unrelated mod candidates.
- Unsupported archive/file layouts.

Review-required items are blocked from automatic apply. They can be imported for reference, but they need manual review before use.

## Safety Notes

- Real apply for supported managed mods is available through Apply Preview.
- Apply Preview refuses blocked or review-required plans before any game-folder write.
- Destructive recovery is limited to manifest-tracked managed files.
- Unknown files are reported, not deleted.
- Saves are not deleted by the manager.
- Restore-vanilla and quarantine are preview/report surfaces only.

## Known Limitations

- No per-mod UE4SS settings editor yet.
- No Nexus metadata parsing or one-click Nexus download integration.
- Manually installed mods cannot be safely uninstalled unless this manager installed them.
- RAR support depends on local archive support.
- SN2P-style root overlays remain review-required.

## Support Report

Use Help / About / Support, then copy or save the local support report. Include the report text, mod filename, active profile, action clicked, and visible warning or error.

Support reports redact user-home paths. Do not include saves, personal account folders, or unrelated logs.

## Windows Security Note

This is an unsigned PyInstaller portable build. Some antivirus tools may flag unsigned Python apps heuristically. The app does not require administrator rights and should be extracted outside the game folder.
