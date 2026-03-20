import logging

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.condition import ConditionChecker
from app.core.matcher import TemplateMatcher
from app.core.mouse import MouseController
from app.core.ocr import OCREngine
from app.core.screen import ScreenCapture
from app.cube.compare_flow import CompareFlowStrategy
from app.cube.simple_flow import SimpleFlowStrategy
from app.models.config import AppConfig
from app.models.potential import RollResult

logger = logging.getLogger(__name__)


class AutomationWorker(QThread):
    """自動化主迴圈，在工作執行緒中執行。"""

    roll_completed = pyqtSignal(RollResult)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self._running = False

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True

        try:
            self.status_changed.emit("初始化 OCR 引擎（首次啟動需下載模型，請稍候）...")
            screen = ScreenCapture()
            ocr = OCREngine()
            mouse = MouseController(delay_ms=self.config.delay_ms)
            matcher = TemplateMatcher()
            checker = ConditionChecker(self.config)
        except Exception as e:
            logger.exception("模組初始化失敗")
            self.error_occurred.emit(f"初始化失敗: {e}")
            self._running = False
            return

        # 根據方塊類型選擇策略
        if self.config.cube_type == "恢復":
            strategy = CompareFlowStrategy(
                self.config, screen, ocr, mouse, matcher, checker
            )
        else:
            strategy = SimpleFlowStrategy(
                self.config, screen, ocr, mouse, matcher, checker
            )

        self.status_changed.emit("開始自動洗方塊...")
        roll_number = 0

        while self._running:
            roll_number += 1
            self.status_changed.emit(f"第 {roll_number} 次...")

            try:
                result = strategy.execute_roll(roll_number)
            except Exception as e:
                logger.exception("第 %d 次洗方塊失敗", roll_number)
                self.error_occurred.emit(f"第 {roll_number} 次執行錯誤: {e}")
                break

            self.roll_completed.emit(result)

            if result.matched:
                self.status_changed.emit(f"達成目標！共洗 {roll_number} 次")
                break

        self._running = False
