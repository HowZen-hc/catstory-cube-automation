import logging
import os
import sys
import warnings

# 先設定 logging，確保在任何 import 之前生效
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 抑制第三方套件噪音
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["PADDLEX_LOG_LEVEL"] = "ERROR"
os.environ["FLAGS_minloglevel"] = "2"  # 抑制 Paddle C++ INFO/WARNING
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")
warnings.filterwarnings("ignore", message="No ccache found")

from PyQt6.QtWidgets import QApplication

from app.gui.main_window import MainWindow

# import 後再抑制第三方 logger，避免被套件自身的設定覆蓋
for _name in ("paddle", "paddlex", "paddleocr", "ppocr"):
    logging.getLogger(_name).setLevel(logging.ERROR)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
