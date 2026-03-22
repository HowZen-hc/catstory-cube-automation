import logging
import threading
import time

from PyQt6.QtCore import QThread, pyqtSignal

from app.core.condition import ConditionChecker, get_num_lines, parse_potential_lines
from app.core.mouse import MouseController, focus_game_window
from app.core.ocr import create_ocr_engine, get_scale_factor
from app.core.ocr_logger import OCRLogSession
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
    target_reached = pyqtSignal(int)  # 參數為洗了幾次

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
            ocr = create_ocr_engine(use_gpu=self.config.use_gpu)
            mouse = MouseController(delay_ms=self.config.delay_ms)
            mouse.bind_stop_flag(self._stop_event)
            checker = ConditionChecker(self.config)
            log_session = OCRLogSession("automation", self.config.cube_type)
        except Exception as e:
            logger.exception("模組初始化失敗")
            self.error_occurred.emit(f"初始化失敗: {e}")
            return

        # 根據方塊類型選擇策略
        if self.config.cube_type == "恢復附加方塊 (紅色)":
            strategy = CompareFlowStrategy(
                self.config, screen, ocr, mouse, checker, log_session
            )
        else:
            strategy = SimpleFlowStrategy(
                self.config, screen, ocr, mouse, checker, log_session
            )

        # 將遊戲視窗拉到前景
        if not focus_game_window():
            self.error_occurred.emit("找不到遊戲視窗，請確認遊戲已啟動")
            return

        # 啟動前先檢查當前潛能
        if self.config.potential_region.is_set():
            self.status_changed.emit("檢查當前潛能...")
            t0 = time.perf_counter()
            pot_img = screen.capture(self.config.potential_region)
            t_cap = time.perf_counter()
            scale = get_scale_factor(self.config.cube_type)
            texts = ocr.recognize(pot_img, scale_factor=scale)
            t_ocr = time.perf_counter()
            num_lines = get_num_lines(self.config.cube_type)
            lines = parse_potential_lines(texts, num_rows=num_lines)
            log_session.log_ocr_result(0, texts, lines)
            logger.info(
                "[初始潛能] 耗時: 截圖 %.0fms / OCR %.0fms",
                (t_cap - t0) * 1000,
                (t_ocr - t_cap) * 1000,
            )
            matched = checker.check(lines)
            logger.info("[初始潛能] 判斷結果: %s", "✅ 符合" if matched else "❌ 不符合")
            self.roll_completed.emit(
                RollResult(roll_number=0, lines=lines, matched=matched)
            )
            if matched:
                self.status_changed.emit("當前潛能已符合目標條件，無需洗方塊")
                self.target_reached.emit(0)
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
                self.target_reached.emit(roll_number)
                break
