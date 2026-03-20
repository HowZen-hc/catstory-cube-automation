from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.models.config import TargetCondition

ATTRIBUTES = [
    "任意",
    "攻擊力%",
    "魔力%",
    "BOSS傷害%",
    "無視防禦%",
    "總傷害%",
    "暴擊傷害%",
    "全屬性%",
    "HP%",
    "MP%",
    "防禦力%",
]

OPERATORS = [">=", "=", "contains"]


class ConditionRow(QWidget):
    """單行條件編輯。"""

    def __init__(self, line_index: int, parent=None) -> None:
        super().__init__(parent)
        self.line_index = line_index
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QComboBox()
        self.label.addItems([f"第{i+1}行" for i in range(3)])
        self.label.setCurrentIndex(self.line_index)
        layout.addWidget(self.label)

        self.attr_combo = QComboBox()
        self.attr_combo.addItems(ATTRIBUTES)
        layout.addWidget(self.attr_combo)

        self.op_combo = QComboBox()
        self.op_combo.addItems(OPERATORS)
        layout.addWidget(self.op_combo)

        self.value_spin = QSpinBox()
        self.value_spin.setRange(0, 100)
        layout.addWidget(self.value_spin)

        self.btn_delete = QPushButton("×")
        self.btn_delete.setFixedWidth(30)
        layout.addWidget(self.btn_delete)

        self.setLayout(layout)

    def to_condition(self) -> TargetCondition:
        return TargetCondition(
            line_index=self.label.currentIndex(),
            attribute=self.attr_combo.currentText(),
            operator=self.op_combo.currentText(),
            value=self.value_spin.value(),
        )


class ConditionEditor(QGroupBox):
    """目標潛能條件編輯器。"""

    def __init__(self, parent=None) -> None:
        super().__init__("目標條件", parent)
        self._rows: list[ConditionRow] = []
        self._init_ui()

    def _init_ui(self) -> None:
        self._layout = QVBoxLayout()

        self.btn_add = QPushButton("+ 新增條件")
        self.btn_add.clicked.connect(self._add_row)
        self._layout.addWidget(self.btn_add)

        self._rows_layout = QVBoxLayout()
        self._layout.addLayout(self._rows_layout)

        self.setLayout(self._layout)

    def _add_row(self) -> None:
        row = ConditionRow(len(self._rows))
        row.btn_delete.clicked.connect(lambda: self._remove_row(row))
        self._rows.append(row)
        self._rows_layout.addWidget(row)

    def _remove_row(self, row: ConditionRow) -> None:
        self._rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()

    def get_conditions(self) -> list[TargetCondition]:
        return [row.to_condition() for row in self._rows]

    def load_conditions(self, conditions: list[TargetCondition]) -> None:
        # 清除現有
        for row in self._rows[:]:
            self._remove_row(row)
        # 加入新條件
        for cond in conditions:
            self._add_row()
            row = self._rows[-1]
            row.label.setCurrentIndex(cond.line_index)
            idx = row.attr_combo.findText(cond.attribute)
            if idx >= 0:
                row.attr_combo.setCurrentIndex(idx)
            op_idx = row.op_combo.findText(cond.operator)
            if op_idx >= 0:
                row.op_combo.setCurrentIndex(op_idx)
            row.value_spin.setValue(cond.value)
