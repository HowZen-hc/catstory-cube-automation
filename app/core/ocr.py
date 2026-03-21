from abc import ABC, abstractmethod

import numpy as np


class OCREngine(ABC):
    """OCR 引擎抽象基類。"""

    @abstractmethod
    def recognize(self, image: np.ndarray) -> list[str]:
        """對圖片進行 OCR，回傳辨識出的文字列表。"""
        ...


class PaddleOCREngine(OCREngine):
    """PaddleOCR 3.x 封裝，繁體中文辨識。"""

    def __init__(self) -> None:
        from paddleocr import PaddleOCR

        self._ocr = PaddleOCR(lang="chinese_cht", enable_mkldnn=False)

    def recognize(self, image: np.ndarray) -> list[str]:
        result = self._ocr.predict(image)
        if not result:
            return []
        return list(result[0].get("rec_texts", []))


def create_ocr_engine() -> OCREngine:
    """建立 OCR 引擎（PaddleOCR）。"""
    return PaddleOCREngine()
