# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Collect all data files
datas = [
    ("config\\*.yaml", "config"),
    (".env.example", "."),
    ("sample_data\\.gitkeep", "sample_data"),
]

# Collect hidden imports for dynamic imports
hiddenimports = [
    "openai",
    "google.generativeai",
    "whisper",
    "moviepy",
    "cv2",
    "numpy",
    "scipy",
    "pydub",
    "PIL",
    "yaml",
    "dotenv",
    "requests",
    "tqdm",
    "schedule",
    "pandas",
    "rich",
    "loguru",
    "click",
    "google.auth",
    "google.auth.oauthlib",
    "google.auth.transport.requests",
    "googleapiclient",
    "ffmpeg",
]

# Collect binaries (FFmpeg if present)
binaries = []
ffmpeg_paths = [
    r"C:\Users\Yash\AppData\Local\Temp\opencode\ai-game-shorts\ffmpeg_bin\ffmpeg.exe",
    r"C:\Users\Yash\AppData\Local\Temp\opencode\ai-game-shorts\ffmpeg_bin\ffprobe.exe",
]
for fp in ffmpeg_paths:
    p = Path(fp)
    if p.exists():
        binaries.append((str(p), "ffmpeg_bin"))

a = Analysis(
    ["scripts\\run_pipeline.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    module_collection_mode={
        "whisper": "pyz",
        "openai": "pyz",
        "google": "pyz",
        "cv2": "pyz",
        "numpy": "pyz",
    },
)

# Collect all subpackages
for pkg in ["core", "ai", "media", "youtube", "pipeline", "utils"]:
    a.datas += Tree(pkg, prefix=pkg)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AI_Game_Shorts",
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
    icon=None,
)
