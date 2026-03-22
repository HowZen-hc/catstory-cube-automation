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
    ETERNAL_EQUIP_TYPES,
    generate_condition_summary,
    get_custom_attributes,
    get_num_lines,
)
from app.models.config import AppConfig, LineCondition

_MAX_OR_ROWS = 5

_MODE_PRESET = "預設規則"
_MODE_AND = "逐排指定"
_MODE_OR = "符合任一"
_MODES = [_MODE_PRESET, _MODE_AND, _MODE_OR]


class _CustomRowWidget(QWidget):
    """自訂模式的單排條件 widget。"""

    def __init__(self, index: int, removable: bool, parent=None) -> None:
        super().__init__(parent)
        self.index = index
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.position_combo = QComboBox()
        self.position_combo.setFixedWidth(85)
        self.prev_position: int | None = None
        layout.addWidget(self.position_combo)

        self.attr_combo = QComboBox()
        self.prev_attr = ""
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
        hide_spin = attr in ("被動技能2", "技能冷卻時間")
        self.value_spin.setVisible(not hide_spin)
        self._ge_label.setVisible(not hide_spin)


class ConditionEditor(QGroupBox):
    """目標潛能條件編輯器 — 根據裝備類型自動產生條件。"""

    def __init__(self, parent=None) -> None:
        super().__init__("目標條件", parent)
        self._num_lines = 3  # 預設 3 排，由 on_cube_type_changed 更新
        self._cube_type = ""  # 由 on_cube_type_changed 更新
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
        # 永恆裝備 checkbox（手套/帽子用）
        self.eternal_check = QCheckBox("永恆裝備")
        self.eternal_check.setChecked(True)
        self.eternal_check.stateChanged.connect(self._update_summary)
        row1.addWidget(self.eternal_check)
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

        self._preset_widget.setLayout(preset_layout)
        layout.addWidget(self._preset_widget)

        # === 自訂模式 widgets ===
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

    def _current_mode(self) -> str:
        return self.mode_combo.currentText()

    def _max_rows(self) -> int:
        if self._current_mode() == _MODE_AND:
            return self._num_lines
        return _MAX_OR_ROWS

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
        elif self._current_mode() == _MODE_OR and self._custom_rows:
            # 符合任一模式：自動選第一個未被使用的屬性
            used = {r.attr_combo.currentText() for r in self._custom_rows}
            for attr in custom_attrs:
                if attr not in used:
                    row.attr_combo.setCurrentText(attr)
                    break

        # 記錄初始值供互換用
        row.prev_attr = row.attr_combo.currentText()

        # 連接 signals
        row.attr_combo.currentTextChanged.connect(self._on_custom_attr_changed)
        row.value_spin.valueChanged.connect(self._update_summary)
        row.remove_btn.clicked.connect(lambda: self._remove_custom_row(row))
        row.position_combo.currentIndexChanged.connect(self._on_position_changed)

        self._custom_rows.append(row)
        # 插在 add 按鈕之前
        self._custom_layout.insertWidget(self._custom_layout.count() - 1, row)

        # 刷新 position combos（填入所有排）
        self._refresh_position_combos()

        # 設定初始排位
        if lc and lc.position > 0 and self._current_mode() == _MODE_AND:
            idx = row.position_combo.findData(lc.position)
            if idx >= 0:
                row.position_combo.blockSignals(True)
                row.position_combo.setCurrentIndex(idx)
                row.position_combo.blockSignals(False)
        elif self._current_mode() == _MODE_AND:
            # 自動選第一個未被使用的排
            used = {r.position_combo.currentData() for r in self._custom_rows if r is not row}
            for i in range(1, self._num_lines + 1):
                if i not in used:
                    idx = row.position_combo.findData(i)
                    if idx >= 0:
                        row.position_combo.blockSignals(True)
                        row.position_combo.setCurrentIndex(idx)
                        row.position_combo.blockSignals(False)
                    break
        row.prev_position = row.position_combo.currentData()

        self._update_add_btn_visibility()
        row.update_visibility()
        self._update_summary()
        return row

    def _refresh_position_combos(self) -> None:
        """刷新所有排的 position combo：AND 模式顯示全部排，OR 模式隱藏。"""
        is_and = self._current_mode() == _MODE_AND
        for row in self._custom_rows:
            row.position_combo.setVisible(is_and)
        if not is_and:
            return

        for row in self._custom_rows:
            current = row.position_combo.currentData()
            row.position_combo.blockSignals(True)
            row.position_combo.clear()
            for i in range(1, self._num_lines + 1):
                row.position_combo.addItem(f"第 {i} 排", i)
            if current is not None:
                idx = row.position_combo.findData(current)
                if idx >= 0:
                    row.position_combo.setCurrentIndex(idx)
            row.position_combo.blockSignals(False)

    def _remove_custom_row(self, row: _CustomRowWidget) -> None:
        """移除一排自訂條件。"""
        if row in self._custom_rows:
            self._custom_rows.remove(row)
            self._custom_layout.removeWidget(row)
            row.deleteLater()
            # 更新剩餘排的 index、remove 按鈕、position combos
            for i, r in enumerate(self._custom_rows):
                r.index = i
                r.remove_btn.setVisible(i > 0)
            self._refresh_position_combos()
            self._update_add_btn_visibility()
            self._update_summary()

    def _update_add_btn_visibility(self) -> None:
        self._add_row_btn.setVisible(len(self._custom_rows) < self._max_rows())

    def _swap_or_attr(self, changed_row: _CustomRowWidget) -> None:
        """符合任一模式屬性互換：若其他 row 有相同屬性，交換兩排屬性。"""
        if self._current_mode() != _MODE_OR:
            changed_row.prev_attr = changed_row.attr_combo.currentText()
            return
        new_attr = changed_row.attr_combo.currentText()
        for row in self._custom_rows:
            if row is changed_row:
                continue
            if row.attr_combo.currentText() == new_attr:
                row.attr_combo.blockSignals(True)
                row.attr_combo.setCurrentText(changed_row.prev_attr)
                row.prev_attr = changed_row.prev_attr
                row.update_visibility()
                row.attr_combo.blockSignals(False)
                break
        changed_row.prev_attr = new_attr

    # ── 萌獸方塊連動 ──

    def on_cube_type_changed(self, cube_type: str) -> None:
        """當方塊類型改變時由 main_window 呼叫。"""
        self._num_lines = get_num_lines(cube_type)
        self._cube_type = cube_type
        if cube_type == "萌獸方塊":
            # 動態加入萌獸選項並選取
            if self.equip_combo.findText("萌獸") < 0:
                self.equip_combo.addItem("萌獸")
            self.equip_combo.setCurrentText("萌獸")
            self._equip_row.setVisible(False)
            self.mode_combo.setCurrentText(_MODE_PRESET)
        else:
            # 移除萌獸選項
            idx = self.equip_combo.findText("萌獸")
            if idx >= 0:
                self.equip_combo.removeItem(idx)
            self._equip_row.setVisible(True)
            # 非萌獸才重設裝備回第一項
            self._reset_to_defaults()

    # ── 模式切換 ──

    def _reset_to_defaults(self) -> None:
        """重設：裝備回第一項、比對模式回預設、自訂排重建。"""
        self.equip_combo.setCurrentIndex(0)
        self.mode_combo.setCurrentText(_MODE_PRESET)

    def _on_mode_changed(self, mode: str) -> None:
        self._preset_widget.setVisible(mode == _MODE_PRESET)
        self._custom_widget.setVisible(mode in (_MODE_AND, _MODE_OR))
        self._update_eternal_visibility()
        # 切換模式時重建自訂排
        if mode in (_MODE_AND, _MODE_OR):
            self._reset_custom_rows()
        self._update_summary()

    # ── 預設模式 handlers ──

    def _on_equip_changed(self, equip_type: str) -> None:
        attrs = EQUIPMENT_ATTRIBUTES.get(equip_type, [])
        self.attr_combo.blockSignals(True)
        self.attr_combo.clear()
        self.attr_combo.addItems(attrs)
        self.attr_combo.blockSignals(False)
        # 永恆 checkbox：手套/帽子切換時預設勾選
        if equip_type in ETERNAL_EQUIP_TYPES:
            self.eternal_check.setChecked(True)
        self._update_eternal_visibility()
        self._on_attr_changed(self.attr_combo.currentText())
        # 切換裝備類型時：比對模式回預設 + 自訂排重建
        self.mode_combo.setCurrentText(_MODE_PRESET)
        self._reset_custom_rows()

    def _update_eternal_visibility(self) -> None:
        """永恆 checkbox 只在手套/帽子 + 預設模式下顯示。"""
        is_eternal_equip = self.equip_combo.currentText() in ETERNAL_EQUIP_TYPES
        is_preset = self._current_mode() == _MODE_PRESET
        self.eternal_check.setVisible(is_eternal_equip and is_preset)

    def _on_attr_changed(self, _attr: str) -> None:
        self._update_summary()

    # ── 自訂模式 handlers ──

    def _reset_custom_rows(self) -> None:
        """清除所有自訂排，重建 1 排（使用新裝備類型的預設屬性）。"""
        while self._custom_rows:
            row = self._custom_rows.pop()
            self._custom_layout.removeWidget(row)
            row.deleteLater()
        self._add_custom_row()

    def _on_position_changed(self) -> None:
        """AND 模式排位變更：選到已被佔用的排時，與對方交換。"""
        if self._current_mode() != _MODE_AND:
            return
        sender = self.sender()
        for changed_row in self._custom_rows:
            if changed_row.position_combo is sender:
                new_pos = changed_row.position_combo.currentData()
                old_pos = changed_row.prev_position
                for other in self._custom_rows:
                    if other is changed_row:
                        continue
                    if other.position_combo.currentData() == new_pos:
                        other.position_combo.blockSignals(True)
                        idx = other.position_combo.findData(old_pos)
                        if idx >= 0:
                            other.position_combo.setCurrentIndex(idx)
                        other.prev_position = old_pos
                        other.position_combo.blockSignals(False)
                        break
                changed_row.prev_position = new_pos
                break
        self._update_summary()

    def _on_custom_attr_changed(self, attr: str) -> None:
        """自訂模式屬性變更：更新 visibility + 最終傷害預設值 + 互換。"""
        sender = self.sender()
        for row in self._custom_rows:
            if row.attr_combo is sender:
                row.update_visibility()
                if attr == "最終傷害":
                    row.value_spin.setValue(20)
                self._swap_or_attr(row)
                break
        self._update_summary()

    # ── 條件預覽 ──

    def _update_summary(self) -> None:
        config = self._build_config_for_summary()
        lines = generate_condition_summary(config)
        self.summary_label.setText("\n".join(lines))

    def _build_config_for_summary(self) -> AppConfig:
        mode = self._current_mode()
        if mode == _MODE_PRESET:
            return AppConfig(
                cube_type=self._cube_type,
                equipment_type=self.equip_combo.currentText(),
                target_attribute=self.attr_combo.currentText(),
                is_eternal=self.eternal_check.isChecked(),
                use_preset=True,
            )
        custom_lines = []
        for row in self._custom_rows:
            position = (row.position_combo.currentData() or 0) if mode == _MODE_AND else 0
            custom_lines.append(LineCondition(
                attribute=row.attr_combo.currentText(),
                min_value=row.value_spin.value(),
                position=position,
            ))
        return AppConfig(
            cube_type=self._cube_type,
            equipment_type=self.equip_combo.currentText(),
            use_preset=False,
            custom_lines=custom_lines,
        )

    # ── config 讀寫 ──

    def apply_to_config(self, config: AppConfig) -> None:
        mode = self._current_mode()
        config.equipment_type = self.equip_combo.currentText()
        config.target_attribute = self.attr_combo.currentText()
        config.is_eternal = self.eternal_check.isChecked()
        config.use_preset = (mode == _MODE_PRESET)
        config.custom_lines = [
            LineCondition(
                attribute=row.attr_combo.currentText(),
                min_value=row.value_spin.value(),
                position=(row.position_combo.currentData() or 0) if mode == _MODE_AND else 0,
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
        self.eternal_check.setChecked(config.is_eternal)

        # 從 config 推導模式
        if config.use_preset:
            mode = _MODE_PRESET
        elif config.custom_lines and config.custom_lines[0].position > 0:
            mode = _MODE_AND
        else:
            mode = _MODE_OR
        self.mode_combo.setCurrentText(mode)

        # 載入自訂排
        max_rows = self._num_lines if mode == _MODE_AND else _MAX_OR_ROWS
        while self._custom_rows:
            row = self._custom_rows.pop()
            self._custom_layout.removeWidget(row)
            row.deleteLater()
        for lc in config.custom_lines[:max_rows]:
            self._add_custom_row(lc)
        if not self._custom_rows:
            self._add_custom_row()
