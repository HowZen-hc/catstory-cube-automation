"""Tests for AutomationWorker startup OCR seeding to strategy."""
from unittest.mock import MagicMock, patch

from app.core.automation import AutomationWorker
from app.models.config import AppConfig, Region


def _make_config(cube_type: str, region_set: bool) -> AppConfig:
    cfg = AppConfig()
    cfg.cube_type = cube_type
    cfg.potential_region = Region(x=0, y=0, width=100, height=50) if region_set else Region()
    cfg.delay_ms = 0
    return cfg


def _run_worker(cfg, matched=False, compare_strategy_cls=None, simple_strategy_cls=None):
    """Invoke AutomationWorker.run() synchronously with all external deps mocked.
    Returns the captured strategy instance for assertion."""
    captured = {}

    compare_spy = compare_strategy_cls or MagicMock(name="CompareFlowStrategy")
    simple_spy = simple_strategy_cls or MagicMock(name="SimpleFlowStrategy")

    # Capture the strategy instance that gets constructed
    def wrap(spy):
        def factory(*args, **kwargs):
            inst = spy(*args, **kwargs)
            captured["strategy"] = inst
            # Exit the main loop immediately after startup phase
            inst.execute_roll = MagicMock(side_effect=lambda n: worker.stop() or MagicMock(matched=True))
            return inst
        return factory

    worker = AutomationWorker(cfg)

    mock_checker = MagicMock()
    mock_checker.check.return_value = matched

    with patch("app.core.automation.ScreenCapture"), \
         patch("app.core.automation.create_ocr_engine"), \
         patch("app.core.automation.MouseController"), \
         patch("app.core.automation.ConditionChecker", return_value=mock_checker), \
         patch("app.core.automation.OCRLogSession"), \
         patch("app.core.automation.focus_game_window", return_value=True), \
         patch("app.core.automation.CompareFlowStrategy", side_effect=wrap(compare_spy)), \
         patch("app.core.automation.SimpleFlowStrategy", side_effect=wrap(simple_spy)), \
         patch("app.core.automation.get_scale_factor", return_value=1.0), \
         patch("app.core.automation.get_num_lines", return_value=3), \
         patch("app.core.automation.parse_potential_lines", return_value=["seeded-lines"]):
        worker.run()

    return captured.get("strategy")


def test_seed_called_on_compare_flow_when_region_set_and_not_matched():
    cfg = _make_config("恢復附加方塊 (紅色)", region_set=True)
    strategy = _run_worker(cfg, matched=False)

    strategy.seed_initial_potential.assert_called_once_with(["seeded-lines"])


def test_seed_not_called_when_region_unset():
    cfg = _make_config("恢復附加方塊 (紅色)", region_set=False)
    strategy = _run_worker(cfg, matched=False)

    strategy.seed_initial_potential.assert_not_called()


def test_seed_not_called_when_initial_match_triggers_early_return():
    cfg = _make_config("恢復附加方塊 (紅色)", region_set=True)
    strategy = _run_worker(cfg, matched=True)

    strategy.seed_initial_potential.assert_not_called()


def test_initial_match_emits_target_reached_zero_and_roll_zero():
    """初始潛能已命中 → roll_completed(0, matched=True) + target_reached(0)，execute_roll 不被呼叫。"""
    cfg = _make_config("恢復附加方塊 (紅色)", region_set=True)
    worker = AutomationWorker(cfg)

    target_hits: list[int] = []
    roll_completed_hits: list = []
    worker.target_reached.connect(target_hits.append)
    worker.roll_completed.connect(roll_completed_hits.append)

    strategy_inst = MagicMock()
    strategy_inst.execute_roll = MagicMock()

    mock_checker = MagicMock()
    mock_checker.check.return_value = True  # 初始即命中

    with patch("app.core.automation.ScreenCapture"), \
         patch("app.core.automation.create_ocr_engine"), \
         patch("app.core.automation.MouseController"), \
         patch("app.core.automation.ConditionChecker", return_value=mock_checker), \
         patch("app.core.automation.OCRLogSession"), \
         patch("app.core.automation.focus_game_window", return_value=True), \
         patch("app.core.automation.CompareFlowStrategy", return_value=strategy_inst), \
         patch("app.core.automation.SimpleFlowStrategy", return_value=strategy_inst), \
         patch("app.core.automation.get_scale_factor", return_value=1.0), \
         patch("app.core.automation.get_num_lines", return_value=3), \
         patch("app.core.automation.parse_potential_lines", return_value=["init-lines"]):
        worker.run()

    assert target_hits == [0]
    assert len(roll_completed_hits) == 1
    assert roll_completed_hits[0].roll_number == 0
    assert roll_completed_hits[0].matched is True
    strategy_inst.execute_roll.assert_not_called()


def test_seed_on_simple_flow_is_harmless_noop():
    """SimpleFlow uses base class no-op seed — still called, but does nothing."""
    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=True)
    strategy = _run_worker(cfg, matched=False)

    # Seed is called uniformly regardless of strategy type (base class handles no-op)
    strategy.seed_initial_potential.assert_called_once_with(["seeded-lines"])


# ── Full run() loop coverage ─────────────────────────────────────


def _run_with_capture(cfg, roll_results=None, focus_ok=True, init_raises=None):
    """Run worker synchronously and capture emitted signals.

    roll_results: iterable of RollResult or exceptions that execute_roll will return/raise
    focus_ok: focus_game_window return value
    init_raises: Exception to raise during ScreenCapture() construction (simulates init failure)
    """
    worker = AutomationWorker(cfg)
    target_hits: list[int] = []
    errors: list[str] = []
    worker.target_reached.connect(target_hits.append)
    worker.error_occurred.connect(errors.append)

    roll_iter = iter(roll_results or [])

    def execute_side_effect(n):
        item = next(roll_iter)
        if isinstance(item, Exception):
            raise item
        return item

    def strategy_factory(*args, **kwargs):
        inst = MagicMock()
        inst.execute_roll = MagicMock(side_effect=execute_side_effect)
        return inst

    screen_mock = MagicMock(side_effect=init_raises) if init_raises else MagicMock()

    mock_checker = MagicMock()
    # Initial potential check uses matched from last result if region_set, else skipped
    # For run-loop tests we force initial-not-matched so the loop is entered.
    mock_checker.check.return_value = False

    with patch("app.core.automation.ScreenCapture", screen_mock), \
         patch("app.core.automation.create_ocr_engine"), \
         patch("app.core.automation.MouseController"), \
         patch("app.core.automation.ConditionChecker", return_value=mock_checker), \
         patch("app.core.automation.OCRLogSession"), \
         patch("app.core.automation.focus_game_window", return_value=focus_ok), \
         patch("app.core.automation.CompareFlowStrategy", side_effect=strategy_factory), \
         patch("app.core.automation.SimpleFlowStrategy", side_effect=strategy_factory), \
         patch("app.core.automation.get_scale_factor", return_value=1.0), \
         patch("app.core.automation.get_num_lines", return_value=3), \
         patch("app.core.automation.parse_potential_lines", return_value=[]):
        worker.run()

    return {"target": target_hits, "errors": errors, "worker": worker}


def test_init_failure_emits_error_and_returns():
    """ScreenCapture 爆 → error_occurred + 不進主迴圈。"""
    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=False)
    out = _run_with_capture(cfg, init_raises=RuntimeError("screen boom"))

    assert out["target"] == []
    assert len(out["errors"]) == 1
    assert "初始化失敗" in out["errors"][0]


def test_focus_game_window_failure_emits_error_and_returns():
    """focus_game_window 回 False → error_occurred + 不進主迴圈。"""
    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=False)
    out = _run_with_capture(cfg, focus_ok=False)

    assert out["target"] == []
    assert len(out["errors"]) == 1
    assert "找不到遊戲視窗" in out["errors"][0]


def test_normal_match_emits_target_reached_with_roll_number():
    """3 輪未命中 + 第 4 輪命中 → target_reached(4)。"""
    from app.models.potential import RollResult

    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=False)
    rolls = [
        RollResult(roll_number=1, lines=[], matched=False),
        RollResult(roll_number=2, lines=[], matched=False),
        RollResult(roll_number=3, lines=[], matched=False),
        RollResult(roll_number=4, lines=[], matched=True),
    ]
    out = _run_with_capture(cfg, roll_results=rolls)

    assert out["target"] == [4]
    assert out["errors"] == []


def test_execute_roll_exception_emits_error_and_breaks_loop():
    """execute_roll 拋 → error_occurred + 中斷迴圈（後續 roll 不會被叫）。"""
    from app.models.potential import RollResult

    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=False)
    rolls = [
        RollResult(roll_number=1, lines=[], matched=False),
        RuntimeError("click failed"),
        RollResult(roll_number=3, lines=[], matched=True),  # 不該被叫到
    ]
    out = _run_with_capture(cfg, roll_results=rolls)

    assert out["target"] == []
    assert len(out["errors"]) == 1
    assert "第 2 次執行錯誤" in out["errors"][0]
    assert "click failed" in out["errors"][0]


def test_stop_mid_loop_exits_before_next_roll():
    """execute_roll 執行中呼叫 worker.stop() → 該輪結果不 emit、下一輪不 run。"""
    from app.models.potential import RollResult

    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=False)
    worker_ref = {}
    captured_strategy = {}

    def stop_after_first(n):
        worker_ref["w"].stop()
        return RollResult(roll_number=n, lines=[], matched=False)

    worker = AutomationWorker(cfg)
    worker_ref["w"] = worker
    target_hits: list[int] = []
    roll_completed_hits: list[RollResult] = []
    worker.target_reached.connect(target_hits.append)
    worker.roll_completed.connect(roll_completed_hits.append)

    def strategy_factory(*args, **kwargs):
        inst = MagicMock()
        inst.execute_roll = MagicMock(side_effect=stop_after_first)
        captured_strategy["inst"] = inst
        return inst

    mock_checker = MagicMock()
    mock_checker.check.return_value = False

    with patch("app.core.automation.ScreenCapture"), \
         patch("app.core.automation.create_ocr_engine"), \
         patch("app.core.automation.MouseController"), \
         patch("app.core.automation.ConditionChecker", return_value=mock_checker), \
         patch("app.core.automation.OCRLogSession"), \
         patch("app.core.automation.focus_game_window", return_value=True), \
         patch("app.core.automation.CompareFlowStrategy", side_effect=strategy_factory), \
         patch("app.core.automation.SimpleFlowStrategy", side_effect=strategy_factory), \
         patch("app.core.automation.get_scale_factor", return_value=1.0), \
         patch("app.core.automation.get_num_lines", return_value=3), \
         patch("app.core.automation.parse_potential_lines", return_value=[]):
        worker.run()

    assert target_hits == []
    # execute_roll 僅跑第 1 輪；stop() 後主迴圈 break 阻止第 2 輪
    assert captured_strategy["inst"].execute_roll.call_count == 1
    # 該輪結果因 stop 發生在 execute_roll 期間、未進入 roll_completed.emit 分支
    assert roll_completed_hits == []


def test_compare_flow_selected_for_red_cube():
    cfg = _make_config("恢復附加方塊 (紅色)", region_set=False)
    worker = AutomationWorker(cfg)

    with patch("app.core.automation.ScreenCapture"), \
         patch("app.core.automation.create_ocr_engine"), \
         patch("app.core.automation.MouseController"), \
         patch("app.core.automation.ConditionChecker"), \
         patch("app.core.automation.OCRLogSession"), \
         patch("app.core.automation.focus_game_window", return_value=False), \
         patch("app.core.automation.CompareFlowStrategy") as compare_cls, \
         patch("app.core.automation.SimpleFlowStrategy") as simple_cls:
        worker.run()

    compare_cls.assert_called_once()
    simple_cls.assert_not_called()


def test_simple_flow_selected_for_non_red_cube():
    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=False)
    worker = AutomationWorker(cfg)

    with patch("app.core.automation.ScreenCapture"), \
         patch("app.core.automation.create_ocr_engine"), \
         patch("app.core.automation.MouseController"), \
         patch("app.core.automation.ConditionChecker"), \
         patch("app.core.automation.OCRLogSession"), \
         patch("app.core.automation.focus_game_window", return_value=False), \
         patch("app.core.automation.CompareFlowStrategy") as compare_cls, \
         patch("app.core.automation.SimpleFlowStrategy") as simple_cls:
        worker.run()

    simple_cls.assert_called_once()
    compare_cls.assert_not_called()
