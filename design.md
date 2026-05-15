# Product Design

## Product Position

Subnautica 2 Mod Manager is a game-specific Windows desktop cockpit for local S2 mods. It should feel like a Subnautica tool: clean, aquatic, operational, and a little alive, not like a generic utility skin.

The core promise:

- Drop a mod file or folder.
- Let the app scan and explain what it found.
- Pick or save a profile.
- Preview exactly what will change.
- Apply, disable, uninstall, or restore safely.

## Design Principles

1. Import first, apply second.
   Source files land in a manager-owned library before the game install is touched.

2. Every write gets a preview.
   Installing, uninstalling, restoring vanilla, or applying a profile should show file paths, backups, and warnings before execution.

3. The app owns only what it can prove.
   Managed files can be removed automatically. Unknown files are quarantined only through explicit restore/cleanup flows.

4. Profiles are app-owned loadouts.
   Subnautica 2 does not expose a native modlist, so profiles should represent the manager's intended enabled components and deployment state.

5. The UI should be specific.
   Use S2 terms and path-aware status, but avoid lore-heavy text that slows down repeated use.

## Reference Draft Alignment

The May 15 draft image is viable and should become the concrete target for the first polished shell. It matches the documented direction, but it is more specific than the original docs in four useful ways:

- It puts the manager directly into the `Installed Mods` workflow instead of opening on a generic dashboard.
- It uses a full underwater backdrop with a glass console overlay, which is closer to Subnautica than a normal utility window.
- It combines mod inventory, selected-mod inspection, load order, and console output in one operational screen.
- It adds diegetic HUD details like the O2/system-health gauge and optional depth/radar readout without blocking the core tools; the outer radar hides on tighter desktop widths.

Implementation should follow the draft's layout, with one pragmatic adjustment: the first working version should use standard Windows window chrome or a simple custom header before attempting fully custom titlebar behavior. Custom titlebars are viable later, but they add resizing, dragging, focus, and accessibility edge cases.

## Primary Shell Layout

The main window should be a single glass console over a full-bleed underwater scene.

Target composition:

- Full-window underwater background image.
- Centered main shell with cyan border glow and dark glass panels.
- Top command bar:
  - app title
  - build/profile badge such as `Community Build`
  - current S2 path selector
  - `Launch Game`
  - `Check Updates`
  - `Settings`
- Left navigation rail:
  - Installed Mods
  - Profiles
  - Recovery
  - Diagnostics
  - Activity
  - Help / Support
  - O2/System Health gauge at the bottom
- Center workspace:
  - compact full-height mod list as the primary work surface
  - the list panel accepts drag/drop sources, not only the small drop target
  - profile/import/edit buttons in a narrow side command rail
- Right inspector:
  - UE4SS tab exposes guarded activation policy for `enabled.txt`, `mods.json`, and `mods.txt`; apply preview shows generated activation-file creates/overwrites/deletes before any write
  - selected mod title, version, author, favorite/pin
  - tabs for Overview, Files, Dependencies, Changelog
  - preview image or generated placeholder
  - metadata grid
  - safety actions
- Bottom strip:
  - console output/log on the left
  - load order chips on the right

This shell means `Installed Mods` acts as the default home screen. A separate Dashboard tab can still exist later, but the first viewport should be useful immediately.

## Viability Notes

The draft is viable with the planned Python/CustomTkinter stack, with these implementation choices:

- Background art: use a static bitmap behind the app surface.
- Glass panels: simulate translucency with opaque dark teal colors; native Tk widgets will not blur the background.
- Cyan border glow: use layered frames/canvas strokes, not real shader effects.
- O2 and radar HUDs: draw with `tk.Canvas`; keep the radar passive and responsive so it never covers inspector actions at 1280x760 or 1500x900.
- Mod thumbnails: use local image assets or generated placeholders via PIL/CTkImage.
- Icons: use small local PNG assets or simple line icons rendered consistently.
- Animated scan/glow effects: optional, subtle, and disabled by preference if performance is poor.
- Custom titlebar: defer until the functional shell is stable.

## Information Architecture

### Installed Mods: Dive Console

Purpose: default operational home for importing, inspecting, enabling, applying, and uninstalling local mods.

Content:

- Game path status and build details.
- UE4SS runtime status: missing, partial, installed, unknown version.
- Active profile and active managed mods count.
- Large drop zone for files and folders.
- Filters: All, Pak bundles, UE4SS runtime, UE4SS mods, Loose overlays, Missing, Warnings.
- Source rows with expandable components.
- Each component shows type, source, size, companion count, imported date, target mapping, and status.
- Right-side inspector for the selected component or source.
- Bottom console output for scan/apply/uninstall messages.
- Bottom load order chip strip for the active profile.
- Quick actions:
  - Import mods
  - Apply active profile
  - Install/update UE4SS
  - Uninstall all managed mods
  - Restore profile
  - Backup before install
  - Launch game
- Context actions:
  - Add to active profile
  - Inspect
  - Reimport/update
  - Open source
  - Open managed copy
  - Remove from library

Drag/drop support:

- `.pak`, `.ucas`, `.utoc`
- `.zip`, `.7z`, `.rar` where supported
- folders containing pak bundles
- folders containing UE4SS runtime files
- folders containing UE4SS mods

### Mod Browser

Purpose: future browsing/search space for local archive sources, manual update metadata, and possibly Nexus-facing links. This should not block v1, and it should not promise automatic downloads until implemented.

### Loadout: Dive Plan

Purpose: ordered profile editor and deployment surface.

Content:

- Active profile selector.
- Enabled/disabled ordered list.
- Reorder controls and drag reorder.
- Badges for type: Pak, UE4SS, Runtime, Loose.
- Warning bands for missing source, missing managed copy, missing UE4SS dependency, duplicate output path, and stale game build.
- Apply targets:
  - Local client
  - Profile-only save
  - Dry-run preview
- Actions:
  - Apply profile
  - Save profile
  - Save as
  - Disable selected
  - Remove selected from profile
  - Uninstall selected from game
  - Uninstall all managed mods

### Scan Results Modal

Purpose: review imports before they enter the library.

Content:

- Archive/folder summary.
- Detected components tree.
- File mapping preview.
- Required dependencies.
- Variant picker when multiple alternatives are detected.
- Ambiguous structure review with selectable components.
- Unsupported files list.
- Import button.

Rules:

- Importing does not write to the game install.
- Ambiguous archive structures require user selection.
- UE4SS runtime and UE4SS mods should be labeled clearly before import.

### Profiles: Expeditions

Purpose: named loadout management.

Content:

- Permanent `Vanilla` profile.
- User profiles with counts, notes, last applied timestamp, and game build at last apply.
- Duplicate, rename, delete, compare, export, import.
- Profile diff view:
  - added components
  - removed components
  - order changes
  - enabled/disabled changes

### Recovery: Black Box

Purpose: undo, backups, and restore workflows.

Content:

- Activity timeline.
- Backup records grouped by installs, overwritten files, modlists/profile state, restore vanilla, and quarantine.
- Restore backup action.
- Uninstall managed selected.
- Uninstall all managed.
- Restore vanilla preview.
- Restore profile action for reverting to the most recent saved/applied profile state.
- Quarantine browser.

Restore vanilla should:

- Remove managed files from `Content\Paks\~mods`.
- Remove managed UE4SS mods.
- Optionally remove UE4SS runtime if it was installed by this manager.
- Offer quarantine of unknown pak/UE4SS files only after preview.
- Never touch saves unless a future explicit save backup feature is added.

### Settings

Purpose: path, safety, storage, and UI preferences.

Content:

- S2 install path with auto-detect and manual browse.
- App data path.
- Backup path.
- Archive library path.
- UI size: compact, default, large.
- Theme intensity: calm, standard, high contrast.
- Archive support status: zip, 7z, rar.
- Advanced safety toggles:
  - require preview for all writes
  - quarantine unmanaged files instead of delete
  - keep source archives after import
  - hash large files on import

### Diagnostics

Purpose: support and troubleshooting.

Content:

- Redacted path summary.
- Game build and Steam manifest summary.
- UE4SS state.
- Managed library counts.
- Backup root and recent backup count.
- Last operation log excerpt.
- Export diagnostics bundle.

## Draft Screen Behavior

Phase 10 polish anchors:

- minimum-window behavior is designed around 1280x760, with tighter command/profile/action controls
- long mod names, source labels, chips, and inspector values clamp or wrap instead of pushing panels sideways
- installed rows distinguish library, inbox candidate, profile membership, enabled state, warnings, and preview plan state with text chips
- the inspector preview is explicitly labeled as safe preview/real apply off
- empty library/inbox states are allowed and explain the next local action without reverting to fake installed mods
- real apply, uninstall, restore, and other destructive actions remain disabled in the UI unless a later guarded flow explicitly changes that

Phase 11 import review anchors:

- drop-zone clicks and fallback buttons open file/folder pickers for pak bundles, archives, and UE4SS folders
- native file drop routes into the same review flow when the tkinterdnd2 runtime is active
- selected local `.pak/.ucas/.utoc` companions are grouped as one manager-owned local-files source before import
- the review dialog shows source status, detected components, file counts, warnings, unsupported files, unsafe path rejections, ambiguity, and target hints
- importing from review still copies only into `data/library`; no game install write path is enabled
- source/component selection is supported, and importing another component from an already-copied source merges into the same library source instead of duplicating it

Phase 12 apply preview anchors:

- `Apply Preview` opens a confirmation dialog instead of dumping only to console
- the dialog shows active profile, target root, dry-run/test-apply state, blocked state, creates, overwrites, skips, warnings, errors, required backups, and exact planned paths
- real detected S2 installs remain disabled/refused from the UI
- fake test installs marked with `.s2mm_fake_install` expose a clearly labeled test-only apply action through the guarded installer
- apply results write manifest records, refresh recovery summaries, and report completed/refused/failed state in the console and dialog

Phase 13 recovery anchors:

- `Recovery` in the console header opens a Recovery / Backups dialog
- the dialog shows manifest install records, status, profile name, target root, deployed file count, backup count, warnings, and errors
- uninstall selected and uninstall all are disabled/refused for real detected S2 installs
- fake test installs marked with `.s2mm_fake_install` expose clearly labeled test-only uninstall actions through `RecoveryService`
- restore-vanilla and quarantine are preview-only; unknown files are reported and never deleted automatically
- recovery actions refresh manifest/recovery summaries and write result text to the console

Phase 14 settings anchors:

- top-bar `Settings` opens path and safety configuration
- manual S2 root selection validates `Subnautica2.exe`, shipping exe, and `Subnautica2/Content/Paks` before saving
- Auto Detect reruns Steam/path discovery and persists the detected state
- Mods inbox changes persist through `settings.json` and immediately rescan candidates
- data, library, and backup locations are visible but read-only until a guarded migration flow exists
- archive support, UI scale placeholder, and safety indicators are shown in one operational dialog

Phase 15 packaging anchors:

- portable Windows builds use the PyInstaller one-folder target
- packaged runtime data is under `%LOCALAPPDATA%/Subnautica2ModManager`
- source-mode runtime data remains in the repo root
- first run creates data, logs, backups, and library folders before UI startup
- missing or corrupt settings are regenerated from safe defaults and reported in the console
- release metadata and packaging/privacy/changelog docs ship with the portable folder

Phase 19 release-polish anchors:

- all app-owned dialogs should open centered over the main shell, stay within the visible screen, and use consistent transient/grab behavior
- all app-owned dialogs and profile prompts should use the app icon and the Subnautica-styled glass prompt/report utility, not default Tk dialogs
- command bar update checks are manual by default; optional startup checks remain a Settings preference that defaults off
- Help / About / Support is the user-facing home for support reports, folder shortcuts, project links, archive support, and safety state
- left navigation opens real operational surfaces for load order, profiles, recovery, diagnostics/needs-attention, activity, and support
- mod rows expose actionable controls: profile-only enable switches, row menus, warning details, and top/up/down/bottom ordering
- Activity / Recent Events records user-visible actions in a bounded JSON log without becoming a heavy operational timeline
- Needs Attention is the compact summary of actionable issues; it should avoid hiding blocking safety or missing-runtime states in lower-level panels only
- UE4SS native/core mods should be marked as protected, and root `scripts/` or `dlls/` archives should clearly say they are wrapped as a named UE4SS mod folder

### Installed Mod Row

Rows should match the draft closely:

- thumbnail or generated placeholder on the left
- mod name and version
- short description
- badges for compatibility, UE4SS, Pak, Runtime, Conflict, Missing
- update badge when a newer imported source appears to supersede the installed one
- warning icon when dependencies/conflicts need attention
- enabled toggle
- inspect/details button
- overflow menu

The row's toggle controls whether the component is enabled in the active profile. It should not immediately mutate the game install unless the app is in an explicit "live apply" mode, which should be off by default.

### Right Inspector

The inspector should show the currently selected row and make the common decision easy:

- `Overview`: description, compatibility, last updated, file size, mod id/source id.
- `Files`: planned target paths, managed source files, companion files.
- `Dependencies`: UE4SS/runtime needs, conflicts, load order notes.
- `Changelog`: local notes, imported archive versions, and future release metadata.

Inspector actions:

- `Backup Before Install`
- `Apply Selected` or `Apply Profile`
- `Restore Profile`
- `Uninstall Selected`

### Load Order Strip

The bottom load order area should be chip-based like the draft:

- each enabled profile component gets an ordered chip
- drag chips to reorder
- disabled components appear dimmed or can be hidden with a filter
- auto-sort is advisory only and should show a preview before changing order

For S2 pak and UE4SS mods, load order is mostly manager-side intent unless a specific runtime respects ordering. The UI should explain this in a short status hint and avoid claiming a game-native load-order file exists.

### Console Output

The console is useful and should stay:

- show timestamped scan/import/apply messages
- color lines by info/success/warning/error
- keep technical details short in the docked console
- open full logs from Diagnostics

## Primary Workflows

### First Run

1. Discover Steam libraries.
2. Detect `appmanifest_1962700.acf`.
3. Validate the S2 root by checking `Subnautica2.exe`, shipping exe, and `Subnautica2\Content\Paks`.
4. Show Dashboard with game path and build status.
5. Seed a `Vanilla` profile.
6. Scan the local `Mods/` inbox and offer import.

### Import Archive

1. User drops or selects one or more archives.
2. Scanner classifies each source.
3. Scan Results shows components and warnings.
4. User confirms import.
5. App copies source archive/folder contents into manager-owned storage.
6. Library rows appear.
7. User can add components to the active profile.

### Apply Profile

1. User clicks Apply active profile.
2. Planner maps enabled profile components to target game paths.
3. Preview lists creates, overwrites, disables, removes, and backups.
4. User confirms.
5. App backs up overwritten files.
6. App writes/copies files.
7. Manifest records deployed paths.
8. Dashboard updates.

### Install UE4SS Runtime

1. User imports a runtime archive or drops the UE4SS folder.
2. Scanner detects runtime markers.
3. Planner maps runtime files to `Subnautica2\Binaries\Win64`.
4. Preview calls out loader files such as `dwmapi.dll`, `UE4SS.dll`, `UE4SS-settings.ini`, and `ue4ss/`.
5. Apply records runtime files separately from normal mods.

### Install UE4SS Mod

1. User imports a UE4SS mod archive or folder.
2. Scanner detects mod shape:
   - `ue4ss/Mods/<Name>/...`
   - `Subnautica2/Binaries/Win64/ue4ss/Mods/<Name>/...`
   - root folder with `Scripts/main.lua`, `Dlls`, `enabled.txt`, or `settings.ini`
3. Planner maps to `Subnautica2\Binaries\Win64\ue4ss\Mods\<Name>`.
4. Preview warns if UE4SS runtime is missing.

### Uninstall All

1. User opens Recovery or Dashboard action.
2. Preview lists every managed file that will be removed and every backup restoration candidate.
3. Unknown files are not removed by default.
4. User confirms.
5. App removes managed files, restores overwritten originals when tracked, and records the action.

## UX Details

- Use dense but readable rows for repeated mod operations.
- Keep the main screen functional on launch; no landing page.
- Give path previews real space. Mod managers fail when users cannot see exactly what will be written.
- Long filenames should truncate in the middle with hover/full-detail tooltips.
- Status chips should use color plus text, not color alone.
- The drop zone should respond visually to valid files, unsupported files, and mixed drops.
- Dangerous actions use preview modals with exact path counts.

## Edge Cases

- Archive contains multiple pak bundles: import as one source with multiple components.
- Archive contains variants: require one variant selection per variant group.
- Archive contains pak plus UE4SS files: classify as mixed and require component review.
- Archive path tries traversal: reject unsafe entries.
- File already exists in target: back up before overwrite.
- Source archive is moved after import: managed copy remains usable.
- Managed copy missing: show repair/reimport option.
- Game update changes build id: show stale-profile warning, but do not block apply.
