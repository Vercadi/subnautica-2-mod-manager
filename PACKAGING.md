# Packaging

This project targets a portable Windows one-folder build for Nexus distribution.

## Build

From the repo root:

```powershell
pip install -r requirements.txt
.\scripts\build_portable.ps1 -Clean
```

The script writes `release-metadata.json`, then runs PyInstaller with `Subnautica2ModManager.spec`.

Run the final checklist in `docs\release-checklist.md` before uploading to Nexus.

## Expected Layout

```text
dist/
  Subnautica2ModManager/
    Subnautica2ModManager.exe
    _internal/
    README.md
    LICENSE
    PRIVACY.md
    release-metadata.json
```

The packaged app writes runtime state to:

```text
%LOCALAPPDATA%\Subnautica2ModManager\
  data/
    settings.json
    logs/
    library/
    install_manifest.json
    profiles.json
  backups/
```

Source mode writes the same runtime folders into the repo root for development.

## First Run

On first launch the app creates data, logs, backups, and manager library directories. If `settings.json` is missing or corrupt, it is regenerated from safe defaults and discovery results.

If `assets/background.png` is missing, the app uses the procedural underwater background. `assets/app.ico` is optional; if absent, the portable build uses the default executable icon.

## Reset / Cleanup

Users can reset manager state by closing the app and deleting:

- `%LOCALAPPDATA%\Subnautica2ModManager\data\settings.json`
- `%LOCALAPPDATA%\Subnautica2ModManager\data\profiles.json`
- `%LOCALAPPDATA%\Subnautica2ModManager\data\library\`
- `%LOCALAPPDATA%\Subnautica2ModManager\data\install_manifest.json`
- `%LOCALAPPDATA%\Subnautica2ModManager\backups\`

Deleting manager state does not delete game saves. Unknown files in the game install are reported by recovery previews, not deleted automatically.

## Safety Limitations

Real apply and destructive recovery actions are disabled for real detected Subnautica 2 installs by default. Test execution is only exposed for fake installs marked with `.s2mm_fake_install`.

Loose root overlays such as `dxgi.dll` plus root `.ini` files are review-required and blocked from automatic apply until explicit target policies exist. The public Nexus page and `README.md` carry the user-facing support and safety wording.

## Windows Security Note

The executable is an unsigned PyInstaller bundle. Some antivirus products may report heuristic warnings on unsigned Python apps. The app does not require administrator rights. Publish hashes with release files when practical, and ask users to report the exact detection name if they see a warning.
