# Research Notes

This document captures the porting research before implementation starts.

## Existing Managers Inspected

Local source projects:

- Local Windrose Mod Deployer reference checkout.
- Local Conan Exiles Mod and Server Manager reference checkout.
- `https://github.com/AtilioA/UE4SS-mod-manager` at commit `576ac46f6f7c6df6cf6ab03b46144c4f2bc18062`

Both are Python 3.12 Windows desktop apps built around CustomTkinter, modular core services, JSON-backed state, PyInstaller packaging, and explicit safety workflows.

## Windrose Patterns To Carry Forward

Windrose is the closest match for Subnautica 2 because it already handles Unreal pak archives and UE4SS-style framework installs.

Useful pieces to port conceptually:

- `archive_handler.py`: common archive interface for `.zip`, `.7z`, and `.rar`.
- `archive_inspector.py`: archive classification into pak-only, loose-file, mixed, unknown, and multi-variant.
- `framework_detector.py`: UE4SS runtime/mod detection from filenames and folder shape.
- `framework_deployment_planner.py`: maps UE4SS runtime and UE4SS mod entries to the right game folders.
- `deployment_planner.py`: builds a file-by-file plan before touching the target install.
- `installer.py`: writes planned files, backs up overwritten files, tracks installed paths, supports enable/disable/uninstall.
- `manifest_store.py`: JSON state for installed mods and deployment history.
- `archive_library_service.py`: copies normal mod archives into manager-owned storage by hash.
- `restore_vanilla_service.py`: preview-driven cleanup that removes managed artifacts and backs up unknown removals.
- `app_window.py`: optional native drag-and-drop, lazy tab construction, status dashboard, update checks, and support diagnostics.

Windrose-specific server and WindrosePlus/RCON features should not be copied directly unless Subnautica 2 later exposes an equivalent server target.

## Conan Patterns To Carry Forward

Conan is the better model for profiles, active loadouts, source library discipline, and preview-first writes.

Useful pieces to port conceptually:

- `local_mod_library.py`: manager-owned local library for raw `.pak`, companion files, and archive-derived components.
- `models/local_mod_library.py`: separates sources from installable components.
- `models/modlist.py`: active entry model with display name, source type, component id, companions, and enabled state.
- `profile_store.py`: named profiles with a permanent Vanilla profile.
- `modlist_service.py`: preview/apply split, target copy plans, selected uninstall, and quarantine option.
- `target_actions.py`: drop classification, multi-selection helpers, reorder helpers, and context-menu action ids.
- `backup_manager.py`: category-based backup records.
- `discovery.py`: Steam library/appmanifest discovery and validator functions.
- `ui/app_window.py`: lazy tabs, native file drop detection, user-facing startup discovery, and app-level service orchestration.

Conan Workshop, SteamCMD, dedicated server, and hosted server workflows are not part of the initial S2 surface.

## UE4SS Mod Manager Patterns To Carry Forward

The AtilioA UE4SS manager is much narrower than Windrose or Conan. It is designed to run in or near a game's `UE4SS\Mods` folder, scan direct UE4SS mod directories, and toggle UE4SS enable state. It does not provide game install discovery, pak handling, profiles, managed library storage, deployment manifests, backups, or recovery.

Useful pieces to borrow conceptually:

- UE4SS enable state should support multiple formats:
  - per-mod `enabled.txt`
  - UE4SS `mods.json`
  - UE4SS `mods.txt`
- UE4SS native/core mods should be protected. Its native mod list includes names such as `BPML_GenericFunctions`, `BPModLoaderMod`, `CheatManagerEnablerMod`, `ConsoleCommandsMod`, `ConsoleEnablerMod`, `Keybinds`, and `ConsoleCommands`.
- UE4SS mod detection should accept both Lua and native C++ style mods:
  - `scripts/main.lua`
  - `dlls/main.dll`
- Dropped UE4SS zip archives sometimes contain `scripts/` at archive root. That shape should be wrapped as a mod folder named after the archive before deployment.
- `scripts/config.lua` can be exposed later as a safe, restricted editor for top-level scalar Lua values. The reference manager preserves formatting/comments, supports boolean/number/string/nil, and ignores nested tables or computed expressions.
- Native drag/drop setup should register both the root window and child widgets so drops work across the visible app surface.
- Packaging should explicitly collect `tkinterdnd2` data in PyInstaller.

Patterns to avoid:

- Direct writes into `UE4SS\Mods` without a manifest or backup.
- Treating `UE4SS\Mods` as the only valid working directory.
- Managing only UE4SS folders; S2 also needs pak bundles, profiles, preview, restore, and diagnostics.
- Replacing duplicate mods without a preview and recovery path.

Follow-up tasks for this project:

- Add scanner tests for root `scripts/main.lua`, root `dlls/main.dll`, mixed-case `Config.LUA`, and native UE4SS mod names.
- Add a UE4SS activation policy step to deployment planning so profiles can choose `enabled.txt`, `mods.json`, and/or `mods.txt` writes.
- Add protected-core warnings for native UE4SS mods in deployment and recovery previews.
- Consider a later `config.lua` inspector/editor after the main UI polish pass.

Phase 19 parity pass results:

- Windrose/Conan centered-dialog helpers are now represented by a shared S2 window placement utility and app-owned dialog behavior.
- Windrose/Conan GitHub Releases checks are represented by S2 update-check plumbing, manual command-bar checks, and an optional startup preference that defaults off.
- Windrose/Conan Help/About support workflows are represented by the S2 Help / About / Support dialog with copy/save support report and folder shortcuts.
- Conan-style activity and needs-attention ideas are represented by a bounded activity log plus a compact Needs Attention summary model.
- UE4SS manager detection ideas are represented by protected native/core warnings and root `scripts`/`dlls` archive wrapping hints.
- The UE4SS manager's direct-write approach remains intentionally avoided; S2 still routes all install behavior through profile preview, fake-test apply, manifests, backups, and real-install guards.

## Local Subnautica 2 Install

Verified local install:

```text
<SteamLibrary>\steamapps\common\Subnautica2
```

Relevant paths:

```text
Subnautica2.exe
Subnautica2\Binaries\Win64\Subnautica2-Win64-Shipping.exe
Subnautica2\Content\Paks
Subnautica2\Saved\SaveGames
version.json
version.txt
```

Steam appmanifest:

```text
<SteamLibrary>\steamapps\appmanifest_1962700.acf
```

Observed app/build data:

- Steam app id: `1962700`
- Steam build id: `23165626`
- Game changelist: `113109`
- Game build number: `34`
- Game timestamp: `2026-05-10T04:15:22`

The inspected clean install has no `Subnautica2\Content\Paks\~mods` folder yet and no UE4SS files under `Subnautica2\Binaries\Win64`.

## Sample Mods In Current Repo

Local inbox:

```text
<ProjectRoot>\..\Mods
```

Observed sample archives:

- `UE4SS SN2-36-EA1-1778748850.zip`
  - Contains `ue4ss/`, `UE4SS.dll`, `UE4SS-settings.ini`, and `dwmapi.dll`.
  - Should classify as UE4SS runtime.
  - Target: `Subnautica2\Binaries\Win64`.
- `SN2ModSettings V1.0.3-20-1-0-3-1778783284.zip`
  - Contains `Subnautica2/Binaries/Win64/ue4ss/Mods/SN2ModSettings/...`.
  - Should classify as UE4SS mod with full game-path prefix.
  - Target: `Subnautica2\Binaries\Win64\ue4ss\Mods\SN2ModSettings`.
- `Infinite Oxygen-56-1-1778788524.zip`
  - Contains `InfiniteOxygen/InfiniteOxygen_P.pak`, `.ucas`, `.utoc`.
  - Should classify as pak bundle with companions.
  - Target: `Subnautica2\Content\Paks\~mods`.
- `Hide HUD-58-1-1778794542.7z`
  - Windows tar could not inspect it because the LZMA codec is unsupported.
  - The manager should inspect this through `py7zr`, as Windrose does.

## S2 Port Implications

The S2 manager should combine these existing strengths:

- Windrose's Unreal archive and UE4SS install planning.
- Conan's manager-owned library, profiles, active loadout, and quarantine-first uninstall behavior.
- A simpler target model focused on the local client install first.

The app should avoid pretending S2 has a Conan-style `modlist.txt` or Workshop flow. Profiles should be app-owned loadouts, not game-native files.

## Initial Non-Goals

- No pak unpacking, pak editing, or repacking.
- No automatic Nexus API downloads.
- No Steam Workshop/SteamCMD flow unless S2 gains Workshop support.
- No dedicated/hosted server workflow until a real S2 server target exists.
- No deletion of user source archives.
