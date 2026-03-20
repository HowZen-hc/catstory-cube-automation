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


class WinOCREngine(OCREngine):
    """Windows 內建 OCR 引擎（winocr），使用 zh-Hant 繁體中文。"""

    def __init__(self) -> None:
        import winocr  # noqa: F401 – 確認可用

    def recognize(self, image: np.ndarray) -> list[str]:
        from winocr import recognize_cv2_sync

        result = recognize_cv2_sync(image, "zh-Hant-TW")
        if not result or "text" not in result:
            return []
        # winocr 回傳整段文字，按行拆分
        lines = [
            line.strip()
            for line in result["text"].splitlines()
            if line.strip()
        ]
        return lines


def create_ocr_engine(engine_name: str = "paddle") -> OCREngine:
    """根據名稱建立 OCR 引擎。"""
    if engine_name == "winocr":
        return WinOCREngine()
    return PaddleOCREngine()
