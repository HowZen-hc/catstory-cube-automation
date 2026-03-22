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

# PaddleX pipeline/module config YAMLs (required at runtime by PaddleOCR)
_paddlex_pkg = Path(sys.prefix, "lib", "python" + ".".join(map(str, sys.version_info[:2])),
                    "site-packages", "paddlex")
# Windows: Lib/site-packages/paddlex
if not _paddlex_pkg.exists():
    _paddlex_pkg = Path(sys.prefix, "Lib", "site-packages", "paddlex")

_paddlex_datas = []
if _paddlex_pkg.exists():
    _configs = _paddlex_pkg / "configs"
    if _configs.exists():
        _paddlex_datas.append((str(_configs), "paddlex/configs"))

# PaddlePaddle native libs (mklml.dll, libiomp5md.dll, dnnl.dll, etc.)
# loaded at runtime via LoadLibrary — PyInstaller cannot detect them.
_paddle_pkg = Path(sys.prefix, "lib", "python" + ".".join(map(str, sys.version_info[:2])),
                   "site-packages", "paddle")
if not _paddle_pkg.exists():
    _paddle_pkg = Path(sys.prefix, "Lib", "site-packages", "paddle")

_paddle_binaries = []
if _paddle_pkg.exists():
    _libs = _paddle_pkg / "libs"
    if _libs.exists():
        for _f in _libs.iterdir():
            if _f.is_file():
                _paddle_binaries.append((str(_f), "."))

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=_paddle_binaries,
    datas=_paddlex_datas,
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
        # "unittest",  # paddle.utils.cpp_extension needs it
        "doctest",
        # "pdb",  # paddle.jit.dy2static needs it
        "profile",
        "pstats",
        # 不需要的大型套件
        "matplotlib",
        "scipy",
        # "pandas",  # PaddleOCR (paddlex) 需要 pandas，不可排除
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
    console=False,
    icon=None,  # 可替換為 .ico 檔案路徑
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=["paddle*.dll", "paddle*.pyd", "cv2*.pyd", "libopenblas*"],
    name="CubeAutomation",
)
