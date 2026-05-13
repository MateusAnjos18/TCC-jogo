# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['popper3\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('popper3\\assets\\popper3_logo.png', 'popper3\\assets'),
        ('popper3\\assets\\popper3.ico', 'popper3\\assets'),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='Popper 3',
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
    icon=['popper3\\assets\\popper3.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Popper 3',
)
