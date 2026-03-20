from app.core.condition import parse_potential_line
from app.cube.base import CubeStrategy
from app.models.potential import RollResult


class SimpleFlowStrategy(CubeStrategy):
    """Flow A：珍貴/絕對/萌獸方塊，直接洗。

    流程：使用方塊 → 等待結果 → OCR 讀取潛能 → 判斷條件
    """

    def execute_roll(self, roll_number: int) -> RollResult:
        # 1. 擷取按鈕區域，找到「使用」按鈕並點擊
        if self.config.button_region.is_set():
            btn_img = self.screen.capture(self.config.button_region)
            # TODO: 用模板匹配找到按鈕座標
            # 目前先用按鈕區域中心點
            cx = self.config.button_region.x + self.config.button_region.width // 2
            cy = self.config.button_region.y + self.config.button_region.height // 2
            self.mouse.click(cx, cy)

        # 2. 等待結果
        self.mouse.wait()

        # 3. OCR 讀取潛能
        lines = []
        if self.config.potential_region.is_set():
            pot_img = self.screen.capture(self.config.potential_region)
            texts = self.ocr.recognize(pot_img)
            lines = [parse_potential_line(t) for t in texts]

        # 4. 判斷條件
        matched = self.checker.check(lines)

        return RollResult(
            roll_number=roll_number,
            lines=lines,
            matched=matched,
        )
