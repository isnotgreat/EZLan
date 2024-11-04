# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ezlan\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('ezlan/resources', 'resources')],
    hiddenimports=['scipy.special._cdflib', 'h2', 'zstandard', 'brotli'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EZLan',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ezlan\\resources\\icon.ico'],
)
