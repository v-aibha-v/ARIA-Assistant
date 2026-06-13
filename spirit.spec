# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all hidden imports for sarvamai, sounddevice, soundfile, pywinauto
hidden_imports = [
    'pyaudio',
    'keyboard',
    'win32api',
    'win32con',
    'win32gui',
    'ctypes',
    'winsound',
    'dotenv',
    'sarvamai',
    'sounddevice',
    'soundfile',
    'pywinauto',
    'speech_recognition',
    'PIL',
]

# Include data files - check if assets exists
import os
assets_data = [('assets', 'assets')] if os.path.exists('assets') else []
# NOTE: .env is NOT bundled — users must provide their own API key
datas = assets_data

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI frameworks not needed
        'tkinter',
        # Heavy ML/data-science packages pulled in by sarvamai but NOT needed
        # (Spirit only uses sarvamai as an HTTP API client)
        'torch', 'torchvision', 'torchaudio',
        'tensorflow', 'keras',
        'transformers', 'tokenizers', 'sentencepiece',
        'scipy', 'pandas',
        'matplotlib', 'plotly', 'seaborn',
        'numpy.distutils',
        'sklearn', 'scikit-learn',
        'jupyter', 'notebook', 'IPython',
        'tensorboard', 'tensorboardX',
        'onnx', 'onnxruntime',
        'triton',
        'sympy',
        'pygments',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Spirit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no console window — pure background process
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\spirit.ico',
    version=None,
)
