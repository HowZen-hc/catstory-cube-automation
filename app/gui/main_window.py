import logging

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.core.automation import AutomationWorker
from app.core.ocr_test_worker import OCRTestWorker
from app.gui.condition_editor import ConditionEditor
from app.gui.region_selector import RegionSelector
from app.gui.roll_log import RollLog
from app.gui.settings_panel import SettingsPanel
from app.models.config import AppConfig, Region
from app.models.potential import RollResult

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = AppConfig.load()
        self._worker: AutomationWorker | OCRTestWorker | None = None
        self._ocr_test_mode = False
        self._roll_count = 0
        self._ui_loaded = False
        self._init_ui()
        self._load_config_to_ui()
        self._ui_loaded = True

    def _init_ui(self) -> None:
        self.setWindowTitle("新楓之谷自動洗方塊")
        self.setMinimumSize(500, 750)

        central = QWidget()
        layout = QVBoxLayout()

        # 設定面板
        self.settings_panel = SettingsPanel()
        self.settings_panel.select_potential_region.connect(
            self._on_select_potential_region
        )
        layout.addWidget(self.settings_panel)

        # 條件編輯器
        self.condition_editor = ConditionEditor()
        self.settings_panel.cube_type_changed.connect(
            self.condition_editor.on_cube_type_changed
        )
        self.settings_panel.cube_type_changed.connect(self._on_cube_type_changed)
        layout.addWidget(self.condition_editor)

        # 控制列
        control_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ 開始")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self._on_start)
        control_layout.addWidget(self.btn_start)

        self.btn_ocr_test = QPushButton("🔍 測試 OCR")
        self.btn_ocr_test.setEnabled(False)
        self.btn_ocr_test.clicked.connect(self._on_ocr_test)
        control_layout.addWidget(self.btn_ocr_test)

        self.btn_stop = QPushButton("■ 停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._on_stop)
        control_layout.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("清除紀錄")
        self.btn_clear.clicked.connect(self._on_clear_log)
        control_layout.addWidget(self.btn_clear)

        self.count_label = QLabel("次數: 0")
        control_layout.addWidget(self.count_label)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 洗方塊紀錄
        self.roll_log = RollLog()
        layout.addWidget(self.roll_log)

        central.setLayout(layout)
        self.setCentralWidget(central)

        # 狀態列
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就緒")

    def _on_select_potential_region(self) -> None:
        self._region_selector = RegionSelector()
        self._region_selector.region_selected.connect(self._set_potential_region)
        self._region_selector.show()

    def _on_cube_type_changed(self, _cube_type: str) -> None:
        """切換方塊類型時清除潛能區域，要求重新框選。"""
        if not self._ui_loaded:
            return
        self.config.potential_region = Region()
        self.btn_start.setEnabled(False)
        self.btn_ocr_test.setEnabled(False)
        self.settings_panel.region_hint.setVisible(True)
        self.status_bar.showMessage("已切換方塊類型，請重新框選潛能區域")

    def _set_potential_region(self, region: Region) -> None:
        self.config.potential_region = region
        self.btn_start.setEnabled(True)
        self.btn_ocr_test.setEnabled(True)
        self.settings_panel.region_hint.setVisible(False)
        self.status_bar.showMessage(
            f"潛能區域已設定: ({region.x}, {region.y}, {region.width}x{region.height})"
        )

    def _load_config_to_ui(self) -> None:
        # 只載入持久性設定（區域、延遲），下拉選單保持 UI 預設值
        self.settings_panel.load_persistent_from_config(self.config)
        # 用 UI 預設的方塊類型觸發萌獸連動
        self.condition_editor.on_cube_type_changed(
            self.settings_panel.cube_type_combo.currentText()
        )
        # 每次啟動都清除潛能區域，要求重新框選
        self.config.potential_region = Region()

    def _on_start(self) -> None:
        self.settings_panel.apply_to_config(self.config)
        self.condition_editor.apply_to_config(self.config)

        # 驗證必要設定
        if not self.config.potential_region.is_set():
            QMessageBox.warning(self, "設定不完整", "請先框選潛能區域")
            return

        self._on_clear_log()
        self._ocr_test_mode = False
        self.config.save()

        self._worker = AutomationWorker(self.config)
        self._worker.roll_completed.connect(self._on_roll_completed)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.target_reached.connect(self._on_target_reached)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

        self._set_running_ui(True)

    def _on_ocr_test(self) -> None:
        self.settings_panel.apply_to_config(self.config)
        self.condition_editor.apply_to_config(self.config)

        if not self.config.potential_region.is_set():
            QMessageBox.warning(self, "設定不完整", "請先框選潛能區域")
            return

        self._on_clear_log()
        self._ocr_test_mode = True

        self._worker = OCRTestWorker(self.config)
        self._worker.roll_completed.connect(self._on_roll_completed)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

        self._set_running_ui(True)

    def _on_clear_log(self) -> None:
        self.roll_log.clear_log()
        self._roll_count = 0
        self.count_label.setText("次數: 0")

    def _on_stop(self) -> None:
        logger.info("使用者按下停止按鈕")
        if self._worker:
            self._worker.stop()
        self.btn_stop.setEnabled(False)
        self.btn_stop.setText("⏹ 停止中...")
        self.btn_stop.setStyleSheet("background-color: #e53935; color: white;")
        self.status_bar.showMessage("正在停止...")

    def _on_roll_completed(self, result: RollResult) -> None:
        if result.roll_number > 0:
            self._roll_count += 1
            self.count_label.setText(f"次數: {self._roll_count}")
        self.roll_log.add_result(result)

    def _on_status_changed(self, msg: str) -> None:
        self.status_bar.showMessage(msg)

    def _on_target_reached(self, roll_count: int) -> None:
        QApplication.beep()
        QMessageBox.information(self, "達成目標", f"達成目標！共洗 {roll_count} 次")

    def _on_error(self, msg: str) -> None:
        logger.error("自動化錯誤: %s", msg)
        self.status_bar.showMessage(f"錯誤: {msg}")

    def _on_worker_finished(self) -> None:
        self._set_running_ui(False)
        if self._ocr_test_mode:
            self.status_bar.showMessage(f"OCR 測試結束，共測試 {self._roll_count} 次")
        else:
            self.status_bar.showMessage(f"已停止，共洗 {self._roll_count} 次")
        # 紅色「已停止」提示 2 秒
        self.btn_start.setText("■ 已停止")
        self.btn_start.setStyleSheet("background-color: #e53935; color: white;")
        QTimer.singleShot(2000, self._restore_start_btn)

    def _restore_start_btn(self) -> None:
        """恢復開始按鈕為正常狀態。"""
        self.btn_start.setText("▶ 開始")
        self.btn_start.setStyleSheet("")

    def _set_running_ui(self, running: bool) -> None:
        """切換執行/停止狀態的 UI。"""
        has_region = self.config.potential_region.is_set()
        self.btn_start.setEnabled(not running and has_region)
        self.btn_ocr_test.setEnabled(not running and has_region)
        self.btn_stop.setEnabled(running)
        self.btn_stop.setText("■ 停止")
        self.btn_stop.setStyleSheet("")
        self.settings_panel.setEnabled(not running)
        self.condition_editor.setEnabled(not running)
        if running:
            self.btn_start.setText("執行中...")
            self.btn_start.setStyleSheet("background-color: #4CAF50; color: white;")
            self.status_bar.showMessage("初始化中...")
        else:
            self.btn_start.setText("▶ 開始")
            self.btn_start.setStyleSheet("")

    def closeEvent(self, event) -> None:
        self.settings_panel.apply_to_config(self.config)
        self.condition_editor.apply_to_config(self.config)
        self.config.save()
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        super().closeEvent(event)
