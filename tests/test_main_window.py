from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox

from app.gui.main_window import MainWindow
from app.gui.settings_panel import SettingsPanel
from app.models.config import AppConfig, Region
from app.models.potential import PotentialLine, RollResult


@pytest.fixture()
def window(qapp):
    w = MainWindow()
    yield w
    w.close()


@pytest.fixture()
def settings_panel(qapp):
    p = SettingsPanel()
    yield p
    p.close()


class TestOnTargetReached:
    def test_calls_worker_stop(self, window):
        """When target is reached, worker.stop() must be called to prevent
        the automation from continuing after the dialog is dismissed."""
        mock_worker = MagicMock()
        window._worker = mock_worker

        with patch.object(QApplication, "beep"), patch(
            "app.gui.main_window.QMessageBox"
        ):
            window._on_target_reached(5)

        mock_worker.stop.assert_called_once()

    def test_no_crash_without_worker(self, window):
        """Should not crash if _worker is None when target is reached."""
        window._worker = None

        with patch.object(QApplication, "beep"), patch(
            "app.gui.main_window.QMessageBox"
        ):
            window._on_target_reached(0)

    def test_roll_count_zero_shows_manual_confirm_hint(self, window):
        """roll_count=0 (initial match, no click fired) must warn the user
        to manually confirm in-game if the before/after dialog is still up."""
        window._worker = None

        with patch.object(QApplication, "beep"), patch(
            "app.gui.main_window.QMessageBox"
        ) as mock_msgbox:
            window._on_target_reached(0)

        _args, _ = mock_msgbox.information.call_args
        message = _args[2]
        assert "未執行任何洗方塊動作" in message
        assert "請手動" in message

    def test_roll_count_positive_shows_standard_message(self, window):
        """roll_count>0 (rolled and matched) keeps the original success copy,
        no manual-confirm hint (script already clicked)."""
        window._worker = None

        with patch.object(QApplication, "beep"), patch(
            "app.gui.main_window.QMessageBox"
        ) as mock_msgbox:
            window._on_target_reached(3)

        _args, _ = mock_msgbox.information.call_args
        message = _args[2]
        assert message == "達成目標！共洗 3 次"


class TestGpuSectionRemoved:
    """R5 AC-1..AC-5 / Signal 7.1.a / 7.1.b: GPU section must be absent from UI
    and config read/write, while AppConfig.use_gpu field remains (per A7)."""

    def test_gpu_checkbox_attr_absent(self, settings_panel):
        """Signal 7.1.a: SettingsPanel no longer exposes gpu_checkbox."""
        assert hasattr(settings_panel, "gpu_checkbox") is False

    def test_load_persistent_from_config_removed(self):
        """Signal 7.1.b: the obsolete method is gone so callers cannot read
        config.use_gpu through it."""
        assert not hasattr(SettingsPanel, "load_persistent_from_config")

    def test_apply_to_config_does_not_write_use_gpu(self, settings_panel):
        """Signal 7.1.b: apply_to_config must not mutate config.use_gpu."""
        config = AppConfig(use_gpu=True)
        settings_panel.apply_to_config(config)
        assert config.use_gpu is True  # untouched by apply_to_config

    def test_appconfig_use_gpu_field_preserved(self):
        """A7: AppConfig.use_gpu dataclass field保留以避免 OCR 引擎引用破壞。"""
        assert hasattr(AppConfig(), "use_gpu")


class TestUpdateButtonStyle:
    """R6 AC-1 / Signal 7.2: 檢查更新按鈕可辨識為按鈕。"""

    def test_button_not_flat(self, window):
        assert window.btn_check_update.isFlat() is False

    def test_button_has_stylesheet(self, window):
        assert window.btn_check_update.styleSheet() != ""

    def test_button_stylesheet_has_border_and_background(self, window):
        """FR-27 機械驗收：非預設 QSS 至少含 border 與 background-color。"""
        qss = window.btn_check_update.styleSheet()
        assert "border" in qss
        assert "background-color" in qss

    def test_button_stylesheet_covers_interactive_states(self, window):
        """FR-27: QSS 需鎖定 hover / pressed / disabled 三態，避免靜態樣式
        退化（只有 normal 態會讓按鈕沒有視覺回饋）。"""
        qss = window.btn_check_update.styleSheet()
        assert "QPushButton:hover" in qss
        assert "QPushButton:pressed" in qss
        assert "QPushButton:disabled" in qss


class TestResolutionHint:
    """R6 AC-3 / Signal 7.3: 解析度提示 label 存在且文字包含 1920/1080。"""

    def test_resolution_hint_exists(self, window):
        assert hasattr(window, "resolution_hint")

    def test_resolution_hint_text_contains_recommended_resolution(self, window):
        text = window.resolution_hint.text()
        assert "1920" in text
        assert "1080" in text

    def test_resolution_hint_uses_info_blue_hint_style(self, window):
        """資訊色藍（#1976d2）+ 12px：比 gray delay_hint 顯眼，
        但仍低於 red region_hint / orange anim_hint 的警告等級。"""
        qss = window.resolution_hint.styleSheet().lower()
        assert "#1976d2" in qss
        assert "12px" in qss
        # 警告色保留給其他 hint，不能用於解析度提示
        assert "red" not in qss
        assert "#e65100" not in qss


class TestRegionSelection:
    """_on_select_potential_region + _set_potential_region + _on_cube_type_changed."""

    def test_select_potential_region_opens_region_selector(self, window):
        with patch("app.gui.main_window.RegionSelector") as rs_cls:
            rs_inst = MagicMock()
            rs_cls.return_value = rs_inst
            window._on_select_potential_region()
            rs_inst.show.assert_called_once()
            rs_inst.region_selected.connect.assert_called_once()

    def test_set_potential_region_enables_buttons_and_updates_status(self, window):
        region = Region(x=10, y=20, width=30, height=40)
        window._set_potential_region(region)

        assert window.config.potential_region is region
        assert window.btn_start.isEnabled() is True
        assert window.btn_ocr_test.isEnabled() is True
        # setVisible(False) → isHidden() is True（offscreen 下 isVisible 恆為 False）
        assert window.settings_panel.region_hint.isHidden() is True
        assert "10" in window.status_bar.currentMessage()

    def test_cube_type_changed_resets_region_after_ui_loaded(self, window):
        """UI 載入完畢後切換方塊類型 → 清 region + 停用按鈕 + 顯示 hint。"""
        window._set_potential_region(Region(x=1, y=2, width=3, height=4))
        assert window.btn_start.isEnabled() is True
        # offscreen 模式下 isVisible() 為 False（視窗未 show()），改用 isHidden() 判斷
        window.settings_panel.region_hint.setVisible(False)
        assert window.settings_panel.region_hint.isHidden() is True

        window._on_cube_type_changed("萌獸方塊")

        assert window.config.potential_region.is_set() is False
        assert window.btn_start.isEnabled() is False
        assert window.btn_ocr_test.isEnabled() is False
        assert window.settings_panel.region_hint.isHidden() is False
        assert "切換方塊類型" in window.status_bar.currentMessage()

    def test_cube_type_changed_noop_before_ui_loaded(self, window):
        """_ui_loaded=False 時不得清 region（避免 __init__ 階段誤清）。"""
        window._set_potential_region(Region(x=1, y=2, width=3, height=4))
        window._ui_loaded = False

        window._on_cube_type_changed("萌獸方塊")

        assert window.config.potential_region.is_set() is True


class TestStartAndOcrTest:
    """_on_start + _on_ocr_test：region 驗證、worker 建立、signal 連線。"""

    def test_start_warns_when_region_unset(self, window):
        window.config.potential_region = Region()  # unset
        with patch("app.gui.main_window.QMessageBox") as mb:
            window._on_start()
            mb.warning.assert_called_once()
        assert window._worker is None

    def test_start_creates_worker_and_sets_running_ui(self, window):
        window._set_potential_region(Region(x=0, y=0, width=100, height=100))
        with patch("app.gui.main_window.AutomationWorker") as worker_cls, \
             patch.object(window.config, "save"):
            worker_inst = MagicMock()
            worker_cls.return_value = worker_inst
            window._on_start()

        assert window._worker is worker_inst
        worker_inst.start.assert_called_once()
        # signal 連線到正確的 slot（避免錯接而不被察覺）
        worker_inst.roll_completed.connect.assert_called_once_with(window._on_roll_completed)
        worker_inst.status_changed.connect.assert_called_once_with(window._on_status_changed)
        worker_inst.error_occurred.connect.assert_called_once_with(window._on_error)
        worker_inst.target_reached.connect.assert_called_once_with(window._on_target_reached)
        worker_inst.finished.connect.assert_called_once_with(window._on_worker_finished)
        assert window.btn_stop.isEnabled() is True
        assert window._ocr_test_mode is False

    def test_ocr_test_warns_when_region_unset(self, window):
        window.config.potential_region = Region()
        with patch("app.gui.main_window.QMessageBox") as mb:
            window._on_ocr_test()
            mb.warning.assert_called_once()

    def test_ocr_test_creates_ocr_test_worker(self, window):
        window._set_potential_region(Region(x=0, y=0, width=10, height=10))
        with patch("app.gui.main_window.OCRTestWorker") as worker_cls:
            worker_inst = MagicMock()
            worker_cls.return_value = worker_inst
            window._on_ocr_test()

        assert window._worker is worker_inst
        assert window._ocr_test_mode is True
        worker_inst.start.assert_called_once()


class TestLogAndStopHandlers:
    def test_clear_log_resets_counter_and_label(self, window):
        window._roll_count = 5
        window.count_label.setText("次數: 5")

        window._on_clear_log()

        assert window._roll_count == 0
        assert window.count_label.text() == "次數: 0"

    def test_stop_calls_worker_stop_and_disables_button(self, window):
        mock_worker = MagicMock()
        window._worker = mock_worker

        window._on_stop()

        mock_worker.stop.assert_called_once()
        assert window.btn_stop.isEnabled() is False
        assert "停止中" in window.btn_stop.text()

    def test_stop_noop_when_no_worker(self, window):
        window._worker = None
        window._on_stop()  # must not crash
        assert window.btn_stop.isEnabled() is False

    def test_roll_completed_increments_counter_for_positive_roll(self, window):
        window._roll_count = 0
        result = RollResult(roll_number=3, lines=[PotentialLine("STR", 9)], matched=False)

        window._on_roll_completed(result)

        assert window._roll_count == 1
        assert window.count_label.text() == "次數: 1"

    def test_roll_completed_skips_counter_for_initial_roll_zero(self, window):
        """roll_number=0 是啟動 OCR 結果，不計入洗方塊次數。"""
        window._roll_count = 0
        result = RollResult(roll_number=0, lines=[], matched=True)

        window._on_roll_completed(result)

        assert window._roll_count == 0

    def test_status_changed_shows_message(self, window):
        window._on_status_changed("hello")
        assert window.status_bar.currentMessage() == "hello"

    def test_error_shows_message_in_status_bar(self, window):
        window._on_error("boom")
        assert "boom" in window.status_bar.currentMessage()


class TestWorkerFinishedAndUI:
    def test_worker_finished_automation_mode_shows_count(self, window):
        window._ocr_test_mode = False
        window._roll_count = 7

        with patch("app.gui.main_window.QTimer.singleShot"):
            window._on_worker_finished()

        assert "7 次" in window.status_bar.currentMessage()
        assert "已停止" in window.btn_start.text()

    def test_worker_finished_ocr_test_mode_shows_ocr_msg(self, window):
        window._ocr_test_mode = True
        window._roll_count = 2

        with patch("app.gui.main_window.QTimer.singleShot"):
            window._on_worker_finished()

        assert "OCR 測試" in window.status_bar.currentMessage()

    def test_restore_start_btn_clears_style_and_text(self, window):
        window.btn_start.setText("■ 已停止")
        window.btn_start.setStyleSheet("background-color: red;")

        window._restore_start_btn()

        assert window.btn_start.text() == "▶ 開始"
        assert window.btn_start.styleSheet() == ""

    def test_set_running_true_disables_panels_and_updates_start_button(self, window):
        window._set_potential_region(Region(x=0, y=0, width=10, height=10))
        window._set_running_ui(True)

        assert window.btn_start.isEnabled() is False
        assert window.btn_stop.isEnabled() is True
        assert window.settings_panel.isEnabled() is False
        assert window.condition_editor.isEnabled() is False
        assert "執行中" in window.btn_start.text()

    def test_set_running_false_reenables_panels_when_region_set(self, window):
        window._set_potential_region(Region(x=0, y=0, width=10, height=10))
        window._set_running_ui(False)

        assert window.btn_start.isEnabled() is True
        assert window.btn_ocr_test.isEnabled() is True
        assert window.btn_stop.isEnabled() is False
        assert window.settings_panel.isEnabled() is True

    def test_set_running_false_keeps_start_disabled_when_no_region(self, window):
        window.config.potential_region = Region()
        window._set_running_ui(False)

        assert window.btn_start.isEnabled() is False
        assert window.btn_ocr_test.isEnabled() is False


class TestUpdateCheckFlow:
    """版本檢查的 4 個 slot: _on_check_update / _on_update_result / _on_update_error / _on_update_finished."""

    def test_check_update_starts_worker_once(self, window):
        with patch("app.gui.main_window._UpdateCheckWorker") as worker_cls:
            worker_inst = MagicMock()
            worker_inst.isRunning.return_value = False
            worker_cls.return_value = worker_inst
            window._on_check_update()

        worker_inst.start.assert_called_once()
        assert window.btn_check_update.isEnabled() is False
        assert "檢查中" in window.btn_check_update.text()

    def test_check_update_ignores_when_already_running(self, window):
        running_worker = MagicMock()
        running_worker.isRunning.return_value = True
        window._update_worker = running_worker

        with patch("app.gui.main_window._UpdateCheckWorker") as worker_cls:
            window._on_check_update()

        worker_cls.assert_not_called()

    def test_update_result_has_update_user_declines(self, window):
        """patch QMessageBox.question 而非整個 class，讓 StandardButton 保持真實枚舉。"""
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No), \
             patch("app.gui.main_window.QDesktopServices.openUrl") as open_url:
            window._on_update_result(True, "1.0.0")

        assert window.btn_check_update.isEnabled() is True
        open_url.assert_not_called()

    def test_update_result_has_update_user_accepts_opens_url(self, window):
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes), \
             patch("app.gui.main_window.QDesktopServices.openUrl") as open_url:
            window._on_update_result(True, "1.0.0")

        open_url.assert_called_once()

    def test_update_result_no_update_shows_info(self, window):
        with patch("app.gui.main_window.QMessageBox") as mb:
            window._on_update_result(False, "")

        mb.information.assert_called_once()

    def test_update_error_logs_warning_and_reenables_button(self, window):
        window.btn_check_update.setEnabled(False)
        with patch("app.gui.main_window.QMessageBox") as mb:
            window._on_update_error("network down")

        assert window.btn_check_update.isEnabled() is True
        mb.warning.assert_called_once()

    def test_update_finished_clears_worker_ref(self, window):
        window._update_worker = MagicMock()
        window._on_update_finished()
        assert window._update_worker is None


class TestUpdateCheckWorkerRun:
    """_UpdateCheckWorker.run — emits result_ready on success, error_occurred on exception."""

    def test_run_emits_result_ready_on_success(self):
        from app.gui.main_window import _UpdateCheckWorker

        worker = _UpdateCheckWorker()
        received: list[tuple[bool, str]] = []
        errors: list[str] = []
        worker.result_ready.connect(lambda h, v: received.append((h, v)))
        worker.error_occurred.connect(errors.append)

        with patch("app.gui.main_window.check_for_update", return_value=(True, "9.9.9")):
            worker.run()

        assert received == [(True, "9.9.9")]
        assert errors == []

    def test_run_emits_error_occurred_on_exception(self):
        from app.gui.main_window import _UpdateCheckWorker

        worker = _UpdateCheckWorker()
        received: list[tuple[bool, str]] = []
        errors: list[str] = []
        worker.result_ready.connect(lambda h, v: received.append((h, v)))
        worker.error_occurred.connect(errors.append)

        with patch("app.gui.main_window.check_for_update", side_effect=RuntimeError("net")):
            worker.run()

        assert received == []
        assert len(errors) == 1
        assert "net" in errors[0]
