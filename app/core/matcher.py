import cv2
import numpy as np


class TemplateMatcher:
    """OpenCV 模板匹配，定位按鈕位置。"""

    def __init__(self, threshold: float = 0.8) -> None:
        self.threshold = threshold

    def match(
        self, screen: np.ndarray, template: np.ndarray
    ) -> tuple[int, int] | None:
        """在螢幕截圖中匹配模板，回傳中心座標或 None。"""
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < self.threshold:
            return None

        # 回傳模板中心座標
        h, w = template.shape[:2]
        cx = max_loc[0] + w // 2
        cy = max_loc[1] + h // 2
        return (cx, cy)

    def load_template(self, path: str) -> np.ndarray:
        """載入模板圖片。"""
        template = cv2.imread(path)
        if template is None:
            raise FileNotFoundError(f"模板圖片不存在: {path}")
        return template
