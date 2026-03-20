import logging
from datetime import datetime
from pathlib import Path

from app.models.potential import PotentialLine

LOG_DIR = Path("logs")
OCR_LOG_FILE = LOG_DIR / "ocr_results.log"

logger = logging.getLogger(__name__)


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(exist_ok=True)


def _format_parsed(parsed: PotentialLine) -> str:
    """格式化解析結果。"""
    if parsed.attribute == "未知":
        return "(未辨識)"
    if parsed.value == 0:
        return parsed.attribute
    attr_name = parsed.attribute.removesuffix("%")
    return f"{attr_name} +{parsed.value}%"


def log_ocr_result(
    roll_number: int,
    raw_texts: list[str],
    parsed_lines: list[PotentialLine],
) -> None:
    """將 OCR 原始結果與解析結果寫入檔案，供後續建立字典使用。"""
    _ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with OCR_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] #{roll_number:05d}\n")
            # 原始 OCR 碎片
            f.write(f"  RAW: {raw_texts}\n")
            # 合併解析後的結果
            for i, parsed in enumerate(parsed_lines, 1):
                f.write(f"  L{i}: {_format_parsed(parsed)}")
                if parsed.raw_text:
                    f.write(f"  (raw: {parsed.raw_text!r})")
                f.write("\n")
    except OSError:
        logger.warning("無法寫入 OCR log: %s", OCR_LOG_FILE)
