"""ConditionEditor GUI tests.

Covers helpers extracted during the refactor
(`_sync_subtype_checks`, `_toggle_subtype_mutex`, `_clear_custom_rows`,
`_build_line_conditions`) and the `apply_to_config` / `load_from_config`
serialization roundtrip.
"""
from unittest.mock import patch

import pytest

from app.gui.condition_editor import ConditionEditor
from app.models.config import AppConfig, LineCondition

_DEFAULT_CUBE = "珍貴附加方塊 (粉紅色)"  # 3-line cube
_GEAR_EQUIP = "永恆 / 光輝"
_NON_GEAR_EQUIP = "主武器 / 徽章 (米特拉)"


@pytest.fixture()
def editor(qapp):
    e = ConditionEditor()
    e.on_cube_type_changed(_DEFAULT_CUBE)
    yield e
    e.close()


class TestSubtypeCheckboxLabels:
    """Phase 2 (R4) AC-8 / Signal 7.4 / Signal 2.1.2: UI label + tooltip 斷言。"""

    def test_glove_check_label(self, editor):
        assert editor.glove_check.text() == "手套"

    def test_hat_check_label_renamed_to_cooldown_hat(self, editor):
        """FR-7: UI label「帽子」→「冷卻帽」（Signal 7.4 widget text 斷言）。"""
        assert editor.hat_check.text() == "冷卻帽"

    def test_checkbox_tooltip_covers_required_tokens(self, editor):
        """Signal 2.1.2: tooltip 文案含「爆擊」、「冷卻」與「三排」或「同屬」。"""
        tip = editor.hat_check.toolTip()
        assert tip == editor.glove_check.toolTip()
        assert "爆擊" in tip
        assert "冷卻" in tip
        assert ("三排" in tip) or ("同屬" in tip)


def _pick_position(row, position):
    idx = row.position_combo.findData(position)
    assert idx >= 0, f"position {position} not found in combo"
    row.position_combo.setCurrentIndex(idx)


class TestBuildLineConditions:
    def test_single_row_matches_widget_state(self, editor):
        editor.equip_combo.setCurrentText(_GEAR_EQUIP)
        editor.mode_combo.setCurrentText("自訂條件")
        assert editor._custom_rows, "custom mode must have at least one row"
        row = editor._custom_rows[0]
        row.attr_combo.setCurrentText("STR")
        row.value_spin.setValue(7)
        _pick_position(row, 1)

        lines = editor._build_line_conditions()

        assert lines == [LineCondition(attribute="STR", min_value=7, position=1)]

    def test_multi_row_preserves_order_and_positions(self, editor):
        editor.equip_combo.setCurrentText(_GEAR_EQUIP)
        editor.mode_combo.setCurrentText("自訂條件")
        editor._add_custom_row()
        assert len(editor._custom_rows) == 2
        first, second = editor._custom_rows
        first.attr_combo.setCurrentText("STR")
        first.value_spin.setValue(5)
        _pick_position(first, 2)
        second.attr_combo.setCurrentText("DEX")
        second.value_spin.setValue(6)
        _pick_position(second, 0)

        lines = editor._build_line_conditions()

        assert lines == [
            LineCondition(attribute="STR", min_value=5, position=2),
            LineCondition(attribute="DEX", min_value=6, position=0),
        ]

    def test_position_none_falls_back_to_zero(self, editor):
        editor.equip_combo.setCurrentText(_GEAR_EQUIP)
        editor.mode_combo.setCurrentText("自訂條件")
        row = editor._custom_rows[0]
        # blockSignals isolates the fallback contract from _on_position_changed
        row.position_combo.blockSignals(True)
        row.position_combo.clear()
        row.position_combo.blockSignals(False)

        lines = editor._build_line_conditions()

        assert len(lines) == 1
        assert lines[0].position == 0


class TestApplyLoadRoundtrip:
    def test_custom_lines_survive_roundtrip(self, editor):
        src = AppConfig(
            cube_type=_DEFAULT_CUBE,
            equipment_type=_GEAR_EQUIP,
            use_preset=False,
            custom_lines=[
                LineCondition(attribute="STR", min_value=7, position=1),
                LineCondition(attribute="DEX", min_value=6, position=0),
                LineCondition(attribute="MaxHP", min_value=10, position=2),
            ],
        )

        editor.on_cube_type_changed(src.cube_type)
        editor.load_from_config(src)
        dst = AppConfig()
        editor.apply_to_config(dst)

        assert dst.use_preset is False
        assert dst.equipment_type == _GEAR_EQUIP
        assert dst.custom_lines == src.custom_lines

    def test_preset_with_glove_flag_survives_roundtrip(self, editor):
        src = AppConfig(
            cube_type=_DEFAULT_CUBE,
            equipment_type=_GEAR_EQUIP,
            target_attribute="STR",
            is_glove=True,
            is_hat=False,
            use_preset=True,
        )

        editor.on_cube_type_changed(src.cube_type)
        editor.load_from_config(src)
        dst = AppConfig()
        editor.apply_to_config(dst)

        assert dst.use_preset is True
        assert dst.is_glove is True
        assert dst.is_hat is False
        assert editor.hat_check.isEnabled() is False
        assert editor.glove_check.isEnabled() is True

    def test_preset_with_glove_survives_roundtrip_when_load_switches_gear_equip(self, editor):
        """Regression: `_on_equip_changed` now unconditionally clears glove/hat
        on any equip switch. `load_from_config` restores flags via
        `_sync_subtype_checks` *after* the equip change signal fires, so a saved
        (equip=一般裝備, is_glove=True) config must still round-trip correctly
        even though editor default equip is 永恆 / 光輝 (switch fires signal)."""
        src = AppConfig(
            cube_type=_DEFAULT_CUBE,
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
            target_attribute="STR",
            is_glove=True,
            is_hat=False,
            use_preset=True,
        )

        editor.on_cube_type_changed(src.cube_type)
        # sanity: default equip differs from src so load triggers _on_equip_changed
        assert editor.equip_combo.currentText() != src.equipment_type
        editor.load_from_config(src)
        dst = AppConfig()
        editor.apply_to_config(dst)

        assert dst.equipment_type == src.equipment_type
        assert dst.is_glove is True
        assert dst.is_hat is False
        assert editor.glove_check.isChecked() is True
        assert editor.hat_check.isEnabled() is False

    def test_empty_custom_lines_creates_default_row(self, editor):
        src = AppConfig(
            cube_type=_DEFAULT_CUBE,
            equipment_type=_GEAR_EQUIP,
            use_preset=False,
            custom_lines=[],
        )

        editor.on_cube_type_changed(src.cube_type)
        editor.load_from_config(src)

        assert len(editor._custom_rows) == 1

    def test_custom_lines_exceeding_max_rows_are_truncated(self, editor):
        max_rows = editor._max_rows()
        oversized = [
            LineCondition(attribute="STR", min_value=i + 1, position=0)
            for i in range(max_rows + 3)
        ]
        src = AppConfig(
            cube_type=_DEFAULT_CUBE,
            equipment_type=_GEAR_EQUIP,
            use_preset=False,
            custom_lines=oversized,
        )

        editor.on_cube_type_changed(src.cube_type)
        editor.load_from_config(src)
        dst = AppConfig()
        editor.apply_to_config(dst)

        assert dst.custom_lines == oversized[:max_rows]


class TestSyncSubtypeChecks:
    def test_glove_true_disables_hat(self, editor):
        editor._sync_subtype_checks(is_glove=True, is_hat=False)

        assert editor.glove_check.isChecked() is True
        assert editor.hat_check.isChecked() is False
        assert editor.glove_check.isEnabled() is True
        assert editor.hat_check.isEnabled() is False

    def test_hat_true_disables_glove(self, editor):
        editor._sync_subtype_checks(is_glove=False, is_hat=True)

        assert editor.hat_check.isChecked() is True
        assert editor.glove_check.isChecked() is False
        assert editor.hat_check.isEnabled() is True
        assert editor.glove_check.isEnabled() is False

    def test_does_not_trigger_toggle_handlers(self, editor):
        """Signal silence: _sync must not trigger _on_*_toggled -> _reset_custom_rows loop."""
        with patch.object(editor, "_reset_custom_rows") as reset_spy, \
             patch.object(editor, "_update_summary") as summary_spy:
            editor._sync_subtype_checks(is_glove=True, is_hat=False)

        reset_spy.assert_not_called()
        summary_spy.assert_not_called()


_GEAR_EQUIP_ALT = "一般裝備 (神秘、漆黑、頂培)"


class TestResetSubtypeChecks:
    def test_switching_to_non_gear_clears_and_reenables_both(self, editor):
        editor.equip_combo.setCurrentText(_GEAR_EQUIP)
        editor.glove_check.setChecked(True)
        assert editor.hat_check.isEnabled() is False

        editor.equip_combo.setCurrentText(_NON_GEAR_EQUIP)

        assert editor.glove_check.isChecked() is False
        assert editor.hat_check.isChecked() is False
        assert editor.glove_check.isEnabled() is True
        assert editor.hat_check.isEnabled() is True

    def test_switching_between_gear_equips_also_clears(self, editor):
        """Regression: gear ↔ gear 切換（永恆 / 光輝 ↔ 一般裝備）也必須清空
        glove / hat 勾選狀態，避免殘留造成用戶誤以為配置仍存在。"""
        editor.equip_combo.setCurrentText(_GEAR_EQUIP)
        editor.glove_check.setChecked(True)
        assert editor.glove_check.isChecked() is True

        editor.equip_combo.setCurrentText(_GEAR_EQUIP_ALT)

        assert editor.glove_check.isChecked() is False
        assert editor.hat_check.isChecked() is False
        assert editor.glove_check.isEnabled() is True
        assert editor.hat_check.isEnabled() is True


class TestCubeTypeChangeRefreshesSummary:
    def test_summary_updates_when_cube_type_changes(self, editor):
        """Regression: switching cube type must refresh summary even when equip / mode
        settle back to identical widget values (no child signal would fire).

        Preconditions: equip/mode already at defaults so `_reset_to_defaults`
        produces no-op setCurrentText calls — the summary can only refresh if
        `on_cube_type_changed` calls `_update_summary` explicitly.
        """
        editor.equip_combo.setCurrentIndex(0)
        editor.mode_combo.setCurrentText("預設規則")
        before = editor.summary_label.text()
        assert "僅支援" not in before  # 珍貴附加 uses preset rules, not whitelist wording

        editor.on_cube_type_changed("絕對附加方塊 (僅洗兩排)")

        assert editor._cube_type == "絕對附加方塊 (僅洗兩排)"
        after = editor.summary_label.text()
        assert after != before
        assert "僅支援" in after  # absolute-cube whitelist wording (FR-22)


class TestToggleSubtypeMutex:
    def test_checking_glove_disables_hat_and_rebuilds_rows(self, editor):
        editor.equip_combo.setCurrentText(_GEAR_EQUIP)
        editor._add_custom_row()
        assert len(editor._custom_rows) == 2

        editor.glove_check.setChecked(True)  # signal-driven path

        assert editor.hat_check.isEnabled() is False
        assert editor.hat_check.isChecked() is False
        # _toggle_subtype_mutex side effect: _reset_custom_rows rebuilds to 1 row
        assert len(editor._custom_rows) == 1

    def test_unchecking_glove_reenables_hat_and_rebuilds_rows(self, editor):
        editor.equip_combo.setCurrentText(_GEAR_EQUIP)
        editor.glove_check.setChecked(True)
        editor._add_custom_row()
        assert len(editor._custom_rows) == 2

        editor.glove_check.setChecked(False)

        assert editor.hat_check.isEnabled() is True
        # _toggle_subtype_mutex side effect applies on uncheck path too
        assert len(editor._custom_rows) == 1
