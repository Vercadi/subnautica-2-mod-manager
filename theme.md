# Theme System

## Direction

Theme name: `Abyssal HUD`.

The UI should feel like a Subnautica 2 field console: glass, depth, scan highlights, pressure warnings, and bioluminescent accents. It should not look like the default CustomTkinter blue theme with renamed labels.

The visual system should stay practical. This is a repeated-use tool, so the water design should guide attention without becoming decorative clutter.

## Draft Target

The supplied draft is the target art direction. Keep these features:

- cinematic underwater background visible outside the main shell
- large dark glass console centered in the window
- cyan luminous shell outline
- title and command bar across the top
- left navigation rail with active cyan slab highlight
- circular O2/System Health gauge in the lower nav
- center mod list with thumbnails and status chips
- right selected-mod inspector with tabbed detail surface
- bottom console output plus load-order chip strip
- optional depth/radar HUD outside or beside the main shell when space allows

Do not copy the draft's sample content literally. Use real S2 manager states and local mod data.

Phase 10 implementation note: the shell now favors a darker abyss center, tighter operational controls, stronger cyan borders, and explicit preview-only/read-only states. Text-heavy surfaces are clamped or wrapped so the minimum 1280x760 window remains usable.

Phase 21 implementation note: the decorative outer depth/radar HUD is shown only when the window has enough horizontal room. At 1280x760 and 1500x900 it stays hidden so inspector buttons and release screenshots remain unobstructed.

Phase 22 implementation note: default Tk prompts are replaced by app-owned glass dialogs with the app icon. Row controls use compact cyan-outline buttons and disabled-state helper text so inactive switches are visibly profile-only instead of dead controls.

## Color Tokens

```text
bg_abyss             #03101A
bg_trench            #061722
panel_deep           #09222D
panel_glass          #0D3444
panel_glass_hover    #143E4B
border_cold          #2A6170
border_soft          #123A49
text_primary         #E7F8F8
text_secondary       #A9CDD0
text_muted           #6F969C
accent_lagoon        #38D6D6
accent_biolume       #7CF7C8
accent_coral         #FF7A59
accent_pressure      #FFD166
accent_kelp          #67D38A
danger               #FF5E6C
warning              #FFD166
success              #67D38A
disabled             #355862
shadow               #02080B
shell_border         #1AC9F4
shell_border_dim     #0B5570
glass_black          #020B13
glass_navy           #061A29
glass_cyan           #08384B
chip_blue            #154D78
chip_purple          #4A3B84
chip_green           #0D5E4C
chip_orange          #7A4312
```

Usage:

- `bg_abyss` for the app root.
- `bg_trench` for major full-width zones.
- `panel_deep` and `panel_glass` for tool panels, repeated rows, and mod source cards.
- `accent_lagoon` for primary actions and active navigation.
- `accent_biolume` for positive scan/ready states.
- `accent_coral` for destructive or attention-grabbing actions.
- `accent_pressure` for warnings and dependency issues.
- `accent_kelp` for installed/synced/healthy mod state.
- `shell_border` for the large outer console outline and active-row border.
- `glass_black`, `glass_navy`, and `glass_cyan` for the simulated translucent panels.
- `chip_blue`, `chip_purple`, `chip_green`, and `chip_orange` for compact type/status badges.

Avoid a one-note blue UI. Use coral, amber, and kelp accents intentionally.

## Typography

Primary font target: Segoe UI Variable or Segoe UI.

Fallbacks:

```text
Segoe UI Variable, Segoe UI, Arial, sans-serif
```

Monospace:

```text
Cascadia Mono, Consolas, monospace
```

Scale:

```text
page_title      22
section_title   15
panel_title     13
row_title       12
body            12
small           11
tiny            10
mono            11
```

Rules:

- No negative letter spacing.
- Avoid oversized marketing text.
- Use compact operational headings.
- File paths use monospace and wrap only in details panels.

## Layout

Window target:

```text
default geometry: 1500x900
minimum: 1280x760
```

Structure:

- Full-window background image.
- Main shell inset from all edges.
- Top command bar inside the shell.
- Left navigation rail with icon + short label.
- Center installed-mods workspace.
- Right selected-mod inspector.
- Bottom console/load-order strip.

Panel radius:

```text
shell_radius: 10
small_panel_radius: 8
row_radius: 5
button_radius: 5
modal_radius: 8
```

Spacing:

```text
outer_margin: 16
panel_gap: 12
row_gap: 6
row_padding_x: 10
row_padding_y: 8
nav_width: 205
inspector_width: 388
bottom_strip_height: 145
top_bar_height: 72
```

No nested cards. Repeated rows can be cards; page sections should be full-width panels or unframed layouts.

## Background And Glass

Use a static background image loaded through PIL/CTkImage and sized to cover the window.

Tk/CustomTkinter does not provide true acrylic blur, so panels should use carefully chosen opaque colors that imitate dark glass:

- main shell fill: `#061523`
- major panels: `#071C2B`
- inner rows: `#0B2838`
- hover rows: `#103B50`
- outer shell border: `shell_border`
- inner separators: `border_soft`

Layering strategy:

1. root background image label/canvas
2. main shell frame with dark fill and cyan border
3. panel frames
4. row/detail widgets
5. canvas HUD widgets for O2 and radar

The background should be visually rich around the shell but darker behind text. If the image is too bright, pre-process a darker copy for the app.

## Component Styling

### Navigation Rail

- Dark trench background.
- Active tab uses a vertical lagoon glow bar.
- Icons should be simple line glyphs.
- Labels stay short and match the draft:
  - Installed Mods
  - Profiles
  - Recovery
  - Diagnostics
  - Activity
  - Help / Support

### Status Strip

- Top command bar with title, build badge, path selector, and command buttons.
- Path selector should look like a compact breadcrumb field.
- `Launch Game` is the primary button.
- `Updates`, `Help`, and `Settings` are secondary buttons.
- State dots use lagoon/success/warning/danger tokens where compact status is needed.

### Dialogs And Support Surfaces

- Modal dialogs use the same abyss background, glass-black frame, glass-navy cards, cyan borders, and compact footer actions as the main shell.
- Dialog placement is app-owned: center over the main shell, clamp to screen bounds, use transient/grab, and avoid long-lived topmost state.
- Help / About / Support uses the same operational styling as Settings rather than a marketing page.
- Activity / Recent Events uses compact timestamped rows and should stay readable at 820x600.

### O2 Gauge

Draw with `tk.Canvas`.

Target details:

- circular segmented progress ring
- center value such as `98%`
- label: `O2` and `System Health`
- use `accent_lagoon` for healthy state, `accent_pressure` below warning threshold, `danger` below critical threshold
- the value should reflect app/system readiness, not actual game oxygen

Suggested readiness calculation:

- game path valid
- UE4SS state healthy or intentionally absent
- active profile has no missing managed files
- last operation did not fail

### Depth/Radar HUD

Optional first-release decoration if the layout has room.

- draw outside the main shell or in a narrow right gutter
- depth value can be decorative/readiness-based
- radar should be passive and never compete with mod actions

### Drop Zone

Visual:

- Dashed cold border.
- Subtle sonar ring background, drawn procedurally if no bitmap asset is available.
- Valid drag state brightens lagoon border.
- Mixed/unsupported drag state uses pressure amber.
- Phase 11 adds compact `Browse Files` and `Browse Folder` fallback controls below the sonar panel.

Text:

- Keep it short and close to the draft: `Drop .pak / UE4SS mods here`
- Details can appear below in small muted text.

### Import Review Dialog

- Glass-black header and scroll body.
- Each source uses a glass-navy card with a checkbox, scan state, path, warnings, unsupported files, unsafe path rejections, and ambiguous review text.
- Components are nested as compact rows with their own checkboxes, file counts, type, and target hints.
- Primary action is `Import Selected`; it writes only to the manager library.

### Mod Rows

Each row:

- Left thumbnail.
- Primary display name.
- Version and short description.
- Badges: Pak, UE4SS, Runtime, Loose, Missing, Warning.
- Right-side update/conflict badge, warning icon, enable toggle, inspect stack icon, overflow menu.

Rows should not resize when badges change. Reserve fixed badge/action areas.

Thumbnails:

- Real thumbnail if a mod provides one.
- Generated placeholder based on component type if no thumbnail exists.
- Pak bundle: sonar/pak cube motif.
- UE4SS mod: plug/module motif.
- Runtime: core module motif.
- Conflict/missing: amber/danger overlay marker.

### Inspector

- Right panel uses the same glass style as mod rows.
- Selected mod title, version, author/source line, and favorite/pin icon.
- Tabs: Overview, Files, Dependencies, Changelog.
- Preview image frame keeps fixed aspect ratio.
- Metadata grid uses compact rows and chips.
- Primary actions sit at the bottom and stay visible.

### Compact Mod List

- The mod list is the dominant right-side work surface.
- Profile, import, scan, and bulk activation buttons live in a narrow side command rail.
- The full mod-list panel is a drag/drop surface when native DND is available.
- Rows favor quick scanning: name, status/type text, warning action, active switch, and overflow menu.
- Ordering controls are hidden because Subnautica 2 load order is not currently treated as a meaningful user-facing workflow.
- UE4SS activation policy controls live in the left detail panel and cover `enabled.txt`, `mods.json`, and `mods.txt` without enabling unsafe writes.

### Loadout Chips

- Rounded chip with numeric prefix.
- Active chip border: `accent_lagoon`.
- Disabled chip fill: `disabled`.
- Conflict chip border: `accent_pressure`.
- Drag target should show a cyan insertion glow.

### Console Output

- Bottom-left console panel.
- Monospace text.
- Info lines use `text_secondary`.
- Success lines use `accent_kelp`.
- Warning lines use `accent_pressure`.
- Error lines use `danger`.
- Keep visible line count small and scrollable.

### Buttons

Primary:

- Fill: `accent_lagoon`
- Text: `bg_abyss`
- Hover: `accent_biolume`

Secondary:

- Fill: transparent/glass
- Border: `border_cold`
- Text: `text_primary`

Danger:

- Fill: transparent
- Border/text: `accent_coral`
- Hover fill: low-alpha coral equivalent if supported.

Use icon buttons for repeated row actions. Text buttons are for major commands.

### Preview Modal

- Header: action, target, risk level.
- Body: split into changes, backups, warnings.
- File paths in monospace.
- Confirmation button wording should name the action: `Apply Profile`, `Uninstall Managed Mods`, `Restore Vanilla`.

Phase 12 apply preview:

- Use the same glass-black header and scroll body as import review.
- Summary cells show mode, blocked state, creates, overwrites, required backups, skips, fake-test state, and real-apply state.
- Real installs show a disabled `Real Apply Disabled` or `Apply Blocked` action.
- Fake test installs show `Apply To Fake Test Install` in cyan only when the plan is executable.
- Result text stays in the footer after execution and also writes to console output.

### Recovery Dialog

- Use the same glass-black header and scroll body as import/apply dialogs.
- Install records are selectable only when they are uninstallable and the target is a fake test install.
- Record rows show status, profile, target root, deployed file count, backup count, warnings, and errors.
- Restore-vanilla and quarantine data are preview-only panels with muted path text.
- Test-only recovery actions use cyan; real-install recovery buttons stay disabled.

### Settings Dialog

- Use the same glass-black header and scroll body as the other operational dialogs.
- Group content into install, storage paths, archive/UI support, and safety state cards.
- Path values wrap in muted text; action buttons stay compact and right-aligned inside cards.
- Invalid path saves report amber feedback in the footer and console.
- Data/library/backup relocation is labeled read-only until migration is implemented.
- Include an About / Release Metadata card with version and portable packaging notes.

### Progress

- Use thin lagoon progress bars.
- For scanning, add a small pulsing scan line only if it remains subtle.
- Never block the UI without status.

## Motion

Keep animation small:

- 120-180 ms hover fade.
- Slow scan-line pulse on active import only.
- No constant background animation unless it can be disabled.

## Icon Direction

Use simple line icons where possible:

- Installed Mods: puzzle/module
- Load Order: ordered list
- Profiles: users/bookmark
- Backups: archive box
- Mod Browser: globe
- Diagnostics: pulse line
- Console: terminal
- Settings: gear
- Apply: check/arrow into target
- Uninstall: remove/minus in tray
- Inspect: magnifier
- Warning: triangle
- UE4SS/runtime: plug/module

If using a Python icon strategy, prefer local PNG assets or small generated vector paths wrapped by reusable helpers. Avoid text-only rounded pills when a known symbol is clearer.

## Optional Asset Prompts

Use these only if we decide bitmap assets are worth adding.

### App Icon Prompt

```text
Create a clean Windows app icon for a Subnautica 2 mod manager. A stylized deep-sea scanner console symbol, circular sonar ring, small modular cube/pak shape, bioluminescent cyan and sea-green glow, dark abyss background, high contrast, readable at 32px, no text, no logos, no copyrighted UI elements, polished game utility icon.
```

### Header Texture Prompt

```text
Create a wide dark underwater sci-fi desktop app background for a Subnautica-inspired mod manager. Deep blue ocean, visible water surface far above, coral and bioluminescent plants near the bottom edges, subtle futuristic submarine silhouette on the right, small distant glowing drones, cinematic but not busy, strong dark center area for a glass UI overlay, cyan and violet accents, no text, no logos, 2560x1440.
```

### Empty State Illustration Prompt

```text
Create a restrained desktop utility empty-state illustration: a transparent glass cargo container floating in dark blue-green water with small glowing mod-chip silhouettes inside, subtle sonar lines, polished Subnautica-inspired mood, no text, no logos, clean edges, 1200x800.
```

### Mod Thumbnail Placeholder Prompt

```text
Create a compact thumbnail set for a Subnautica-inspired mod manager UI. Dark underwater sci-fi HUD style, cyan bioluminescent highlights, small modular tech objects, no text, no logos. Variants for pak bundle, UE4SS mod, runtime core, conflict warning, missing file. 512x288 each.
```

## Accessibility

- Every color state needs a label or icon.
- Warnings and destructive actions cannot rely on color alone.
- Text contrast should stay readable on `panel_deep`.
- UI size setting must affect token scale, row height, and wrap widths.
- Tooltips are required for icon-only controls.
