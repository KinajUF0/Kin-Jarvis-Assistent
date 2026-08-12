# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Kin/Jarvis AI Assistant."""

import os
from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH).parent

import customtkinter
ctk_dir = os.path.dirname(customtkinter.__file__)

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / 'config'), 'config'),
        (str(project_root / 'assets'), 'assets'),
        (str(project_root / '.env.example'), '.'),
        (ctk_dir, 'customtkinter'),
    ],
    hiddenimports=[
        'google.generativeai',
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'speech_recognition',
        'edge_tts',
        'pygame',
        'rapidfuzz',
        'pyautogui',
        'psutil',
        'yaml',
        'dotenv',
        'comtypes',
        'pycaw',
        'pycaw.pycaw',
        'win32gui',
        'win32con',
        'win32process',
        'win32api',
        'keyboard',
    ],
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
    exclude_binaries=True,
    name='KinJarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'logo.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='KinJarvis',
)
