# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Internet Speed Test Application
# This file includes a runtime hook to fix speedtest-cli compatibility issues

block_cipher = None

a = Analysis(
    ['internet_speedtest_backup.py'],  # Your original script - NO CHANGES NEEDED!
    pathex=[],
    binaries=[],
    datas=[
        ('logo.png', '.'),  # Include logo.png in root of bundle
    ],
    hiddenimports=[
        'speedtest',
        'builtins',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.sip',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'http.client',
        'queue',
        'xml.etree.ElementTree',
        'json',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_speedtest.py'],  # Runtime hook to fix speedtest issues
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='InternetSpeedTest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'  # Optional: remove if you don't have logo.ico
)