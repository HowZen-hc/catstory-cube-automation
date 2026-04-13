from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from app.gui.main_window import MainWindow


@pytest.fixture()
def window(qapp):
    w = MainWindow()
    yield w
    w.close()


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
