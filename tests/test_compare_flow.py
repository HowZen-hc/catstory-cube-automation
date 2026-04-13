"""Unit tests for CompareFlowStrategy's before-OCR caching behavior."""
from unittest.mock import MagicMock, patch

import pytest

from app.cube.compare_flow import CompareFlowStrategy
from app.cube.simple_flow import SimpleFlowStrategy
from app.models.potential import PotentialLine


def _make_strategy(cls):
    """Build strategy with mocked dependencies. Override _read_potential per test."""
    config = MagicMock()
    config.potential_region.is_set.return_value = False
    config.cube_type = "恢復附加方塊 (紅色)"
    config.delay_ms = 0

    screen = MagicMock()
    ocr = MagicMock()
    mouse = MagicMock()
    checker = MagicMock()
    checker.check.return_value = False
    log_session = MagicMock()

    return cls(config, screen, ocr, mouse, checker, log_session)


def _line(attr: str, value: int) -> PotentialLine:
    return PotentialLine(attribute=attr, value=value, raw_text=f"{attr}+{value}%")


@pytest.fixture
def strategy():
    s = _make_strategy(CompareFlowStrategy)
    s._read_potential = MagicMock(return_value=[_line("OCR", 1)])
    return s


def test_seed_skips_first_before_ocr(strategy):
    """Seeded initial potential must be used as before_lines, skipping OCR."""
    seeded = [_line("STR", 9), _line("DEX", 3)]
    strategy.seed_initial_potential(seeded)

    strategy.execute_roll(1)

    # 1 call only: for after_lines. before_lines came from cache.
    assert strategy._read_potential.call_count == 1


def test_without_seed_first_roll_reads_twice(strategy):
    """No seed → first roll must OCR both before and after."""
    strategy.execute_roll(1)

    assert strategy._read_potential.call_count == 2


def test_cache_updated_after_roll(strategy):
    """Cache must be after_lines, not before_lines — use distinct values to prove it."""
    seeded_before = [_line("STR", 42)]
    after = [_line("LUK", 7)]
    strategy._read_potential = MagicMock(return_value=after)
    strategy.seed_initial_potential(seeded_before)

    strategy.execute_roll(1)

    assert strategy._last_lines == after
    assert strategy._last_lines != seeded_before


def test_second_roll_reuses_cached_after(strategy):
    """Second roll's before_lines should come from previous after, no extra OCR."""
    strategy.seed_initial_potential([_line("STR", 9)])

    strategy.execute_roll(1)
    strategy.execute_roll(2)

    # 2 rolls × 1 after OCR each = 2 calls. before_lines cached both times.
    assert strategy._read_potential.call_count == 2


@pytest.mark.parametrize("is_better_result", [True, False])
def test_keep_or_cancel_todo_does_not_break_cache(strategy, is_better_result):
    """Both _is_better branches must cache after_lines while TODO click is unimplemented.
    When click is implemented, cancel branch must switch to before_lines (see step 7 comment)."""
    after = [_line("INT", 5)]
    strategy._read_potential = MagicMock(return_value=after)
    strategy._is_better = MagicMock(return_value=is_better_result)
    strategy.seed_initial_potential([_line("INT", 99)])

    strategy.execute_roll(1)

    assert strategy._is_better.call_count == 1
    assert strategy._last_lines == after


def test_simple_flow_seed_is_noop():
    """SimpleFlow inherits base no-op seed — must return None and not change execute_roll behavior."""
    s = _make_strategy(SimpleFlowStrategy)

    # Contract: seed_initial_potential returns None and must not raise
    assert s.seed_initial_potential([_line("STR", 9)]) is None

    # Behavior: execute_roll still performs exactly one OCR (no before/after split like CompareFlow)
    s._read_potential = None  # SimpleFlow doesn't use _read_potential helper; use inline capture instead
    s.screen.capture = MagicMock(return_value=b"img")
    s.config.potential_region.is_set.return_value = True
    with patch("app.cube.simple_flow.get_scale_factor", return_value=1.0), \
         patch("app.cube.simple_flow.get_num_lines", return_value=3), \
         patch("app.cube.simple_flow.parse_potential_lines", return_value=[]):
        s.execute_roll(1)

    # One capture call = one OCR. Seed had no effect on flow.
    assert s.screen.capture.call_count == 1
