from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.models.config import AppConfig

CUBE_TYPES = ["珍貴附加方塊(粉紅色)", "絕對附加方塊", "萌獸方塊", "恢復附加方塊(紅色)"]


class SettingsPanel(QGroupBox):
    """設定面板：方塊類型、延遲、快捷鍵、區域框選。"""

    select_potential_region = pyqtSignal()
    select_button_region = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("設定區", parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        # 方塊類型
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("方塊類型:"))
        self.cube_type_combo = QComboBox()
        self.cube_type_combo.addItems(CUBE_TYPES)
        row1.addWidget(self.cube_type_combo)
        row1.addStretch()
        layout.addLayout(row1)

        # 螢幕區域
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("螢幕區域:"))
        self.btn_select_potential = QPushButton("框選潛能區域")
        self.btn_select_potential.clicked.connect(self.select_potential_region.emit)
        row2.addWidget(self.btn_select_potential)
        self.btn_select_button = QPushButton("框選重新設定按鈕區域")
        self.btn_select_button.clicked.connect(self.select_button_region.emit)
        row2.addWidget(self.btn_select_button)
        row2.addStretch()
        layout.addLayout(row2)

        # 延遲
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("延遲(ms):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(100, 5000)
        self.delay_spin.setValue(500)
        self.delay_spin.setSingleStep(100)
        row3.addWidget(self.delay_spin)
        row3.addStretch()
        layout.addLayout(row3)

        # 快捷鍵
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("快捷鍵:"))
        self.hotkey_label = QLabel("F9 開始/停止")
        row4.addWidget(self.hotkey_label)
        row4.addStretch()
        layout.addLayout(row4)

        self.setLayout(layout)

    def apply_to_config(self, config: AppConfig) -> None:
        config.cube_type = self.cube_type_combo.currentText()
        config.delay_ms = self.delay_spin.value()

    def load_from_config(self, config: AppConfig) -> None:
        idx = self.cube_type_combo.findText(config.cube_type)
        if idx >= 0:
            self.cube_type_combo.setCurrentIndex(idx)
        self.delay_spin.setValue(config.delay_ms)
