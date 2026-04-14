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

