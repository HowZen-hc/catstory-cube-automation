import numpy as np
import mss

from app.models.config import Region


class ScreenCapture:
    """mss 螢幕擷取，回傳 numpy array。"""

    def __init__(self) -> None:
        self._sct = mss.mss()

    def capture(self, region: Region) -> np.ndarray:
        """擷取指定螢幕區域，回傳 BGR numpy array。"""
        monitor = {
            "left": region.x,
            "top": region.y,
            "width": region.width,
            "height": region.height,
        }
        screenshot = self._sct.grab(monitor)
        # mss 回傳 BGRA，轉成 BGR（OpenCV 格式）
        img = np.array(screenshot)
        return img[:, :, :3]

    def capture_full(self) -> np.ndarray:
        """擷取整個主螢幕。"""
        monitor = self._sct.monitors[1]  # 主螢幕
        screenshot = self._sct.grab(monitor)
        img = np.array(screenshot)
        return img[:, :, :3]
