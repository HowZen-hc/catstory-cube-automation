"""Unit tests for SimpleFlowStrategy.execute_roll."""
from unittest.mock import MagicMock, call, patch

from app.cube.simple_flow import SimpleFlowStrategy
from app.models.potential import PotentialLine


def _line(attr: str, value: int) -> PotentialLine:
    return PotentialLine(attribute=attr, value=value, raw_text=f"{attr}+{value}%")


def _make_strategy(cube_type: str, region_set: bool = True):
    config = MagicMock()
    config.cube_type = cube_type
    config.delay_ms = 500
    config.potential_region.is_set.return_value = region_set

    screen = MagicMock()
    ocr = MagicMock()
    mouse = MagicMock()
    checker = MagicMock()
    checker.check.return_value = False
    log_session = MagicMock()

    return SimpleFlowStrategy(config, screen, ocr, mouse, checker, log_session)


def _patch_ocr_pipeline(lines):
    return patch.multiple(
        "app.cube.simple_flow",
        get_scale_factor=MagicMock(return_value=1.0),
        get_num_lines=MagicMock(return_value=3),
        parse_potential_lines=MagicMock(return_value=lines),
    )


def test_pink_cube_uses_two_confirms_and_user_delay():
    """珍貴方塊（粉紅色）→ press 1 + press 2，wait 用 user delay_ms。"""
    s = _make_strategy("珍貴附加方塊 (粉紅色)")

    with _patch_ocr_pipeline([_line("STR", 9)]):
        s.execute_roll(1)

    assert s.mouse.press_confirm.call_args_list == [call(times=1), call(times=2)]
    # wait：先 ms=150、再 default（user delay_ms）
    assert s.mouse.wait.call_args_list == [call(ms=150), call()]


def test_pet_cube_uses_single_confirm():
    """萌獸方塊 → press 1 + press 1（只確認一次）。"""
    s = _make_strategy("萌獸方塊")

    with _patch_ocr_pipeline([]):
        s.execute_roll(1)

    assert s.mouse.press_confirm.call_args_list == [call(times=1), call(times=1)]


def test_pet_cube_uses_min_delay_when_user_delay_lower():
    """萌獸 delay_ms=500 < 2200 → wait 用 2200 兜底。"""
    s = _make_strategy("萌獸方塊")
    s.config.delay_ms = 500

    with _patch_ocr_pipeline([]):
        s.execute_roll(1)

    wait_calls = s.mouse.wait.call_args_list
    # 第 2 次 wait（結果等待）應該是 2200ms（萌獸下限）
    assert wait_calls[1].kwargs == {"ms": 2200}


def test_pet_cube_uses_user_delay_when_higher():
    """萌獸 delay_ms=3000 > 2200 → wait 用 3000。"""
    s = _make_strategy("萌獸方塊")
    s.config.delay_ms = 3000

    with _patch_ocr_pipeline([]):
        s.execute_roll(1)

    wait_calls = s.mouse.wait.call_args_list
    assert wait_calls[1].kwargs == {"ms": 3000}


def test_region_unset_returns_empty_lines():
    """potential_region 未設定 → 不截圖、lines=[]，仍回 RollResult。"""
    s = _make_strategy("珍貴附加方塊 (粉紅色)", region_set=False)

    result = s.execute_roll(7)

    assert result.roll_number == 7
    assert result.lines == []
    assert result.matched is False
    s.screen.capture.assert_not_called()
    s.ocr.recognize.assert_not_called()


def test_matched_propagates_from_checker():
    """checker.check 回 True → RollResult.matched=True。"""
    s = _make_strategy("珍貴附加方塊 (粉紅色)")
    s.checker.check.return_value = True

    with _patch_ocr_pipeline([_line("STR", 9)]):
        result = s.execute_roll(1)

    assert result.matched is True
    assert result.lines == [_line("STR", 9)]
