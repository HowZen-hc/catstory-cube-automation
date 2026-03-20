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


class AutomationWorker(QThread):
    """自動化主迴圈，在工作執行緒中執行。"""

    roll_completed = pyqtSignal(RollResult)
    status_changed = pyqtSignal(str)

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self._running = False

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        self.status_changed.emit("初始化模組...")

        screen = ScreenCapture()
        ocr = OCREngine()
        mouse = MouseController(delay_ms=self.config.delay_ms)
        matcher = TemplateMatcher()
        checker = ConditionChecker(self.config.conditions)

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

            result = strategy.execute_roll(roll_number)
            self.roll_completed.emit(result)

            if result.matched:
                self.status_changed.emit(f"達成目標！共洗 {roll_number} 次")
                break

        self._running = False
