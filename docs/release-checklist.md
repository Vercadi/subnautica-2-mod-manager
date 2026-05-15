# Nexus Release Checklist

Run these checks before uploading a public portable build.

## Build

- Run `pytest -q` and confirm all tests pass.
- Run `.\scripts\build_portable.ps1 -Clean`.
- Confirm `dist\Subnautica2ModManager\Subnautica2ModManager.exe` exists.
- Confirm `release-metadata.json` version matches the intended release.
- Confirm top-level package files exist: `README.md`, `CHANGELOG.md`, `PRIVACY.md`, `PACKAGING.md`, `docs\`, and `assets\`.
- Confirm `assets\app.ico` and `assets\app_icon.png` are included.

## Clean Launch

- Launch the portable exe from a folder outside the repo and outside the game install.
- Confirm first-run creates manager data, logs, library, backups, settings, profiles, and activity log.
- Confirm Settings opens centered and shows the detected S2 install/build state.
- Confirm Help / About / Support opens centered, can copy/save a support report, and shows folder shortcuts.
- Confirm Activity / Recent Events opens centered and shows startup/settings events.
- Confirm Recovery opens centered and only manifest-tracked managed uninstall actions are available.

## Mod Workflow

- Scan/import the real sample `..\Mods` inbox.
- Confirm pak bundles, UE4SS runtime, UE4SS mods, and review-required loose overlays classify correctly.
- Create a non-Vanilla profile and add safe deployable components.
- Open Apply Preview and confirm exact targets, blocked state, warnings, and Apply Profile availability for safe managed plans.
- Verify `SN2P`-style loose root overlays remain blocked and actionable.
- Apply a small safe managed profile to the real install only after confirming backups/manifest state, then uninstall it from Recovery and verify only managed files changed.

## Fake-Install Execution

- Create a fake S2 install with `.s2mm_fake_install`, `Subnautica2.exe`, shipping exe, `Subnautica2\Content\Paks`, and `Subnautica2\Binaries\Win64`.
- Switch Settings to the fake install.
- Apply a safe profile using the test-only apply action.
- Confirm manifest records, deployed files, backups if overwrites exist, activity entries, and recovery summaries.
- Run test-only uninstall-all and confirm managed files are removed/restored.
- Confirm real S2 install folders were not modified.

## Nexus Upload

- Zip the `dist\Subnautica2ModManager` folder contents as the portable release.
- Include concise release notes from `CHANGELOG.md`.
- Include the safety limitations: Apply Preview required, manifest-tracked recovery only, loose root overlays review-required.
- Include the Windows security note: unsigned PyInstaller builds can trigger heuristic antivirus detections and the app does not require administrator rights.
- Add screenshots of the main shell, Settings, Help/About, Import Review, Apply Preview, and Recovery if available.

## Current Artifact

After `.\scripts\build_portable.ps1 -Clean` and `.\scripts\package_release.ps1`, upload the zip from:

- Release zip: `dist\release\Subnautica2ModManager-0.1.0-portable.zip`
- SHA256 sums: `dist\release\SHA256SUMS.txt`
- Portable exe: `dist\Subnautica2ModManager\Subnautica2ModManager.exe`
- Screenshot folder: `screenshots`

Do not hard-code package hashes in this bundled checklist; `SHA256SUMS.txt` is the source of truth because the checklist is included inside the zip.
