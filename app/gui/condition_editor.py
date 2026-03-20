from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.condition import (
    EQUIPMENT_ATTRIBUTES,
    EQUIPMENT_TYPES,
    GLOVE_TYPES,
    STATS_WITH_ALL_STATS,
    generate_condition_summary,
    get_custom_attributes,
)
from app.models.config import AppConfig, LineCondition


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
        self._equip_row = QWidget()
        self._equip_row.setLayout(row1)
        layout.addWidget(self._equip_row)

        # 使用預設規則 checkbox
        self.preset_check = QCheckBox("使用預設規則")
        self.preset_check.setChecked(True)
        self.preset_check.stateChanged.connect(self._on_preset_toggled)
        layout.addWidget(self.preset_check)

        # === 預設模式 widgets ===
        self._preset_widget = QWidget()
        preset_layout = QVBoxLayout()
        preset_layout.setContentsMargins(0, 0, 0, 0)

        # 目標屬性
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("目標屬性:"))
        self.attr_combo = QComboBox()
        self.attr_combo.setMinimumWidth(150)
        self.attr_combo.currentTextChanged.connect(self._on_attr_changed)
        row2.addWidget(self.attr_combo)
        row2.addStretch()
        preset_layout.addLayout(row2)

        # 含全屬性
        self.all_stats_check = QCheckBox("含全屬性")
        self.all_stats_check.stateChanged.connect(self._update_summary)
        preset_layout.addWidget(self.all_stats_check)

        self._preset_widget.setLayout(preset_layout)
        layout.addWidget(self._preset_widget)

        # === 自訂模式 widgets ===
        self._custom_widget = QWidget()
        custom_layout = QVBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)

        self._custom_attr_combos: list[QComboBox] = []
        self._custom_value_spins: list[QSpinBox] = []

        for i in range(3):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"第{i+1}行:"))

            attr_combo = QComboBox()
            attr_combo.setMinimumWidth(150)
            attr_combo.currentTextChanged.connect(self._on_custom_changed)
            row.addWidget(attr_combo)

            row.addWidget(QLabel(">="))

            value_spin = QSpinBox()
            value_spin.setRange(1, 99)
            value_spin.setValue(1)
            value_spin.setSingleStep(1)
            value_spin.setSuffix(" %")
            value_spin.valueChanged.connect(self._on_custom_changed)
            row.addWidget(value_spin)

            row.addStretch()
            custom_layout.addLayout(row)

            self._custom_attr_combos.append(attr_combo)
            self._custom_value_spins.append(value_spin)

        self._custom_widget.setLayout(custom_layout)
        self._custom_widget.setVisible(False)
        layout.addWidget(self._custom_widget)

        # 條件預覽
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(self.summary_label)

        self.setLayout(layout)

        # 初始化
        self._on_equip_changed(self.equip_combo.currentText())

    # ── 萌獸方塊連動 ──

    def on_cube_type_changed(self, cube_type: str) -> None:
        """當方塊類型改變時由 main_window 呼叫。"""
        if cube_type == "萌獸方塊":
            idx = self.equip_combo.findText("萌獸")
            if idx >= 0:
                self.equip_combo.setCurrentIndex(idx)
            self._equip_row.setVisible(False)
        else:
            self._equip_row.setVisible(True)

    # ── 預設/自訂切換 ──

    def _on_preset_toggled(self, _state: int) -> None:
        use_preset = self.preset_check.isChecked()
        self._preset_widget.setVisible(use_preset)
        self._custom_widget.setVisible(not use_preset)
        self._update_summary()

    # ── 預設模式 handlers ──

    def _on_equip_changed(self, equip_type: str) -> None:
        attrs = EQUIPMENT_ATTRIBUTES.get(equip_type, [])
        self.attr_combo.blockSignals(True)
        self.attr_combo.clear()
        self.attr_combo.addItems(attrs)
        self.attr_combo.blockSignals(False)
        self._on_attr_changed(self.attr_combo.currentText())
        # 更新自訂模式的屬性選單
        self._refresh_custom_attr_combos(equip_type)

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

    # ── 自訂模式 handlers ──

    def _refresh_custom_attr_combos(self, equip_type: str) -> None:
        """根據裝備類型更新自訂模式的屬性下拉選單。"""
        custom_attrs = get_custom_attributes(equip_type)
        for combo in self._custom_attr_combos:
            combo.blockSignals(True)
            prev = combo.currentText()
            combo.clear()
            combo.addItems(custom_attrs)
            # 嘗試恢復先前選擇
            idx = combo.findText(prev)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.blockSignals(False)
        self._update_custom_spin_visibility()

    def _on_custom_changed(self) -> None:
        self._update_custom_spin_visibility()
        self._update_summary()

    def _update_custom_spin_visibility(self) -> None:
        """被動技能2 不需要數值，隱藏 spin。"""
        for combo, spin in zip(self._custom_attr_combos, self._custom_value_spins):
            spin.setVisible(combo.currentText() != "被動技能2")

    # ── 條件預覽 ──

    def _update_summary(self) -> None:
        config = self._build_config_for_summary()
        lines = generate_condition_summary(config)
        self.summary_label.setText("\n".join(lines))

    def _build_config_for_summary(self) -> AppConfig:
        use_preset = self.preset_check.isChecked()
        if use_preset:
            return AppConfig(
                equipment_type=self.equip_combo.currentText(),
                target_attribute=self.attr_combo.currentText(),
                include_all_stats=self.all_stats_check.isChecked(),
                use_preset=True,
            )
        custom_lines = []
        for combo, spin in zip(self._custom_attr_combos, self._custom_value_spins):
            custom_lines.append(LineCondition(
                attribute=combo.currentText(),
                min_value=spin.value(),
            ))
        return AppConfig(
            equipment_type=self.equip_combo.currentText(),
            use_preset=False,
            custom_lines=custom_lines,
        )

    # ── config 讀寫 ──

    def apply_to_config(self, config: AppConfig) -> None:
        config.equipment_type = self.equip_combo.currentText()
        config.target_attribute = self.attr_combo.currentText()
        config.include_all_stats = self.all_stats_check.isChecked()
        config.use_preset = self.preset_check.isChecked()
        config.custom_lines = [
            LineCondition(
                attribute=combo.currentText(),
                min_value=spin.value(),
            )
            for combo, spin in zip(self._custom_attr_combos, self._custom_value_spins)
        ]

    def load_from_config(self, config: AppConfig) -> None:
        idx = self.equip_combo.findText(config.equipment_type)
        if idx >= 0:
            self.equip_combo.setCurrentIndex(idx)
        attr_idx = self.attr_combo.findText(config.target_attribute)
        if attr_idx >= 0:
            self.attr_combo.setCurrentIndex(attr_idx)
        self.all_stats_check.setChecked(config.include_all_stats)
        self.preset_check.setChecked(config.use_preset)
        # 載入自訂條件
        for i, lc in enumerate(config.custom_lines[:3]):
            combo = self._custom_attr_combos[i]
            cidx = combo.findText(lc.attribute)
            if cidx >= 0:
                combo.setCurrentIndex(cidx)
            self._custom_value_spins[i].setValue(lc.min_value)
        self._update_custom_spin_visibility()
