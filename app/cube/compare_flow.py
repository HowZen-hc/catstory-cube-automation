from app.core.condition import parse_potential_line
from app.cube.base import CubeStrategy
from app.models.potential import PotentialLine, RollResult


class CompareFlowStrategy(CubeStrategy):
    """Flow B：恢復附加方塊(紅色)，需前後比較決定保留。

    流程：OCR 讀取當前潛能 → 使用方塊 → 等待結果
          → OCR 讀取新潛能 → 比較 → 點「使用」或「取消」
    """

    def execute_roll(self, roll_number: int) -> RollResult:
        # 1. OCR 讀取當前（使用前）潛能
        before_lines = self._read_potential()

        # 2. 點擊使用方塊
        if self.config.button_region.is_set():
            cx = self.config.button_region.x + self.config.button_region.width // 2
            cy = self.config.button_region.y + self.config.button_region.height // 2
            self.mouse.click(cx, cy)

        # 3. 等待結果
        self.mouse.wait()

        # 4. OCR 讀取新潛能
        after_lines = self._read_potential()

        # 5. 判斷是否符合目標
        matched = self.checker.check(after_lines)

        # 6. 比較新舊，決定保留或取消
        if self._is_better(after_lines, before_lines):
            # TODO: 點擊「使用」按鈕
            pass
        else:
            # TODO: 點擊「取消」按鈕
            pass

        return RollResult(
            roll_number=roll_number,
            lines=after_lines,
            matched=matched,
        )

    def _read_potential(self) -> list[PotentialLine]:
        if not self.config.potential_region.is_set():
            return []
        img = self.screen.capture(self.config.potential_region)
        texts = self.ocr.recognize(img)
        return [parse_potential_line(t) for t in texts]

    def _is_better(
        self,
        new_lines: list[PotentialLine],
        old_lines: list[PotentialLine],
    ) -> bool:
        """比較新潛能是否優於舊潛能。

        簡易策略：新潛能符合的條件數量 >= 舊潛能。
        """
        new_score = sum(1 for line in new_lines if line.value > 0)
        old_score = sum(1 for line in old_lines if line.value > 0)
        return new_score >= old_score
