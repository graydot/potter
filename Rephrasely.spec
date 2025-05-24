# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('.env', '.'), ('cocoa_settings.py', '.')]
binaries = []
hiddenimports = ['six.moves', 'six.moves.urllib', 'pynput.keyboard', 'pynput.mouse', 'pyobjc-framework-Cocoa', 'pyobjc-framework-Quartz', 'pyobjc-framework-Foundation', 'pyobjc-framework-AppKit', 'pyobjc-framework-ApplicationServices']
tmp_ret = collect_all('pynput')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pyobjc')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['rephrasely.py'],
    pathex=['/System/Library/Frameworks/Tk.framework/Versions/8.5/Resources/Scripts', '/usr/local/lib/python3.13/site-packages'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Rephrasely',
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
    name='Rephrasely',
)
app = BUNDLE(
    coll,
    name='Rephrasely.app',
    icon='app_icon.icns',
    bundle_identifier='com.rephrasely.app',
)
