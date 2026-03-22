import logging
import os
import sys
import warnings

# 抑制第三方套件噪音（環境變數需在 import paddle 前設定）
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_minloglevel"] = "2"  # 抑制 Paddle C++ INFO/WARNING
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")
warnings.filterwarnings("ignore", message="No ccache found")

from PyQt6.QtWidgets import QApplication

from app.gui.main_window import MainWindow

# 為 app namespace 設定獨立的 handler，不依賴 root logger（避免被 PaddleX 覆蓋）
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
_app_logger = logging.getLogger("app")
_app_logger.setLevel(logging.INFO)
_app_logger.addHandler(_handler)
_app_logger.propagate = False  # 不往 root logger 傳，避免重複或被吃掉


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
