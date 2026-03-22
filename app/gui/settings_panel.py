from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


from app.models.config import AppConfig

CUBE_TYPES = ["恢復附加方塊 (紅色)", "珍貴附加方塊 (粉紅色)", "絕對附加方塊 (僅洗兩排)", "萌獸方塊"]


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
        self.region_hint = QLabel("⚠ 請先框選潛能區域")
        self.region_hint.setStyleSheet("color: red;")
        row2.addWidget(self.region_hint)
        row2.addStretch()
        layout.addLayout(row2)

        # 每次洗方塊間隔延遲
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("洗完後等待(ms):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimumWidth(120)
        self.delay_spin.setRange(500, 2000)
        self.delay_spin.setValue(1000)
        self.delay_spin.setSingleStep(100)
        self.delay_spin.setToolTip("每次洗方塊後等待畫面更新的時間，太低可能截到舊畫面")
        row3.addWidget(self.delay_spin)
        row3.addStretch()
        layout.addLayout(row3)

        # GPU 加速
        row4 = QHBoxLayout()
        self.gpu_checkbox = QCheckBox("啟用 GPU 加速（需要 NVIDIA 顯卡 + CUDA）")
        self.gpu_checkbox.setEnabled(False)
        self.gpu_checkbox.setToolTip("目前已停用此選項")
        row4.addWidget(self.gpu_checkbox)
        row4.addStretch()
        layout.addLayout(row4)

        self.setLayout(layout)

    def apply_to_config(self, config: AppConfig) -> None:
        config.cube_type = self.cube_type_combo.currentText()
        config.delay_ms = self.delay_spin.value()
        config.use_gpu = self.gpu_checkbox.isChecked()

    def load_from_config(self, config: AppConfig) -> None:
        idx = self.cube_type_combo.findText(config.cube_type)
        if idx >= 0:
            self.cube_type_combo.setCurrentIndex(idx)
        self.delay_spin.setValue(config.delay_ms)

    def load_persistent_from_config(self, config: AppConfig) -> None:
        """只載入持久性設定（延遲、GPU），下拉選單保持 UI 預設值。"""
        self.delay_spin.setValue(config.delay_ms)
        self.gpu_checkbox.setChecked(config.use_gpu)
