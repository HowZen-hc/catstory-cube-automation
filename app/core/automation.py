import logging
import threading

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.condition import ConditionChecker
from app.core.mouse import MouseController, focus_game_window
from app.core.ocr import create_ocr_engine
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
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def _running(self) -> bool:
        return not self._stop_event.is_set()

    def run(self) -> None:
        self._stop_event.clear()

        try:
            self.status_changed.emit("初始化 OCR 引擎（首次啟動需下載模型，請稍候）...")
            screen = ScreenCapture()
            ocr = create_ocr_engine(self.config.ocr_engine)
            mouse = MouseController(delay_ms=self.config.delay_ms)
            mouse.bind_stop_flag(self._stop_event)
            checker = ConditionChecker(self.config)
        except Exception as e:
            logger.exception("模組初始化失敗")
            self.error_occurred.emit(f"初始化失敗: {e}")
            return

        # 根據方塊類型選擇策略
        if self.config.cube_type == "恢復附加方塊(紅色)":
            strategy = CompareFlowStrategy(
                self.config, screen, ocr, mouse, checker
            )
        else:
            strategy = SimpleFlowStrategy(
                self.config, screen, ocr, mouse, checker
            )

        # 將遊戲視窗拉到前景
        if not focus_game_window():
            self.error_occurred.emit("找不到遊戲視窗，請確認遊戲已啟動")
            return

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

            if not self._running:
                break

            self.roll_completed.emit(result)

            if result.matched:
                self.status_changed.emit(f"達成目標！共洗 {roll_number} 次")
                break
