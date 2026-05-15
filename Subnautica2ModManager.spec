# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT = Path(SPECPATH)
ASSETS = ROOT / "assets"
ICON = ASSETS / "app.ico"

datas = [
    (str(ASSETS), "assets"),
    (str(ROOT / "docs"), "docs"),
    (str(ROOT / "README.md"), "."),
    (str(ROOT / "PACKAGING.md"), "."),
    (str(ROOT / "PRIVACY.md"), "."),
    (str(ROOT / "CHANGELOG.md"), "."),
    (str(ROOT / "release-metadata.json"), "."),
]
datas += collect_data_files("tkinterdnd2")

hiddenimports = collect_submodules("tkinterdnd2")

a = Analysis(
    ["app.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Subnautica2ModManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON) if ICON.is_file() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Subnautica2ModManager",
)
