import re

from app.models.config import AppConfig
from app.models.potential import PotentialLine


# OCR 文字 → 屬性名稱 + 數值
ATTRIBUTE_PATTERNS: dict[str, re.Pattern[str]] = {
    # 主要屬性（用於條件判斷）
    "STR%": re.compile(r"STR\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "DEX%": re.compile(r"DEX\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "INT%": re.compile(r"INT\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "LUK%": re.compile(r"LUK\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "全屬性%": re.compile(r"全屬性\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "MaxHP%": re.compile(r"MaxHP\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "物理攻擊力%": re.compile(r"物理攻擊力\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "魔法攻擊力%": re.compile(r"魔法攻擊力\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "爆擊傷害%": re.compile(r"爆[擊擎]傷害\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    # 紀錄用屬性（不參與條件判斷，但顯示在 log 中）
    "MaxMP%": re.compile(r"MaxMP\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "防禦力%": re.compile(r"防禦力\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "無視怪物防禦%": re.compile(r"無視怪物防禦\s*[力]?\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "總傷害%": re.compile(r"總傷害\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "Boss傷害%": re.compile(r"[Bb][Oo][Ss][Ss]\s*怪物攻擊時傷害\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    # 萌獸屬性
    "最終傷害%": re.compile(r"最終傷害\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
    "加持技能持續時間%": re.compile(r"加持技能持續時間\s*[:\uff1a]?\s*\+?\s*(\d+)\s*%"),
}

# 文字描述型屬性（無數值）
TEXT_ATTRIBUTE_PATTERNS: dict[str, re.Pattern[str]] = {
    "被動技能2": re.compile(r"依照被動技能\s*2\s*來增加"),
}


# OCR 常見誤讀修正表
_OCR_FIXES: list[tuple[str, str]] = [
    ("攻撃", "攻擊"),  # 日文漢字 → 繁體
    ("擊カ", "擊力"),
    ("攻擊カ", "攻擊力"),
    ("傷宝", "傷害"),
    ("屬住", "屬性"),
]


def _fix_ocr_text(text: str) -> str:
    """修正 OCR 常見誤讀字元。"""
    for wrong, correct in _OCR_FIXES:
        text = text.replace(wrong, correct)
    return text


def parse_potential_line(text: str) -> PotentialLine:
    """解析單段 OCR 文字為 PotentialLine。"""
    text = _fix_ocr_text(text)
    # 先檢查純文字屬性（無數值）
    for attr_name, pattern in TEXT_ATTRIBUTE_PATTERNS.items():
        if pattern.search(text):
            return PotentialLine(attribute=attr_name, value=0, raw_text=text)
    # 再檢查數值型屬性
    for attr_name, pattern in ATTRIBUTE_PATTERNS.items():
        match = pattern.search(text)
        if match:
            return PotentialLine(
                attribute=attr_name,
                value=int(match.group(1)),
                raw_text=text,
            )
    return PotentialLine(attribute="未知", value=0, raw_text=text)


def parse_potential_lines(raw_texts: list[str]) -> list[PotentialLine]:
    """將 OCR 碎片合併後解析出所有潛能行。

    OCR 經常把一行潛能拆成多段（如 ['STR', '+9%']），
    這裡先合併成一整段文字，再用 regex 抽出所有匹配的潛能。
    """
    merged = " ".join(raw_texts)
    merged = _fix_ocr_text(merged)

    results: list[PotentialLine] = []

    # 文字型屬性
    for attr_name, pattern in TEXT_ATTRIBUTE_PATTERNS.items():
        if pattern.search(merged):
            results.append(PotentialLine(attribute=attr_name, value=0, raw_text=merged))

    # 數值型屬性：找出所有匹配
    for attr_name, pattern in ATTRIBUTE_PATTERNS.items():
        for match in pattern.finditer(merged):
            results.append(PotentialLine(
                attribute=attr_name,
                value=int(match.group(1)),
                raw_text=match.group(0),
            ))

    return results


# ── 數值表 ──────────────────────────────────────────────

# (S潛, 罕見) for target attribute
# (S潛, 罕見) for 全屬性 (None if not applicable)
THRESHOLD_TABLE: dict[str, dict[str, tuple[tuple[int, int], tuple[int, int] | None]]] = {
    "永恆裝備·光輝套裝 (250等+)": {
        "STR": ((9, 7), (7, 6)),
        "DEX": ((9, 7), (7, 6)),
        "INT": ((9, 7), (7, 6)),
        "LUK": ((9, 7), (7, 6)),
        "MaxHP": ((12, 9), None),
    },
    "一般裝備 (神秘、漆黑、頂培)": {
        "STR": ((8, 6), (6, 5)),
        "DEX": ((8, 6), (6, 5)),
        "INT": ((8, 6), (6, 5)),
        "LUK": ((8, 6), (6, 5)),
        "MaxHP": ((11, 8), None),
    },
    "主武器": {
        "物理攻擊力": ((13, 10), None),
        "魔法攻擊力": ((13, 10), None),
    },
    "徽章": {
        "物理攻擊力": ((13, 10), None),
        "魔法攻擊力": ((13, 10), None),
    },
    "輔助武器": {
        "物理攻擊力": ((12, 9), None),
        "魔法攻擊力": ((12, 9), None),
    },
    "手套 (永恆)": {
        "STR": ((9, 7), (7, 6)),
        "DEX": ((9, 7), (7, 6)),
        "INT": ((9, 7), (7, 6)),
        "LUK": ((9, 7), (7, 6)),
    },
    "手套 (非永恆)": {
        "STR": ((8, 6), (6, 5)),
        "DEX": ((8, 6), (6, 5)),
        "INT": ((8, 6), (6, 5)),
        "LUK": ((8, 6), (6, 5)),
    },
    "萌獸": {
        "最終傷害": ((20, 20), None),
        "物理攻擊力": ((20, 20), None),
        "魔法攻擊力": ((20, 20), None),
        "加持技能持續時間": ((50, 50), None),
    },
}

# 裝備類型 → 可選屬性
EQUIPMENT_ATTRIBUTES: dict[str, list[str]] = {
    "永恆裝備·光輝套裝 (250等+)": ["STR", "DEX", "INT", "LUK", "MaxHP"],
    "一般裝備 (神秘、漆黑、頂培)": ["STR", "DEX", "INT", "LUK", "MaxHP"],
    "主武器": ["物理攻擊力", "魔法攻擊力"],
    "徽章": ["物理攻擊力", "魔法攻擊力"],
    "輔助武器": ["物理攻擊力", "魔法攻擊力"],
    "手套 (永恆)": ["STR", "DEX", "INT", "LUK"],
    "手套 (非永恆)": ["STR", "DEX", "INT", "LUK"],
    "萌獸": ["最終傷害", "物理攻擊力", "魔法攻擊力", "加持技能持續時間", "雙終被"],
}

EQUIPMENT_TYPES = list(EQUIPMENT_ATTRIBUTES.keys())

# 可勾選全屬性的屬性
STATS_WITH_ALL_STATS = {"STR", "DEX", "INT", "LUK"}

# 手套類型
GLOVE_TYPES = {"手套 (永恆)", "手套 (非永恆)"}


def _attr_to_ocr_key(attr: str) -> str:
    """將目標屬性名稱轉成 OCR 解析後的 key。"""
    mapping = {
        "STR": "STR%",
        "DEX": "DEX%",
        "INT": "INT%",
        "LUK": "LUK%",
        "MaxHP": "MaxHP%",
        "物理攻擊力": "物理攻擊力%",
        "魔法攻擊力": "魔法攻擊力%",
        "最終傷害": "最終傷害%",
        "加持技能持續時間": "加持技能持續時間%",
    }
    return mapping.get(attr, attr)


def _check_line(
    line: PotentialLine,
    target_key: str,
    target_min: int,
    all_stats_min: int | None,
    accept_crit3: bool,
) -> bool:
    """檢查單行潛能是否合格。"""
    # 目標屬性符合
    if line.attribute == target_key and line.value >= target_min:
        return True
    # 全屬性符合
    if all_stats_min is not None and line.attribute == "全屬性%" and line.value >= all_stats_min:
        return True
    # 手套：爆擊傷害 3% 也算合格
    if accept_crit3 and line.attribute == "爆擊傷害%" and line.value >= 3:
        return True
    return False


def generate_condition_summary(config: AppConfig) -> list[str]:
    """根據 config 產生人可讀的條件描述（顯示在 UI 上）。"""
    equip = config.equipment_type
    attr = config.target_attribute
    include_all = config.include_all_stats

    # 萌獸雙終被：特殊條件
    if equip == "萌獸" and attr == "雙終被":
        return [
            "需要 3 行中包含:",
            "  2 行 最終傷害% >= 20",
            "  1 行 被動技能2（依照被動技能 2 來增加）",
        ]

    thresholds = THRESHOLD_TABLE.get(equip, {}).get(attr)
    if not thresholds:
        return ["無法產生條件：裝備類型或屬性不正確"]

    (s_val, r_val), all_stats_thresholds = thresholds
    is_glove = equip in GLOVE_TYPES
    target_key = _attr_to_ocr_key(attr)

    # 萌獸：三排同屬性，不分 S潛/罕見
    if equip == "萌獸":
        return [f"三排 {target_key} >= {s_val}"]

    lines = []
    for i in range(3):
        is_legendary = (i == 0)
        min_val = s_val if is_legendary else r_val
        parts = [f"{target_key} >= {min_val}"]

        if include_all and all_stats_thresholds:
            all_min = all_stats_thresholds[0] if is_legendary else all_stats_thresholds[1]
            parts.append(f"全屬性% >= {all_min}")

        if is_glove:
            parts.append("爆擊傷害% == 3")

        tier = "S潛" if is_legendary else "罕見"
        lines.append(f"第{i+1}行({tier}): {' 或 '.join(parts)}")

    return lines


class ConditionChecker:
    """根據 AppConfig 的裝備設定判斷潛能是否合格。"""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        equip = config.equipment_type
        attr = config.target_attribute

        # 萌獸雙終被：特殊條件
        self._is_雙終被 = equip == "萌獸" and attr == "雙終被"
        if self._is_雙終被:
            self._valid = True
            return

        thresholds = THRESHOLD_TABLE.get(equip, {}).get(attr)
        if not thresholds:
            self._valid = False
            return

        self._valid = True
        (self._s_val, self._r_val), all_stats = thresholds
        self._target_key = _attr_to_ocr_key(attr)
        self._is_glove = equip in GLOVE_TYPES
        self._include_all = config.include_all_stats and all_stats is not None

        if self._include_all and all_stats:
            self._all_s, self._all_r = all_stats
        else:
            self._all_s, self._all_r = 0, 0

    def check(self, lines: list[PotentialLine]) -> bool:
        """三行都符合才回傳 True。"""
        if not self._valid:
            return False
        if len(lines) < 3:
            return False

        if self._is_雙終被:
            return self._check_雙終被(lines)

        for i in range(3):
            is_legendary = (i == 0)
            target_min = self._s_val if is_legendary else self._r_val
            all_stats_min = (self._all_s if is_legendary else self._all_r) if self._include_all else None

            if not _check_line(
                lines[i],
                self._target_key,
                target_min,
                all_stats_min,
                accept_crit3=self._is_glove,
            ):
                return False
        return True

    def _check_雙終被(self, lines: list[PotentialLine]) -> bool:
        """雙終被：2 行最終傷害 >= 20% + 1 行被動技能2。"""
        final_dmg_count = sum(
            1 for l in lines if l.attribute == "最終傷害%" and l.value >= 20
        )
        passive2_count = sum(1 for l in lines if l.attribute == "被動技能2")
        return final_dmg_count >= 2 and passive2_count >= 1
