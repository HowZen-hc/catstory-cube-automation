import re
from dataclasses import dataclass
from itertools import permutations
from typing import Literal

from app.models.config import AppConfig, LineCondition
from app.models.potential import PotentialLine

# ── 白名單 combo 型別 ──

MatchKind = Literal["target", "all_stats", "crit3", "cooldown"]


# OCR 文字 → 屬性名稱 + 數值
ATTRIBUTE_PATTERNS: dict[str, re.Pattern[str]] = {
    # 主要屬性（用於條件判斷）
    "STR%": re.compile(r"STR\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "DEX%": re.compile(r"(?<![A-Za-z0-9\u4e00-\u9fff:\uff1a])D?EX\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "INT%": re.compile(r"INT\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "LUK%": re.compile(r"LUK\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "全屬性%": re.compile(r"全屬性\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "MaxHP%": re.compile(r"MaxHP\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "物理攻擊力%": re.compile(r"物理攻擊力\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "魔法攻擊力%": re.compile(r"魔法攻擊力\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    # 爆擊傷害 泛化辨識：爆 + 1-3 任意字 + (可選 傷) + 害/喜 + 值
    # 覆蓋 18 個真實 OCR 誤讀案例（爆華害/爆擎悔害/爆馨擊傷害/爆挛售害/爆華恆喜/爆馨偏喜/...）
    # 不預先排除未觀察到的字元（per 「只收真實觀察」方法論），未來出現 FP 再局部補強
    "爆擊傷害%": re.compile(r"爆.{1,3}\s*傷?[害喜]\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    # 紀錄用屬性（不參與條件判斷，但顯示在 log 中）
    "MaxMP%": re.compile(r"MaxMP\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "防禦力%": re.compile(r"防禦力\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "無視怪物防禦%": re.compile(r"無視怪物防禦\s*[力率]?\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    # 必須在 爆擊傷害% 之後，避免 爆X傷害 被誤判為傷害
    "傷害%": re.compile(r"(?<![擊擎時終])傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
    "Boss傷害%": re.compile(r"攻擊\s*[Bb][Oo][Ss][Ss]\s*怪物時\s*傷害\s*[:\uff1a]?\s*\+?\s*(\d+) ?%"),
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
    ("uxHP", "MaxHP"),
    # 傷害誤讀（傷 → 低/值/佩/集/優/信/但/亿/焦/氣/僵/悔/侮/售）
    ("低害", "傷害"),
    ("值害", "傷害"),
    ("佩害", "傷害"),
    ("集害", "傷害"),
    ("優害", "傷害"),
    ("信害", "傷害"),
    ("但害", "傷害"),
    ("亿害", "傷害"),
    ("焦害", "傷害"),
    ("氣害", "傷害"),
    ("僵害", "傷害"),
    ("悔害", "傷害"),
    ("侮害", "傷害"),
    ("售害", "傷害"),
    # 害 → 喜 誤讀
    ("傷喜", "傷害"),
    ("集喜", "傷害"),
    # 傷害兩字被讀成一個字（最終喜/最終害 → 最終傷害）
    ("最終喜", "最終傷害"),
    ("最終害", "最終傷害"),
    # 攻擊誤讀
    ("攻事", "攻擊"),
    # 爆擊誤讀（爆 → 爆華/爆草/爆吉/煬/煜華）
    ("煜華", "爆擊"),
    # MUST come before 爆華 → 爆擊 — scoped pairs for 爆擊傷害 variants
    # 若 broad pair 先觸發，爆華害 會被降階為 爆擊害，scoped 分支永不生效
    # M1' regex 的 傷? optional 仍可命中 爆擊害，attribute/value 正確，但
    # (a) merged-path raw_text 退化，(b) scoped 分支失去 regression 覆蓋
    ("爆華害", "爆擊傷害"),   # 擊→華 + 傷 dropped
    ("爆挛害", "爆擊傷害"),   # 擊→挛 + 傷 dropped
    ("爆擎害", "爆擊傷害"),   # 擊→擎 + 傷 dropped
    ("爆馨擊", "爆擊"),       # 爆馨擊傷害 → 爆擊傷害（多出 馨）
    ("爆華", "爆擊"),
    ("爆草", "爆擊"),
    ("爆吉", "爆擊"),
    ("煬擊", "爆擊"),
    # LUK/DEX/INT 誤讀
    ("LIK", "LUK"),
    ("LJK", "LUK"),
    ("DIK", "DEX"),
    ("DT+", "DEX+"),
    ("工T", "INT"),
    # 屬性誤讀（屬 → 屋/國/慶）
    ("全屋性", "全屬性"),
    ("全國性", "全屬性"),
    ("全慶性", "全屬性"),
    # 簡體 → 繁體（視）
    ("無视", "無視"),
    # 無視怪物防禦誤讀（禦 被吃掉，防率 → 防禦率）
    ("怪物防率", "怪物防禦率"),
    # HP恢復道具誤讀（恢递具 → 恢復道具，H → HP）
    # 注意：H恢復道具 依賴上一行先將 恢递具 → 恢復道具，順序不可對調
    ("恢递具", "恢復道具"),
    ("H恢復道具", "HP恢復道具"),
]

# MaxHP/MaxMP 誤讀（M 被吃掉，axHP → MaxHP），前方不能有字母以避免誤改正確的 MaxHP
_OCR_AX_TO_MAX = re.compile(r"(?<![A-Za-z])ax(HP|MP)")
# DEX 小寫誤讀（ex → DEX），前方不能有字母以避免誤匹配
_OCR_LOWERCASE_EX = re.compile(r"(?<![a-zA-Z])ex(?=[+:\uff1a\d])")
# DEX 誤讀（DET/DEI/DE/DEK/DEY/DX → DEX），需邊界限制（含 CJK/數字/冒號）
_OCR_DEX_FIXES = re.compile(r"(?<![A-Za-z0-9\u4e00-\u9fff:\uff1a])(?:DET|DEI|DEK|DEY|DE|DX)(?=[+:\uff1a\d])")
# STR 誤讀（STE → STR），需邊界限制避免 SYSTEM/STEP 等誤匹配
_OCR_STE_TO_STR = re.compile(r"(?<![A-Za-z])STE(?=[+:\uff1a\d%])")
# INT 誤讀（I↔1 混淆 + N↔T/M 混淆 + IHT/IMT/IINT/JNT/TIT），前方不能有字母數字以避免誤匹配
_OCR_INT_FIXES = re.compile(r"(?<![A-Za-z0-9])(?:IINT|IHT|IMT|1NT|1IT|1TT|IIT|IT|IM|JNT|TIT)(?=[\+\d:\uff1a])")
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
    # ex → DEX（小寫修正，前方無字母時）
    text = _OCR_LOWERCASE_EX.sub("DEX", text)
    # DET/DEI/DE/DEK/DEY → DEX
    text = _OCR_DEX_FIXES.sub("DEX", text)
    # STE → STR（R→E 誤讀，邊界限制）
    text = _OCR_STE_TO_STR.sub("STR", text)
    # INT 誤讀修正（IINT/IHT/IMT/IT/1NT/1IT/1TT/IIT/IM/JNT/TIT → INT）
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
    "萌獸": {
        "最終傷害": ((20, 20), None),
        "物理攻擊力": ((20, 20), None),
        "魔法攻擊力": ((20, 20), None),
        "加持技能持續時間": ((50, 50), None),
    },
}

# 副手雙攻擊力（可轉換）— 遊戲內副手可整件互轉物攻／魔攻
_ATTACK_CONVERTIBLE = "物理/魔法攻擊力 (可轉換)"

# 裝備類型 → 可選屬性
EQUIPMENT_ATTRIBUTES: dict[str, list[str]] = {
    "永恆 / 光輝": ["所有屬性", "STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "一般裝備 (神秘、漆黑、頂培)": ["所有屬性", "STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "主武器 / 徽章 (米特拉)": ["物理攻擊力", "魔法攻擊力"],
    "輔助武器 (副手)": [_ATTACK_CONVERTIBLE],
    "萌獸": ["最終傷害", "物理攻擊力", "魔法攻擊力", "加持技能持續時間", "雙終被"],
}

EQUIPMENT_TYPES = list(EQUIPMENT_ATTRIBUTES.keys())

# 選擇 STR/DEX/INT/LUK 時自動含全屬性的屬性
_STATS_WITH_ALL_STATS = {"STR", "DEX", "INT", "LUK"}

# 支援手套 / 帽子子類別的 gear 裝備集合（FR-3 縱深防禦）
# 公開為 module-level 常數，供 UI 層（condition_editor.py）共用，避免分散定義漂移
GEAR_EQUIP_TYPES: frozenset[str] = frozenset(
    {"永恆 / 光輝", "一般裝備 (神秘、漆黑、頂培)"}
)

# OCR 容錯值：防止 8→6、5↔6 等誤讀導致好結果被洗掉
# 套用對象：主屬性、全屬性、HP、副手攻擊力
# 不套用：爆擊傷害、技能冷卻時間、主武器/徽章、萌獸
_OCR_TOLERANCE = 2
_NO_TOLERANCE_EQUIP = {"主武器 / 徽章 (米特拉)", "萌獸"}

# 自訂模式可選屬性（依裝備類型分類）
# 註：keys 使用英文避免與 UI 顯示字串混用（NFR-2）
CUSTOM_SELECTABLE_ATTRIBUTES: dict[str, list[str]] = {
    "gear": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP"],
    "gear_glove": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP", "爆擊傷害"],
    "gear_hat": ["STR", "DEX", "INT", "LUK", "全屬性", "MaxHP", "技能冷卻時間"],
    "weapon": ["物理攻擊力", "魔法攻擊力"],
    "beast": ["最終傷害", "物理攻擊力", "魔法攻擊力", "加持技能持續時間", "被動技能2"],
}

# 裝備類型 → 自訂模式屬性分類（不含 gear_glove / gear_hat；那兩者由 is_glove / is_hat 旗標路由）
_EQUIP_TO_CUSTOM_CATEGORY: dict[str, str] = {
    "永恆 / 光輝": "gear",
    "一般裝備 (神秘、漆黑、頂培)": "gear",
    "主武器 / 徽章 (米特拉)": "weapon",
    "輔助武器 (副手)": "weapon",
    "萌獸": "beast",
}


def get_custom_attributes(
    equipment_type: str,
    is_glove: bool = False,
    is_hat: bool = False,
) -> list[str]:
    """取得該裝備類型在自訂模式可選的屬性列表。

    is_glove / is_hat 僅在 gear 裝備（永恆/光輝、一般裝備）時有意義；
    其他裝備類型會忽略兩個旗標（FR-3 縱深防禦）。
    """
    is_gear = equipment_type in GEAR_EQUIP_TYPES
    if is_gear and is_glove:
        return CUSTOM_SELECTABLE_ATTRIBUTES["gear_glove"]
    if is_gear and is_hat:
        return CUSTOM_SELECTABLE_ATTRIBUTES["gear_hat"]
    category = _EQUIP_TO_CUSTOM_CATEGORY.get(equipment_type, "gear")
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


def _classify_line(
    line: PotentialLine,
    target_key: str,
    target_min: int,
    all_stats_min: int | None,
    accept_crit3: bool,
    accept_cooldown: bool = False,
    tolerance: int = 0,
) -> MatchKind | None:
    """分類單行潛能的 match 類型。回傳 None = 不合格。"""
    # 目標屬性符合（含容錯）
    if line.attribute == target_key and line.value + tolerance >= target_min:
        return "target"
    # 全屬性符合（含容錯）
    if all_stats_min is not None and line.attribute == "全屬性%" and line.value + tolerance >= all_stats_min:
        return "all_stats"
    # 手套：爆擊傷害 3% 也算合格（不套用容錯）
    if accept_crit3 and line.attribute == "爆擊傷害%" and line.value >= 3:
        return "crit3"
    # 帽子：技能冷卻時間 -1秒 也算合格（不套用容錯）
    if accept_cooldown and line.attribute == "技能冷卻時間" and line.value >= 1:
        return "cooldown"
    return None


def _check_line(
    line: PotentialLine,
    target_key: str,
    target_min: int,
    all_stats_min: int | None,
    accept_crit3: bool,
    accept_cooldown: bool = False,
    tolerance: int = 0,
) -> bool:
    """檢查單行潛能是否合格（wrapper）。"""
    return _classify_line(
        line, target_key, target_min, all_stats_min,
        accept_crit3, accept_cooldown, tolerance,
    ) is not None


def _run_preset_any_pos(
    lines: list[PotentialLine],
    num_lines: int,
    target_key: str,
    s_val: int,
    r_val: int,
    all_stats_min_s: int | None,
    all_stats_min_r: int | None,
    accept_crit3: bool,
    accept_cooldown: bool,
    tolerance: int,
) -> bool:
    """預設模式任意位置的純函式版本：嘗試所有排列找到一組符合的分配。

    不讀取任何 ConditionChecker 實例狀態，所有輸入皆透過參數傳入，
    讓多條呼叫路徑（例：副手物攻 + 魔攻）可安全共用同一套判定邏輯。
    """
    for perm in permutations(lines[:num_lines]):
        ok = True
        for i in range(num_lines):
            is_legendary = (i == 0) if num_lines == 3 else True
            target_min = s_val if is_legendary else r_val
            if all_stats_min_s is not None:
                all_stats_min = all_stats_min_s if is_legendary else all_stats_min_r
            else:
                all_stats_min = None
            if not _check_line(
                perm[i],
                target_key,
                target_min,
                all_stats_min,
                accept_crit3=accept_crit3,
                accept_cooldown=accept_cooldown,
                tolerance=tolerance,
            ):
                ok = False
                break
        if ok:
            return True
    return False


_TWO_LINE_CUBE_TYPES = {"絕對附加方塊 (僅洗兩排)"}


@dataclass(frozen=True)
class _WhitelistCombo:
    """絕對附加白名單的單一 combo 定義。"""
    target_key: str   # OCR attribute key (e.g., "STR%", "全屬性%", "爆擊傷害%")
    target_min: int   # S 潛門檻（或固定常數：爆擊=3, 冷卻=1）
    tolerance: int    # (a)(b)(c) = _OCR_TOLERANCE; (d)(e) = 0


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


# ── v3 Summary shorthand（社群標記法） ───────────────────

# 主屬縮寫：STR→力, DEX→敏, INT→智, LUK→幸
_STAT_TO_ZH: dict[str, str] = {
    "STR": "力",
    "DEX": "敏",
    "INT": "智",
    "LUK": "幸",
}

# 副手共通註記：遊戲內可進行物魔日冕
_SUB_WEAPON_DAYGUAN_NOTE = "（副手可於遊戲內進行物魔日冕）"


def _fmt_stat_shorthand(stat: str, s_val: int) -> str:
    """格式化主屬 shorthand，例：STR + 9 → "99 力"。"""
    zh = _STAT_TO_ZH.get(stat, stat)
    return f"{s_val}{s_val} {zh}"


def _fmt_hp(s_val: int) -> str:
    """MaxHP shorthand，例：12 → "12 12 HP"（兩數字間空格，符合社群慣用）。"""
    return f"{s_val} {s_val} HP"


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
    """根據 config 產生人可讀的條件描述（顯示在 UI 上）。

    Phase 2（FR-16..25）：預設規則 summary 以結構性簡述為主，不列裝備等級數值；
    絕對附加採「僅支援」明示封閉白名單；冷卻帽絕對附加加註「77 全 冷卻」備援與
    「洗到主屬會洗掉」警示。
    """
    if not config.use_preset:
        return _generate_custom_summary(config.custom_lines)

    equip = config.equipment_type
    attr = config.target_attribute
    num_lines = get_num_lines(config.cube_type)

    # 萌獸雙終被：特殊條件
    if equip == "萌獸" and attr == "雙終被":
        return [
            "需要 3 排中包含:",
            "  2 排 最終傷害 ≥ 20%",
            "  1 排 被動技能2（依照被動技能 2 來增加）",
        ]

    # 副手雙攻擊力（可轉換）— D2 強制：僅限副手
    if attr == _ATTACK_CONVERTIBLE:
        if equip != "輔助武器 (副手)":
            return ["無法產生條件：『物理/魔法攻擊力 (可轉換)』僅適用於輔助武器 (副手)"]
        equip_thresholds = THRESHOLD_TABLE.get(equip, {})
        phys = equip_thresholds.get("物理攻擊力")
        magic = equip_thresholds.get("魔法攻擊力")
        if not phys or not magic:
            return ["無法產生條件：裝備類型或屬性不正確"]
        if num_lines == 2:
            # 絕對附加副手：保留既有「日冕」術語結尾（FR-21.1）
            (phys_s, _), _ = phys
            (magic_s, _), _ = magic
            return [
                "兩排需同屬性（全物攻 或 全魔攻）且符合:",
                f"  · 物理攻擊力 {phys_s}%",
                f"  · 魔法攻擊力 {magic_s}%",
                _SUB_WEAPON_DAYGUAN_NOTE,
            ]
        # 3-line 副手 shorthand「三物 / 三魔」（FR-21.1 維持）
        return [
            f"三物 / 三魔{_SUB_WEAPON_DAYGUAN_NOTE}",
        ]

    # FR-3 縱深防禦：is_glove / is_hat 僅在 gear 裝備上有意義
    is_gear = equip in GEAR_EQUIP_TYPES
    is_glove = config.is_glove and is_gear
    is_hat = config.is_hat and is_gear

    # 絕對附加方塊：白名單（2-line）
    if num_lines == 2 and config.cube_type in _TWO_LINE_CUBE_TYPES:
        # FR-24 / FR-25：手套 / 冷卻帽 在絕對附加情境下覆蓋 target 文案
        if is_glove:
            return ["僅支援 33 爆"]
        if is_hat:
            return ["支援 -1 -1 冷卻，也接受 77 全 冷卻；若洗到主屬會直接洗掉"]
        if attr == "所有屬性":
            if attr not in EQUIPMENT_ATTRIBUTES.get(equip, []):
                return ["無法產生條件：『所有屬性』僅適用於永恆 / 光輝與一般裝備"]
            return _generate_absolute_all_attrs_summary(equip)
        thresholds = THRESHOLD_TABLE.get(equip, {}).get(attr)
        if not thresholds:
            return ["無法產生條件：裝備類型或屬性不正確"]
        (s_val, _r_val), _all = thresholds
        return _generate_absolute_summary(attr, s_val)

    # 3-line 珍貴 / 恢復方塊 — Phase 2 結構性簡述
    # 子類別 checkbox 覆蓋 target 文案（FR-19 / FR-20）
    if is_glove:
        return ["必須符合一排為爆擊傷害 3%，支援雙爆、3S、雙 S"]
    if is_hat:
        return ["必須符合一排為技能冷卻時間 -1 秒，支援 -2 冷卻、3S、雙 S"]

    # 主武器 / 徽章：依目標物 / 魔分流（FR-21）
    if equip == "主武器 / 徽章 (米特拉)" and num_lines == 3:
        if attr == "物理攻擊力":
            return ["三物（支援 3S、雙 S）"]
        if attr == "魔法攻擊力":
            return ["三魔（支援 3S、雙 S）"]

    # 所有屬性（gear 裝備、3-line）— FR-16
    if attr == "所有屬性":
        if attr not in EQUIPMENT_ATTRIBUTES.get(equip, []):
            return ["無法產生條件：『所有屬性』僅適用於永恆 / 光輝與一般裝備"]
        return ["支援 力 / 敏 / 智 / 幸、全屬、HP，包含 3S、雙 S 及全屬混搭"]

    # gear 主屬 / 全屬性 / HP（3-line）— FR-17 / FR-18 / row 3-G-HP
    if is_gear and num_lines == 3:
        if attr in _STATS_WITH_ALL_STATS:
            return ["支援 3S、雙 S，包含全屬混搭"]
        if attr == "全屬性":
            return ["包含 3S、雙 S 的情況"]
        if attr == "MaxHP":
            return ["支援 HP、全屬，包含 3S、雙 S 及全屬混搭"]

    # 萌獸 / 其他非 gear：保留底層門檻顯示
    thresholds = THRESHOLD_TABLE.get(equip, {}).get(attr)
    if not thresholds:
        return ["無法產生條件：裝備類型或屬性不正確"]

    (s_val, _r_val), _all_stats_thresholds = thresholds

    if equip == "萌獸":
        return [f"三排: {attr} ≥ {s_val}%"]

    # fallback：非絕對附加的 2-line cube（目前未開放）
    if num_lines == 2:
        return [f"兩排: {attr} {s_val}%"]

    return [f"{attr} {s_val}%"]


def _generate_absolute_summary(target_attr: str, s_val: int) -> list[str]:
    """絕對附加 + 單一目標屬性的 Phase 2 shorthand（FR-23 / FR-23.1）。

    主屬：`99 力`；HP：`12 12 HP`；全屬性：`77全`（無空格）。
    手套 / 冷卻帽 checkbox 由上層 dispatch 處理（FR-24 / FR-25），不在此函式內混入。
    """
    if target_attr in _STATS_WITH_ALL_STATS:
        return [_fmt_stat_shorthand(target_attr, s_val)]
    if target_attr == "全屬性":
        return [f"{s_val}{s_val}全"]  # 注意：無空格，與 FR-22 「77全」一致
    if target_attr == "MaxHP":
        return [_fmt_hp(s_val)]
    # 非 gear 屬性（保留 fallback；主武器 / 副手攻擊力於絕對附加不常見）
    return [f"{target_attr} {s_val}%"]


def _generate_absolute_all_attrs_summary(resolved_equip: str) -> list[str]:
    """絕對附加 + 目標 = 所有屬性的 Phase 2 白名單（FR-22）。

    輸出格式：`僅支援 99 四屬、77全、12 12 HP`（永恆）/ `僅支援 88 四屬、66全、11 11 HP`（一般）。
    手套 / 冷卻帽 由上層 dispatch 覆蓋（FR-24 / FR-25），不在此函式內混入。
    """
    equip_thresholds = THRESHOLD_TABLE.get(resolved_equip, {})

    # 取主屬 s_val（任一主屬皆同；以 STR 為代表）
    stat_entry = equip_thresholds.get("STR")
    all_entry = equip_thresholds.get("全屬性")
    hp_entry = equip_thresholds.get("MaxHP")
    if not stat_entry or not all_entry or not hp_entry:
        return ["無法產生條件：裝備類型或屬性不正確"]

    (stat_s, _), _ = stat_entry
    (all_s, _), _ = all_entry
    (hp_s, _), _ = hp_entry

    # `77全` 無空格、`12 12 HP` 兩數字間空格（與 FR-22 逐字一致）
    return [f"僅支援 {stat_s}{stat_s} 四屬、{all_s}{all_s}全、{hp_s} {hp_s} HP"]


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
        resolved = equip  # v3: equipment_type 即為 THRESHOLD_TABLE 的 key
        attr = config.target_attribute

        # 預設旗標：任何早退分支都不會讓後續屬性存取出錯
        self._is_attack_convertible = False
        self._is_absolute_append = False

        # 萌獸雙終被：特殊條件
        self._is_雙終被 = equip == "萌獸" and attr == "雙終被"
        if self._is_雙終被:
            self._valid = True
            return

        # FR-3 縱深防禦：即使 config.is_glove / is_hat 為 True，
        # 若裝備類型不是 gear（永恆/光輝 或 一般裝備），強制忽略兩個旗標。
        # 防止手改 config 或未來 UI bug 造成主武器 / 副手 / 萌獸 的誤判。
        is_gear = equip in GEAR_EQUIP_TYPES
        self._is_glove = config.is_glove and is_gear
        self._is_hat = config.is_hat and is_gear

        # 絕對附加白名單：必須在所有屬性 early return 之前設定
        # 用 attr != _ATTACK_CONVERTIBLE 而非 self._is_attack_convertible（此時尚未設定為最終值）
        self._is_absolute_append = (
            config.cube_type in _TWO_LINE_CUBE_TYPES
            and attr != _ATTACK_CONVERTIBLE
        )
        if self._is_absolute_append:
            # 防呆：target_attribute 必須是該裝備類型的合法選項
            valid_attrs = EQUIPMENT_ATTRIBUTES.get(equip, [])
            if attr not in valid_attrs:
                self._valid = False
                return
            self._is_所有屬性 = attr == "所有屬性"
            equip_thresholds = THRESHOLD_TABLE.get(resolved, {})
            self._equip_thresholds = equip_thresholds
            self._whitelist_combos = self._build_whitelist(
                equip_thresholds, attr,
            )
            self._valid = bool(self._whitelist_combos)
            return

        # 所有屬性：每行可以是任一有效屬性
        self._is_所有屬性 = attr == "所有屬性"
        if self._is_所有屬性:
            self._equip_thresholds = THRESHOLD_TABLE.get(resolved, {})
            self._valid = bool(self._equip_thresholds)
            return

        # 副手雙攻擊力（可轉換）— D2 強制：僅允許副手，防止手改 config 繞過 UI
        self._is_attack_convertible = (
            attr == _ATTACK_CONVERTIBLE and equip == "輔助武器 (副手)"
        )
        if self._is_attack_convertible:
            equip_thresholds = THRESHOLD_TABLE.get(resolved, {})
            phys = equip_thresholds.get("物理攻擊力")
            magic = equip_thresholds.get("魔法攻擊力")
            if phys is None or magic is None:
                self._valid = False
                return
            (self._phys_s_val, self._phys_r_val), _ = phys
            (self._magic_s_val, self._magic_r_val), _ = magic
            self._valid = True
            return

        # 防呆：attr == _ATTACK_CONVERTIBLE 但 equip 不是副手（手改 config 情境）
        if attr == _ATTACK_CONVERTIBLE:
            self._valid = False
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

        if self._is_attack_convertible:
            return self._check_attack_convertible(lines)

        if self._is_absolute_append:
            return self._check_absolute_append(lines)

        if self._is_所有屬性:
            return self._check_所有屬性(lines)

        return self._check_preset_any_pos(lines)

    def _check_preset_any_pos(self, lines: list[PotentialLine]) -> bool:
        """預設模式任意位置：嘗試所有排列找到一組符合的分配。"""
        return _run_preset_any_pos(
            lines=lines,
            num_lines=self._num_lines,
            target_key=self._target_key,
            s_val=self._s_val,
            r_val=self._r_val,
            all_stats_min_s=self._all_s if self._include_all else None,
            all_stats_min_r=self._all_r if self._include_all else None,
            accept_crit3=self._is_glove,
            accept_cooldown=self._is_hat,
            tolerance=self._tolerance,
        )

    # ── 絕對附加白名單 ──

    def _build_whitelist(
        self,
        equip_thresholds: dict[str, tuple[tuple[int, int], tuple[int, int] | None]],
        target_attr: str,
    ) -> list[_WhitelistCombo]:
        """依裝備等級建立白名單 combo list。"""
        combos: list[_WhitelistCombo] = []
        added_keys: set[str] = set()

        if self._is_所有屬性:
            attrs_to_check = [a for a in ("STR", "DEX", "INT", "LUK") if a in equip_thresholds]
        elif target_attr in equip_thresholds:
            attrs_to_check = [target_attr]
        else:
            attrs_to_check = []

        for attr in attrs_to_check:
            (s_val, _r_val), _all_stats = equip_thresholds[attr]
            ocr_key = _attr_to_ocr_key(attr)
            # (a) 同種主屬 × 2
            combos.append(_WhitelistCombo(
                target_key=ocr_key, target_min=s_val, tolerance=self._tolerance,
            ))
            added_keys.add(ocr_key)

        # (b) 全屬 × 2（避免與 target 重複）
        all_stats_entry = equip_thresholds.get("全屬性")
        if all_stats_entry and "全屬性%" not in added_keys:
            (all_s, _all_r), _ = all_stats_entry
            combos.append(_WhitelistCombo(
                target_key="全屬性%", target_min=all_s, tolerance=self._tolerance,
            ))

        # (c) MaxHP × 2（避免與 target 重複）
        hp_entry = equip_thresholds.get("MaxHP")
        if hp_entry and "MaxHP%" not in added_keys:
            (hp_s, _hp_r), _ = hp_entry
            combos.append(_WhitelistCombo(
                target_key="MaxHP%", target_min=hp_s, tolerance=self._tolerance,
            ))

        # (d) 冷卻 × 2（僅帽子）— 不套用 tolerance
        if self._is_hat:
            combos.append(_WhitelistCombo(
                target_key="技能冷卻時間", target_min=1, tolerance=0,
            ))

        # (e) 爆擊傷害 × 2（僅手套）— 不套用 tolerance
        if self._is_glove:
            combos.append(_WhitelistCombo(
                target_key="爆擊傷害%", target_min=3, tolerance=0,
            ))

        return combos

    def _check_absolute_append(self, lines: list[PotentialLine]) -> bool:
        """絕對附加白名單：兩排必須命中同一 combo type（同 attribute name + 達門檻）。"""
        l0, l1 = lines[0], lines[1]
        for combo in self._whitelist_combos:
            if (l0.attribute == combo.target_key
                    and l0.value + combo.tolerance >= combo.target_min
                    and l1.attribute == combo.target_key
                    and l1.value + combo.tolerance >= combo.target_min):
                return True
        return False

    def _check_attack_convertible(self, lines: list[PotentialLine]) -> bool:
        """副手雙攻擊力（可轉換）：三排全物攻 或 三排全魔攻皆合格。

        整件轉換語意（D1）：混合洗出（例：2 物 1 魔）不通過，
        因遊戲內防具轉換是整件統一互換，混合無法完整轉為單一屬性。
        """
        candidates = (
            ("物理攻擊力%", self._phys_s_val, self._phys_r_val),
            ("魔法攻擊力%", self._magic_s_val, self._magic_r_val),
        )
        return any(
            _run_preset_any_pos(
                lines=lines,
                num_lines=self._num_lines,
                target_key=target_key,
                s_val=s_val,
                r_val=r_val,
                all_stats_min_s=None,
                all_stats_min_r=None,
                accept_crit3=False,
                accept_cooldown=False,
                tolerance=self._tolerance,
            )
            for target_key, s_val, r_val in candidates
        )

    def _check_所有屬性(self, lines: list[PotentialLine]) -> bool:
        """所有屬性模式：對每個可能的主屬性跑一次預設規則，任一通過即可。

        例如永恆手套選「所有屬性」→ 分別以 STR/DEX/INT/LUK 為主屬各跑一次，
        三排必須都能用同一種主屬性（含全屬性、爆傷、冷卻）湊齊才算通過。
        """
        for attr, ((s_val, r_val), all_stats) in self._equip_thresholds.items():
            include_all = attr in _STATS_WITH_ALL_STATS and all_stats is not None
            if _run_preset_any_pos(
                lines=lines,
                num_lines=self._num_lines,
                target_key=_attr_to_ocr_key(attr),
                s_val=s_val,
                r_val=r_val,
                all_stats_min_s=all_stats[0] if include_all else None,
                all_stats_min_r=all_stats[1] if include_all else None,
                accept_crit3=self._is_glove,
                accept_cooldown=self._is_hat,
                tolerance=self._tolerance,
            ):
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
        # 爆擊傷害不套用容錯（1% 和 3% 差距太小，容錯會讓 1% 通過 3% 的門檻）
        if lc.attribute == "爆擊傷害":
            return line.attribute == target_key and line.value >= lc.min_value
        return line.attribute == target_key and line.value + self._tolerance >= lc.min_value

    def _check_雙終被(self, lines: list[PotentialLine]) -> bool:
        """雙終被：2 行最終傷害 >= 20% + 1 行被動技能2。"""
        final_dmg_count = sum(
            1 for line in lines if line.attribute == "最終傷害%" and line.value >= 20
        )
        passive2_count = sum(1 for line in lines if line.attribute == "被動技能2")
        return final_dmg_count >= 2 and passive2_count >= 1
