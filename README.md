# Subnautica 2 Mod Manager

Safety-first Windows mod manager for Subnautica 2 UE4SS and pak mods.

The app imports mods into a manager-owned library, lets users build profiles, previews every planned file action, applies supported managed mods, records installs in a manifest, and can uninstall or restore only files it installed.

## Features

- Steam install discovery for Subnautica 2 app id `1962700`
- Manual install path selection and validation
- Drag/drop and browse import for files, folders, `.zip`, `.7z`, and supported archive layouts
- Pak bundle detection for `.pak`, `.ucas`, and `.utoc`
- UE4SS runtime detection
- UE4SS Lua and C++ mod detection
- Manager-owned mod library
- Protected Vanilla profile plus editable modded profiles
- Enable/disable controls and bulk profile actions
- UE4SS activation file support for `enabled.txt`, `mods.txt`, and `mods.json`
- Apply Preview with exact creates, overwrites, skips, warnings, errors, and blocked actions
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

Review-required layouts are detected but blocked from automatic apply:

- Loose game-root overlays
- SN2P-style root overlays
- Ambiguous archives containing multiple unrelated mod candidates
- Unsupported archive/file layouts
- Unexpected unmanaged game-root overwrites

## Safety Model

Supported managed mods can be installed through Apply Preview. The preview shows exactly what will be created, overwritten, skipped, or blocked before applying a profile.

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
- [docs/release-notes-v0.1.0.md](docs/release-notes-v0.1.0.md) - first release notes
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
