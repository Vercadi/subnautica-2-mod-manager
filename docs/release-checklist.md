# Nexus Release Checklist

Run these checks before uploading a public portable build.

## Build

- Run `pytest -q` and confirm all tests pass.
- Run `.\scripts\build_portable.ps1 -Clean`.
- Confirm `dist\Subnautica2ModManager\Subnautica2ModManager.exe` exists.
- Confirm `release-metadata.json` version matches the intended release.
- Confirm top-level package files exist: `README.md`, `LICENSE`, `PRIVACY.md`, and `release-metadata.json`.
- Confirm `_internal\assets\app.ico` and `_internal\assets\app_icon.png` are included.

## Clean Launch

- Launch the portable exe from a folder outside the repo and outside the game install.
- Confirm first-run creates manager data, logs, library, backups, settings, profiles, and activity log.
- Confirm Settings opens centered and shows the detected S2 install/build state.
- Confirm Settings shows the install variant, project folder, binaries folder, pak folder, and any Game Pass experimental warning.
- Confirm Help / About / Support opens centered, can copy/save a support report, and shows folder shortcuts.
- Confirm Activity / Recent Events opens centered and shows startup/settings events.
- Confirm Recovery opens centered and only manifest-tracked managed uninstall actions are available.

## Mod Workflow

- Scan/import the real sample `..\Mods` inbox.
- Confirm pak bundles, UE4SS runtime, UE4SS mods, and review-required loose overlays classify correctly.
- Create a non-Vanilla profile and add safe deployable components.
- Open Preview & Apply Profile and confirm exact targets, blocked state, warnings, and Apply Profile availability for safe managed plans.
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
- Include concise release notes from `docs\release-notes-v0.1.2.md` or the current release notes file.
- Include the safety limitations: Preview & Apply required, manifest-tracked recovery only, loose root overlays review-required.
- Include the Windows security note: unsigned PyInstaller builds can trigger heuristic antivirus detections and the app does not require administrator rights.
- Add screenshots of the main shell, Settings, Help/About, Import Review, Preview & Apply, and Recovery if available.

## Current Artifact

After `.\scripts\build_portable.ps1 -Clean` and `.\scripts\package_release.ps1`, upload the zip from:

- Release zip: `dist\release\Subnautica2ModManager-0.1.2-portable.zip`
- SHA256 sums: `dist\release\SHA256SUMS.txt`
- Portable exe: `dist\Subnautica2ModManager\Subnautica2ModManager.exe`
- Screenshot folder: `screenshots`
- Current exe SHA256: `2d488e090421f81a6738023149f9916259943df8a332cd3def11160583bffe2a`
- Current zip SHA256: `eb45cc6537fe0deb23a610b7bf8de89d59ba7df4e4908b9959e83c7c0945ae7f`

Regenerate these hashes after any rebuild; `SHA256SUMS.txt` is the source of truth.
