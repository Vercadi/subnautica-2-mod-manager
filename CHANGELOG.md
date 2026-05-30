# Changelog

## 0.2.2

Hotfix focused on Nexus feedback around inbox installs, duplicate old versions, mod-list cleanup, and confusing actions.

Changed:

- Inbox mods can now be selected and installed/enabled from the main mod list instead of requiring a separate review-dialog path.
- The row menu now shows `Install & Enable` for inbox candidates.
- The side action changes from `Enable` to `Install & Enable` when an inbox candidate is selected.
- Row helper text now explains that supported inbox candidates can be installed from the list.
- Review-required loose overlays still stay blocked and cannot be bypassed by the inbox shortcut.
- Added an explicit `Delete From List` action for uninstalled imported mods. This removes the manager-owned `data/library/sources/src_*` copy and `library_state.json` entry, and removes stale profile references.
- Renamed the profile-only action to `Remove from Profile` so it is not confused with uninstalling or deleting a library entry.
- New imports now replace likely duplicate old uninstalled library entries instead of filling the list with multiple versions of the same mod.
- Duplicate entries that cannot be replaced because they are installed are marked with a `Duplicate` badge and can be cleaned after uninstalling.
- Added `Delete Old Versions` to the row menu for cleaning older uninstalled duplicate entries while keeping the selected one.
- Apply/plan errors now include clearer next-action wording for missing sources, target conflicts, unsafe paths, and missing install paths.
- Apply Preview includes a `Copy Details` action when warnings/errors exist.

## 0.2.0

Visual polish pass based on the Subnautica 2 in-game PDA screenshots.

Changed:

- Restyled the main shell toward an S2 PDA surface with brighter cyan outlines, darker glass panels, subtle hex texture, and cyan corner brackets.
- Moved the selected-mod inspector to the right side so the mod list remains the main workspace.
- Changed active navigation, profile selector, and Apply styling toward the amber in-game selected-state language.
- Improved compact mod rows and review-required presentation; loose/review-required entries now read as `Limited Access` visually.
- Kept the proven 0.1.5 install/apply/remove/uninstall behavior unchanged.

## 0.1.5

Stabilization pass focused on the confusing Apply/Remove/Uninstall cases reported after 0.1.4.

Changed:

- Remove is now profile-only and works for installed mods; it creates a visible pending Apply change instead of telling users to uninstall first.
- Uninstall removes manager-installed game files from the manifest and keeps the mod available in the manager list for reinstall later.
- Reset to Vanilla now switches to Vanilla and runs manifest-backed uninstall directly, leaving unknown/manual files alone.
- Apply can still install supported mods while unrelated loose/review-required items are present; blocked loose overlays are skipped rather than softlocking safe changes.
- Disabled profile entries whose manager/library copy is missing no longer block cleanup of already installed files.
- Missing-source Apply refusals now give one next step instead of a technical error block.
- UE4SS runtime warning detection now recognizes runtime-like imported packages by install kind, badges, and display name to avoid false warnings when runtime is enabled.

Safety:

- Unknown/manual files are still never deleted.
- Loose overlays and SN2P-style root overlays remain review-required and skipped by automatic Apply.
- Manifest-backed uninstall and reset do not depend on library/source archives still being present.
- Critical uninstall/reset confirmations remain non-disableable.

## 0.1.4

UX clarity, installed-config editing, and responsiveness hardening.

Changed:

- Added unified mod states so rows and inspector text use clearer labels like Available, Enabled, Pending Apply, Installed, Will Remove, Needs Review, and Blocked.
- Main row selection actions now expose clearer enable/disable/remove/uninstall availability and disabled reasons.
- Safe unambiguous drag/drop or Install From File sources can now install into the manager and enable automatically without forcing Import Review.
- Review-required loose overlays stay skipped while supported safe profile changes can still apply.
- Normal warning details now route to inline/console context instead of opening noisy noncritical popups.
- Native drag/drop registration was fixed for the full mod list area.
- Inbox scans use a persistent cache and timing logs to reduce repeated scan cost.

Added:

- Installed-mod-only config discovery and editing for safe text config files: `.lua`, `.ini`, `.json`, `.txt`, and `.cfg`.
- Config edits back up the installed file before saving and can restore the imported original.
- Game Pass / WinGDK UE4SS health output for runtime root, mod target, proxy DLLs, and experimental layout warnings.
- Runtime warning suppression is stricter when UE4SS is installed, manually present, or enabled in the active profile.

Safety:

- Config editing is only available for manager-installed files.
- Imported-but-not-installed mods show install-first guidance instead of an editor.
- Unknown/manual files are still never deleted.
- Loose overlays and SN2P-style root overlays remain review-required.
- Critical uninstall/reset confirmations remain non-disableable.

## 0.1.3

UX simplification and profile/game sync redesign.

Changed:

- Main flow is now drag/drop -> Install & Enable -> Apply -> Launch.
- Main action labels are simplified: Apply, Install, Enable, Disable, Remove, Uninstall, Reset to Vanilla.
- Recovery / Backups is now Installed Files / Backups.
- Mod rows now use Available, Enabled, Disabled, Installed, and Needs Review states.
- Apply now syncs the game folder to the active profile, including removal of manager-installed files that are no longer enabled.
- Apply skips review-required loose overlays while installing supported selected mods.
- Added an Open Mods Folder action for the detected game-side mod target.

Safety:

- Unknown/manual files are still reported only and are not deleted.
- Loose overlays remain blocked.
- Overwrites are still backed up before install.
- Uninstall/reset confirmations remain critical and cannot be disabled.

## 0.1.2

Patch release for update visibility.

Changed:

- Startup update checks now default to enabled for new installs and missing/corrupt settings.
- Existing users who already saved an update-check preference keep their current choice.
- Update checks still only query GitHub Releases; the app does not auto-download or auto-install updates.

## 0.1.1

Patch release focused on non-Steam install layouts.

Added:

- Epic/manual Win64 layout validation that does not require the Steam root wrapper exe.
- Manual path normalization for the outer install root, inner `Subnautica2` folder, `Subnautica2\Binaries\Win64`, `Content\Subnautica2`, and `Content\Subnautica2\Binaries\WinGDK`.
- Experimental Game Pass WinGDK layout detection for the user-reported `Content\Subnautica2\Binaries\WinGDK` structure.
- Layout-derived deployment targets for paks, UE4SS runtime files, and UE4SS mods.
- Game Pass UE4SS targeting now follows the ProtonLabs Game Pass package notes: base/runtime payloads can be applied from the `Content` root, while standard Lua mods target `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods`.
- UE4SS LogicMods pak target support: non-`_P` pak bundles deploy to `Content\Paks\LogicMods`; `_P` patch paks deploy to `Content\Paks\~mods`.
- Existing imported non-`_P` pak library entries are migrated to LogicMods targets on load.
- Settings, diagnostics, support-report, Needs Attention, and Preview & Apply wording for detected install variants.
- WinGDK and Game Pass `Content\ue4ss` prefix stripping for full-path UE4SS runtime archives.
- Clearer UE4SS runtime guidance explaining that the runtime can be imported into the same manager profile.

Changed:

- Steam auto-detection remains unchanged, but install layout details now show the detected variant, project folder, binaries folder, pak folder, UE4SS runtime root, and UE4SS target folder.
- Invalid manual path messages now list missing expected files/folders and suggest valid folder levels to select.

Notes:

- Game Pass support is experimental. The manager can detect WinGDK and target standard Lua mods to `WinGDK\ue4ss\Mods`, but individual mods may still crash if they are not compatible with that build/runtime.
- Loose root overlays and unsafe unmanaged writes remain blocked.

## 0.1.0

Initial public release.

Added:

- Portable Windows build for Subnautica 2 Mod Manager.
- Steam install discovery and manual install path validation.
- Manager-owned mod library with drag/drop, browse, archive, and folder imports.
- Pak bundle detection for `.pak`, `.ucas`, and `.utoc` files.
- UE4SS runtime, Lua mod, and C++ mod detection.
- Profile management with protected Vanilla profile, enable/disable controls, and bulk actions.
- UE4SS activation-file support for `enabled.txt`, `mods.txt`, and `mods.json`.
- Preview & Apply for planned creates, overwrites, skips, warnings, errors, and blocked files.
- Managed apply for supported pak and UE4SS mods.
- Manifest-backed managed uninstall, backup, and recovery.
- Diagnostics, redacted support reports, Needs Attention summaries, and activity logging.
- Settings, Help/About/Support, Recovery, Import Review, and Activity dialogs.
- Subnautica-inspired underwater UI theme.

Safety:

- Unknown files are reported, not deleted.
- Recovery only touches manifest-tracked managed files.
- Loose game-root overlays and SN2P-style overlays are review-required and blocked from automatic apply.
- Support reports redact personal home paths where practical.

Known limitations:

- Per-mod UE4SS settings editing is not implemented.
- Manually installed mods cannot be safely uninstalled unless they were installed by this manager.
- Loose root overlays require manual review.
- RAR support depends on local archive support.
