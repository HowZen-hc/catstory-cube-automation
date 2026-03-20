import logging
import os
import sys
import warnings

# 抑制第三方套件噪音
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="urllib3.*doesn't match a supported version")

from PyQt6.QtWidgets import QApplication

from app.gui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# 將 PaddlePaddle/PaddleX 的 log 層級提高到 WARNING，只保留自己的 INFO log
for _name in ("paddle", "paddlex", "paddleocr"):
    logging.getLogger(_name).setLevel(logging.WARNING)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
