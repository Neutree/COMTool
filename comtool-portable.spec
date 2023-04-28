# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['COMTool/Main.py'],
    pathex=['COMTool'],
    binaries=[],
    datas=[('COMTool/assets', 'assets'), ('COMTool/locales', 'locales'), ('COMTool/protocols', 'protocols'), ('README.MD', './'), ('README_ZH.MD', './')],
    hiddenimports=['babel.numbers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='comtool',
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
    icon=['COMTool/assets/logo.ico'],
)
