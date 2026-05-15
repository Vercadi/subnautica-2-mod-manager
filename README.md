# Subnautica 2 Mod Manager

Safety-first Windows mod manager for Subnautica 2 UE4SS and pak mods.

The app imports mods into a manager-owned library, lets users build profiles, previews every planned file action, applies supported managed mods, records installs in a manifest, and can uninstall or restore only files it installed.

## Features

- Steam install discovery for Subnautica 2 app id `1962700`
- Manual install path selection and validation for Steam/Epic-style Win64 layouts
- Experimental Game Pass WinGDK layout support
- Drag/drop and browse import for files, folders, `.zip`, `.7z`, and supported archive layouts
- Pak bundle detection for `.pak`, `.ucas`, and `.utoc`
- UE4SS LogicMods pak target support for non-`_P` Blueprint/logic pak bundles
- UE4SS runtime detection
- UE4SS Lua and C++ mod detection
- Manager-owned mod library
- Protected Vanilla profile plus editable modded profiles
- Enable/disable controls and bulk profile actions
- UE4SS activation file support for `enabled.txt`, `mods.txt`, and `mods.json`
- Primary Preview & Apply Profile flow with exact creates, overwrites, skips, warnings, errors, and blocked actions
- Manifest-backed managed install, uninstall, backup, and recovery
- Diagnostics, redacted support report generation, and activity logging
- Portable PyInstaller build with Subnautica-inspired UI

## Supported Mods

Supported for managed import/apply:

- UE4SS runtime folders or archives
- UE4SS mods using `Scripts/main.lua`
- UE4SS mods using `dlls/main.dll`
- Pak bundles:
  - `.pak`
  - `.pak` + `.ucas`
  - `.pak` + `.utoc`
  - `.pak` + `.ucas` + `.utoc`
- Zip archives
- 7z archives
- Folders containing supported mod structures

## Storefront / Install Layout Support

- Steam: tested and auto-detected through Steam library/appmanifest discovery.
- Epic/manual Win64: supported through Settings manual path selection when the install exposes the normal Unreal layout with `Subnautica2\Binaries\Win64` and `Subnautica2\Content\Paks`.
- Game Pass: experimental support for the user-reported WinGDK layout under `Content\Subnautica2\Binaries\WinGDK`. Game Pass UE4SS base/runtime packages are treated as Content-root payloads, while standard Lua mods target `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods`. Pak targets still use the detected `Content\Paks` folder. This path is less tested and mod crashes may still be caused by individual mod compatibility.

Manual path selection accepts the outer install folder, the inner `Subnautica2` project folder, `Subnautica2\Binaries\Win64`, the Game Pass `Content` folder, `Content\Subnautica2`, or `Content\Subnautica2\Binaries\WinGDK`.

Review-required layouts are detected but blocked from automatic apply:

- Loose game-root overlays
- SN2P-style root overlays
- Ambiguous archives containing multiple unrelated mod candidates
- Unsupported archive/file layouts
- Unexpected unmanaged game-root overwrites

## Safety Model

Supported managed mods can be installed through Preview & Apply Profile. The preview shows exactly what will be created, overwritten, skipped, or blocked before applying a profile.

Pak target policy:

- Patch paks ending in `_P` deploy to `Subnautica2\Content\Paks\~mods`.
- UE4SS Blueprint/logic pak bundles without `_P`, such as SeaSprint, deploy to `Subnautica2\Content\Paks\LogicMods`.
- Archives that already include `Content\Paks\LogicMods` or `Content\Paks\~mods` keep that target folder.

Every managed apply is recorded in `install_manifest.json`. If an existing managed target is overwritten, the original file is backed up first. Recovery and uninstall actions only touch files recorded in the manager manifest. Unknown files are reported, not deleted.

## Install From Source

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
.\scripts\package_release.ps1
```

The release zip is written to `dist\release`.

## Documentation

- [PACKAGING.md](PACKAGING.md) - build and reset notes
- [PRIVACY.md](PRIVACY.md) - local data and support-report privacy
- [CHANGELOG.md](CHANGELOG.md) - release changes
- [docs/nexus-release-guide.md](docs/nexus-release-guide.md) - Nexus-facing user guide
- [docs/release-notes-v0.1.2.md](docs/release-notes-v0.1.2.md) - current release notes
- [docs/release-checklist.md](docs/release-checklist.md) - final manual release checks

## Project Layout

```text
S2 Mod Manager/
  Mods/
  Mod Manager/
    app.py
    s2_mod_manager/
    tests/
    assets/
    docs/
```

`..\Mods\` is treated as the local import inbox beside the app project. The Git repo lives in `Mod Manager/`.

## License

MIT. See [LICENSE](LICENSE).
