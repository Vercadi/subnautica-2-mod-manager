# Assets

Phase 1 generates a procedural underwater background in memory.

Future static assets can be placed here, including:

- `background.png`
- `app_icon_source.png` original user-provided icon source
- `app_icon.png` circular masked PNG used as the icon artwork
- `app.ico` for the Windows executable and window icon
- `app_icon_placeholder.svg` as a fallback concept only
- mod thumbnail placeholders
- small UI glyphs

The PyInstaller spec uses `assets/app.ico` if it exists. If not, packaging continues with the default executable icon.
