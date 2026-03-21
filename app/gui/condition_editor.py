from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
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

_MAX_CUSTOM_ROWS = 5

_MODE_PRESET = "預設規則"
_MODE_CUSTOM = "自訂"
_MODES = [_MODE_PRESET, _MODE_CUSTOM]

_POSITION_OPTIONS = ["任意一排", "第1排", "第2排", "第3排"]


class _CustomRowWidget(QWidget):
    """自訂模式的單排條件 widget。"""

    def __init__(self, index: int, removable: bool, parent=None) -> None:
        super().__init__(parent)
        self.index = index
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.position_combo = QComboBox()
        self.position_combo.addItems(_POSITION_OPTIONS)
        layout.addWidget(self.position_combo)

        self.attr_combo = QComboBox()
        layout.addWidget(self.attr_combo)

        self._ge_label = QLabel("至少")
        layout.addWidget(self._ge_label)

        self.value_spin = QSpinBox()
        self.value_spin.setRange(1, 99)
        self.value_spin.setValue(1)
        self.value_spin.setSingleStep(1)
        self.value_spin.setSuffix(" %")
        layout.addWidget(self.value_spin)

        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedWidth(28)
        self.remove_btn.setVisible(removable)
        layout.addWidget(self.remove_btn)

        layout.addStretch()
        self.setLayout(layout)

    def update_visibility(self) -> None:
        """根據屬性更新 spin 顯示。"""
        attr = self.attr_combo.currentText()
        self.value_spin.setVisible(attr != "被動技能2")
        self._ge_label.setVisible(attr != "被動技能2")


class ConditionEditor(QGroupBox):
    """目標潛能條件編輯器 — 根據裝備類型自動產生條件。"""

    def __init__(self, parent=None) -> None:
        super().__init__("目標條件", parent)
        self._prev_equip: str = ""  # 切換萌獸前的裝備類型
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()

        # 裝備類型
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("裝備類型:"))
        self.equip_combo = QComboBox()
        self.equip_combo.setMinimumWidth(200)
        self.equip_combo.addItems([t for t in EQUIPMENT_TYPES if t != "萌獸"])
        self.equip_combo.currentTextChanged.connect(self._on_equip_changed)
        row1.addWidget(self.equip_combo)
        row1.addStretch()
        self._equip_row = QWidget()
        self._equip_row.setLayout(row1)
        layout.addWidget(self._equip_row)

        # 比對模式下拉選單
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("比對模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(_MODES)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

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

        # === 自訂模式 widgets（位置比對用） ===
        self._custom_widget = QWidget()
        self._custom_layout = QVBoxLayout()
        self._custom_layout.setContentsMargins(0, 0, 0, 0)

        self._custom_rows: list[_CustomRowWidget] = []

        # 新增條件排按鈕
        self._add_row_btn = QPushButton("+ 新增條件排")
        self._add_row_btn.clicked.connect(self._add_custom_row)
        self._custom_layout.addWidget(self._add_row_btn)

        self._custom_widget.setLayout(self._custom_layout)
        self._custom_widget.setVisible(False)
        layout.addWidget(self._custom_widget)

        # 條件預覽
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(self.summary_label)

        # 初始建立 1 排（需在 summary_label 之後，因為會觸發 _update_summary）
        self._add_custom_row()

        self.setLayout(layout)

        # 初始化
        self._on_equip_changed(self.equip_combo.currentText())

    # ── 自訂模式動態排管理 ──

    def _add_custom_row(self, lc: LineCondition | None = None) -> _CustomRowWidget:
        """新增一排自訂條件。"""
        index = len(self._custom_rows)
        removable = index > 0  # 第一排不可移除
        row = _CustomRowWidget(index, removable)

        # 填入屬性選單
        equip = self.equip_combo.currentText()
        custom_attrs = get_custom_attributes(equip)
        row.attr_combo.addItems(custom_attrs)

        if lc:
            cidx = row.attr_combo.findText(lc.attribute)
            if cidx >= 0:
                row.attr_combo.setCurrentIndex(cidx)
            row.value_spin.setValue(lc.min_value)
            row.position_combo.setCurrentIndex(lc.position)

        # 連接 signals
        row.attr_combo.currentTextChanged.connect(self._on_custom_attr_changed)
        row.value_spin.valueChanged.connect(self._on_custom_changed)
        row.position_combo.currentIndexChanged.connect(self._on_custom_changed)
        row.remove_btn.clicked.connect(lambda: self._remove_custom_row(row))

        self._custom_rows.append(row)
        # 插在 add 按鈕之前
        self._custom_layout.insertWidget(self._custom_layout.count() - 1, row)

        self._update_add_btn_visibility()
        row.update_visibility()
        self._update_summary()
        return row

    def _remove_custom_row(self, row: _CustomRowWidget) -> None:
        """移除一排自訂條件。"""
        if row in self._custom_rows:
            self._custom_rows.remove(row)
            self._custom_layout.removeWidget(row)
            row.deleteLater()
            for i, r in enumerate(self._custom_rows):
                r.remove_btn.setVisible(i > 0)
            self._update_add_btn_visibility()
            self._update_summary()

    def _update_add_btn_visibility(self) -> None:
        self._add_row_btn.setVisible(len(self._custom_rows) < _MAX_CUSTOM_ROWS)

    # ── 萌獸方塊連動 ──

    def on_cube_type_changed(self, cube_type: str) -> None:
        """當方塊類型改變時由 main_window 呼叫。"""
        if cube_type == "萌獸方塊":
            # 記住當前裝備類型，切回時還原
            current = self.equip_combo.currentText()
            if current != "萌獸":
                self._prev_equip = current
            # 動態加入萌獸選項並選取
            if self.equip_combo.findText("萌獸") < 0:
                self.equip_combo.addItem("萌獸")
            self.equip_combo.setCurrentText("萌獸")
            self._equip_row.setVisible(False)
        else:
            # 移除萌獸選項，還原之前的裝備類型
            idx = self.equip_combo.findText("萌獸")
            if idx >= 0:
                self.equip_combo.removeItem(idx)
            if self._prev_equip:
                self.equip_combo.setCurrentText(self._prev_equip)
            self._equip_row.setVisible(True)

    # ── 模式切換 ──

    def _on_mode_changed(self, mode: str) -> None:
        self._preset_widget.setVisible(mode == _MODE_PRESET)
        self._custom_widget.setVisible(mode == _MODE_CUSTOM)
        self._update_summary()

    # ── 預設模式 handlers ──

    def _on_equip_changed(self, equip_type: str) -> None:
        attrs = EQUIPMENT_ATTRIBUTES.get(equip_type, [])
        self.attr_combo.blockSignals(True)
        self.attr_combo.clear()
        self.attr_combo.addItems(attrs)
        self.attr_combo.blockSignals(False)
        self._on_attr_changed(self.attr_combo.currentText())
        # 切換裝備類型時重設自訂排為 1 排
        self._reset_custom_rows()

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
        for row in self._custom_rows:
            row.attr_combo.blockSignals(True)
            prev = row.attr_combo.currentText()
            row.attr_combo.clear()
            row.attr_combo.addItems(custom_attrs)
            idx = row.attr_combo.findText(prev)
            if idx >= 0:
                row.attr_combo.setCurrentIndex(idx)
            row.attr_combo.blockSignals(False)
            row.update_visibility()
        self._update_summary()

    def _reset_custom_rows(self) -> None:
        """清除所有自訂排，重建 1 排（使用新裝備類型的預設屬性）。"""
        while self._custom_rows:
            row = self._custom_rows.pop()
            self._custom_layout.removeWidget(row)
            row.deleteLater()
        self._add_custom_row()

    def _on_custom_attr_changed(self, attr: str) -> None:
        """自訂模式屬性變更：更新 visibility + 最終傷害預設值。"""
        sender = self.sender()
        for row in self._custom_rows:
            if row.attr_combo is sender:
                row.update_visibility()
                if attr == "最終傷害":
                    row.value_spin.setValue(20)
                break
        self._update_summary()

    def _on_custom_changed(self) -> None:
        self._update_summary()

    # ── 條件預覽 ──

    def _update_summary(self) -> None:
        config = self._build_config_for_summary()
        lines = generate_condition_summary(config)
        self.summary_label.setText("\n".join(lines))

    def _build_config_for_summary(self) -> AppConfig:
        mode = self.mode_combo.currentText()
        if mode == _MODE_PRESET:
            return AppConfig(
                equipment_type=self.equip_combo.currentText(),
                target_attribute=self.attr_combo.currentText(),
                include_all_stats=self.all_stats_check.isChecked(),
                use_preset=True,
            )
        custom_lines = []
        for row in self._custom_rows:
            custom_lines.append(LineCondition(
                attribute=row.attr_combo.currentText(),
                min_value=row.value_spin.value(),
                position=row.position_combo.currentIndex(),
            ))
        return AppConfig(
            equipment_type=self.equip_combo.currentText(),
            use_preset=False,
            custom_lines=custom_lines,
        )

    # ── config 讀寫 ──

    def apply_to_config(self, config: AppConfig) -> None:
        mode = self.mode_combo.currentText()
        config.equipment_type = self.equip_combo.currentText()
        config.target_attribute = self.attr_combo.currentText()
        config.include_all_stats = self.all_stats_check.isChecked()
        config.use_preset = (mode == _MODE_PRESET)
        config.custom_lines = [
            LineCondition(
                attribute=row.attr_combo.currentText(),
                min_value=row.value_spin.value(),
                position=row.position_combo.currentIndex(),
            )
            for row in self._custom_rows
        ]

    def load_from_config(self, config: AppConfig) -> None:
        idx = self.equip_combo.findText(config.equipment_type)
        if idx >= 0:
            self.equip_combo.setCurrentIndex(idx)
        attr_idx = self.attr_combo.findText(config.target_attribute)
        if attr_idx >= 0:
            self.attr_combo.setCurrentIndex(attr_idx)
        self.all_stats_check.setChecked(config.include_all_stats)

        # 從 config 欄位推導模式
        mode = _MODE_PRESET if config.use_preset else _MODE_CUSTOM
        self.mode_combo.setCurrentText(mode)

        # 載入自訂排
        while self._custom_rows:
            row = self._custom_rows.pop()
            self._custom_layout.removeWidget(row)
            row.deleteLater()
        for lc in config.custom_lines[:_MAX_CUSTOM_ROWS]:
            self._add_custom_row(lc)
        if not self._custom_rows:
            self._add_custom_row()
