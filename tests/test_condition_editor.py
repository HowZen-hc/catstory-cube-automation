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
