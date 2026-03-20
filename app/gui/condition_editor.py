from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)

from app.core.condition import (
    EQUIPMENT_ATTRIBUTES,
    EQUIPMENT_TYPES,
    GLOVE_TYPES,
    STATS_WITH_ALL_STATS,
    generate_condition_summary,
)
from app.models.config import AppConfig


class ConditionEditor(QGroupBox):
    """目標潛能條件編輯器 — 根據裝備類型自動產生條件。"""

    def __init__(self, parent=None) -> None:
        super().__init__("目標條件", parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        # 裝備類型
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("裝備類型:"))
        self.equip_combo = QComboBox()
        self.equip_combo.setMinimumWidth(200)
        self.equip_combo.addItems(EQUIPMENT_TYPES)
        self.equip_combo.currentTextChanged.connect(self._on_equip_changed)
        row1.addWidget(self.equip_combo)
        row1.addStretch()
        layout.addLayout(row1)

        # 目標屬性
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("目標屬性:"))
        self.attr_combo = QComboBox()
        self.attr_combo.setMinimumWidth(150)
        self.attr_combo.currentTextChanged.connect(self._on_attr_changed)
        row2.addWidget(self.attr_combo)
        row2.addStretch()
        layout.addLayout(row2)

        # 含全屬性
        self.all_stats_check = QCheckBox("含全屬性")
        self.all_stats_check.stateChanged.connect(self._update_summary)
        layout.addWidget(self.all_stats_check)

        # 條件預覽
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(self.summary_label)

        self.setLayout(layout)

        # 初始化
        self._on_equip_changed(self.equip_combo.currentText())

    def _on_equip_changed(self, equip_type: str) -> None:
        attrs = EQUIPMENT_ATTRIBUTES.get(equip_type, [])
        self.attr_combo.blockSignals(True)
        self.attr_combo.clear()
        self.attr_combo.addItems(attrs)
        self.attr_combo.blockSignals(False)
        self._on_attr_changed(self.attr_combo.currentText())

    def _on_attr_changed(self, attr: str) -> None:
        equip = self.equip_combo.currentText()
        # 全屬性 checkbox 只在 STR/DEX/INT/LUK 時顯示
        can_all_stats = attr in STATS_WITH_ALL_STATS and equip not in GLOVE_TYPES
        # 手套也可以含全屬性（第2、3行）
        if equip in GLOVE_TYPES and attr in STATS_WITH_ALL_STATS:
            can_all_stats = True
        self.all_stats_check.setVisible(can_all_stats)
        if not can_all_stats:
            self.all_stats_check.setChecked(False)
        self._update_summary()

    def _update_summary(self) -> None:
        config = AppConfig(
            equipment_type=self.equip_combo.currentText(),
            target_attribute=self.attr_combo.currentText(),
            include_all_stats=self.all_stats_check.isChecked(),
        )
        lines = generate_condition_summary(config)
        self.summary_label.setText("\n".join(lines))

    def apply_to_config(self, config: AppConfig) -> None:
        config.equipment_type = self.equip_combo.currentText()
        config.target_attribute = self.attr_combo.currentText()
        config.include_all_stats = self.all_stats_check.isChecked()

    def load_from_config(self, config: AppConfig) -> None:
        idx = self.equip_combo.findText(config.equipment_type)
        if idx >= 0:
            self.equip_combo.setCurrentIndex(idx)
        attr_idx = self.attr_combo.findText(config.target_attribute)
        if attr_idx >= 0:
            self.attr_combo.setCurrentIndex(attr_idx)
        self.all_stats_check.setChecked(config.include_all_stats)
