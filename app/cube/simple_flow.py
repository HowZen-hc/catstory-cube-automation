import logging
import time

from app.core.condition import get_num_lines, parse_potential_lines
from app.core.ocr import get_scale_factor
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

        # 2. 按空白鍵確認（萌獸方塊只需 1 次，其餘需 2 次）
        confirm_times = 1 if self.config.cube_type == "萌獸方塊" else 2
        self.mouse.press_confirm(times=confirm_times)

        # 3. 等待結果（萌獸方塊動畫較長，至少等 3 秒）
        _PET_MIN_DELAY_MS = 2200
        if self.config.cube_type == "萌獸方塊":
            self.mouse.wait(ms=max(self.config.delay_ms, _PET_MIN_DELAY_MS))
        else:
            self.mouse.wait()

        # 4. OCR 讀取潛能
        lines = []
        if self.config.potential_region.is_set():
            t0 = time.perf_counter()
            pot_img = self.screen.capture(self.config.potential_region)
            t_cap = time.perf_counter()
            scale = get_scale_factor(self.config.cube_type)
            texts = self.ocr.recognize(pot_img, scale_factor=scale)
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
                self.log_session.save_debug_image(roll_number, pot_img)

        # 5. 判斷條件
        matched = self.checker.check(lines)
        logger.info("#%05d 判斷結果: %s", roll_number, "✅ 符合" if matched else "❌ 不符合")

        return RollResult(
            roll_number=roll_number,
            lines=lines,
            matched=matched,
        )
