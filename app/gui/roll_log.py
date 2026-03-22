from PyQt6.QtWidgets import QGroupBox, QListWidget, QListWidgetItem, QVBoxLayout

from app.models.potential import RollResult


class RollLog(QGroupBox):
    """洗方塊歷史紀錄顯示。"""

    MAX_ENTRIES = 1000

    def __init__(self, parent=None) -> None:
        super().__init__("洗方塊紀錄", parent)
        self._results: list[RollResult] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def add_result(self, result: RollResult) -> None:
        self._results.append(result)
        icon = "\u2705" if result.matched else "\u274c"
        if result.roll_number == 0:
            text = f"[初始潛能] | {icon} {result.summary()}"
        else:
            text = f"#{result.roll_number:05d} | {icon} {result.summary()}"
        item = QListWidgetItem(text)
        self.list_widget.addItem(item)
        self.list_widget.scrollToBottom()

        # 超過上限時移除最舊的紀錄
        while self.list_widget.count() > self.MAX_ENTRIES:
            self.list_widget.takeItem(0)
            self._results.pop(0)

    def clear_log(self) -> None:
        self._results.clear()
        self.list_widget.clear()

    def export_csv(self) -> str:
        # 從實際結果推斷欄數（取最大 line 數，至少 2）
        max_cols = max((len(r.lines) for r in self._results), default=3)
        header_cols = ",".join(f"line{i+1}" for i in range(max_cols))
        lines = [f"roll_number,matched,{header_cols}"]
        for r in self._results:
            potentials = [l.raw_text for l in r.lines]
            while len(potentials) < max_cols:
                potentials.append("")
            quoted = ",".join(f'"{p}"' for p in potentials)
            lines.append(f"{r.roll_number},{r.matched},{quoted}")
        return "\n".join(lines)
