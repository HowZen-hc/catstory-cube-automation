from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.settings_panel import SettingsPanel
from app.models.config import AppConfig


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
