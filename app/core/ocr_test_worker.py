import logging
import threading
import time

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.condition import ConditionChecker, get_num_lines, parse_potential_lines
from app.core.ocr import create_ocr_engine, get_scale_factor
from app.core.ocr_logger import OCRLogSession
from app.core.screen import ScreenCapture
from app.models.config import AppConfig
from app.models.potential import RollResult

logger = logging.getLogger(__name__)

OCR_TEST_INTERVAL = 3.0  # 每次 OCR 間隔秒數


class OCRTestWorker(QThread):
    """純 OCR 測試模式：只截圖 + OCR 解析，不操作鍵盤/滑鼠。"""

    roll_completed = pyqtSignal(RollResult)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        self._stop_event.clear()

        try:
            self.status_changed.emit("初始化 OCR 引擎（首次啟動需下載模型，請稍候）...")
            screen = ScreenCapture()
            ocr = create_ocr_engine(use_gpu=self.config.use_gpu)
            checker = ConditionChecker(self.config)
            log_session = OCRLogSession("ocr_test", self.config.cube_type)
        except Exception as e:
            logger.exception("OCR 測試模式初始化失敗")
            self.error_occurred.emit(f"初始化失敗: {e}")
            return

        self.status_changed.emit("OCR 測試模式執行中...")
        count = 0

        while not self._stop_event.is_set():
            count += 1
            self.status_changed.emit(f"OCR 測試 #{count}...")

            try:
                t0 = time.perf_counter()
                pot_img = screen.capture(self.config.potential_region)
                t_cap = time.perf_counter()
                scale = get_scale_factor(self.config.cube_type)
                texts = ocr.recognize(pot_img, scale_factor=scale)
                t_ocr = time.perf_counter()
                num_lines = get_num_lines(self.config.cube_type)
                lines = parse_potential_lines(texts, num_rows=num_lines)
                log_session.save_debug_image(count, pot_img, ocr.last_processed)
                log_session.log_ocr_result(count, texts, lines)
                logger.info(
                    "OCR 測試 #%05d 耗時: 截圖 %.0fms / OCR %.0fms",
                    count,
                    (t_cap - t0) * 1000,
                    (t_ocr - t_cap) * 1000,
                )
                matched = checker.check(lines)
                self.roll_completed.emit(
                    RollResult(roll_number=count, lines=lines, matched=matched)
                )
            except Exception as e:
                logger.exception("OCR 測試 #%d 失敗", count)
                self.error_occurred.emit(f"OCR 測試 #{count} 錯誤: {e}")
                break

            # 等待間隔，可被 stop 中斷
            self._stop_event.wait(OCR_TEST_INTERVAL)

        self.status_changed.emit(f"OCR 測試結束，共測試 {count} 次")
