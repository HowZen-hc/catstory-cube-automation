# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for CatStory Cube Automation.

Build command:
    uv run pyinstaller cube_automation.spec

Output:
    dist/CubeAutomation/CubeAutomation.exe
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "paddleocr",
        "paddle",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 測試 & 開發工具
        "pytest",
        "_pytest",
        "pluggy",
        # 不需要的標準庫
        "tkinter",
        "unittest",
        "doctest",
        "pdb",
        "profile",
        "pstats",
        # 不需要的大型套件
        "matplotlib",
        "scipy",
        "pandas",
        "IPython",
        "notebook",
        "jupyter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 排除測試檔案、文件、開發用檔案
EXCLUDE_PATTERNS = {
    "tests",
    "test_",
    "README",
    ".md",
    ".pytest_cache",
    "__pycache__",
}


def should_exclude(name: str) -> bool:
    return any(pat in name for pat in EXCLUDE_PATTERNS)


a.datas = [d for d in a.datas if not should_exclude(d[0])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CubeAutomation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 除錯用，確認正常後改回 False
    icon=None,  # 可替換為 .ico 檔案路徑
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CubeAutomation",
)
