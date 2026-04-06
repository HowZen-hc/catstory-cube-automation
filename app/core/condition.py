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
    "爆擊傷害%": re.compile(r"爆.\s*傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    # 紀錄用屬性（不參與條件判斷，但顯示在 log 中）
    "MaxMP%": re.compile(r"MaxMP\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "防禦力%": re.compile(r"防禦力\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "無視怪物防禦%": re.compile(r"無視怪物防禦\s*[力率]?\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    # 必須在 爆擊傷害% 之後，避免 爆X傷害 被誤判為傷害
    "傷害%": re.compile(r"(?<![擊擎時終])傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "Boss傷害%": re.compile(r"[Bb][Oo][Ss][Ss]\s*怪物攻擊時\s*傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
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
    # 技能冷卻時間（帽子用，非 %）
    "技能冷卻時間": re.compile(r"技能冷卻時間\s*-?\s*(\d+)\s*秒"),
    # 萌獸屬性
    "最終傷害%": re.compile(r"最終\s*傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
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
    ("时間", "時間"),
    ("恢复", "恢復"),
    ("衣照", "依照"),
    ("来增加", "來增加"),
    ("攻擎", "攻擊"),
    ("攻革", "攻擊"),
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
    ("屈性", "屬性"),
    ("恢覆", "恢復"),
    ("MaxMOP", "MaxMP"),
    ("MaxCP", "MaxMP"),
    # 傷害誤讀（傷 → 低/值/佩/集/優/信）
    ("低害", "傷害"),
    ("值害", "傷害"),
    ("佩害", "傷害"),
    ("集害", "傷害"),
    ("優害", "傷害"),
    ("信害", "傷害"),
    # 害 → 喜 誤讀
    ("傷喜", "傷害"),
    ("集喜", "傷害"),
    # 傷害兩字被讀成一個字（最終喜/最終害 → 最終傷害）
    ("最終喜", "最終傷害"),
    ("最終害", "最終傷害"),
    # 攻擊誤讀
    ("攻事", "攻擊"),
    # 爆擊誤讀（爆 → 爆華/煬）
    ("爆華", "爆擊"),
    ("煬擊", "爆擊"),
    # LUK/DEX 誤讀
    ("LIK", "LUK"),
    ("DIK", "DEX"),
    # 屬性誤讀（屬 → 屋/國/慶）
    ("全屋性", "全屬性"),
    ("全國性", "全屬性"),
    ("全慶性", "全屬性"),
    # 簡體 → 繁體（視）
    ("無视", "無視"),
    # HP恢復道具誤讀（恢递具 → 恢復道具，H → HP）
    # 注意：H恢復道具 依賴上一行先將 恢递具 → 恢復道具，順序不可對調
    ("恢递具", "恢復道具"),
    ("H恢復道具", "HP恢復道具"),
]

# MaxHP/MaxMP 誤讀（M 被吃掉，axHP → MaxHP），前方不能有字母以避免誤改正確的 MaxHP
_OCR_AX_TO_MAX = re.compile(r"(?<![A-Za-z])ax(HP|MP)")
# INT 誤讀（I↔1 混淆 + N↔T/M 混淆），前方不能有字母數字以避免誤匹配
_OCR_INT_FIXES = re.compile(r"(?<![A-Za-z0-9])(?:1NT|1IT|1TT|IIT|IT|IM)(?=[\+\d])")
_OCR_DIGIT_FIXES = re.compile(r"(?<=[+\-])B(?=%)")
# OCR 有時在 % 後多讀到下一碎片的殘留數字（如 +6%6 → +6%）
_TRAILING_AFTER_PERCENT = re.compile(r"(%)\d+$")
# % 被 OCR 誤讀為 9（如 +79 → +7%），僅在文字中無 % 時套用
_PERCENT_AS_NINE = re.compile(r"(\d)9$")


def _fix_ocr_text(text: str) -> str:
    """修正 OCR 常見誤讀字元。"""
    # 移除 OCR 產生的多餘空白（含全形空格 \u3000、tab 等 Unicode 空白）
    text = re.sub(r"\s", "", text)
    for wrong, correct in _OCR_FIXES:
        text = text.replace(wrong, correct)
    # axHP → MaxHP, axMP → MaxMP（前方無字母時）
    text = _OCR_AX_TO_MAX.sub(r"Max\1", text)
    # INT 誤讀修正（IT/1NT/1IT/1TT/IIT → INT）
    text = _OCR_INT_FIXES.sub("INT", text)
    # 數值位置的 B → 8（如 +B% → +8%）
    text = _OCR_DIGIT_FIXES.sub("8", text)
    # 移除 % 後多餘的數字（如 +6%6 → +6%）
    text = _TRAILING_AFTER_PERCENT.sub(r"\1", text)
    return text


def _try_parse(fixed: str, text: str) -> PotentialLine | None:
    """嘗試從修正後文字解析屬性，成功回傳 PotentialLine，失敗回傳 None。"""
    for attr_name, pattern in ATTRIBUTE_PATTERNS.items():
        match = pattern.search(fixed)
        if match:
            return PotentialLine(
                attribute=attr_name,
                value=int(match.group(1)),
                raw_text=text,
            )
    for attr_name, pattern in TEXT_ATTRIBUTE_PATTERNS.items():
        if pattern.search(fixed):
            return PotentialLine(attribute=attr_name, value=0, raw_text=text)
    return None


def parse_potential_line(text: str) -> PotentialLine:
    """解析單段 OCR 文字為 PotentialLine。"""
    fixed = _fix_ocr_text(text)
    result = _try_parse(fixed, text)
    if result is not None:
        return result
    # Fallback: % 可能被 OCR 誤讀為 9（如 +79 → +7%），僅在無 % 且首次解析失敗時嘗試
    if "%" not in fixed:
        retried = _PERCENT_AS_NINE.sub(r"\1%", fixed)
        if retried != fixed:
            result = _try_parse(retried, text)
            if result is not None:
                return result
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

    # Fallback: % 可能被 OCR 誤讀為 9，僅在無 % 且首次解析失敗時嘗試
    if "%" not in merged:
        retried = _PERCENT_AS_NINE.sub(r"\1%", merged)
        if retried != merged:
            result = _try_parse(retried, merged)
            if result is not None:
                return result

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
    num_rows: int = 3,
) -> list[PotentialLine]:
    """將 OCR 碎片按 y 座標分群成 num_rows 個物理行，再逐行解析。

    永遠回傳恰好 num_rows 個 PotentialLine，偵測不到的行填 PotentialLine("未知", 0)。
    若相鄰行皆為未知，嘗試合併後重新解析（處理 OCR 碎片跨行分割的情況）。
    """
    raw_texts = _merge_value_fragments(raw_texts)
    rows = _group_fragments_by_y(raw_texts, num_rows=num_rows)
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
    "永恆 / 光輝": {
        "STR": ((9, 7), (7, 6)),
        "DEX": ((9, 7), (7, 6)),
        "INT": ((9, 7), (7, 6)),
        "LUK": ((9, 7), (7, 6)),
        "MaxHP": ((12, 9), None),
        "全屬性": ((7, 6), None),
    },
    "一般裝備 (神秘、漆黑、頂培)": {
        "STR": ((8, 6), (6, 5)),
        "DEX": ((8, 6), (6, 5)),
        "INT": ((8, 6), (6, 5)),
        "LUK": ((8, 6), (6, 5)),
        "MaxHP": ((11, 8), None),
        "全屬性": ((6, 5), None),
    },
    "主武器 / 徽章 (米特拉)": {
        "物理攻擊力": ((13, 10), None),
        "魔法攻擊力": ((13, 10), None),
    },
    "輔助武器 (副手)": {
        "物理攻擊力": ((12, 9), None),
        "魔法攻擊力": ((12, 9), None),
    },
    "手套 (永恆)": {
        "STR": ((9, 7), (7, 6)),
        "DEX": ((9, 7), (7, 6)),
        "INT": ((9, 7), (7, 6)),
        "LUK": ((9, 7), (7, 6)),
        "全屬性": ((7, 6), None),
        "MaxHP": ((12, 9), None),
    },
    "手套 (非永恆)": {
        "STR": ((8, 6), (6, 5)),
        "DEX": ((8, 6), (6, 5)),
        "INT": ((8, 6), (6, 5)),
        "LUK": ((8, 6), (6, 5)),
        "全屬性": ((6, 5), None),
        "MaxHP": ((11, 8), None),
    },
    "帽子 (永恆)": {
        "STR": ((9, 7), (7, 6)),
        "DEX": ((9, 7), (7, 6)),
        "INT": ((9, 7), (7, 6)),
        "LUK": ((9, 7), (7, 6)),
        "MaxHP": ((12, 9), None),
        "全屬性": ((7, 6), None),
    },
    "帽子 (非永恆)": {
        "STR": ((8, 6), (6, 5)),
        "DEX": ((8, 6), (6, 5)),
        "INT": ((8, 6), (6, 5)),
        "LUK": ((8, 6), (6, 5)),
        "MaxHP": ((11, 8), None),
        "全屬性": ((6, 5), None),
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
    "永恆 / 光輝": ["所有屬性", "STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "一般裝備 (神秘、漆黑、頂培)": ["所有屬性", "STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "主武器 / 徽章 (米特拉)": ["物理攻擊力", "魔法攻擊力"],
    "輔助武器 (副手)": ["物理攻擊力", "魔法攻擊力"],
    "手套": ["所有屬性", "STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "帽子": ["所有屬性", "STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "萌獸": ["最終傷害", "物理攻擊力", "魔法攻擊力", "加持技能持續時間", "雙終被"],
}

EQUIPMENT_TYPES = list(EQUIPMENT_ATTRIBUTES.keys())

# 選擇 STR/DEX/INT/LUK 時自動含全屬性的屬性
_STATS_WITH_ALL_STATS = {"STR", "DEX", "INT", "LUK"}

# 手套類型
GLOVE_TYPES = {"手套"}

# 帽子類型
HAT_TYPES = {"帽子"}

# 需要 is_eternal 解析的裝備類型
ETERNAL_EQUIP_TYPES = {"手套", "帽子"}


def _resolve_equip_type(equip: str, is_eternal: bool) -> str:
    """將合併後的裝備名稱解析為 THRESHOLD_TABLE 的 key。"""
    if equip in ETERNAL_EQUIP_TYPES:
        suffix = "永恆" if is_eternal else "非永恆"
        return f"{equip} ({suffix})"
    return equip

# OCR 容錯值：防止 8→6、5↔6 等誤讀導致好結果被洗掉
# 套用對象：主屬性、全屬性、HP、副手攻擊力
# 不套用：爆擊傷害、技能冷卻時間、主武器/徽章、萌獸
_OCR_TOLERANCE = 2
_NO_TOLERANCE_EQUIP = {"主武器 / 徽章 (米特拉)", "萌獸"}

# 自訂模式可選屬性（依裝備類型分類）
CUSTOM_SELECTABLE_ATTRIBUTES: dict[str, list[str]] = {
    "裝備": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "手套": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP", "爆擊傷害"],
    "帽子": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP", "技能冷卻時間"],
    "武器": ["物理攻擊力", "魔法攻擊力"],
    "萌獸": ["最終傷害", "物理攻擊力", "魔法攻擊力", "加持技能持續時間", "被動技能2"],
}

# 裝備類型 → 自訂模式屬性分類
_EQUIP_TO_CUSTOM_CATEGORY: dict[str, str] = {
    "永恆 / 光輝": "裝備",
    "一般裝備 (神秘、漆黑、頂培)": "裝備",
    "主武器 / 徽章 (米特拉)": "武器",
    "輔助武器 (副手)": "武器",
    "手套": "手套",
    "帽子": "帽子",
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
    accept_cooldown: bool = False,
    tolerance: int = 0,
) -> bool:
    """檢查單行潛能是否合格。"""
    # 目標屬性符合（含容錯）
    if line.attribute == target_key and line.value + tolerance >= target_min:
        return True
    # 全屬性符合（含容錯）
    if all_stats_min is not None and line.attribute == "全屬性%" and line.value + tolerance >= all_stats_min:
        return True
    # 手套：爆擊傷害 3% 也算合格（不套用容錯）
    if accept_crit3 and line.attribute == "爆擊傷害%" and line.value >= 3:
        return True
    # 帽子：技能冷卻時間 -1秒 也算合格（不套用容錯）
    if accept_cooldown and line.attribute == "技能冷卻時間" and line.value >= 1:
        return True
    return False


_TWO_LINE_CUBE_TYPES = {"絕對附加方塊", "絕對附加方塊 (僅洗兩排)"}


def get_num_lines(cube_type: str) -> int:
    """根據方塊類型回傳潛能排數（絕對附加方塊只洗 2 排）。"""
    return 2 if cube_type in _TWO_LINE_CUBE_TYPES else 3


_POSITION_LABELS = ["任意一排", "第 1 排", "第 2 排", "第 3 排"]


def _format_custom_line(lc: LineCondition) -> str:
    """格式化單條自訂條件。"""
    if lc.attribute == "被動技能2":
        return "被動技能2（依照被動技能 2 來增加）"
    if lc.attribute == "技能冷卻時間":
        return "技能冷卻時間 -1 秒"
    return f"{lc.attribute} ≥ {lc.min_value}%"


def _generate_custom_summary(custom_lines: list[LineCondition]) -> list[str]:
    """自訂模式的條件摘要。"""
    fixed = [lc for lc in custom_lines if lc.position != 0]
    any_pos = [lc for lc in custom_lines if lc.position == 0]

    lines: list[str] = []

    if fixed and any_pos:
        # 混合模式
        lines.append("需同時符合:")
        for lc in fixed:
            pos_label = _POSITION_LABELS[lc.position] if lc.position < len(_POSITION_LABELS) else f"第 {lc.position} 排"
            lines.append(f"  {pos_label}: {_format_custom_line(lc)}")
        lines.append("且符合任一:")
        for lc in any_pos:
            lines.append(f"  任意一排: {_format_custom_line(lc)}")
    elif fixed:
        # 只有指定位置
        lines.append("需同時符合:")
        for lc in fixed:
            pos_label = _POSITION_LABELS[lc.position] if lc.position < len(_POSITION_LABELS) else f"第 {lc.position} 排"
            lines.append(f"  {pos_label}: {_format_custom_line(lc)}")
    elif any_pos:
        # 只有任意一排
        lines.append("符合任一即可:")
        for lc in any_pos:
            lines.append(f"  任意一排: {_format_custom_line(lc)}")

    return lines


def generate_condition_summary(config: AppConfig) -> list[str]:
    """根據 config 產生人可讀的條件描述（顯示在 UI 上）。"""
    if not config.use_preset:
        return _generate_custom_summary(config.custom_lines)

    equip = config.equipment_type
    resolved = _resolve_equip_type(equip, config.is_eternal)
    attr = config.target_attribute
    num_lines = get_num_lines(config.cube_type)

    # 萌獸雙終被：特殊條件
    if equip == "萌獸" and attr == "雙終被":
        return [
            "需要 3 排中包含:",
            "  2 排 最終傷害 ≥ 20%",
            "  1 排 被動技能2（依照被動技能 2 來增加）",
        ]

    is_glove = equip in GLOVE_TYPES
    is_hat = equip in HAT_TYPES

    # 所有屬性：列出所有可接受的屬性
    if attr == "所有屬性":
        return _generate_all_attrs_summary(resolved, is_glove, is_hat, num_lines)

    thresholds = THRESHOLD_TABLE.get(resolved, {}).get(attr)
    if not thresholds:
        return ["無法產生條件：裝備類型或屬性不正確"]

    (s_val, r_val), all_stats_thresholds = thresholds

    # 萌獸：三排同屬性，不分 S潛/罕見
    if equip == "萌獸":
        return [f"三排: {attr} ≥ {s_val}%"]

    # 絕對附加方塊：兩排都是 S潛
    if num_lines == 2:
        parts = [f"  · {attr} {s_val}%"]
        if attr in _STATS_WITH_ALL_STATS and all_stats_thresholds:
            all_s, _all_r = all_stats_thresholds
            parts.append(f"  · 全屬性 {all_s}%")
        if is_glove:
            parts.append("  · 爆擊傷害 3%")
        if is_hat:
            parts.append("  · 技能冷卻時間 -1 秒")
        if len(parts) == 1:
            return [f"兩排: {attr} {s_val}%"]
        return ["兩排需符合以下任一:"] + parts

    parts = [f"  · {attr} {s_val}% or {r_val}%"]

    # STR/DEX/INT/LUK 自動含全屬性
    if attr in _STATS_WITH_ALL_STATS and all_stats_thresholds:
        all_s, all_r = all_stats_thresholds
        parts.append(f"  · 全屬性 {all_s}% or {all_r}%")

    if is_glove:
        parts.append("  · 爆擊傷害 3%")

    if is_hat:
        parts.append("  · 技能冷卻時間 -1 秒")

    if len(parts) == 1:
        return [f"每排: {attr} {s_val}% or {r_val}%"]
    return ["每排需符合以下任一:"] + parts


def _generate_all_attrs_summary(
    equip: str, is_glove: bool, is_hat: bool, num_lines: int = 3,
) -> list[str]:
    """所有屬性模式的條件摘要。"""
    equip_thresholds = THRESHOLD_TABLE.get(equip, {})
    parts: list[str] = []

    # 逐一列出每個屬性
    for attr in ("STR", "DEX", "INT", "LUK"):
        if attr not in equip_thresholds:
            continue
        (s_val, r_val), _ = equip_thresholds[attr]
        if num_lines == 2:
            parts.append(f"  · {attr} {s_val}%")
        else:
            parts.append(f"  · {attr} {s_val}% or {r_val}%")

    # 全屬性（從第一個主屬性取）
    stat_attrs = [a for a in ("STR", "DEX", "INT", "LUK") if a in equip_thresholds]
    if stat_attrs:
        _, all_stats = equip_thresholds[stat_attrs[0]]
        if all_stats:
            all_s, all_r = all_stats
            if num_lines == 2:
                parts.append(f"  · 全屬性 {all_s}%")
            else:
                parts.append(f"  · 全屬性 {all_s}% or {all_r}%")

    if "MaxHP" in equip_thresholds:
        (s_val, r_val), _ = equip_thresholds["MaxHP"]
        if num_lines == 2:
            parts.append(f"  · MaxHP {s_val}%")
        else:
            parts.append(f"  · MaxHP {s_val}% or {r_val}%")

    if is_glove:
        parts.append("  · 爆擊傷害 3%")
    if is_hat:
        parts.append("  · 技能冷卻時間 -1 秒")

    # 兩個一排，減少 GUI 佔用空間
    paired = []
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            paired.append(parts[i] + "  " + parts[i + 1])
        else:
            paired.append(parts[i])

    row_label = "兩排" if num_lines == 2 else "三排"
    return [f"{row_label}需為同一屬性 (可混搭全屬性):"] + paired


class ConditionChecker:
    """根據 AppConfig 的裝備設定判斷潛能是否合格。"""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._use_preset = config.use_preset
        self._num_lines = get_num_lines(config.cube_type)

        equip = config.equipment_type
        self._tolerance = 0 if equip in _NO_TOLERANCE_EQUIP else _OCR_TOLERANCE

        if not self._use_preset:
            self._custom_lines = config.custom_lines
            self._valid = True
            return
        resolved = _resolve_equip_type(equip, config.is_eternal)
        attr = config.target_attribute

        # 萌獸雙終被：特殊條件
        self._is_雙終被 = equip == "萌獸" and attr == "雙終被"
        if self._is_雙終被:
            self._valid = True
            return

        self._is_glove = equip in GLOVE_TYPES
        self._is_hat = equip in HAT_TYPES

        # 所有屬性：每行可以是任一有效屬性
        self._is_所有屬性 = attr == "所有屬性"
        if self._is_所有屬性:
            self._equip_thresholds = THRESHOLD_TABLE.get(resolved, {})
            self._valid = bool(self._equip_thresholds)
            return

        thresholds = THRESHOLD_TABLE.get(resolved, {}).get(attr)
        if not thresholds:
            self._valid = False
            return

        self._valid = True
        (self._s_val, self._r_val), all_stats = thresholds
        self._target_key = _attr_to_ocr_key(attr)
        # STR/DEX/INT/LUK 自動含全屬性（不再需要 checkbox）
        self._include_all = attr in _STATS_WITH_ALL_STATS and all_stats is not None

        if self._include_all and all_stats:
            self._all_s, self._all_r = all_stats
        else:
            self._all_s, self._all_r = 0, 0

    def check(self, lines: list[PotentialLine]) -> bool:
        """所有行都符合才回傳 True。"""
        if not self._valid:
            return False
        if len(lines) < self._num_lines:
            return False

        if not self._use_preset:
            return self._check_custom(lines)

        if self._is_雙終被:
            return self._check_雙終被(lines)

        if self._is_所有屬性:
            return self._check_所有屬性(lines)

        return self._check_preset_any_pos(lines)

    def _check_preset_any_pos(self, lines: list[PotentialLine]) -> bool:
        """預設模式任意位置：嘗試所有排列找到一組符合的分配。"""
        for perm in permutations(lines[:self._num_lines]):
            ok = True
            for i in range(self._num_lines):
                is_legendary = (i == 0) if self._num_lines == 3 else True
                target_min = self._s_val if is_legendary else self._r_val
                all_stats_min = (self._all_s if is_legendary else self._all_r) if self._include_all else None
                if not _check_line(
                    perm[i],
                    self._target_key,
                    target_min,
                    all_stats_min,
                    accept_crit3=self._is_glove,
                    accept_cooldown=self._is_hat,
                    tolerance=self._tolerance,
                ):
                    ok = False
                    break
            if ok:
                return True
        return False

    def _check_所有屬性(self, lines: list[PotentialLine]) -> bool:
        """所有屬性模式：對每個可能的主屬性跑一次預設規則，任一通過即可。

        例如永恆手套選「所有屬性」→ 分別以 STR/DEX/INT/LUK 為主屬各跑一次，
        三排必須都能用同一種主屬性（含全屬性、爆傷、冷卻）湊齊才算通過。
        """
        for attr, ((s_val, r_val), all_stats) in self._equip_thresholds.items():
            target_key = _attr_to_ocr_key(attr)
            include_all = attr in _STATS_WITH_ALL_STATS and all_stats is not None
            all_s = all_stats[0] if include_all and all_stats else 0
            all_r = all_stats[1] if include_all and all_stats else 0

            for perm in permutations(lines[:self._num_lines]):
                ok = True
                for i in range(self._num_lines):
                    is_legendary = (i == 0) if self._num_lines == 3 else True
                    target_min = s_val if is_legendary else r_val
                    all_stats_min = (all_s if is_legendary else all_r) if include_all else None
                    if not _check_line(
                        perm[i],
                        target_key,
                        target_min,
                        all_stats_min,
                        accept_crit3=self._is_glove,
                        accept_cooldown=self._is_hat,
                        tolerance=self._tolerance,
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
                any(self._match_line(lc, line) for line in lines[:self._num_lines])
                for lc in any_pos_conditions
            ):
                return False

        return True

    def _match_line(self, lc: LineCondition, line: PotentialLine) -> bool:
        """檢查單行是否符合條件（含 OCR 容錯）。"""
        if lc.attribute == "被動技能2":
            return line.attribute == "被動技能2"
        if lc.attribute == "技能冷卻時間":
            return line.attribute == "技能冷卻時間" and line.value >= 1
        target_key = _attr_to_ocr_key(lc.attribute)
        return line.attribute == target_key and line.value + self._tolerance >= lc.min_value

    def _check_雙終被(self, lines: list[PotentialLine]) -> bool:
        """雙終被：2 行最終傷害 >= 20% + 1 行被動技能2。"""
        final_dmg_count = sum(
            1 for l in lines if l.attribute == "最終傷害%" and l.value >= 20
        )
        passive2_count = sum(1 for l in lines if l.attribute == "被動技能2")
        return final_dmg_count >= 2 and passive2_count >= 1
