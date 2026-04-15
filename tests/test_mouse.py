"""Unit tests for MouseController.click + _send_click."""
import threading
from unittest.mock import MagicMock, patch


def _fake_windll(setcursor_ok: bool = True, sendinput_result: int = 1):
    """Build a fake ctypes.windll with configurable return values."""
    fake = MagicMock()
    fake.user32.SetCursorPos.return_value = 1 if setcursor_ok else 0
    fake.user32.SendInput.return_value = sendinput_result
    fake.user32.FindWindowW.return_value = 0
    fake.user32.GetForegroundWindow.return_value = 0
    fake.kernel32.GetCurrentThreadId.return_value = 0
    return fake


def test_send_click_returns_event_count():
    from app.core import mouse as m

    fake = _fake_windll(sendinput_result=1)
    with patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        assert m._send_click() == 2

    assert fake.user32.SendInput.call_count == 2


def test_click_calls_foreground_then_cursor_then_sendinput():
    from app.core import mouse as m

    fake = _fake_windll()
    controller = m.MouseController()

    with patch.object(m, "_ensure_game_foreground") as fg, \
         patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        parent = MagicMock()
        parent.attach_mock(fg, "fg")
        parent.attach_mock(fake.user32.SetCursorPos, "setcursor")
        parent.attach_mock(fake.user32.SendInput, "sendinput")

        assert controller.click(123, 456) is True

        names = [c[0] for c in parent.mock_calls]
        assert names[0] == "fg"
        assert "setcursor" in names
        assert names.index("setcursor") < names.index("sendinput")
        fake.user32.SetCursorPos.assert_called_once_with(123, 456)
        assert fake.user32.SendInput.call_count == 2


def test_click_respects_stop_flag():
    """stop_flag set → foreground still called first (AC-1 order), then silent False, no cursor/send."""
    from app.core import mouse as m

    event = threading.Event()
    event.set()
    controller = m.MouseController()
    controller.bind_stop_flag(event)

    fake = _fake_windll()
    with patch.object(m, "_ensure_game_foreground") as fg, \
         patch.object(m.ctypes, "windll", fake, create=True):
        assert controller.click(10, 20) is False

    fg.assert_called_once()
    fake.user32.SetCursorPos.assert_not_called()
    fake.user32.SendInput.assert_not_called()


def test_click_returns_false_on_setcursorpos_failure(caplog):
    from app.core import mouse as m

    fake = _fake_windll(setcursor_ok=False)
    controller = m.MouseController()

    with patch.object(m, "_ensure_game_foreground"), \
         patch.object(m.ctypes, "windll", fake, create=True), \
         caplog.at_level("WARNING", logger="app.core.mouse"):
        assert controller.click(10, 20) is False

    fake.user32.SendInput.assert_not_called()
    assert any("SetCursorPos 失敗" in r.message for r in caplog.records)


def test_click_returns_false_on_sendinput_failure(caplog):
    from app.core import mouse as m

    fake = _fake_windll(sendinput_result=0)
    controller = m.MouseController()

    with patch.object(m, "_ensure_game_foreground"), \
         patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"), \
         caplog.at_level("WARNING", logger="app.core.mouse"):
        assert controller.click(10, 20) is False

    assert any("SendInput(mouse) 失敗" in r.message for r in caplog.records)


def test_click_stop_flag_is_silent(caplog):
    """stop_flag 中斷路徑不得產生任何 warning，語義對齊 press_confirm。"""
    from app.core import mouse as m

    event = threading.Event()
    event.set()
    controller = m.MouseController()
    controller.bind_stop_flag(event)

    fake = _fake_windll()
    with patch.object(m, "_ensure_game_foreground"), \
         patch.object(m.ctypes, "windll", fake, create=True), \
         caplog.at_level("WARNING", logger="app.core.mouse"):
        assert controller.click(10, 20) is False

    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert warnings == []


def test_click_returns_false_on_partial_sendinput(caplog):
    """SendInput 注入 1+0 事件（第二次失敗）→ 回 False 並 warning。"""
    from app.core import mouse as m

    fake = _fake_windll()
    fake.user32.SendInput.side_effect = [1, 0]
    controller = m.MouseController()

    with patch.object(m, "_ensure_game_foreground"), \
         patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"), \
         caplog.at_level("WARNING", logger="app.core.mouse"):
        assert controller.click(10, 20) is False

    assert any("SendInput(mouse) 失敗" in r.message for r in caplog.records)


# ── _send_key ────────────────────────────────────────────────────

def test_send_key_returns_event_count():
    from app.core import mouse as m

    fake = _fake_windll(sendinput_result=1)
    with patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        assert m._send_key(0x20, 0x39) == 2

    assert fake.user32.SendInput.call_count == 2


# ── press_confirm ────────────────────────────────────────────────

def test_press_confirm_calls_foreground_and_sends_one_event():
    """times=1 → foreground check + 1 次 _send_key（2 個 SendInput 事件）。"""
    from app.core import mouse as m

    fake = _fake_windll()
    controller = m.MouseController()

    with patch.object(m, "_ensure_game_foreground") as fg, \
         patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        assert controller.press_confirm(times=1) is True

    fg.assert_called_once()
    assert fake.user32.SendInput.call_count == 2


def test_press_confirm_times_three_applies_gap_sleep_between():
    """times=3 → 中間兩段 _KEY_GAP_SEC 睡眠；第一次無 gap。"""
    from app.core import mouse as m

    fake = _fake_windll()
    controller = m.MouseController()

    with patch.object(m, "_ensure_game_foreground"), \
         patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep") as sleep_mock:
        assert controller.press_confirm(times=3) is True

    assert fake.user32.SendInput.call_count == 6
    gap_sleeps = [c for c in sleep_mock.call_args_list if c.args == (m._KEY_GAP_SEC,)]
    assert len(gap_sleeps) == 2


def test_press_confirm_respects_stop_flag_midway():
    """stop_flag 在第 1 次送完後被 set → 第 2 次迴圈 early return False。"""
    from app.core import mouse as m

    event = threading.Event()
    fake = _fake_windll()

    def flip_after_first_key(*_args, **_kwargs):
        event.set()
        return 1

    fake.user32.SendInput.side_effect = flip_after_first_key

    controller = m.MouseController()
    controller.bind_stop_flag(event)

    with patch.object(m, "_ensure_game_foreground"), \
         patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        assert controller.press_confirm(times=5) is False

    assert fake.user32.SendInput.call_count == 2


def test_press_confirm_returns_false_on_sendinput_failure(caplog):
    """SendInput 注入 < 2 事件 → False + warning。"""
    from app.core import mouse as m

    fake = _fake_windll(sendinput_result=0)
    controller = m.MouseController()

    with patch.object(m, "_ensure_game_foreground"), \
         patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"), \
         caplog.at_level("WARNING", logger="app.core.mouse"):
        assert controller.press_confirm(times=1) is False

    assert any("SendInput 失敗" in r.message for r in caplog.records)


# ── wait ────────────────────────────────────────────────────────

def test_wait_uses_event_wait_when_stop_flag_bound():
    from app.core import mouse as m

    event = MagicMock(spec=threading.Event)
    event.is_set.return_value = False
    controller = m.MouseController(delay_ms=100)
    controller.bind_stop_flag(event)

    with patch.object(m.time, "sleep") as sleep_mock:
        controller.wait(ms=250)

    event.wait.assert_called_once_with(0.25)
    sleep_mock.assert_not_called()


def test_wait_uses_time_sleep_without_stop_flag():
    from app.core import mouse as m

    controller = m.MouseController(delay_ms=100)

    with patch.object(m.time, "sleep") as sleep_mock:
        controller.wait(ms=500)

    sleep_mock.assert_called_once_with(0.5)


def test_wait_defaults_to_delay_ms_when_ms_none():
    from app.core import mouse as m

    controller = m.MouseController(delay_ms=777)

    with patch.object(m.time, "sleep") as sleep_mock:
        controller.wait()

    sleep_mock.assert_called_once_with(0.777)


# ── bind_stop_flag / stopped ─────────────────────────────────────

def test_stopped_defaults_false_without_flag():
    from app.core import mouse as m

    assert m.MouseController().stopped is False


def test_stopped_reflects_event_state():
    from app.core import mouse as m

    controller = m.MouseController()
    event = threading.Event()
    controller.bind_stop_flag(event)

    assert controller.stopped is False
    event.set()
    assert controller.stopped is True


# ── focus_game_window / _find_game_hwnd / _ensure_game_foreground ─

def test_find_game_hwnd_caches_found_handle():
    from app.core import mouse as m

    m._game_hwnd = 0
    fake = _fake_windll()
    fake.user32.FindWindowW.return_value = 42
    with patch.object(m.ctypes, "windll", fake, create=True):
        assert m._find_game_hwnd() == 42
        assert m._game_hwnd == 42
    m._game_hwnd = 0


def test_focus_game_window_returns_false_when_not_found(caplog):
    from app.core import mouse as m

    m._game_hwnd = 0
    fake = _fake_windll()
    fake.user32.FindWindowW.return_value = 0
    with patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"), \
         caplog.at_level("WARNING", logger="app.core.mouse"):
        assert m.focus_game_window() is False

    assert any("找不到遊戲視窗" in r.message for r in caplog.records)


def test_focus_game_window_returns_true_when_found():
    from app.core import mouse as m

    m._game_hwnd = 0
    fake = _fake_windll()
    fake.user32.FindWindowW.return_value = 99
    fake.user32.GetForegroundWindow.return_value = 1  # 不同於 99 → 觸發 attach/set
    fake.user32.GetWindowThreadProcessId.return_value = 2
    fake.kernel32.GetCurrentThreadId.return_value = 3
    with patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        assert m.focus_game_window() is True

    fake.user32.SetForegroundWindow.assert_called_once_with(99)
    m._game_hwnd = 0


def test_ensure_game_foreground_noop_when_already_foreground():
    """前景已是遊戲 → 不得呼叫 SetForegroundWindow / AttachThreadInput。"""
    from app.core import mouse as m

    m._game_hwnd = 77
    fake = _fake_windll()
    fake.user32.GetForegroundWindow.return_value = 77
    with patch.object(m.ctypes, "windll", fake, create=True):
        m._ensure_game_foreground()

    fake.user32.SetForegroundWindow.assert_not_called()
    fake.user32.AttachThreadInput.assert_not_called()
    m._game_hwnd = 0


def test_ensure_game_foreground_returns_early_if_hwnd_missing():
    from app.core import mouse as m

    m._game_hwnd = 0
    fake = _fake_windll()
    fake.user32.FindWindowW.return_value = 0
    with patch.object(m.ctypes, "windll", fake, create=True):
        m._ensure_game_foreground()

    fake.user32.GetForegroundWindow.assert_not_called()
    fake.user32.SetForegroundWindow.assert_not_called()


def test_ensure_game_foreground_skips_attach_when_same_thread():
    """前景視窗與目前同一 thread → 不呼叫 AttachThreadInput，仍嘗試 SetForegroundWindow。"""
    from app.core import mouse as m

    m._game_hwnd = 77
    fake = _fake_windll()
    fake.user32.GetForegroundWindow.return_value = 1  # 不等於 77 → 進入 switch 路徑
    fake.kernel32.GetCurrentThreadId.return_value = 5
    fake.user32.GetWindowThreadProcessId.return_value = 5  # 同 thread

    with patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        m._ensure_game_foreground()

    fake.user32.AttachThreadInput.assert_not_called()
    fake.user32.SetForegroundWindow.assert_called_once_with(77)
    m._game_hwnd = 0


def test_ensure_game_foreground_attaches_when_different_thread():
    """前景視窗屬於不同 thread → AttachThreadInput 被呼叫兩次（True + False）。"""
    from app.core import mouse as m

    m._game_hwnd = 77
    fake = _fake_windll()
    fake.user32.GetForegroundWindow.return_value = 1
    fake.kernel32.GetCurrentThreadId.return_value = 10
    fake.user32.GetWindowThreadProcessId.return_value = 20  # 不同 thread

    with patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        m._ensure_game_foreground()

    assert fake.user32.AttachThreadInput.call_count == 2
    fake.user32.AttachThreadInput.assert_any_call(10, 20, True)
    fake.user32.AttachThreadInput.assert_any_call(10, 20, False)
    m._game_hwnd = 0


def test_focus_game_window_skips_attach_when_same_thread():
    from app.core import mouse as m

    m._game_hwnd = 0
    fake = _fake_windll()
    fake.user32.FindWindowW.return_value = 99
    fake.kernel32.GetCurrentThreadId.return_value = 2
    fake.user32.GetWindowThreadProcessId.return_value = 2  # 同 thread → 跳過 attach

    with patch.object(m.ctypes, "windll", fake, create=True), \
         patch.object(m.time, "sleep"):
        assert m.focus_game_window() is True

    fake.user32.AttachThreadInput.assert_not_called()
    fake.user32.SetForegroundWindow.assert_called_once_with(99)
    m._game_hwnd = 0
