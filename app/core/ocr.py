from abc import ABC, abstractmethod

import numpy as np


class OCREngine(ABC):
    """OCR 引擎抽象基類。"""

    @abstractmethod
    def recognize(self, image: np.ndarray) -> list[tuple[str, float]]:
        """對圖片進行 OCR，回傳 (文字, y 中心點) 列表。"""
        ...


class PaddleOCREngine(OCREngine):
    """PaddleOCR 3.x 封裝，繁體中文辨識。"""

    def __init__(self) -> None:
        from paddleocr import PaddleOCR

        self._ocr = PaddleOCR(lang="chinese_cht", enable_mkldnn=False)

    def recognize(self, image: np.ndarray) -> list[tuple[str, float]]:
        result = self._ocr.predict(image)
        if not result:
            return []
        texts = result[0].get("rec_texts", [])
        polys = result[0].get("dt_polys", [])
        out: list[tuple[str, float]] = []
        for text, poly in zip(texts, polys):
            y_center = sum(pt[1] for pt in poly) / len(poly)
            out.append((text, y_center))
        return out


def create_ocr_engine() -> OCREngine:
    """建立 OCR 引擎（PaddleOCR）。"""
    return PaddleOCREngine()
