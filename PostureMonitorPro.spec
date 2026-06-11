# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Posture Monitor Pro (desktop .exe).

Build with:
    pyinstaller PostureMonitorPro.spec --noconfirm

Produces dist/PostureMonitorPro/PostureMonitorPro.exe (one-folder build).
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

PROJECT_ROOT = os.path.abspath(".")

datas = []
binaries = []
hiddenimports = []

# Bundle the built Vue frontend (served by the backend at runtime).
# Matches backend.app._resolve_frontend_dist() -> sys._MEIPASS / "frontend_dist".
datas += [(os.path.join("frontend", "dist"), "frontend_dist")]

# MediaPipe ships pose graphs / .binarypb / .tflite as data files + native libs.
for package in ("mediapipe", "cv2"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# uvicorn loads its protocol/loop implementations dynamically.
hiddenimports += collect_submodules("uvicorn")
hiddenimports += [
    "backend.app",
    "backend.config",
    "backend.models",
    "posture_analyzer",
    "posture_alerts",
    "posture_translator",
    "websockets",
    "anyio",
    "bcrypt",
]

block_cipher = None

a = Analysis(
    ["desktop_app.py"],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
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
    name="PostureMonitorPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PostureMonitorPro",
)
