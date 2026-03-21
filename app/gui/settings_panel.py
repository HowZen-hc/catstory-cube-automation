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

CUBE_TYPES = ["恢復附加方塊 (紅色)", "珍貴附加方塊 (粉紅色)", "絕對附加方塊", "萌獸方塊"]


class SettingsPanel(QGroupBox):
    """設定面板：方塊類型、延遲、區域框選。"""

    select_potential_region = pyqtSignal()
    cube_type_changed = pyqtSignal(str)

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
        self.cube_type_combo.currentTextChanged.connect(self.cube_type_changed.emit)
        row1.addWidget(self.cube_type_combo)
        row1.addStretch()
        layout.addLayout(row1)

        # 螢幕區域
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("螢幕區域:"))
        self.btn_select_potential = QPushButton("框選潛能區域")
        self.btn_select_potential.setMinimumWidth(200)
        self.btn_select_potential.clicked.connect(self.select_potential_region.emit)
        row2.addWidget(self.btn_select_potential)
        row2.addStretch()
        layout.addLayout(row2)

        # 每次洗方塊間隔延遲
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("每次間隔(ms):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimumWidth(120)
        self.delay_spin.setRange(1000, 5000)
        self.delay_spin.setValue(1000)
        self.delay_spin.setSingleStep(100)
        row3.addWidget(self.delay_spin)
        row3.addStretch()
        layout.addLayout(row3)

        self.setLayout(layout)

    def apply_to_config(self, config: AppConfig) -> None:
        config.cube_type = self.cube_type_combo.currentText()
        config.delay_ms = self.delay_spin.value()

    def load_from_config(self, config: AppConfig) -> None:
        idx = self.cube_type_combo.findText(config.cube_type)
        if idx >= 0:
            self.cube_type_combo.setCurrentIndex(idx)
        self.delay_spin.setValue(config.delay_ms)

    def load_persistent_from_config(self, config: AppConfig) -> None:
        """只載入持久性設定（延遲），下拉選單保持 UI 預設值。"""
        self.delay_spin.setValue(config.delay_ms)
