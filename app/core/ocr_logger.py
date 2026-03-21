import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from app.models.potential import PotentialLine, format_line

LOG_DIR = Path("logs")
OCR_LOG_FILE = LOG_DIR / "ocr_results.log"
DEBUG_IMG_DIR = LOG_DIR / "debug"

logger = logging.getLogger(__name__)


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(exist_ok=True)


def save_debug_image(roll_number: int, image: np.ndarray) -> None:
    """儲存 OCR 截圖供除錯用（僅保留最近 5 張）。"""
    try:
        import cv2

        DEBUG_IMG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = DEBUG_IMG_DIR / f"ocr_{timestamp}_{roll_number:05d}.png"
        cv2.imwrite(str(path), image)

        # 只保留最近 5 張
        imgs = sorted(DEBUG_IMG_DIR.glob("ocr_*.png"))
        for old in imgs[:-5]:
            old.unlink(missing_ok=True)
    except Exception:
        logger.debug("無法儲存 debug 截圖", exc_info=True)


def log_ocr_result(
    roll_number: int,
    raw_texts: list[tuple[str, float]],
    parsed_lines: list[PotentialLine],
) -> None:
    """將 OCR 原始結果與解析結果寫入檔案，供後續建立字典使用。"""
    _ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 抽取文字部分用於顯示
    text_only = [t for t, _ in raw_texts]

    # 同步印到 console：RAW 碎片 + 合併解析結果
    prefix = "[初始潛能]" if roll_number == 0 else f"#{roll_number:05d}"
    parts = [f"{prefix} RAW={text_only}"]
    for i, parsed in enumerate(parsed_lines, 1):
        parts.append(f"  L{i}: {format_line(parsed)}")
    logger.info("\n".join(parts))

    try:
        with OCR_LOG_FILE.open("a", encoding="utf-8") as f:
            label = "[初始潛能]" if roll_number == 0 else f"#{roll_number:05d}"
            f.write(f"[{timestamp}] {label}\n")
            # 原始 OCR 碎片
            f.write(f"  RAW: {text_only}\n")
            # 合併解析後的結果
            for i, parsed in enumerate(parsed_lines, 1):
                f.write(f"  L{i}: {format_line(parsed)}")
                if parsed.raw_text:
                    f.write(f"  (raw: {parsed.raw_text!r})")
                f.write("\n")
    except OSError:
        logger.warning("無法寫入 OCR log: %s", OCR_LOG_FILE)
