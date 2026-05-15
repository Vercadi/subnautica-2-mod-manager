# Changelog

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
- Apply Preview for planned creates, overwrites, skips, warnings, errors, and blocked files.
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
