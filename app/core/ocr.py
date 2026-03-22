from abc import ABC, abstractmethod

import cv2
import numpy as np

# 預處理放大倍率
_SCALE_FACTOR = 1.5
_SCALE_FACTOR_SMALL = 2.0
# 放大後四周補白邊（像素），防止邊緣文字被 OCR 截斷
_PADDING_PX = 20


def preprocess_for_ocr(image: np.ndarray, scale_factor: float = _SCALE_FACTOR) -> np.ndarray:
    """放大 + 灰階 + 二值化 + padding，提升 OCR 辨識率。"""
    # 放大
    h, w = image.shape[:2]
    scaled = cv2.resize(image, (int(w * scale_factor), int(h * scale_factor)), interpolation=cv2.INTER_CUBIC)
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
    def recognize(self, image: np.ndarray, scale_factor: float = _SCALE_FACTOR) -> list[tuple[str, float]]:
        """對圖片進行 OCR，回傳 (文字, y 中心點) 列表。"""
        ...


class PaddleOCREngine(OCREngine):
    """PaddleOCR 3.x 封裝，繁體中文辨識。"""

    def __init__(self, use_gpu: bool = False) -> None:
        import os
        import sys

        from app.paths import MODEL_DIR

        os.environ["FLAGS_use_mkldnn"] = "0"
        os.environ["PADDLEOCR_HOME"] = str(MODEL_DIR)

        # Ensure paddle native libs (mklml.dll, etc.) are findable in
        # the PyInstaller bundle directory.
        if getattr(sys, "frozen", False):
            bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(bundle_dir)

        # PyInstaller strips .dist-info metadata, causing paddlex
        # is_dep_available() to return False for bundled packages.
        # Many paddlex modules conditionally import packages (e.g. cv2)
        # at module level using is_dep_available(), so we must patch
        # BEFORE any paddlex module is imported — not after.
        if getattr(sys, "frozen", False):
            import importlib.metadata as _im
            import importlib.util

            if not getattr(_im, "_frozen_patched", False):
                _orig_version = _im.version
                # Dist-name → import-name for packages where they differ
                _DIST_TO_IMPORT = {
                    "opencv-contrib-python": "cv2",
                    "opencv-python": "cv2",
                    "opencv-python-headless": "cv2",
                    "Pillow": "PIL",
                    "scikit-learn": "sklearn",
                    "pyyaml": "yaml",
                    "python-dateutil": "dateutil",
                    "python-bidi": "bidi",
                    "beautifulsoup4": "bs4",
                    "Jinja2": "jinja2",
                }

                def _frozen_version(pkg):
                    try:
                        return _orig_version(pkg)
                    except _im.PackageNotFoundError:
                        # Only fake version for packages actually bundled;
                        # excluded packages (e.g. matplotlib) must stay missing.
                        mod = _DIST_TO_IMPORT.get(pkg, pkg.replace("-", "_"))
                        if importlib.util.find_spec(mod) is not None:
                            return "0.0.0"
                        raise

                _im.version = _frozen_version
                _im._frozen_patched = True

        from paddleocr import PaddleOCR

        device = "gpu:0" if use_gpu else "cpu"
        self._ocr = PaddleOCR(
            lang="chinese_cht",
            device=device,
            enable_mkldnn=False,
            # 遊戲截圖不需要文件矯正，停用以避免載入 UVDoc 模型
            # （UVDoc 在部分機器上會觸發 PermissionError）
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
        )

    def recognize(self, image: np.ndarray, scale_factor: float = _SCALE_FACTOR) -> list[tuple[str, float]]:
        processed = preprocess_for_ocr(image, scale_factor=scale_factor)
        result = self._ocr.predict(processed)
        if not result:
            return []
        texts = result[0].get("rec_texts", [])
        polys = result[0].get("dt_polys", [])
        out: list[tuple[str, float]] = []
        for text, poly in zip(texts, polys):
            # y 座標扣除 padding 後除以放大倍率，還原為原始座標
            y_center = (sum(pt[1] for pt in poly) / len(poly) - _PADDING_PX) / scale_factor
            out.append((text, y_center))
        return out


# 恢復附加方塊的潛能框較小，需要更大的放大倍率
_SMALL_FRAME_CUBE_TYPES = {"恢復附加方塊 (紅色)"}


def get_scale_factor(cube_type: str) -> float:
    """根據方塊類型取得放大倍率。"""
    if cube_type in _SMALL_FRAME_CUBE_TYPES:
        return _SCALE_FACTOR_SMALL
    return _SCALE_FACTOR


def create_ocr_engine(use_gpu: bool = False) -> OCREngine:
    """建立 OCR 引擎（PaddleOCR）。"""
    return PaddleOCREngine(use_gpu=use_gpu)
