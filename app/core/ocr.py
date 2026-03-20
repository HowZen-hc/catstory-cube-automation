import numpy as np
from paddleocr import PaddleOCR


class OCREngine:
    """PaddleOCR 3.x 封裝，繁體中文辨識。"""

    def __init__(self) -> None:
        self._ocr = PaddleOCR(lang="chinese_cht")

    def recognize(self, image: np.ndarray) -> list[str]:
        """對圖片進行 OCR，回傳辨識出的文字列表。"""
        result = self._ocr.predict(image)
        if not result:
            return []
        return list(result[0].get("rec_texts", []))

    def recognize_with_confidence(
        self, image: np.ndarray
    ) -> list[tuple[str, float]]:
        """回傳 (文字, 信心值) 的列表。"""
        result = self._ocr.predict(image)
        if not result:
            return []
        texts = result[0].get("rec_texts", [])
        scores = result[0].get("rec_scores", [])
        return list(zip(texts, scores))
