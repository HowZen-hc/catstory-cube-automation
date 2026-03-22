"""應用程式路徑：根據 frozen (PyInstaller) 或開發模式決定基礎目錄。"""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # PyInstaller 打包後，exe 所在目錄
    APP_DIR = Path(sys.executable).parent
else:
    # 開發模式，專案根目錄
    APP_DIR = Path(__file__).resolve().parent.parent

LOG_DIR = APP_DIR / "logs"
MODEL_DIR = APP_DIR / "models"
CONFIG_PATH = APP_DIR / "config.json"
