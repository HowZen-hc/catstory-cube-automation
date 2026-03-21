from abc import ABC, abstractmethod

import cv2
import numpy as np

# 預處理放大倍率
_SCALE_FACTOR = 1.5
# 放大後四周補白邊（像素），防止邊緣文字被 OCR 截斷
_PADDING_PX = 20


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """放大 + 灰階 + 二值化 + padding，提升 OCR 辨識率。"""
    # 放大
    h, w = image.shape[:2]
    scaled = cv2.resize(image, (int(w * _SCALE_FACTOR), int(h * _SCALE_FACTOR)), interpolation=cv2.INTER_CUBIC)
    # 灰階
    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
    # OTSU 二值化
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 遊戲為深色底 + 淺色字，若背景偏暗（均值 < 128）則反轉為白底黑字
    if np.mean(binary) < 128:
        binary = cv2.bitwise_not(binary)
    # 反轉為黑字白底後，對黑字做膨脹（加粗筆畫），防止細筆畫斷裂（如 8→6）
    binary = cv2.bitwise_not(binary)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.dilate(binary, kernel, iterations=1)
    binary = cv2.bitwise_not(binary)
    # 四周補白邊，避免邊緣字母被截斷
    binary = cv2.copyMakeBorder(
        binary, _PADDING_PX, _PADDING_PX, _PADDING_PX, _PADDING_PX,
        cv2.BORDER_CONSTANT, value=255,
    )
    # 轉回 BGR（PaddleOCR 預期 3 通道）
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


class OCREngine(ABC):
    """OCR 引擎抽象基類。"""

    @abstractmethod
    def recognize(self, image: np.ndarray) -> list[tuple[str, float]]:
        """對圖片進行 OCR，回傳 (文字, y 中心點) 列表。"""
        ...


class PaddleOCREngine(OCREngine):
    """PaddleOCR 3.x 封裝，繁體中文辨識。"""

    def __init__(self, use_gpu: bool = False) -> None:
        import os
        os.environ["FLAGS_use_mkldnn"] = "0"

        from paddleocr import PaddleOCR

        device = "gpu:0" if use_gpu else "cpu"
        self._ocr = PaddleOCR(lang="chinese_cht", device=device, enable_mkldnn=False)

    def recognize(self, image: np.ndarray) -> list[tuple[str, float]]:
        processed = preprocess_for_ocr(image)
        result = self._ocr.predict(processed)
        if not result:
            return []
        texts = result[0].get("rec_texts", [])
        polys = result[0].get("dt_polys", [])
        out: list[tuple[str, float]] = []
        for text, poly in zip(texts, polys):
            # y 座標扣除 padding 後除以放大倍率，還原為原始座標
            y_center = (sum(pt[1] for pt in poly) / len(poly) - _PADDING_PX) / _SCALE_FACTOR
            out.append((text, y_center))
        return out


def create_ocr_engine(use_gpu: bool = False) -> OCREngine:
    """建立 OCR 引擎（PaddleOCR）。"""
    return PaddleOCREngine(use_gpu=use_gpu)
