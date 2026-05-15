# Phase 16 Real Sample Mod Validation

Validation date: 2026-05-15

Real game install used for read-only validation:

- Root: `<SteamLibrary>\steamapps\common\Subnautica2`
- Steam app id: `1962700`
- Steam build: `23165626`
- Game version: `Build 34 / CL 113109 / 2026-05-10`
- UE4SS runtime in real install: not present
- Safety: dry-run preview only; no files were written to the real install

Sample inbox:

- `<ProjectRoot>\..\Mods`
- `README.md` is skipped as inbox documentation
- Archive support during validation: `.zip` yes, `.7z` yes, `.rar` yes

## Source Results

| Source | Classification | Components | Warnings | Unsafe / Unsupported | Target hint |
| --- | --- | ---: | --- | --- | --- |
| `Hide HUD-58-1-1778794542.7z` | UE4SS mod | 1 | Requires UE4SS runtime | 0 / 0 | `Subnautica2\Binaries\Win64\ue4ss\Mods\HUDToggle` |
| `Infinite Oxygen-56-1-1778788524.zip` | Pak bundle | 1 | None | 0 / 0 | `Subnautica2\Content\Paks\~mods` |
| `ScannerSpeedMod-57-1-8-0-1778790428.zip` | UE4SS mod | 1 | Requires UE4SS runtime | 0 / 0 | `Subnautica2\Binaries\Win64\ue4ss\Mods\ScannerSpeedMod` |
| `SeaSprint 1.0.0-55-1-0-0-1778784735.zip` | Pak bundle | 1 | None | 0 / 0 | `Subnautica2\Content\Paks\LogicMods` |
| `SN2ModSettings V1.0.3-20-1-0-3-1778783284.zip` | UE4SS mod | 1 | Requires UE4SS runtime | 0 / 0 | `Subnautica2\Binaries\Win64\ue4ss\Mods\SN2ModSettings` |
| `SN2P - 5.14.26-18-1-0-1778780636.zip` | Loose overlay | 1 | Manual review required | 0 / 0 | `review required` |
| `UE4SS SN2-36-EA1-1778748850.zip` | UE4SS runtime | 1 | None | 0 / 0 | `Subnautica2\Binaries\Win64` |

## Component Details

- `HUDToggle`: detected from `ue4ss/mods/HUDToggle`; deploys to `ue4ss\Mods\HUDToggle`.
- `InfiniteOxygen P`: `.pak`, `.ucas`, and `.utoc` companions are grouped as one pak bundle.
- `ScannerSpeedMod`: wrapped UE4SS mod folder is preserved. `ScannerSpeedMod/original_durations.lua` now stays in the UE4SS mod component instead of becoming a loose overlay.
- `SeaSprint`: `.pak`, `.ucas`, and `.utoc` companions are grouped as one UE4SS logic pak bundle and deploy to `LogicMods`.
- `SN2ModSettings`: full `Subnautica2/Binaries/Win64/ue4ss/Mods` prefix is stripped to the correct UE4SS mod-relative target.
- `SN2P`: contains root `dxgi.dll` and `snsnp_settings.ini`. It remains a loose overlay and is blocked in deployment preview pending explicit manual review policy.
- `UE4SS Runtime`: runtime archive includes the UE4SS core files plus bundled files under `ue4ss/Mods`; these are treated as part of the runtime payload.

## Flow Audit

- Scanner: 7 real sources scanned, 7 recognized components, 0 unsafe paths, 0 unsupported files, 0 ambiguous multi-pak sources.
- Import: all 7 sources imported successfully into a temporary manager data directory; duplicate source hash reuse was confirmed.
- Profile: all 7 imported components could be added to a non-Vanilla validation profile; Vanilla remains protected.
- Deployment preview against the real install during Phase 16: dry-run only, 36 create actions, 0 overwrite actions, 2 blocked loose-overlay actions, 1 warning, 1 error. The blocked plan comes only from `SN2P`. Later release hardening enables real managed apply through Apply Preview for non-blocked plans.
- Recovery preview against the real install: 0 managed install records, 0 managed files, 0 unknown files, no saves touched.
- Settings view: real install validates, Steam manifest/build status resolves, inbox path exists, safety indicators remain disabled or preview-only for real installs.

## Fixes From This Pass

- Hardened UE4SS wrapped-folder detection so archives with `ModName/Scripts/main.lua` keep `ModName` as the target folder.
- Included sibling files under a detected wrapped UE4SS mod root, which fixes `ScannerSpeedMod/original_durations.lua`.
- Added regression tests for wrapped UE4SS mod archives and root-level UE4SS mod archives.
- Added LogicMods target detection for non-`_P` UE4SS pak bundles such as SeaSprint; `_P` patch paks remain in `~mods`.

## Known Limitations

- `SN2P` still needs manual review before it can be safely represented as an installable root overlay or runtime-like component.
- Runtime archives with bundled `ue4ss/Mods` content are currently imported as one runtime payload, not split into separate optional built-in runtime mods.
- The scanner does not parse Nexus metadata from filenames yet; long source names may still appear in source rows, though deployment safety is unaffected.
- Current release behavior: non-blocked managed plans can apply through Preview & Apply, while loose overlays remain blocked and recovery only touches manifest-tracked managed files.
