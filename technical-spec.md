# Technical Specification

## Stack

Target stack:

- Python 3.12+
- CustomTkinter
- tkinterdnd2 for native drag/drop
- py7zr for `.7z`
- rarfile plus external UnRAR only if `.rar` support is enabled
- pytest
- PyInstaller

This matches the Windrose and Conan managers closely enough to port proven service patterns without changing the desktop architecture.

## Package Layout

```text
app.py
s2_mod_manager/
  __init__.py
  core/
    archive_handler.py
    archive_inspector.py
    backup_manager.py
    deployment_planner.py
    diagnostics.py
    discovery.py
    framework_detector.py
    installer.py
    library_store.py
    logging_service.py
    manifest_store.py
    profile_store.py
    recovery_service.py
    target_actions.py
    update_checker.py
  models/
    app_paths.py
    app_preferences.py
    archive_info.py
    backup.py
    library.py
    manifest.py
    profile.py
    diagnostics.py
    recovery.py
    ui_state.py
  ui/
    app_window.py
    ui_tokens.py
    shell/
      background.py
      command_bar.py
      navigation.py
      status_gauge.py
      console_panel.py
      load_order_strip.py
    tabs/
      installed_mods_tab.py
      loadout_tab.py
      profiles_tab.py
      backups_tab.py
      mod_browser_tab.py
      settings_tab.py
      diagnostics_tab.py
    widgets/
      drop_zone.py
      mod_row.py
      mod_inspector.py
      preview_dialog.py
  utils/
    filesystem.py
    hashing.py
    json_io.py
    naming.py
tests/
assets/
```

## UI Shell Implementation

The app should target the supplied draft layout.

Shell layers:

1. `BackgroundLayer`: loads and scales a static underwater image to cover the window.
2. `MainShellFrame`: dark glass-like container with cyan border.
3. `CommandBar`: title, build badge, path selector, launch/update/settings buttons.
4. `NavigationRail`: left route buttons and O2/System Health gauge.
5. `InstalledModsView`: center drop zone and mod rows.
6. `ModInspector`: right selected-mod panel with tabs.
7. `ConsolePanel`: bottom-left timestamped output.
8. `LoadOrderStrip`: bottom-right draggable profile chips.

CustomTkinter/Tk constraints:

- Do not depend on true transparent blur.
- Simulate glass through dark opaque fills and bright borders.
- Use `tk.Canvas` for gauges, sonar rings, and optional radar.
- Keep animations optional and lightweight.
- Defer frameless/custom titlebar behavior until after core workflows are stable.

Asset loading:

- Store app-owned UI assets in `assets/`.
- Use PIL/CTkImage for background and thumbnails.
- Generate placeholder thumbnails when a mod has no image.
- Never require internet access to render the UI.

## App Paths

Model: `S2AppPaths`.

Fields:

- `client_root`
- `steamapps_dirs`
- `client_manifest`
- `data_dir`
- `backup_dir`
- `archive_inbox_dir`

Derived paths:

```text
client_exe              = <root>\Subnautica2.exe
shipping_exe            = <root>\Subnautica2\Binaries\Win64\Subnautica2-Win64-Shipping.exe
content_paks            = <root>\Subnautica2\Content\Paks
mods_paks               = <root>\Subnautica2\Content\Paks\~mods
win64                   = <root>\Subnautica2\Binaries\Win64
ue4ss_root              = <root>\Subnautica2\Binaries\Win64\ue4ss
ue4ss_mods              = <root>\Subnautica2\Binaries\Win64\ue4ss\Mods
save_games              = <root>\Subnautica2\Saved\SaveGames
version_json            = <root>\version.json
version_txt             = <root>\version.txt
```

Validation:

- `client_root` exists.
- `Subnautica2.exe` exists.
- `shipping_exe` exists.
- `content_paks` exists.

Steam detection:

- App id: `1962700`.
- Locate `appmanifest_1962700.acf` through Steam library discovery.
- Use manifest `installdir` when valid.

## Source-Mode Storage

When running from source:

```text
data/
  settings.json
  library_state.json
  profiles.json
  install_manifest.json
  app_state.json
  activity_log.json
  archives/
  components/
  deploy_cache/
backups/
  installs/
  mods/
  runtime/
  profiles/
  restore_vanilla/
  metadata/
quarantine/
Mods/
```

When packaged:

```text
%LOCALAPPDATA%\Subnautica2ModManager\
```

## Core Models

### ModSource

Represents an imported source artifact.

Fields:

- `source_id`
- `source_type`: `archive`, `folder`, `local_files`, `external_link`
- `display_name`
- `original_path`
- `managed_path`
- `component_ids`
- `size`
- `modified_time`
- `sha256`
- `imported_at`

### ModComponent

Represents one installable mod unit found inside a source.

Fields:

- `component_id`
- `source_id`
- `display_name`
- `component_type`: `pak_bundle`, `ue4ss_runtime`, `ue4ss_mod`, `loose_overlay`, `mixed`
- `primary_file`
- `companion_files`
- `relative_files`
- `install_kind`
- `dependency_warnings`
- `selected_variant`
- `enabled`
- `notes`

### ActiveLoadoutEntry

Fields:

- `component_id`
- `display_name`
- `enabled`
- `order`
- `profile_notes`
- `last_known_component_hash`

### ModProfile

Fields:

- `profile_id`
- `name`
- `entries`
- `notes`
- `created_at`
- `updated_at`
- `last_applied_at`
- `last_applied_game_build`

The store creates a permanent `Vanilla` profile with no entries.

### InstallRecord

Fields:

- `install_id`
- `component_id`
- `profile_id`
- `action`: `install`, `uninstall`, `disable`, `enable`, `restore_vanilla`
- `target_root`
- `deployed_files`
- `backup_ids`
- `timestamp`
- `game_build`
- `notes`

## Import Classification

Supported inputs:

- `.pak`
- `.pak` with same-stem `.ucas` and `.utoc`
- `.zip`
- `.7z`
- `.rar` if optional dependency is available
- folder containing pak bundles
- folder containing UE4SS runtime files
- folder containing UE4SS mod files

### Pak Bundle

Detection:

- At least one `.pak`.
- Same-stem `.ucas` and `.utoc` are companions.

Target:

```text
Subnautica2\Content\Paks\~mods
```

Rules:

- Create `~mods` lazily.
- Never write into the base pak folder unless a future manual advanced override exists.
- Copy companions with the primary pak.

### UE4SS Runtime

Detection markers:

- `UE4SS.dll`
- `UE4SS-settings.ini`
- `ue4ss/`
- `dwmapi.dll`
- `xinput1_3.dll`
- `dwmappi.dll`

Target:

```text
Subnautica2\Binaries\Win64
```

Rules:

- Runtime files are tracked separately from normal mods.
- If a runtime already exists, preview overwrites and backup first.
- Warn when runtime appears partial.

### UE4SS Mod

Detection shapes:

```text
ue4ss/Mods/<ModName>/...
Subnautica2/Binaries/Win64/ue4ss/Mods/<ModName>/...
<ModName>/Scripts/main.lua
<ModName>/Dlls/...
<ModName>/enabled.txt
<ModName>/settings.ini
```

Target:

```text
Subnautica2\Binaries\Win64\ue4ss\Mods\<ModName>
```

Rules:

- Warn if runtime is missing.
- Preserve the mod folder name.
- Do not merge two different imported components into the same UE4SS mod folder without a conflict preview.

### Full Game-Path Archives

Archives may include prefixes like:

```text
Subnautica2/Content/Paks/...
Subnautica2/Binaries/Win64/...
Content/Paks/...
Binaries/Win64/...
```

The planner strips recognized prefixes and maps to the real install root.

### Loose Overlay

Loose overlay installs are high risk.

Rules:

- Allow only after review.
- Show exact target paths.
- Back up overwrites.
- Prefer classifying known UE4SS or pak content instead of broad root overlay.

## Deployment Planning

Deployment is split into two steps:

1. Build a `DeploymentPlan`.
2. Execute the plan only after confirmation.

Plan fields:

- target label
- component list
- files to create
- files to overwrite
- files to remove
- backups needed
- warnings
- invalid reasons

Planner rules:

- Reject absolute archive entries.
- Reject `..` traversal.
- Deduplicate target paths.
- Detect conflicting enabled components that write the same target file.
- Warn if game is running before writes.
- Warn if UE4SS mod is enabled without runtime.

## Install/Uninstall Safety

Apply:

- Ensure target directories.
- Backup every existing target file before overwrite.
- Copy manager-owned files to target.
- Generate guarded UE4SS activation files from the active profile when enabled by policy:
  - `enabled.txt` markers are created for enabled UE4SS profile entries and deleted for disabled entries when present.
  - `mods.txt` is merged where possible, preserving existing unknown/native entries and inserting managed entries before `Keybinds`.
  - `mods.json` is merged as an array of `{ "mod_name": "...", "mod_enabled": true|false }` entries.
- Record every deployed file.

Disable:

- Prefer renaming managed target files with `.disabled` for pak bundles where safe.
- For UE4SS mods, prefer activation-file updates over folder rename; folder rename remains future/manual-review only.

Uninstall selected:

- Remove only files tracked in the manifest.
- Restore overwritten originals from backup where available.
- Leave source archives and library copies intact.

Uninstall all:

- Same as selected, across all managed install records.
- Unknown files are not touched.

Restore vanilla:

- Remove managed pak bundles.
- Remove managed UE4SS mods.
- Optionally remove managed UE4SS runtime.
- Offer quarantine preview for unknown files in `~mods` and `ue4ss\Mods`.

## Tests

Initial test groups:

- Path validation and Steam appmanifest discovery.
- Archive reader supports zip and 7z.
- Archive classification for the four local sample mods.
- Pak grouping with companions.
- UE4SS runtime detection.
- UE4SS mod path-prefix stripping.
- Deployment plan target mapping.
- Unsafe archive entry rejection.
- Backup-before-overwrite.
- Uninstall restores backup.
- Profile save/load/duplicate/delete.
- Drop classification for files and folders.
- Restore vanilla preview does not touch saves.

## Packaging

Target:

- PyInstaller one-folder release for normal use.
- Optional one-file/Nexus upload package later.

Packaged data:

- App writes runtime data to `%LOCALAPPDATA%\Subnautica2ModManager`.
- It must not write inside the packaged exe directory.

## Out Of Scope For First Release

- Nexus API downloads.
- Steam Workshop.
- Dedicated/hosted server management.
- Pak unpack/repack.
- Save editing.
- Automatic UE4SS internet download.
