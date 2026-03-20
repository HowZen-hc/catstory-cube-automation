import ctypes
import ctypes.wintypes
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Windows API 常數
_VK_SPACE = 0x20
_SCAN_SPACE = 0x39  # space 鍵的 scan code
_INPUT_KEYBOARD = 1
_KEYEVENTF_KEYUP = 0x0002
_GAME_WINDOW_TITLE = "貓貓TMS"

# 按鍵時序參數（秒）
_KEY_HOLD_SEC = 0.03  # key down → key up 之間的 hold 時間
_KEY_GAP_SEC = 0.08  # 連續按鍵之間的間隔

# 遊戲視窗 handle 快取
_game_hwnd: int = 0


# ── SendInput struct 定義 ──────────────────────────────────────────


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.wintypes.DWORD),
        ("wParamL", ctypes.wintypes.WORD),
        ("wParamH", ctypes.wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", _KEYBDINPUT),
        ("mi", _MOUSEINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


# ── 核心函式 ──────────────────────────────────────────────────────


def _find_game_hwnd() -> int:
    """取得遊戲視窗 handle，找到後快取。"""
    global _game_hwnd
    hwnd = ctypes.windll.user32.FindWindowW(None, _GAME_WINDOW_TITLE)
    if hwnd:
        _game_hwnd = hwnd
    return hwnd


def _send_key(vk_code: int, scan_code: int) -> int:
    """透過 SendInput 發送一次按鍵，回傳成功注入的事件數。"""
    # Key down
    inp_down = _INPUT()
    inp_down.type = _INPUT_KEYBOARD
    inp_down.union.ki.wVk = vk_code
    inp_down.union.ki.wScan = scan_code
    inp_down.union.ki.dwFlags = 0
    inp_down.union.ki.time = 0
    inp_down.union.ki.dwExtraInfo = 0

    result_down = ctypes.windll.user32.SendInput(
        1, ctypes.byref(inp_down), ctypes.sizeof(_INPUT)
    )

    time.sleep(_KEY_HOLD_SEC)

    # Key up
    inp_up = _INPUT()
    inp_up.type = _INPUT_KEYBOARD
    inp_up.union.ki.wVk = vk_code
    inp_up.union.ki.wScan = scan_code
    inp_up.union.ki.dwFlags = _KEYEVENTF_KEYUP
    inp_up.union.ki.time = 0
    inp_up.union.ki.dwExtraInfo = 0

    result_up = ctypes.windll.user32.SendInput(
        1, ctypes.byref(inp_up), ctypes.sizeof(_INPUT)
    )

    return result_down + result_up


def _ensure_game_foreground() -> None:
    """如果前景不是遊戲視窗，重新拉回前景。"""
    hwnd = _game_hwnd or _find_game_hwnd()
    if not hwnd:
        return
    fg = ctypes.windll.user32.GetForegroundWindow()
    if fg == hwnd:
        return
    logger.warning("前景視窗非遊戲 (fg=%s)，重新拉回", fg)
    user32 = ctypes.windll.user32
    current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
    foreground_tid = user32.GetWindowThreadProcessId(fg, None)
    if current_tid != foreground_tid:
        user32.AttachThreadInput(current_tid, foreground_tid, True)
    user32.SetForegroundWindow(hwnd)
    if current_tid != foreground_tid:
        user32.AttachThreadInput(current_tid, foreground_tid, False)
    time.sleep(0.3)


def focus_game_window() -> bool:
    """將遊戲視窗拉到前景，回傳是否成功。

    只在自動化開始時呼叫一次，避免反覆切換干擾輸入狀態。
    """
    hwnd = _find_game_hwnd()
    if not hwnd:
        logger.warning("找不到遊戲視窗: %s", _GAME_WINDOW_TITLE)
        return False

    user32 = ctypes.windll.user32
    current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
    foreground_tid = user32.GetWindowThreadProcessId(
        user32.GetForegroundWindow(), None
    )
    if current_tid != foreground_tid:
        user32.AttachThreadInput(current_tid, foreground_tid, True)
    user32.SetForegroundWindow(hwnd)
    if current_tid != foreground_tid:
        user32.AttachThreadInput(current_tid, foreground_tid, False)

    time.sleep(0.3)
    return True


class MouseController:
    """遊戲輸入控制器。"""

    def __init__(self, delay_ms: int = 500) -> None:
        self.delay_ms = delay_ms
        self._stop_flag: threading.Event | None = None

    def bind_stop_flag(self, stop_event: threading.Event) -> None:
        """綁定停止旗標，讓 wait / press_confirm 可即時中斷。"""
        self._stop_flag = stop_event

    @property
    def stopped(self) -> bool:
        return self._stop_flag is not None and self._stop_flag.is_set()

    def press_confirm(self, times: int = 1) -> bool:
        """透過 SendInput 發送空白鍵到前景視窗。

        送鍵前會檢查前景是否為遊戲視窗，不是的話自動拉回。
        """
        _ensure_game_foreground()

        for i in range(times):
            if self.stopped:
                return False
            if i > 0:
                time.sleep(_KEY_GAP_SEC)
            result = _send_key(_VK_SPACE, _SCAN_SPACE)
            if result < 2:
                logger.warning("SendInput 失敗: 預期注入 2 事件，實際 %d", result)
                return False
        return True

    def wait(self, ms: int | None = None) -> None:
        """等待指定毫秒，可被 stop_flag 提前中斷。"""
        delay = ms if ms is not None else self.delay_ms
        if self._stop_flag is not None:
            # 用 Event.wait 取代 time.sleep，可被 set() 瞬間喚醒
            self._stop_flag.wait(delay / 1000.0)
        else:
            time.sleep(delay / 1000.0)
