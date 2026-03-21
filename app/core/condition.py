import re
from itertools import permutations

from app.models.config import AppConfig, LineCondition
from app.models.potential import PotentialLine


# OCR 文字 → 屬性名稱 + 數值
ATTRIBUTE_PATTERNS: dict[str, re.Pattern[str]] = {
    # 主要屬性（用於條件判斷）
    "STR%": re.compile(r"STR\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "DEX%": re.compile(r"D?EX\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "INT%": re.compile(r"INT\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "LUK%": re.compile(r"LUK\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "全屬性%": re.compile(r"全屬性\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "MaxHP%": re.compile(r"MaxHP\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "物理攻擊力%": re.compile(r"物理攻擊力\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "魔法攻擊力%": re.compile(r"魔法攻擊力\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "爆擊傷害%": re.compile(r"爆[擊擎]傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    # 紀錄用屬性（不參與條件判斷，但顯示在 log 中）
    "MaxMP%": re.compile(r"MaxMP\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "防禦力%": re.compile(r"防禦力\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "無視怪物防禦%": re.compile(r"無視怪物防禦\s*[力率]?\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "傷害%": re.compile(r"(?<![擊擎時終])傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "Boss傷害%": re.compile(r"[Bb][Oo][Ss][Ss]\s*怪物攻擊時傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "爆擊機率%": re.compile(r"爆擊機率\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "HP恢復效率%": re.compile(r"HP恢復道具及恢復技能效率\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "MP消耗%": re.compile(r"所有技能的?MP消耗\s*[:\uff1a]?\s*-?\s*(\d+) ?%"),
    # 以角色等級為準每N級 STAT +N（非%，特殊處理）
    "每級STR": re.compile(r"以角色等級為準每\d+級\s*STR\s*\+?\s*(\d+)"),
    "每級DEX": re.compile(r"以角色等級為準每\d+級\s*DEX\s*\+?\s*(\d+)"),
    "每級INT": re.compile(r"以角色等級為準每\d+級\s*INT\s*\+?\s*(\d+)"),
    "每級LUK": re.compile(r"以角色等級為準每\d+級\s*LUK\s*\+?\s*(\d+)"),
    # 純數值屬性（非%，紀錄用）
    "STR": re.compile(r"(?<![a-zA-Z])STR\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "DEX": re.compile(r"(?<![a-zA-Z])DEX\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "INT": re.compile(r"(?<![a-zA-Z])INT\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "LUK": re.compile(r"(?<![a-zA-Z])LUK\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "MaxHP": re.compile(r"MaxHP\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "MaxMP": re.compile(r"MaxMP\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "物理攻擊力": re.compile(r"物理攻擊力\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "魔法攻擊力": re.compile(r"魔法攻擊力\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    "防禦力": re.compile(r"防禦力\s*[:\uff1a]?\s*\+\s*(\d+)(?!\s*%)"),
    # 萌獸屬性
    "最終傷害%": re.compile(r"最終傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "加持技能持續時間%": re.compile(r"加持技能持續時間\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
}

# 文字描述型屬性（無數值）
TEXT_ATTRIBUTE_PATTERNS: dict[str, re.Pattern[str]] = {
    "被動技能2": re.compile(r"依照被動技能\s*2\s*來增加"),
    "HP恢復效率": re.compile(r"HP恢復道具及恢復技能效率"),
    "MP消耗": re.compile(r"所有技能的?MP消耗"),
    "每級STR": re.compile(r"以角色等級為準每\d+級\s*STR"),
    "每級DEX": re.compile(r"以角色等級為準每\d+級\s*DEX"),
    "每級INT": re.compile(r"以角色等級為準每\d+級\s*INT"),
    "每級LUK": re.compile(r"以角色等級為準每\d+級\s*LUK"),
}


# OCR 常見誤讀修正表
_OCR_FIXES: list[tuple[str, str]] = [
    ("攻撃", "攻擊"),  # 日文漢字 → 繁體
    ("擊カ", "擊力"),
    ("攻擊カ", "攻擊力"),
    ("傷宝", "傷害"),
    ("屬住", "屬性"),
    # 簡體 → 繁體
    ("最终", "最終"),
    ("全国性", "全屬性"),
    ("伤害", "傷害"),
    ("属性", "屬性"),
    ("时间", "時間"),
    ("恢复", "恢復"),
    ("衣照", "依照"),
    ("来增加", "來增加"),
    ("攻擎", "攻擊"),
    ("爆机率", "爆擊機率"),
    ("爆機率", "爆擊機率"),
    ("爆率", "爆擊機率"),
    ("机率", "機率"),
    # 以角色等級為準系列
    ("等级", "等級"),
    ("级", "級"),
    ("为准", "為準"),
    ("為准", "為準"),
    ("为準", "為準"),
    # 屬性誤讀
    ("勿理", "物理"),
    ("厨性", "屬性"),
    ("MaxMOP", "MaxMP"),
]


def _fix_ocr_text(text: str) -> str:
    """修正 OCR 常見誤讀字元。"""
    # 移除 OCR 產生的多餘空格（如「魔 法攻擊力」→「魔法攻擊力」）
    text = text.replace(" ", "")
    for wrong, correct in _OCR_FIXES:
        text = text.replace(wrong, correct)
    return text


def parse_potential_line(text: str) -> PotentialLine:
    """解析單段 OCR 文字為 PotentialLine。"""
    fixed = _fix_ocr_text(text)
    # 先檢查數值型屬性（含 % 的較精確）
    for attr_name, pattern in ATTRIBUTE_PATTERNS.items():
        match = pattern.search(fixed)
        if match:
            return PotentialLine(
                attribute=attr_name,
                value=int(match.group(1)),
                raw_text=text,
            )
    # 再檢查純文字屬性（無數值，作為 fallback）
    for attr_name, pattern in TEXT_ATTRIBUTE_PATTERNS.items():
        if pattern.search(fixed):
            return PotentialLine(attribute=attr_name, value=0, raw_text=text)
    return PotentialLine(attribute="未知", value=0, raw_text=text)


def _parse_merged_text(merged: str) -> PotentialLine:
    """從合併後的文字中解析出一個 PotentialLine。"""
    merged = _fix_ocr_text(merged)

    # 數值型屬性：取第一個匹配（含 % 的較精確，優先）
    best: tuple[int, PotentialLine] | None = None
    for attr_name, pattern in ATTRIBUTE_PATTERNS.items():
        m = pattern.search(merged)
        if m:
            candidate = (m.start(), PotentialLine(
                attribute=attr_name,
                value=int(m.group(1)),
                raw_text=m.group(0),
            ))
            if best is None or candidate[0] < best[0]:
                best = candidate

    if best is not None:
        return best[1]

    # 純文字屬性（無數值，作為 fallback）
    for attr_name, pattern in TEXT_ATTRIBUTE_PATTERNS.items():
        if pattern.search(merged):
            return PotentialLine(attribute=attr_name, value=0, raw_text=merged)

    return PotentialLine(attribute="未知", value=0, raw_text=merged)


_VALUE_ONLY_RE = re.compile(r"^[+\-]?\d+%?$")


def _merge_value_fragments(
    fragments: list[tuple[str, float]],
) -> list[tuple[str, float]]:
    """將純數值碎片（如 '+10%'）合併到 y 座標最近的屬性碎片。"""
    if len(fragments) <= 1:
        return fragments

    value_indices: set[int] = set()
    for i, (text, _) in enumerate(fragments):
        if _VALUE_ONLY_RE.match(text.strip()):
            value_indices.add(i)

    if not value_indices or len(value_indices) == len(fragments):
        return fragments

    result = list(fragments)
    merged: set[int] = set()
    used_targets: set[int] = set()

    for vi in sorted(value_indices):
        vtext, vy = result[vi]
        # 找 y 座標最近且尚未接收過數值的屬性碎片
        best_idx = -1
        best_dist = float("inf")
        for j, (_, jy) in enumerate(result):
            if j in value_indices or j in used_targets:
                continue
            dist = abs(jy - vy)
            if dist < best_dist:
                best_dist = dist
                best_idx = j
        if best_idx >= 0:
            atext, ay = result[best_idx]
            result[best_idx] = (atext + vtext, ay)
            merged.add(vi)
            used_targets.add(best_idx)

    return [f for i, f in enumerate(result) if i not in merged]


def _group_fragments_by_y(
    fragments: list[tuple[str, float]],
    num_rows: int = 3,
) -> list[str]:
    """將 OCR 碎片按 y 座標分群成 num_rows 個物理行。

    按 y_center 排序後，用最大的 (num_rows-1) 個相鄰間距作為切割點。
    每個群組內的文字合併。不足 num_rows 群時補空字串。
    """
    if not fragments:
        return [""] * num_rows

    sorted_frags = sorted(fragments, key=lambda f: f[1])

    if len(sorted_frags) == 1:
        rows = [sorted_frags[0][0]]
        while len(rows) < num_rows:
            rows.append("")
        return rows

    # 計算相鄰碎片的 y 距離
    gaps: list[tuple[float, int]] = []
    for i in range(len(sorted_frags) - 1):
        gap = sorted_frags[i + 1][1] - sorted_frags[i][1]
        gaps.append((gap, i))

    # 找最大的間距作為切割點，只選間距 >= MIN_ROW_GAP 的
    MIN_ROW_GAP = 5.0
    gaps_sorted = sorted(gaps, key=lambda g: g[0], reverse=True)

    split_indices: list[int] = []
    for gap_val, idx in gaps_sorted:
        if len(split_indices) >= num_rows - 1:
            break
        if gap_val >= MIN_ROW_GAP:
            split_indices.append(idx)
    split_indices.sort()

    # 按切割點分群
    groups: list[list[str]] = []
    start = 0
    for idx in split_indices:
        groups.append([f[0] for f in sorted_frags[start : idx + 1]])
        start = idx + 1
    groups.append([f[0] for f in sorted_frags[start:]])

    rows = ["".join(g) for g in groups]
    while len(rows) < num_rows:
        rows.append("")
    return rows


def parse_potential_lines(
    raw_texts: list[tuple[str, float]],
) -> list[PotentialLine]:
    """將 OCR 碎片按 y 座標分群成 3 個物理行，再逐行解析。

    永遠回傳恰好 3 個 PotentialLine，偵測不到的行填 PotentialLine("未知", 0)。
    若相鄰行皆為未知，嘗試合併後重新解析（處理 OCR 碎片跨行分割的情況）。
    """
    raw_texts = _merge_value_fragments(raw_texts)
    rows = _group_fragments_by_y(raw_texts, num_rows=3)
    result: list[PotentialLine] = []
    for row_text in rows:
        if not row_text.strip():
            result.append(PotentialLine(attribute="未知", value=0))
        else:
            result.append(_parse_merged_text(row_text))

    # 後處理：相鄰未知行嘗試合併
    for i in range(len(result) - 1):
        if result[i].attribute != "未知" or result[i + 1].attribute != "未知":
            continue
        if not rows[i].strip() or not rows[i + 1].strip():
            continue
        # 若下一行以 % 開頭，不合併（避免偷走隔壁行的 %）
        if rows[i + 1].lstrip().startswith("%"):
            continue
        merged = rows[i] + rows[i + 1]
        parsed = _parse_merged_text(merged)
        if parsed.attribute != "未知":
            result[i] = parsed
            result[i + 1] = PotentialLine(attribute="未知", value=0, raw_text=rows[i + 1])

    return result


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

# 自訂模式可選屬性（依裝備類型分類）
CUSTOM_SELECTABLE_ATTRIBUTES: dict[str, list[str]] = {
    "裝備": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "手套": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP", "爆擊傷害"],
    "武器": ["物理攻擊力", "魔法攻擊力"],
    "萌獸": ["最終傷害", "物理攻擊力", "魔法攻擊力", "加持技能持續時間", "被動技能2"],
}

# 裝備類型 → 自訂模式屬性分類
_EQUIP_TO_CUSTOM_CATEGORY: dict[str, str] = {
    "永恆裝備·光輝套裝 (250等+)": "裝備",
    "一般裝備 (神秘、漆黑、頂培)": "裝備",
    "主武器": "武器",
    "徽章": "武器",
    "輔助武器": "武器",
    "手套 (永恆)": "手套",
    "手套 (非永恆)": "手套",
    "萌獸": "萌獸",
}


def get_custom_attributes(equipment_type: str) -> list[str]:
    """取得該裝備類型在自訂模式可選的屬性列表。"""
    category = _EQUIP_TO_CUSTOM_CATEGORY.get(equipment_type, "裝備")
    return CUSTOM_SELECTABLE_ATTRIBUTES[category]


def _attr_to_ocr_key(attr: str) -> str:
    """將目標屬性名稱轉成 OCR 解析後的 key。"""
    mapping = {
        "STR": "STR%",
        "DEX": "DEX%",
        "INT": "INT%",
        "LUK": "LUK%",
        "全屬性": "全屬性%",
        "MaxHP": "MaxHP%",
        "物理攻擊力": "物理攻擊力%",
        "魔法攻擊力": "魔法攻擊力%",
        "最終傷害": "最終傷害%",
        "加持技能持續時間": "加持技能持續時間%",
        "爆擊傷害": "爆擊傷害%",
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


_POSITION_LABELS = ["任意一排", "第1排", "第2排", "第3排"]


def _generate_custom_summary(custom_lines: list[LineCondition]) -> list[str]:
    """自訂模式的條件摘要。"""
    lines = []
    for lc in custom_lines:
        pos_label = _POSITION_LABELS[lc.position] if lc.position < len(_POSITION_LABELS) else f"第{lc.position}排"
        if lc.attribute == "被動技能2":
            lines.append(f"{pos_label}: 被動技能2（依照被動技能 2 來增加）")
        else:
            lines.append(f"{pos_label}: {lc.attribute} 至少 {lc.min_value}%")
    return lines


def generate_condition_summary(config: AppConfig) -> list[str]:
    """根據 config 產生人可讀的條件描述（顯示在 UI 上）。"""
    if not config.use_preset:
        return _generate_custom_summary(config.custom_lines)

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

    # 萌獸：三排同屬性，不分 S潛/罕見
    if equip == "萌獸":
        return [f"三排: {attr} 至少 {s_val}%"]

    # 精簡一行格式
    parts = [f"三排 {attr} 至少 {s_val}%/{r_val}%"]

    if include_all and all_stats_thresholds:
        all_s, all_r = all_stats_thresholds
        parts.append(f"全屬性 至少 {all_s}%/{all_r}%")

    if is_glove:
        parts.append("爆擊傷害 至少 3%")

    return [" 或 ".join(parts)]


class ConditionChecker:
    """根據 AppConfig 的裝備設定判斷潛能是否合格。"""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._use_preset = config.use_preset

        if not self._use_preset:
            self._custom_lines = config.custom_lines
            self._valid = True
            return

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
        """所有行都符合才回傳 True。"""
        if not self._valid:
            return False
        if len(lines) < 3:
            return False

        if not self._use_preset:
            return self._check_custom(lines)

        if self._is_雙終被:
            return self._check_雙終被(lines)

        return self._check_preset_any_pos(lines)

    def _check_preset_any_pos(self, lines: list[PotentialLine]) -> bool:
        """預設模式任意位置：嘗試所有排列找到一組符合的分配。"""
        for perm in permutations(lines[:3]):
            ok = True
            for i in range(3):
                is_legendary = (i == 0)
                target_min = self._s_val if is_legendary else self._r_val
                all_stats_min = (self._all_s if is_legendary else self._all_r) if self._include_all else None
                if not _check_line(
                    perm[i],
                    self._target_key,
                    target_min,
                    all_stats_min,
                    accept_crit3=self._is_glove,
                ):
                    ok = False
                    break
            if ok:
                return True
        return False

    def _check_custom(self, lines: list[PotentialLine]) -> bool:
        """自訂模式：指定位置條件用 AND，任意一排條件用 OR。

        所有指定位置（position>=1）的條件必須全部符合，
        任意一排（position=0）的條件只要任一符合即可。
        """
        any_pos_conditions = []
        fixed_pos_conditions = []
        for lc in self._custom_lines:
            if lc.position == 0:
                any_pos_conditions.append(lc)
            else:
                fixed_pos_conditions.append(lc)

        # 指定位置條件：全部必須符合（AND）
        for lc in fixed_pos_conditions:
            idx = lc.position - 1
            if idx >= len(lines) or not self._match_line(lc, lines[idx]):
                return False

        # 任意一排條件：任一符合即可（OR）
        if any_pos_conditions:
            if not any(
                any(self._match_line(lc, line) for line in lines[:3])
                for lc in any_pos_conditions
            ):
                return False

        return True

    @staticmethod
    def _match_line(lc: LineCondition, line: PotentialLine) -> bool:
        """檢查單行是否符合條件。"""
        if lc.attribute == "被動技能2":
            return line.attribute == "被動技能2"
        target_key = _attr_to_ocr_key(lc.attribute)
        return line.attribute == target_key and line.value >= lc.min_value

    def _check_雙終被(self, lines: list[PotentialLine]) -> bool:
        """雙終被：2 行最終傷害 >= 20% + 1 行被動技能2。"""
        final_dmg_count = sum(
            1 for l in lines if l.attribute == "最終傷害%" and l.value >= 20
        )
        passive2_count = sum(1 for l in lines if l.attribute == "被動技能2")
        return final_dmg_count >= 2 and passive2_count >= 1
