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


def test_seed_on_simple_flow_is_harmless_noop():
    """SimpleFlow uses base class no-op seed — still called, but does nothing."""
    cfg = _make_config("珍貴附加方塊 (粉紅色)", region_set=True)
    strategy = _run_worker(cfg, matched=False)

    # Seed is called uniformly regardless of strategy type (base class handles no-op)
    strategy.seed_initial_potential.assert_called_once_with(["seeded-lines"])
