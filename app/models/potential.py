from dataclasses import dataclass, field


@dataclass
class PotentialLine:
    """單行潛能資料。"""

    attribute: str  # 屬性名稱，如 "攻擊力%", "BOSS傷害%"
    value: int  # 數值，如 12
    raw_text: str = ""  # OCR 原始文字


def format_line(line: PotentialLine) -> str:
    """格式化單行潛能為人可讀字串。"""
    if line.attribute == "未知":
        return "(未辨識)"
    if line.value == 0:
        return line.attribute
    attr_name = line.attribute.removesuffix("%")
    if line.attribute.endswith("%"):
        return f"{attr_name} +{line.value}%"
    if line.attribute == "技能冷卻時間":
        return f"{attr_name} -{line.value}秒"
    return f"{attr_name} +{line.value}"


@dataclass
class RollResult:
    """一次洗方塊的完整結果。"""

    roll_number: int
    lines: list[PotentialLine] = field(default_factory=list)
    matched: bool = False  # 是否符合目標條件

    def summary(self) -> str:
        return " / ".join(format_line(line) for line in self.lines)
