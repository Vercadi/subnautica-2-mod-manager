# Subnautica 2 Mod Manager v0.1.1

Patch release for Epic/manual installs and experimental Game Pass WinGDK layout support.

## Highlights

- Steam auto-detection remains supported and unchanged.
- Epic/manual Win64 installs can now be selected manually when they expose the normal Unreal layout.
- Manual path selection now accepts common folder levels instead of only the outer Steam-style root.
- Game Pass WinGDK layout support is included as experimental for `Content\Subnautica2\Binaries\WinGDK`.
- UE4SS runtime/mod deployment targets now come from the detected install layout instead of assuming Win64.
- Game Pass UE4SS targeting follows the ProtonLabs package notes: base/runtime payloads can be applied from the `Content` root, while standard Lua mods target `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods`.
- Diagnostics and support reports now include install variant, project root, binaries folder, pak folder, and UE4SS target folder.
- UE4SS runtime warnings now explain that users can import/add the UE4SS Runtime package through the manager instead of only installing it manually.
- Main flow is simpler: drag/drop or install from file, use Import & Enable, toggle mods on/off, then Preview & Apply Profile.
- Toggling an imported mod now adds/enables it in the active editable profile automatically. If Vanilla is active, the manager creates or selects `Default Modded`.
- A primary Preview & Apply Profile button is visible on the main screen; it is no longer hidden behind the row menu.
- Fixed SeaSprint-style UE4SS pak deployment: non-`_P` pak bundles now install to `Subnautica2\Content\Paks\LogicMods`.
- Patch pak bundles ending in `_P` still install to `Subnautica2\Content\Paks\~mods`.
- Existing imported non-`_P` pak library entries from older builds are migrated to `LogicMods` automatically.

## Manual Path Selection

Settings can validate and normalize:

- Outer install root
- Inner `Subnautica2` project folder
- `Subnautica2\Binaries\Win64`
- `Content`
- `Content\Subnautica2`
- `Content\Subnautica2\Binaries\WinGDK`

## Storefront Notes

- Steam: tested and auto-detected.
- Epic/manual Win64: supported through manual path selection when the shipping exe and pak folder exist.
- Game Pass WinGDK: experimental. The manager can detect WinGDK and map UE4SS mods to `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods`, but some mods may still crash because of mod/runtime compatibility.

## Safety Notes

- Preview & Apply Profile is still required before install.
- Managed recovery still only touches files recorded in `install_manifest.json`.
- Loose root overlays and unsafe unmanaged writes remain blocked.
- Unknown files are reported, not deleted.
