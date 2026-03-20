import re

from app.models.config import TargetCondition
from app.models.potential import PotentialLine


# OCR 文字中常見的潛能屬性對應
ATTRIBUTE_PATTERNS: dict[str, re.Pattern[str]] = {
    "攻擊力%": re.compile(r"攻擊力\s*[:\uff1a]?\s*\+?(\d+)%"),
    "魔力%": re.compile(r"魔力\s*[:\uff1a]?\s*\+?(\d+)%"),
    "BOSS傷害%": re.compile(r"(?:BOSS|Boss|boss)\s*(?:傷害|攻擊)\s*[:\uff1a]?\s*\+?(\d+)%"),
    "無視防禦%": re.compile(r"無視\s*(?:怪物)?\s*防禦\s*[:\uff1a]?\s*\+?(\d+)%"),
    "總傷害%": re.compile(r"總傷害\s*[:\uff1a]?\s*\+?(\d+)%"),
    "暴擊傷害%": re.compile(r"暴擊傷害\s*[:\uff1a]?\s*\+?(\d+)%"),
    "全屬性%": re.compile(r"全屬性\s*[:\uff1a]?\s*\+?(\d+)%"),
    "HP%": re.compile(r"HP\s*[:\uff1a]?\s*\+?(\d+)%"),
    "MP%": re.compile(r"MP\s*[:\uff1a]?\s*\+?(\d+)%"),
    "防禦力%": re.compile(r"防禦力\s*[:\uff1a]?\s*\+?(\d+)%"),
}


def parse_potential_line(text: str) -> PotentialLine:
    """解析 OCR 文字為 PotentialLine。"""
    for attr_name, pattern in ATTRIBUTE_PATTERNS.items():
        match = pattern.search(text)
        if match:
            return PotentialLine(
                attribute=attr_name,
                value=int(match.group(1)),
                raw_text=text,
            )
    # 無法辨識的屬性
    return PotentialLine(attribute="未知", value=0, raw_text=text)


def check_condition(line: PotentialLine, condition: TargetCondition) -> bool:
    """檢查單行潛能是否符合目標條件。"""
    if condition.attribute == "任意":
        return True

    if condition.operator == "contains":
        return condition.attribute in line.raw_text

    if line.attribute != condition.attribute:
        return False

    if condition.operator == ">=":
        return line.value >= condition.value
    if condition.operator == "=":
        return line.value == condition.value

    return False


class ConditionChecker:
    """判斷 OCR 結果是否符合所有目標條件。"""

    def __init__(self, conditions: list[TargetCondition]) -> None:
        self.conditions = conditions

    def check(self, lines: list[PotentialLine]) -> bool:
        """所有條件都符合才回傳 True。"""
        for cond in self.conditions:
            if cond.line_index >= len(lines):
                return False
            if not check_condition(lines[cond.line_index], cond):
                return False
        return True
