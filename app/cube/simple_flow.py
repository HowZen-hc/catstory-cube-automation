import logging

from app.core.condition import parse_potential_line
from app.cube.base import CubeStrategy
from app.models.potential import RollResult

logger = logging.getLogger(__name__)


class SimpleFlowStrategy(CubeStrategy):
    """Flow A：珍貴附加方塊/絕對附加方塊/萌獸方塊，直接洗。

    流程：使用方塊 → 等待結果 → OCR 讀取潛能 → 判斷條件
    """

    def execute_roll(self, roll_number: int) -> RollResult:
        # 1. 按空白鍵觸發「重新設定」按鈕
        self.mouse.press_confirm(times=1)
        self.mouse.wait(ms=150)

        # 2. 按兩次空白鍵確認（遊戲防呆雙重確認）
        self.mouse.press_confirm(times=2)

        # 3. 等待結果
        self.mouse.wait(ms=300)

        # 4. OCR 讀取潛能
        lines = []
        if self.config.potential_region.is_set():
            pot_img = self.screen.capture(self.config.potential_region)
            texts = self.ocr.recognize(pot_img)
            logger.info("OCR 原始結果: %s", texts)
            lines = [parse_potential_line(t) for t in texts]

        # 4. 判斷條件
        matched = self.checker.check(lines)

        return RollResult(
            roll_number=roll_number,
            lines=lines,
            matched=matched,
        )
