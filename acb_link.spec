# -*- mode: python ; coding: utf-8 -*-
"""
ACB Link Desktop - PyInstaller Specification
Builds Windows executable and installer package.
"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

block_cipher = None

# Application metadata
APP_NAME = "ACB Link Desktop"
APP_VERSION = "1.0.0"
APP_PUBLISHER = "American Council of the Blind"
APP_DESCRIPTION = "Your gateway to ACB media content"

a = Analysis(
    ['acb_link/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include data files
        ('data', 'data'),
        # Include documentation
        ('docs', 'docs'),
        # Include LICENSE
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        # wxPython
        'wx',
        'wx.html2',
        'wx.adv',
        'wx.media',
        # FastAPI/Uvicorn
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # Accessibility
        'accessible_output2',
        'accessible_output2.outputs',
        'accessible_output2.outputs.auto',
        'accessible_output2.outputs.nvda',
        'accessible_output2.outputs.jaws',
        'accessible_output2.outputs.sapi5',
        # Voice control
        'speech_recognition',
        'pyttsx3',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        # Other
        'feedparser',
        'requests',
        'dateutil',
        'icalendar',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
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
    exclude_binaries=True,
    name='ACBLink',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='data/s3/acb512.png',  # App icon
    version='installer/version_info.txt',
    uac_admin=False,
    uac_uiaccess=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ACBLink',
)
