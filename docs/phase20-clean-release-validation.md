# Phase 20 Clean Release Validation

Date: 2026-05-15

## Portable Package

Validated `dist\Subnautica2ModManager` as a Nexus-style portable folder.

Observed required top-level contents:

- `Subnautica2ModManager.exe`
- `_internal\`
- `assets\`
- `docs\`
- `README.md`
- `CHANGELOG.md`
- `PRIVACY.md`
- `PACKAGING.md`
- `release-metadata.json`

The package includes app icon assets, bundled CustomTkinter/TkDND runtime data, release metadata, and public docs.

## Frozen First Run

Launched the packaged executable with an isolated temporary `LOCALAPPDATA` value to avoid touching normal user app data.

Result:

- executable launched successfully
- app created frozen-mode runtime root under the temporary app data folder
- `data\`, `data\logs\`, `data\library\`, `backups\`, `settings.json`, `profiles.json`, and `activity_log.json` were created
- no normal app data location was used for this smoke

## Real Sample Mods Against Fake Install

Used the real sample inbox at:

```text
<ProjectRoot>\..\Mods
```

Smoke result:

- 7 source(s) scanned
- 7 component(s) detected
- 7 source(s) imported into a temp manager library
- 6 safe deployable component(s) added to a temp profile
- fake `.s2mm_fake_install` apply preview was ready
- test apply deployed 36 file(s)
- manifest recorded 1 completed install
- uninstall-all removed 36 managed file(s)
- recovery summary updated to 1 uninstalled record

`SN2P`-style loose root overlay remained outside the safe deployable component set and stays review-required.

## Real Install Safety Check

The smoke compared real install markers before and after fake-install work:

```text
<SteamLibrary>\steamapps\common\Subnautica2
```

Observed unchanged:

- real install root exists
- real `Subnautica2\Content\Paks\~mods` marker state
- real `Subnautica2\Binaries\Win64\ue4ss\Mods` marker state

No real S2 install write was performed.

## Remaining Manual Upload Checks

See `docs\release-checklist.md`.

Before public Nexus upload, still do a human visual pass over:

- main window at 1280x760 and 1500x900
- Settings centered over the app
- Help / About / Support copy/save report
- Activity / Recent Events
- Import Review
- Apply Preview
- Recovery / Backups
