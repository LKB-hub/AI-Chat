# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['c:\\Users\\Administrator\\Desktop\\python\\ai\\main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['core', 'core.helpers', 'core.api_manager', 'core.session_manager', 'core.system_prompts', 'core.settings', 'core.shortcutter', 'core.export_manager', 'core.markdown'],
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
    name='AI-Chat',
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
)
