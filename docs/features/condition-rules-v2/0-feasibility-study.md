# 條件規則系統 v2 可行性研究

> **Created**: 2026-04-12
> **Requirements**: [1-requirements.md](./1-requirements.md)

## 1. Problem Essence

### 1.1 Surface Requirement

重新定義條件系統的語意邊界：預設規則覆蓋所有合法結果、合併 custom mode、絕對附加限縮為 5 類白名單、說明文字依 cube_type 差異化。

### 1.2 Underlying Problem

條件系統以「排列組合」而非「目標屬性達成與否」為判定核心。`_check_line()` 只回傳 `bool`，不回報「為什麼通過」，導致 2-line cube 的白名單（同種×2）無法從現有介面實作。

### 1.3 Success Criteria

| # | Criterion | Metric |
|---|-----------|--------|
| SC-1 | 手套 / 帽子 preset edge cases 明確鎖定 | 新增 6+ lockdown tests 全綠 |
| SC-2 | Custom mode 整併後 UI 僅有預設 / 自訂 | `_MODE_OR` 從 codebase 消失 |
| SC-3 | 絕對附加 preset 限縮為同種×2 白名單 | 白名單 pass + FP fail 測試全綠 |
| SC-4 | summary_label 依 cube_type + equip_type 差異化 | UI text 含正確白名單數值 |
| SC-5 | 既有 tests 全綠，無 regression（不寫死數量，以升級前 pytest 為 baseline）| `uv run pytest` 全綠 |

## 2. Constraints

| Type | Constraint | Source | Flexibility |
|------|-----------|--------|-------------|
| Technical | `_check_line` 目前回傳 bool，不含 match type 資訊 | Code | **Med** — 可擴充 |
| Technical | `_OCR_TOLERANCE = 2` 必須沿用，不得改為 `==` | C6 | None |
| Technical | `LineCondition.position = 0` 語意不得改變 | C1 | None |
| Compatibility | 既有 config.json 必須相容（mode 不持久化，position 推導） | FR-10 | None |
| Compatibility | `_check_attack_convertible` 必須優先於白名單（**提案 dispatch 順序** — 目前 code 順序為 所有屬性 → convertible → preset，需重排） | Proposed | None |
| Business | 白名單僅套用在預設模式；自訂模式不限 | C3 / FR-14 | None |
| Technical | 爆擊傷害 / 冷卻不在 `THRESHOLD_TABLE`，且 **不套用 tolerance**（爆擊 1% 和 3% 差距太小，tolerance=2 會讓 1% 通過 3% 門檻 = FP）。注意：此行為與 `1-requirements.md` FR-12.1 的「所有組合均沿用 `_OCR_TOLERANCE`」敘述衝突 → tech-spec 階段需修正 FR-12.1(d)(e) 為「沿用現有無 tolerance 比較」 | Code:573,576,1014 | None — 不可改 |

## 3. Existing Capability Inventory

### 3.1 Related Modules

| Module | Reusable Logic |
|--------|---------------|
| `_run_preset_any_pos` (581) | 純函式，試所有排列 → 直接可用於 non-absolute preset |
| `_check_line` (556) | 單行判定（bool only）→ 可擴充為 classifier |
| `_check_attack_convertible` (928) | 已有雙路徑（物攻/魔攻）dispatch 模式 → 白名單可仿此架構 |
| `_check_所有屬性` (954) | 迴圈試每種主屬 → absolute + 所有屬性需在白名單內部處理 |
| `_check_custom` (977) | `position=0` ↔ any, `position>=1` ↔ fixed 語意 → 合併後直接沿用 |
| `generate_condition_summary` (674) | 已有 2-line / 3-line 分支 → 需新增 cube_type+equip_type 條件 |

### 3.2 Design Patterns

- **Dispatch-by-flag**：`check()` 依 `self._is_X` 分流至專用 method（雙終被、所有屬性、可轉換、preset）
- **Pure function extraction**：`_run_preset_any_pos` 無狀態依賴，可安全多路呼叫

### 3.3 Tech Debt

| Debt | Impact |
|------|--------|
| `_TWO_LINE_CUBE_TYPES` 含無後綴 `"絕對附加方塊"`（UI 未暴露） | FR-19 清理 |
| summary 與 checker 邏輯分離（各自 if/else）→ 容易 drift | Area 4 需注意同步 |
| `load_from_config` 推導 AND/OR mode（461-466）→ 合併後需簡化 | Area 2 |
| OR mode `_max_rows` 不限 `_num_lines`（可達 5）→ 合併後需保留相容 | Area 2 |

## 4. Possible Solutions

### Option A: Pure Additive — 新增 `_check_absolute_append()` 不動既有函式

**Core idea**: 新增獨立 dispatch 路徑，直接做 attribute name + value 比對，不修改 `_check_line` 或 `_run_preset_any_pos`。

**Implementation path**:

1. `__init__`：新增 `self._is_absolute_append` flag
2. `check()`：在 `_check_attack_convertible` 之後、`_check_所有屬性` 之前插入 dispatch
3. `_check_absolute_append()`：建立白名單 combo list，迴圈比對兩排是否同種+達門檻
4. 若 `_is_所有屬性` + absolute：在 `_check_absolute_append` 內部迴圈所有 attr types

**Feasibility assessment**:

| Dimension | Rating | Notes |
|-----------|:------:|-------|
| Technical Feasibility | 🟢 | 仿 `_check_attack_convertible` 模式 |
| Effort | 🟢 < 3d | 新函式 + dispatch + tests |
| Risk | 🟢 | 不動既有函式，regression 極低 |
| Extensibility | 🟡 | 白名單匹配邏輯與 `_check_line` 重複 → 日後 drift |
| Maintenance Cost | 🟡 | 兩套 matching 邏輯需同步維護 |

---

### Option D: Hybrid — 抽取 `_classify_line()` + 新增 `_check_absolute_append()`

**Core idea**: 從 `_check_line` 抽取一個 classifier 純函式回傳 match type，白名單和舊路徑共用分類邏輯，消除 logic drift。

**Implementation path**:

1. 抽取 `_classify_line()` → 回傳 `MatchKind | None`
   ```python
   MatchKind = Literal["target:STR", "target:DEX", ..., "all_stats", "crit3", "cooldown"]
   ```
   - `"target:{attr}"` 粒度以屬性名稱區分（Q3 同種定義需要此粒度）
   - 邏輯完全從 `_check_line` 搬出，`_check_line` 變為 `return _classify_line(...) is not None`
2. `_run_preset_any_pos`：不改動（仍呼叫 `_check_line`）
3. `_check_absolute_append()`：
   ```python
   def _check_absolute_append(self, lines):
       for combo_params in self._whitelist_combos:
           k0 = _classify_line(lines[0], **combo_params)
           k1 = _classify_line(lines[1], **combo_params)
           if k0 is not None and k0 == k1:
               return True
       return False
   ```
   - `_whitelist_combos` 在 `__init__` 中從 THRESHOLD_TABLE S 潛欄 + 固定常數建立
   - 所有屬性 case：迴圈 THRESHOLD_TABLE 各 attr 生成 combo_params
4. Dispatch 順序：
   ```
   雙終被 → attack_convertible → absolute_append → 所有屬性 → preset_any_pos
   ```
   - `absolute_append` 在 `所有屬性` 之前，內部處理 `_is_所有屬性` case

**Feasibility assessment**:

| Dimension | Rating | Notes |
|-----------|:------:|-------|
| Technical Feasibility | 🟢 | `_check_line` 唯一 caller 是 `_run_preset_any_pos` — 重構局部化 |
| Effort | 🟢 < 3d | 抽取 classifier + 新 dispatch + tests |
| Risk | 🟢 | `_check_line` wrapper 行為完全等價；`_run_preset_any_pos` 不改 |
| Extensibility | 🟢 | 未來新 combo type 只需新增 classifier 分支 |
| Maintenance Cost | 🟡→🟢 | classifier 可共用 → 需 Area 4 步驟 1.1 明確整合才達 🟢；若不整合則與 A 同為 🟡 |

---

### Option E: Rule-Table Driven — 資料驅動白名單

**Core idea**: 定義白名單規則為 data structure，同時驅動 `check()` 和 `generate_condition_summary()`。

**Implementation path**:

1. 定義 `ABSOLUTE_WHITELIST` 資料結構：
   ```python
   ABSOLUTE_WHITELIST = [
       {"kind": "target", "label_tpl": "{attr} {s_val}%", "equip_filter": None},
       {"kind": "all_stats", "label_tpl": "全屬性 {all_s}%", "equip_filter": None},
       {"kind": "hp", "label_tpl": "MaxHP {hp_s}%", "equip_filter": None},
       {"kind": "crit3", "label_tpl": "爆擊傷害 3%", "equip_filter": GLOVE_TYPES},
       {"kind": "cooldown", "label_tpl": "冷卻 -1 秒", "equip_filter": HAT_TYPES},
   ]
   ```
2. `_check_absolute_append()` 讀 rule table + THRESHOLD_TABLE 生成 combo params
3. `generate_condition_summary()` 讀同一 rule table 生成文字
4. Checker 和 summary 保證語意一致（single source of truth）

**Feasibility assessment**:

| Dimension | Rating | Notes |
|-----------|:------:|-------|
| Technical Feasibility | 🟢 | 既有 THRESHOLD_TABLE 已是 data-driven |
| Effort | 🟡 3-5d | 新 data structure + 重構 summary + tests |
| Risk | 🟡 | Summary 重構範圍大（674-815 行），snapshot tests 全需更新 |
| Extensibility | 🟢 | 新 combo type = 新增一行 rule |
| Maintenance Cost | 🟢 | Single source of truth — 最低 drift |

## 5. Codex In-Depth Discussion Record

### 5.1 Discussion Process Summary

| Round | Discussion Topic | Codex Key Viewpoint |
|-------|-----------------|---------------------|
| 1 | 初始方案列舉 + 風險識別 | 發現 FR-12 白名單與 `_check_attack_convertible` 的衝突；`_check_line` 只有 1 個 caller（`_run_preset_any_pos`），Option C blast radius 被高估；提出 Hybrid D |
| 2 | Option D 具體設計 + 所有屬性互動 | `_classify_line` 需 stat 粒度（`"target:STR"` vs `"target:DEX"`）以支援 Q3 同種定義；所有屬性 case 應在 absolute_append 內部處理 |
| 3 | Dispatch 順序 + 實作計畫驗證 | 確認 `雙終被 → convertible → absolute → 所有屬性 → preset_any_pos` 順序；Area 2 不可強制 `_max_rows = _num_lines`（舊 OR config 相容）；爆擊 / 冷卻不在 THRESHOLD_TABLE 需另外處理 min value |

### 5.2 Solution Directions Suggested by Codex

- **Hybrid D**（`_classify_line` 抽取 + `_check_absolute_append` 新增）— 原始 Option A/B/C 之外的第 4 方案
- **Rule-table approach**（data-driven whitelist shared by checker + summary）— 最高一致性但 effort 較大
- **Explicit convertible guard**：`self._is_absolute_append = is_absolute_cube and not self._is_attack_convertible`

### 5.3 Risks/Issues Identified by Codex

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | FR-12 白名單若全域套用會破壞副手可轉換 2-line 判定 | High | Dispatch 順序確保 convertible 優先 + explicit guard |
| R2 | Area 2 mode merge 不只 rename — `save_to_config` 強制 position=0 on OR mode | High | 修改為 always read from per-row combo data |
| R3 | `所有屬性` + 絕對附加 → `_check_所有屬性` 會 bypass 白名單 | High | absolute_append dispatch 在 所有屬性 之前，內部處理迴圈 |
| R4 | `_classify_line` 需 stat 粒度否則 STR+DEX 誤 pass | Medium | 回傳 `"target:{attr_name}"` 而非 `"target"` |
| R5 | Summary 與 checker drift — summary 目前獨立 if/else | Medium | Option D/E 的 classifier 可雙用；或至少共用常數 |
| R6 | 舊 OR config 可能 >3 rows → 合併後需保留 row 數相容 | Medium | 不強制 `_max_rows = _num_lines`，保留合理上限 |
| R7 | 爆擊 / 冷卻的 tolerance policy（code 故意不套 tolerance）| Low | 白名單中 (d)(e) 沿用現有無 tolerance 比較 |

### 5.4 Differences from Claude's Analysis

| Viewpoint | Claude | Codex | Adopted |
|-----------|--------|-------|---------|
| Option C blast radius | 高（需改所有 caller） | 低（`_check_line` 只有 1 caller） | **Codex** — 重新評估 |
| Area 2 `_max_rows` | 合併後 = `_num_lines` | 不可 — 舊 OR config 相容 | **Codex** — 保留相容上限 |
| 所有屬性 dispatch | 所有屬性先、absolute 後 | **absolute 先**，所有屬性在 absolute 內部處理 | **Codex** — 避免白名單 bypass |
| `_classify_line` 粒度 | 4 種 kind | 需 stat 粒度（`target:STR`） | **Codex** — Q3 必要 |
| Summary drift 風險 | 有意識但未提方案 | 共用 classifier / rule source | **Codex** — 整合 |

### 5.5 Integrated Conclusion

**Option D（Hybrid）** 在 effort / risk / extensibility 三維度都優於 Option A。唯一劣勢是比 A 多一步 `_classify_line` 抽取，但因 `_check_line` 只有 1 個 caller，重構局部化，不增加實質風險。Option E（Rule-table）長期最優但 effort 較大（summary 重構），適合作為 v3 進化方向。

## 6. Solution Comparison

| Dimension | Option A (Additive) | Option D (Hybrid) | Option E (Rule-table) |
|-----------|:-------------------:|:-----------------:|:---------------------:|
| Technical Feasibility | 🟢 | 🟢 | 🟢 |
| Effort | 🟢 < 3d | 🟢 < 3d | 🟡 3-5d |
| Risk | 🟢 | 🟢 | 🟡 |
| Extensibility | 🟡 | 🟢 | 🟢 |
| Maintenance Cost | 🟡 drift 風險 | 🟡 classifier 可共用但需 Area 4 明確整合 | 🟢 |
| Summary 一致性 | 🔴 分離 | 🟡 需 Area 4 步驟 1.1 明確引用 classifier | 🟢 single source |

## 7. Recommendation

**Recommended**: Option D（Hybrid — `_classify_line` 抽取 + `_check_absolute_append` dispatch）

**Rationale**:
- Effort 與 Option A 相同（< 3d），但消除了 logic drift 風險
- `_check_line` 只有 1 個 caller → 抽取 classifier 安全且局部化
- Dispatch 順序自然解決 convertible / 所有屬性 / absolute 三者互動
- `_classify_line` 回傳 stat 粒度 `"target:{attr}"` 精確支援 Q3 同種定義
- 未來若要 Rule-table（Option E）進化，classifier 已抽取可直接銜接

**Backup**: Option A（Pure Additive）
**Applicable scenario**: 若 `_classify_line` 抽取在實作中發現意外耦合（例如 `_run_preset_any_pos` 的 hot path 效能敏感），可退回 A — 邏輯重複但零風險。

## 8. Open Questions

- [ ] ~~Q6: 絕對附加白名單實作策略~~ → **Resolved: Option D**
- [ ] Q9: 萌獸方塊 + 絕對附加的白名單行為？（萌獸有自己的 THRESHOLD_TABLE 且 attr 不同 — 需要使用者確認是否在 scope 內）
- [ ] Q10: `_max_rows` 合併後的上限值？建議保留 `max(_num_lines, _MAX_OR_ROWS)` 相容，或限縮為 `_num_lines` + migration warning

## 9. Next Steps

1. `/sd0x-dev-flow:tech-spec condition-rules-v2` — 以 Option D 為方向產出技術規格
2. `/sd0x-dev-flow:feature-dev` — 依 tech-spec 實作
3. 實作順序建議：Area 1（tests only）→ Area 3（classifier + whitelist）→ Area 2（UI merge）→ Area 4（summary）→ Area 5（cube type 字串清理）

## 10. Implementation Plan Summary (Option D)

### Area 1: Preset Rules — Test Lockdown Only

| Step | Action |
|------|--------|
| 1 | 新增 6+ 測試：手套 crit × N (N=1,2,3) + 主屬 × (3-N) |
| 2 | 新增 6+ 測試：帽子 cooldown × N (N=1,2,3) + 主屬 × (3-N) |
| 3 | 包含至少 1 個 `全屬性%` 案例以鎖定 FR-4 |

### Area 2: Custom Mode Merge

| Step | Action |
|------|--------|
| 1 | `_MODE_AND` → `_MODE_CUSTOM`，移除 `_MODE_OR` |
| 2 | `_MODES = [_MODE_PRESET, _MODE_CUSTOM]` |
| 3 | per-row position combo 永遠顯示（含「任一排」data=0） |
| 4 | `save_to_config`：always read position from per-row combo（移除 OR branch） |
| 5 | `load_from_config`：`use_preset ? PRESET : CUSTOM`（移除 AND/OR 推導） |
| 6 | Value spinbox min：THRESHOLD_TABLE 罕見欄 + 爆擊 3 / 冷卻 1 特殊處理 |
| 7 | `_max_rows`：保留合理上限（相容舊 OR config） |

### Area 3: Absolute Append Whitelist (Option D)

| Step | Action |
|------|--------|
| 1 | 抽取 `_classify_line()` → `MatchKind \| None`（粒度 `"target:{attr}"`） |
| 2 | `_check_line()` = `_classify_line(...) is not None` |
| 3 | `__init__`：新增 `self._is_absolute_append` flag（含 convertible guard） |
| 4 | `__init__`：從 THRESHOLD_TABLE + 固定常數建立 `_whitelist_combos` |
| 5 | `check()` dispatch：雙終被 → convertible → **absolute** → 所有屬性 → preset |
| 6 | `_check_absolute_append()`：迴圈 whitelist_combos，k0 == k1 判定 |
| 7 | 所有屬性 case：在 `_check_absolute_append` 內部迴圈 THRESHOLD_TABLE 各 attr |
| 8 | 新增 15+ 測試：白名單 pass（5 類 × 2 裝備等級）+ FP fail（**5+** 跨類型/跨屬性，per NFR-4）|

### Area 4: Description Text

| Step | Action |
|------|--------|
| 1 | `generate_condition_summary`：新增 `cube_type in _TWO_LINE_CUBE_TYPES` 分支 |
| 1.1 | 絕對附加 summary 路徑應引用 `_classify_line` / whitelist combo 常數（與 Area 3 `_check_absolute_append` 共用同一資料來源），避免 checker/summary drift |
| 2 | 絕對附加 summary：依 equip_type 顯示白名單 5 類具體數值 |
| 3 | 一般方塊 summary：補充 3S / 雙 S / 帽子 -2 冷卻 / 手套雙爆 |
| 4 | FR-18：一般方塊手套 summary 不含具體 % 數字 |
| 5 | 更新 summary snapshot tests |

### Area 5: Cube Type String Cleanup (FR-19)

| Step | Action |
|------|--------|
| 1 | `_TWO_LINE_CUBE_TYPES`：移除無後綴 `"絕對附加方塊"`，僅保留 `"絕對附加方塊 (僅洗兩排)"` |
| 2 | `grep -r "絕對附加方塊\"" tests/` 找出所有使用無後綴字串的測試，改用有後綴版本 |
| 3 | 確認 `uv run pytest` 全綠 |
