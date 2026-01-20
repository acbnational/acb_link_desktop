# -*- mode: python ; coding: utf-8 -*-
"""
ACB Link Desktop - PyInstaller Specification
Builds Windows executable and installer package.

Note: Heavy ML dependencies (torch, transformers, onnxruntime) are excluded
to keep the installer under 200MB. Wake word detection uses these libraries
but the app gracefully falls back to keyboard-activated voice control.
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

# Heavy packages to exclude - these add 500MB+ and are optional
EXCLUDED_PACKAGES = [
    # GUI toolkits we don't use (wxPython is used)
    'tkinter', '_tkinter', 'Tkinter',
    'PySide6', 'PySide2',
    'PyQt5', 'PyQt6', 'PyQt4',
    'sip', 'sipbuild',

    # Heavy ML/AI libraries (openwakeword dependencies)
    # App handles ImportError gracefully - falls back to keyboard voice control
    'torch', 'torchaudio', 'torchvision',
    'transformers', 'huggingface_hub', 'safetensors',
    'onnxruntime', 'onnxruntime_gpu', 'onnx',
    'openwakeword',
    'tensorflow', 'keras',

    # Scientific computing (not needed - numpy only used by excluded openwakeword)
    'numpy', 'numpy.core', 'numpy.linalg', 'numpy.fft', 'numpy.random',
    'scipy', 'sympy',
    'sklearn', 'scikit-learn',
    'pandas',
    'matplotlib', 'mpl_toolkits',
    'PIL', 'Pillow',
    'cv2', 'opencv',

    # NLP libraries (pulled by transformers)
    'nltk', 'datasets', 'tokenizers',
    'sentencepiece', 'sacremoses',

    # JIT compilers (pulled by torch)
    'numba', 'llvmlite',

    # Data formats we don't use
    'pyarrow', 'parquet',
    'h5py', 'tables',

    # gRPC (pulled by various libs)
    'grpc', 'grpcio',

    # Audio ML libs
    'librosa', 'soundfile', 'audioread',
    'lightning', 'pytorch_lightning',

    # Config frameworks
    'hydra', 'omegaconf',

    # Dev/doc tools (should never be bundled)
    'sphinx', 'docutils', 'alabaster',
    'pytest', 'coverage', '_pytest',
    'black', 'mypy', 'flake8', 'pylint',
    'ipython', 'jupyter', 'notebook',
    # IDE/interactive tools pulled transitively
    'jedi', 'parso', 'astroid', 'IPython',
    'prompt_toolkit', 'tiktoken', 'pygments',

    # Monitoring
    'sentry_sdk', 'prometheus_client',

    # ctranslate2 and av (heavy, not used)
    'ctranslate2',
    'av',

    # pywin32 components not used
    'Pythonwin', 'pythonwin', 'win32ui', 'win32uiole',
    'pywin32_testutil', 'win32traceutil',

    # Jupyter/interactive ecosystem (pulled transitively, never used)
    'zmq', 'pyzmq',
    'ipykernel', 'ipywidgets', 'jupyter_client', 'jupyter_core',
    'traitlets',
    'tornado',
    'rich', 'markdown_it', 'mdurl',  # pretty printing

    # uvicorn dev-only features
    'watchfiles', 'watchgod',

    # aiohttp dependencies (only used in admin_config, can use requests)
    'multidict', 'yarl', 'frozenlist', 'propcache', 'aiosignal',
]

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
        'wx', 'wx.adv', 'wx.media',
        # Note: wx.html2 uses Edge WebView2 which is a system component
        'wx.html2',
        # FastAPI/Uvicorn
        'fastapi', 'uvicorn',
        'uvicorn.logging', 'uvicorn.protocols',
        'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        # Accessibility
        'accessible_output2',
        'accessible_output2.outputs', 'accessible_output2.outputs.auto',
        'accessible_output2.outputs.nvda', 'accessible_output2.outputs.jaws',
        'accessible_output2.outputs.sapi5',
        # Voice control (core - not ML libs)
        'speech_recognition', 'pyttsx3',
        'pyttsx3.drivers', 'pyttsx3.drivers.sapi5',
        # Other
        'feedparser', 'requests', 'dateutil', 'icalendar',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['hooks/rthook_block_heavy_imports.py'],
    excludes=EXCLUDED_PACKAGES,
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
