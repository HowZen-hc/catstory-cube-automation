import ctypes
import logging
import time

import pyautogui

logger = logging.getLogger(__name__)

# 關閉 pyautogui 的安全暫停（預設每次操作後暫停 0.1 秒）
pyautogui.PAUSE = 0.05
# 關閉 fail-safe（移到左上角不會中斷）
pyautogui.FAILSAFE = False

# Windows API 常數
_VK_SPACE = 0x20
_KEYEVENTF_KEYUP = 0x0002
_GAME_WINDOW_TITLE = "貓貓TMS"


def _press_key(vk_code: int) -> None:
    """透過 Windows API keybd_event 發送按鍵。"""
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, _KEYEVENTF_KEYUP, 0)


def focus_game_window() -> bool:
    """將遊戲視窗拉到前景，回傳是否成功。"""
    hwnd = ctypes.windll.user32.FindWindowW(None, _GAME_WINDOW_TITLE)
    if not hwnd:
        logger.warning("找不到遊戲視窗: %s", _GAME_WINDOW_TITLE)
        return False
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    return True


class MouseController:
    """pyautogui 滑鼠移動與點擊。"""

    def __init__(self, delay_ms: int = 500) -> None:
        self.delay_ms = delay_ms

    def click(self, x: int, y: int) -> None:
        """移動到指定座標並點擊。"""
        pyautogui.click(x, y)

    def press_confirm(self, times: int = 1) -> None:
        """按下空白鍵確認（遊戲防呆），使用 Windows API 發送。"""
        for i in range(times):
            if i > 0:
                time.sleep(0.2)
            _press_key(_VK_SPACE)

    def move(self, x: int, y: int) -> None:
        """移動到指定座標。"""
        pyautogui.moveTo(x, y)

    def wait(self, ms: int | None = None) -> None:
        """等待指定毫秒，預設使用 self.delay_ms。"""
        delay = ms if ms is not None else self.delay_ms
        time.sleep(delay / 1000.0)
