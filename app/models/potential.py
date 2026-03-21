from dataclasses import dataclass, field


@dataclass
class PotentialLine:
    """單行潛能資料。"""

    attribute: str  # 屬性名稱，如 "攻擊力%", "BOSS傷害%"
    value: int  # 數值，如 12
    raw_text: str = ""  # OCR 原始文字


@dataclass
class RollResult:
    """一次洗方塊的完整結果。"""

    roll_number: int
    lines: list[PotentialLine] = field(default_factory=list)
    matched: bool = False  # 是否符合目標條件

    def summary(self) -> str:
        parts = []
        for line in self.lines:
            if line.attribute == "未知":
                parts.append("(未辨識)")
            elif line.value == 0:
                parts.append(line.attribute)
            else:
                attr_name = line.attribute.removesuffix("%")
                if line.attribute.endswith("%"):
                    parts.append(f"{attr_name} +{line.value}%")
                elif line.attribute == "技能冷卻時間":
                    parts.append(f"{attr_name} -{line.value}秒")
                else:
                    parts.append(f"{attr_name} +{line.value}")
        return " / ".join(parts)
