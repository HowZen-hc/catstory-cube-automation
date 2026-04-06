import logging
import re
from datetime import datetime
from pathlib import Path

import numpy as np

from app.models.potential import PotentialLine, format_line
from app.paths import LOG_DIR

logger = logging.getLogger(__name__)

DEBUG_IMG_DIR = LOG_DIR / "debug"


def _imwrite(path: Path, image: np.ndarray) -> None:
    """cv2.imwrite 不支援 Windows Unicode 路徑，改用 imencode + write_bytes。"""
    import cv2

    ok, buf = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError(f"cv2.imencode failed: {path}")
    path.write_bytes(buf.tobytes())


def _sanitize_filename(name: str) -> str:
    """移除檔名中不合法的字元。"""
    return re.sub(r'[\\/*?:"<>|() ]', "", name)


class OCRLogSession:
    """一次執行 session 的 log 管理器。

    每次「開始」或「OCR 測試」都會建立新的 session，
    產生獨立的 log 檔案，例如：
      logs/automation_珍貴附加方塊_20260322_151200.log
      logs/ocr_test_萌獸方塊_20260322_152000.log
    """

    def __init__(self, mode: str, cube_type: str) -> None:
        """
        Parameters
        ----------
        mode : str
            "automation" 或 "ocr_test"
        cube_type : str
            方塊類型名稱，例如 "珍貴附加方塊 (粉紅色)"
        """
        LOG_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_cube = _sanitize_filename(cube_type)
        self._log_file = LOG_DIR / f"{mode}_{safe_cube}_{timestamp}.log"

    @property
    def log_file(self) -> Path:
        return self._log_file

    def save_debug_image(
        self,
        roll_number: int,
        raw_image: np.ndarray,
        processed_image: np.ndarray | None = None,
    ) -> None:
        """儲存 OCR 截圖供除錯用（僅保留最近 10 組）。

        每組包含原始截圖 + 預處理後的圖（供 OCR 的輸入）。
        """
        _MAX_KEEP = 10
        try:
            DEBUG_IMG_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            prefix = f"ocr_{timestamp}_{roll_number:05d}"
            _imwrite(DEBUG_IMG_DIR / f"{prefix}_raw.png", raw_image)
            if processed_image is not None:
                _imwrite(DEBUG_IMG_DIR / f"{prefix}_proc.png", processed_image)

            # 只保留最近 N 組（按 raw 檔計數）
            raws = sorted(DEBUG_IMG_DIR.glob("ocr_*_raw.png"))
            for old_raw in raws[:-_MAX_KEEP]:
                old_raw.unlink(missing_ok=True)
                old_proc = old_raw.with_name(
                    old_raw.name.replace("_raw.png", "_proc.png")
                )
                old_proc.unlink(missing_ok=True)
            # 清理舊格式（無 _raw/_proc 後綴）的遺留檔案
            for legacy in DEBUG_IMG_DIR.glob("ocr_*.png"):
                if "_raw.png" not in legacy.name and "_proc.png" not in legacy.name:
                    legacy.unlink(missing_ok=True)
        except Exception:
            logger.warning("無法儲存 debug 截圖", exc_info=True)

    def log_ocr_result(
        self,
        roll_number: int,
        raw_texts: list[tuple[str, float]],
        parsed_lines: list[PotentialLine],
    ) -> None:
        """將 OCR 原始結果與解析結果寫入 session log 檔案。"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_only = [t for t, _ in raw_texts]

        # console 輸出
        prefix = "[初始潛能]" if roll_number == 0 else f"#{roll_number:05d}"
        parts = [f"{prefix} RAW={text_only}"]
        for i, parsed in enumerate(parsed_lines, 1):
            parts.append(f"  L{i}: {format_line(parsed)}")
        print()
        logger.info("\n".join(parts))

        # 寫入檔案
        try:
            with self._log_file.open("a", encoding="utf-8") as f:
                label = "[初始潛能]" if roll_number == 0 else f"#{roll_number:05d}"
                f.write(f"[{timestamp}] {label}\n")
                f.write(f"  RAW: {text_only}\n")
                for i, parsed in enumerate(parsed_lines, 1):
                    f.write(f"  L{i}: {format_line(parsed)}")
                    if parsed.raw_text:
                        f.write(f"  (raw: {parsed.raw_text!r})")
                    f.write("\n")
        except OSError:
            logger.warning("無法寫入 OCR log: %s", self._log_file)
