import logging

from app.core.condition import parse_potential_line
from app.cube.base import CubeStrategy
from app.models.potential import RollResult

logger = logging.getLogger(__name__)


class SimpleFlowStrategy(CubeStrategy):
    """Flow A：珍貴/絕對/萌獸方塊，直接洗。

    流程：使用方塊 → 等待結果 → OCR 讀取潛能 → 判斷條件
    """

    def execute_roll(self, roll_number: int) -> RollResult:
        # 1. 點擊按鈕區域中心
        if self.config.button_region.is_set():
            cx = self.config.button_region.x + self.config.button_region.width // 2
            cy = self.config.button_region.y + self.config.button_region.height // 2
            logger.info("點擊座標: (%d, %d)", cx, cy)
            self.mouse.click(cx, cy)

        # 2. 等待結果
        self.mouse.wait()

        # 3. OCR 讀取潛能
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
