# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

project_dir = Path(SPECPATH)
ffmpeg_dir = Path(os.environ.get("FFMPEG_DIR", r"E:\ffmpeg"))
node_exe = Path(os.environ["NODE_EXE"])
node_license = node_exe.parent / "LICENSE"
gpl_license = project_dir / "licenses" / "GPL-3.0.txt"

yt_dlp_datas, yt_dlp_binaries, yt_dlp_hiddenimports = collect_all("yt_dlp")
ejs_datas, ejs_binaries, ejs_hiddenimports = collect_all("yt_dlp_ejs")

a = Analysis(
    [str(project_dir / "downloader-mp4-modificado.py")],
    pathex=[str(project_dir)],
    binaries=[
        (str(ffmpeg_dir / "ffmpeg.exe"), "."),
        (str(ffmpeg_dir / "ffprobe.exe"), "."),
        (str(node_exe), "."),
        *yt_dlp_binaries,
        *ejs_binaries,
    ],
    datas=[
        *yt_dlp_datas,
        *ejs_datas,
        (str(project_dir / "THIRD_PARTY_NOTICES.txt"), "."),
        (str(gpl_license), "licenses"),
        (str(node_license), "licenses"),
    ],
    hiddenimports=[*yt_dlp_hiddenimports, *ejs_hiddenimports],
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
    name="downloader-mp4-modificado",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="downloader-mp4-modificado",
)
