from app.core.condition import parse_potential_line
from app.core.mouse import focus_game_window
from app.cube.base import CubeStrategy
from app.models.potential import PotentialLine, RollResult


class CompareFlowStrategy(CubeStrategy):
    """Flow B：恢復附加方塊(紅色)，需前後比較決定保留。

    流程：OCR 讀取當前潛能 → 使用方塊 → 等待結果
          → OCR 讀取新潛能 → 比較 → 點「使用」或「取消」
    """

    def execute_roll(self, roll_number: int) -> RollResult:
        # 0. 確保遊戲視窗在前景
        focus_game_window()
        self.mouse.wait(ms=200)

        # 1. OCR 讀取當前（使用前）潛能
        before_lines = self._read_potential()

        # 2. 按空白鍵觸發使用方塊
        self.mouse.press_confirm(times=1)
        self.mouse.wait(ms=300)

        # 3. 按三次空白鍵確認（恢復附加方塊需要三次確認）
        self.mouse.press_confirm(times=3)

        # 4. 等待結果
        self.mouse.wait()

        # 5. OCR 讀取新潛能
        after_lines = self._read_potential()

        # 6. 判斷是否符合目標
        matched = self.checker.check(after_lines)

        # 7. 比較新舊，決定保留或取消
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
