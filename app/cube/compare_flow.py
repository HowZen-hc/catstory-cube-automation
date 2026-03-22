import logging
import time

from app.core.condition import get_num_lines, parse_potential_lines
from app.core.ocr import get_scale_factor
from app.cube.base import CubeStrategy
from app.models.potential import PotentialLine, RollResult

logger = logging.getLogger(__name__)


class CompareFlowStrategy(CubeStrategy):
    """Flow B：恢復附加方塊(紅色)，需前後比較決定保留。

    流程：OCR 讀取當前潛能 → 使用方塊 → 等待結果
          → OCR 讀取新潛能 → 比較 → 點「使用」或「取消」
    """

    def execute_roll(self, roll_number: int) -> RollResult:
        # 1. OCR 讀取當前（使用前）潛能
        before_lines = self._read_potential(roll_number)

        # 2. 按空白鍵觸發使用方塊
        self.mouse.press_confirm(times=1)
        self.mouse.wait(ms=150)

        # 3. 按三次空白鍵確認（恢復附加方塊需要三次確認）
        self.mouse.press_confirm(times=3)

        # 4. 等待結果（使用使用者設定的間隔時間）
        self.mouse.wait()

        # 5. OCR 讀取新潛能
        after_lines = self._read_potential(roll_number)

        # 6. 判斷是否符合目標
        matched = self.checker.check(after_lines)
        logger.info("#%05d 判斷結果: %s", roll_number, "✅ 符合" if matched else "❌ 不符合")

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

    def _read_potential(self, roll_number: int) -> list[PotentialLine]:
        if not self.config.potential_region.is_set():
            return []
        t0 = time.perf_counter()
        img = self.screen.capture(self.config.potential_region)
        t_cap = time.perf_counter()
        scale = get_scale_factor(self.config.cube_type)
        texts = self.ocr.recognize(img, scale_factor=scale)
        t_ocr = time.perf_counter()
        num_lines = get_num_lines(self.config.cube_type)
        lines = parse_potential_lines(texts, num_rows=num_lines)
        self.log_session.log_ocr_result(roll_number, texts, lines)
        logger.info(
            "#%05d 耗時: 截圖 %.0fms / OCR %.0fms",
            roll_number,
            (t_cap - t0) * 1000,
            (t_ocr - t_cap) * 1000,
        )
        if not texts:
            self.log_session.save_debug_image(roll_number, img)
        return lines

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
