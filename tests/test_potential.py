"""Unit tests for PotentialLine / RollResult / format_line."""
from app.models.potential import PotentialLine, RollResult, format_line


def test_format_line_unknown_attribute():
    assert format_line(PotentialLine(attribute="未知", value=0)) == "(未辨識)"


def test_format_line_zero_value_returns_bare_attribute():
    """value=0 → 純屬性名（去掉 + 與數值）。"""
    assert format_line(PotentialLine(attribute="STR%", value=0)) == "STR%"


def test_format_line_percent_suffix_strips_and_formats():
    """屬性以 % 結尾 → 去 %、加 +X%。"""
    assert format_line(PotentialLine(attribute="STR%", value=9)) == "STR +9%"


def test_format_line_cooldown_uses_minus_seconds():
    """技能冷卻時間 → -N 秒（不是 +）。"""
    assert format_line(PotentialLine(attribute="技能冷卻時間", value=1)) == "技能冷卻時間 -1秒"


def test_format_line_non_percent_integer_attribute():
    """整數型屬性（例如 HP）→ +N，無 %、無秒。"""
    assert format_line(PotentialLine(attribute="最大HP", value=12)) == "最大HP +12"


def test_rollresult_summary_joins_lines_with_slash():
    """multi lines → ` / ` 連接，各 line 走 format_line。"""
    result = RollResult(
        roll_number=1,
        lines=[
            PotentialLine(attribute="STR%", value=9),
            PotentialLine(attribute="技能冷卻時間", value=1),
        ],
    )
    assert result.summary() == "STR +9% / 技能冷卻時間 -1秒"


def test_rollresult_summary_empty_lines_returns_empty_string():
    assert RollResult(roll_number=0).summary() == ""
