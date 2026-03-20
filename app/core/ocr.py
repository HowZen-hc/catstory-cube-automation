import numpy as np
from paddleocr import PaddleOCR


class OCREngine:
    """PaddleOCR 封裝，繁體中文辨識。"""

    def __init__(self) -> None:
        self._ocr = PaddleOCR(lang="chinese_cht", show_log=False)

    def recognize(self, image: np.ndarray) -> list[str]:
        """對圖片進行 OCR，回傳辨識出的文字列表。"""
        result = self._ocr.ocr(image, cls=False)
        lines: list[str] = []
        if not result or not result[0]:
            return lines
        for line_info in result[0]:
            text = line_info[1][0]
            lines.append(text)
        return lines

    def recognize_with_confidence(
        self, image: np.ndarray
    ) -> list[tuple[str, float]]:
        """回傳 (文字, 信心值) 的列表。"""
        result = self._ocr.ocr(image, cls=False)
        lines: list[tuple[str, float]] = []
        if not result or not result[0]:
            return lines
        for line_info in result[0]:
            text = line_info[1][0]
            confidence = line_info[1][1]
            lines.append((text, confidence))
        return lines
