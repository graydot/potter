# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/potter.py'],
    pathex=[],
    binaries=[],
    datas=[('src/cocoa_settings.py', '.')],
    hiddenimports=['six.moves', 'six.moves.urllib', 'six', 'objc', 'Foundation', 'AppKit', 'UserNotifications', 'ApplicationServices', 'Quartz'],
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
    name='Potter',
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
    icon=['app_icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Potter',
)
app = BUNDLE(
    coll,
    name='Potter.app',
    icon='app_icon.icns',
    bundle_identifier='com.rephrasely.app',
)
