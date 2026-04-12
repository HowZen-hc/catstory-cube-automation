# Requirements: 條件規則系統 v2（預設規則覆蓋 + 模式整併 + 絕對附加限縮 + 說明文字差異化）

> **Created**: 2026-04-12
> **Updated**: 2026-04-12 (v2 — 使用者 Q1–Q5 答覆整合)
> **Tier**: standard
> **Requests**: [R1 — Core](./requests/2026-04-12-core-preset-whitelist-cleanup-r1.md) | [R2 — UI](./requests/2026-04-12-ui-mode-merge-summary-r2.md)
> **Tech Spec**: （尚未建立，建議後續執行 `/feasibility-study` → `/tech-spec`）

## 1. Problem Statement

現行條件系統把「成功」定義在特定排列組合（例如手套的「1 排爆擊傷害 + 2 排主屬」、絕對附加的「任意雙 S」）而非回到「是否成功洗到目標屬性」這個核心問題。使用者此次重新定義了條件系統的語意邊界，並確認這是 **需求調整（spec change）** 而非僅為 bug fix — 即使現行 code 在某些邊界案例碰巧通過，新語意必須以明確的 FR + 測試鎖定，並同步更新 UI 說明文字。這造成四個連動痛點：

1. **預設規則的認知落差**：使用者無法從 UI 說明或內部行為確信低機率但合法的結果（手套 33/333 全爆傷、帽子雙 -1 秒、一般方塊雙 S 對屬）是否被判定為成功，導致對工具判定結果信心不足。
2. **自訂模式過度彈性**：「逐排指定」（AND）與「符合任一」（OR）兩個模式並存時，實際上只為了回答「有沒有洗到目標」一個問題，卻產生「任一排但可選 1%」這類語意不合理的組合，使得條件編輯複雜且易誤用。
3. **絕對附加語意失焦**：絕對附加方塊設計目的明確（保證雙排 S 屬性，用來洗特定雙排目標），但現行判定沿用一般方塊的「任意雙 S 通過」邏輯，把不符合主要使用情境的組合（例如永恆裝備語境下的「9 屬 + 7 全」跨類型雙 S 組合）也算成功。
4. **說明文字無法精準描述支援範圍**：模式下方的 `summary_label` 目前對所有 cube_type 共用同一套生成邏輯，沒有依方塊類型差異化，使用者看不到當前 cube_type 實際支援的組合清單。

### 5-Why Trace

| # | 層次 | 內容 |
|---|------|------|
| 1 | 表面需求 | 預設規則要兼容所有合法結果；合併 custom mode；限縮絕對附加；說明文字要差異化 |
| 2 | 為什麼現況不夠 | 預設規則的 UI/語意以「常見案例」描述，使用者無法確認邊界案例；兩種 custom mode 過度彈性卻沒有解決核心問題；絕對附加語意被一般方塊判定吃掉；說明文字統一，無法反映 cube_type 差異 |
| 3 | 為什麼會這樣設計 | 系統把「特定排列組合」作為成功條件，而非以「目標屬性達成與否」為核心；cube_type 只用於決定行數，未進入判定語意 |
| 4 | 為什麼影響大 | FN（好卷被誤判繼續洗）成本極高（整件方塊覆蓋後無法回復）；複雜的 mode 設定增加誤用風險；絕對附加誤判會讓使用者繼續洗已達標的卷；模糊的說明讓使用者不敢信任工具 |
| 5 | 根因 | 條件系統的抽象層次錯誤 — 應以「目標屬性是否達成」為判定中心，並依裝備類型 / 方塊類型做差異化分支，而非維持「排列組合 + 共用說明」的舊模型 |

## 2. Goals / Non-Goals

| Goals | Non-Goals |
|-------|-----------|
| 預設規則以「目標屬性達成與否」為判定核心，完整覆蓋合法結果 | 改變非手套 / 非帽子裝備的主屬判定邏輯 |
| 合併 `_MODE_AND` 與 `_MODE_OR` 為單一 custom mode | 新增額外的 custom 模式或 row 類型 |
| 絕對附加限縮為明確白名單，不再沿用一般方塊判定 | 自動偵測 cube_type（維持 UI 手選） |
| 說明文字依 cube_type 差異化，精準描述支援範圍 | 重寫 OCR / threshold table |
| 升級不破壞現有 config / 不引入 migration | 變更 `LineCondition.position` 欄位語意 |

## 3. Stakeholders

| Stakeholder | Role | Key Concern |
|-------------|------|-------------|
| 使用者（單一） | User + Developer + Operator | 預設規則不漏判合法卷、UI 操作化簡、升級零破壞 |
| `app/core/condition.py` | Dependent (code) | 預設判定語意統一；新增絕對附加白名單分支 |
| `app/gui/condition_editor.py` | Dependent (code) | Mode 下拉 3→2 選項；per-row 位置選項新增「任一排」；說明文字依 cube_type 分流 |
| `app/cube/*.py`（compare_flow, simple_flow） | Dependent (code) | 成功判定結果讀取，不變動介面 |
| `app/models/config.py` | Dependent (config) | 既有 config 欄位語意不變（Phase 2 確認 mode 並未持久化，從 `use_preset` + position 推導，零 migration） |
| `tests/test_condition.py` | Dependent (tests) | 現有 preset / custom / glove / hat / 2-line cube 測試需保持綠燈；新增絕對附加白名單測試 |

## 4. Use Cases

| # | Actor | Action | Expected Outcome |
|---|-------|--------|-----------------|
| UC-1 | 使用者 | 設定手套為預設模式，目標 = 爆擊傷害 3% | 系統對 `1 爆傷 + 2 主屬`、`2 爆傷 + 1 主屬`、`3 爆傷` 三種情況皆判定為成功 |
| UC-2 | 使用者 | 設定帽子為預設模式，目標 = 技能冷卻時間 -1 秒 | 系統對 `-1 + 主屬 + 主屬`、`-1 + -1 + 主屬` 皆判定為成功；主屬包含全屬 |
| UC-3 | 使用者 | 一般方塊（珍貴/恢復）洗到對屬性雙 S（例：STR 9 + STR 9 + 全屬 7） | 系統判定為成功，不因機率低而排除 |
| UC-4 | 使用者 | 打開自訂模式 | 只看到單一 custom mode（AND/OR 合併），per-row 位置下拉中可選「任一排」或具體排數 |
| UC-5 | 使用者 | 自訂模式中選「任一排」+ 數值 | 數值欄位自動帶入該裝備的合理下限（避免 1% 這類不合理選項） |
| UC-6 | 使用者 | 絕對附加預設模式 + 非白名單雙 S（例：STR 9 + 全屬 7） | 系統判定為**失敗**，繼續洗 |
| UC-7 | 使用者 | 絕對附加預設模式 + 白名單組合（例：HP 12 + HP 12） | 系統判定為成功，停手 |
| UC-8 | 使用者 | 切換 cube_type（珍貴 ↔ 絕對附加） | `summary_label` 的說明文字隨即更新，顯示當前 cube_type 對應的支援範圍 |

## 5. Functional Requirements

### 5.1 預設規則覆蓋（手套 / 帽子）

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-1 | 預設規則的成功判定必須以「目標屬性是否達成」為核心，而非以特定排列組合為前提 | Must | 回應 root problem；避免 FN |
| FR-2 | 手套預設規則必須接受所有「爆擊傷害 3% × N + 主屬 × (3-N)」組合（N ∈ {1, 2, 3}） | Must | 使用者明確列出三種合法情況 |
| FR-3 | 帽子預設規則必須接受所有「技能冷卻時間 -1 秒 × N + 主屬 × (3-N)」組合（N ∈ {1, 2, 3}） | Must | 同上 |
| FR-4 | 帽子 / 手套預設規則的「主屬」判定必須包含全屬性作為合法來源 | Must | 使用者明確要求；現行 `_STATS_WITH_ALL_STATS` 已支援 STR/DEX/INT/LUK → 全屬，需延伸到手套帽子的特殊屬性路徑 |
| FR-5 | 一般方塊（珍貴 / 恢復）的預設規則不得因機率低而排除對屬性雙 S 結果 | Must | 使用者明確要求 |

### 5.2 Custom Mode 整併

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-6 | 移除 `_MODE_OR`；原 `_MODE_AND` 重新命名為 `_MODE_CUSTOM`，UI mode 下拉僅保留「預設 / 自訂」兩個選項 | Must | 使用者明確要求整併；統一命名避免「AND」語意誤導（合併後位置由每 row 自行決定） |
| FR-7 | Custom mode 的 per-row 位置下拉必須新增「任一排」選項，對應 `LineCondition.position = 0` | Must | 合併後以 position 欄位表達模式差異（memory A6 已由 Phase 2 驗證 `position=0` 已是「任一排」語意） |
| FR-8 | Custom mode 的數值欄位必須依「裝備類型 × 屬性」自動限制下限，下限值 = 該組合在 `THRESHOLD_TABLE` 的「罕見」欄位值。具體（由 Q5 使用者確認，對應 `condition.py:404-467`）：<br>**永恆 / 光輝（含手套 / 帽子 永恆）**：主屬 ≥ 7%、全屬 ≥ 6%、MaxHP ≥ 9%<br>**一般裝備（含手套 / 帽子 非永恆）**：主屬 ≥ 6%、全屬 ≥ 5%、MaxHP ≥ 8%<br>**主武器 / 徽章**：攻擊力 ≥ 10%<br>**輔助武器（副手）**：攻擊力 ≥ 9%<br>**萌獸**：最終傷害 / 攻擊力 ≥ 20%、加持技能持續時間 ≥ 50% | Must | 使用者 Q5 明確指定；直接引用 `THRESHOLD_TABLE` 罕見欄避免魔術數字重複定義 |
| FR-9 | Custom mode 的 UI 行為不得要求使用者先選 mode 再選 row 類型，row 類型應直接在行內選擇 | Should | 降低操作步數 |
| FR-10 | Custom mode 整併後，既有儲存的 config（無論原本是 AND 或 OR）必須正確載入且行為等價 | Must | Phase 2 確認 mode 從 `use_preset` + position 推導，無持久化欄位 — 零 migration |

### 5.3 絕對附加白名單

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-11 | 絕對附加方塊的預設成功條件必須限縮為白名單（見 FR-12），不再沿用一般方塊「任意雙 S」邏輯 | Must | 使用者明確要求 |
| FR-12 | 絕對附加預設白名單必須恰好包含 **5 類雙排組合**，每類的具體數值依 **裝備等級**（永恆/光輝 vs 一般裝備）差異化（見 FR-12.1 對應表）。判定比較沿用現有 `_OCR_TOLERANCE = 2` 容錯機制（`value + tolerance >= 門檻`），不採精確相等 — 因為絕對附加保證 S 潛結果，OCR 向上/向下誤讀仍需安全通過，避免因低解析度造成 FN | Must | 使用者 Q2 定義的「目標值」即 S 潛最高檔（如永恆主屬 = 9）；Q3 明確「同種」= 同一屬性名稱。比較方式由使用者確認沿用 OCR 容錯（絕對附加保證 S 潛，`>=` 不會引入 FP） |
| FR-12.1 | 絕對附加白名單對應表。所有數值為**門檻值**（比較方式 = `value + _OCR_TOLERANCE >= 門檻`，非精確相等）：<br><br>**(a) 同種主屬×2**：<br>　・永恆/光輝（含手套/帽子 永恆）：同一 STR/DEX/INT/LUK **門檻 9%**（兩排皆 `>= 9`）<br>　・一般裝備（含手套/帽子 非永恆）：同一 STR/DEX/INT/LUK **門檻 8%**（兩排皆 `>= 8`）<br>　・**「同種」定義（Q3）**：兩排必須為**同一個**屬性名稱（STR+STR ✓、DEX+DEX ✓；STR+DEX ✗、LUK+INT ✗）<br><br>**(b) 全屬×2**：<br>　・永恆/光輝：全屬性 **門檻 7%**<br>　・一般裝備：全屬性 **門檻 6%**<br><br>**(c) MaxHP×2**：<br>　・永恆/光輝：MaxHP **門檻 12%**<br>　・一般裝備：MaxHP **門檻 11%**<br><br>**(d) 技能冷卻時間 -1 秒 × 2**：<br>　・僅適用帽子裝備（永恆 / 非永恆皆適用 — 不受裝備等級分級影響）<br>　・兩排皆 `>= 1`<br>　・**不套用 `_OCR_TOLERANCE`**（冷卻值只有 1，無 tolerance 需求）<br><br>**(e) 爆擊傷害 3% × 2**：<br>　・僅適用手套裝備（永恆 / 非永恆皆適用）<br>　・兩排皆 `>= 3`<br>　・**不套用 `_OCR_TOLERANCE`**（1% 和 3% 差距僅 2，tolerance=2 會讓 1% 通過 3% 門檻 = FP；見 `condition.py:1014`） | Must | 數值分兩類來源：**(a)(b)(c)** 的門檻值來自 `condition.py:404-467 THRESHOLD_TABLE` 的「S 潛」欄位（index [0][0]），沿用 `_OCR_TOLERANCE = 2` 容錯（`condition.py:508`）— 永恆 / 一般裝備各自有對應 key；**(d)(e)** 的 `-1` / `3%` 為固定常數，由 `condition.py:572-577` 的 `accept_crit3` / `accept_cooldown` flag 判定路徑決定，不在 `THRESHOLD_TABLE` 中，且 **不套用 tolerance**（沿用 code 現行行為） |
| FR-13 | 絕對附加預設模式不得接受以下非白名單組合（範例，列舉用）：<br>・STR 9% + 全屬 7%（**跨類型**雙 S — 兩排屬性名稱不同）<br>・STR 9% + DEX 9%（**跨屬性**同數值 — Q3 明確排除，兩排必須同一屬性名稱）<br>・STR 9% + MaxHP 12%（**跨類型** — 即使各自達標，組合類型不在白名單） | Must | Q3（同種定義）明確排除。注意：數值層面的「低於 S 潛」或「高於 S 潛」場景不列為 FP 案例 — 因為 (a) 絕對附加保證 S 潛結果，不可能產出低值；(b) `>=` 比較加 OCR 容錯確保辨識誤差仍通過。白名單的核心篩選維度是 **屬性類型 + 同名** 而非數值 |
| FR-14 | 絕對附加自訂模式維持既有的 per-row 自由設定（白名單僅套用在預設模式） | Should | 自訂模式服務的是手動進階使用情境 — 白名單僅為預設語意的邊界 |
| FR-14.1 | 冷卻 / 爆擊傷害白名單組合僅適用對應裝備類型：冷卻 → 帽子、爆擊傷害 → 手套；其他裝備類型選擇絕對附加時這兩組不進入白名單檢查 | Must | 語意正確性：其他裝備本來就不會洗出這兩種屬性 |

### 5.4 說明文字差異化

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-15 | `summary_label` 必須依 `cube_type` 顯示不同內容 | Must | 使用者明確要求 |
| FR-16 | 絕對附加的說明文字必須依**當前 equipment_type**（透過 `_resolve_equip_type` 後的 key）動態顯示 FR-12.1 對應的 5 類白名單具體數值。範例：<br>**永恆 / 光輝（含手套 永恆 / 帽子 永恆）**：99 屬（同種主屬）、77 全屬、12 12 HP、-1 -1 冷卻（帽子）、雙爆手 3% + 3%（手套）<br>**一般裝備（含手套 非永恆 / 帽子 非永恆）**：88 屬（同種主屬）、66 全屬、11 11 HP、-1 -1 冷卻（帽子）、雙爆手 3% + 3%（手套）<br>（冷卻 / 雙爆手僅在對應裝備類型顯示） | Must | 使用者明確要求避免誤解支援範圍；依 FR-12.1 分級，summary 必須同步反映裝備等級差異，否則與白名單本體不一致 |
| FR-17 | 一般方塊（珍貴 / 恢復）的說明文字必須補充：支援 3S、雙 S；帽子加註支援 -2 冷卻；手套加註支援雙爆 | Must | 使用者明確要求 |
| FR-18 | 一般方塊（珍貴 / 恢復）的手套說明文字不得標示爆擊傷害的具體百分比（因目標定義已以 3% 為基準，避免資訊冗餘）；此限制不適用於絕對附加（FR-16 需明示 3%+3%） | Must | 使用者明確要求；與 FR-16 作用域切分以避免互相拉扯 |

### 5.5 Cube Type 字串清理

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-19 | `_TWO_LINE_CUBE_TYPES` 必須移除無後綴的 `"絕對附加方塊"` 字串，僅保留 `"絕對附加方塊 (僅洗兩排)"`（UI 唯一暴露的版本） | Should | 使用者 Q4 明確確認保留有後綴的版本；無後綴字串為歷史殘留，UI 從未暴露，移除可降低後續維護混淆。清理後的引用同步（含測試 fixture）屬於實作細節，由 FR-19 的驗收條件（NFR-4 全綠）自動涵蓋 |

## 6. Non-Functional Requirements

| ID | Category | Requirement | Metric |
|----|----------|-------------|--------|
| NFR-1 | Maintainability | Custom mode 整併後，`_check_custom` 等核心判定函式的 cyclomatic complexity 不得上升 | 對比重構前後 `radon cc` 分數 |
| NFR-2 | Maintainability | `_MODE_OR` 常數及其分支必須從 UI 層完全移除；`_MODE_AND` 必須 rename 為 `_MODE_CUSTOM`；UI 下拉僅剩「預設 / 自訂」 | `grep -r "_MODE_OR\|_MODE_AND" app/gui/` 結果為 0 |
| NFR-3 | Compatibility | 既有 config.json 在升級後載入不得報錯，且條件語意等價 | 以升級前保存的 config fixture 執行 `load_from_config()` 驗證 |
| NFR-4 | Reliability | 現有 `tests/test_condition.py` 所有測試必須全綠（不寫死數量，以升級前後 pytest 結果對比為準）；新增測試覆蓋 FR-12.1 分級白名單（5 類 × 2 裝備等級 = 10 組以上 pass case）+ FR-13 至少 5 個 FP 案例 | `uv run pytest tests/test_condition.py` 全綠，新增測試 ≥ 15 個 |
| NFR-5 | Usability | Custom mode 的行數建立 / 修改操作步數（起始空列表 → 完成三排設定）不得增加 | 升級前後手動操作計數對比 |
| NFR-6 | Correctness | 預設判定對「目標屬性達成但常見案例順序不同」的邊界結果不得產生 FN | FR-2、FR-3 的所有 N ∈ {1,2,3} 組合測試全綠 |

## 7. Constraints & Assumptions

| # | Type | Description | Source |
|---|------|-------------|--------|
| C1 | Constraint | `LineCondition.position = 0` 的語意（= 任一排）必須維持不變 | Phase 2 code verification (condition.py:646, 986) |
| C2 | Constraint | 不得改變 OCR / threshold table / 裝備屬性定義（out of scope） | Goals / Non-Goals |
| C3 | Constraint | 白名單僅套用在絕對附加的**預設模式**；自訂模式不受限 | FR-14 |
| C4 | Constraint | 手套目標屬性鎖定「爆擊傷害 3%」單一基準；不含 4%、5% 變體 | User statement |
| C5 | Constraint | 本次重構必須遵守 `feedback_case_vs_inference.md`（cases-only methodology） — 只處理使用者提供的實際案例，不為未觀察到的情境預寫防禦性 code | Memory + project convention |
| C6 | Constraint | 白名單 (a)(b)(c) 沿用 `_OCR_TOLERANCE = 2`（`condition.py:508`）容錯；(d) 冷卻 / (e) 爆擊 **不套用 tolerance**（沿用 code 現行行為 — 爆擊 1% 和 3% 差距太小，tolerance=2 會造成 FP）。所有比較皆不得改為精確相等 `==` | 使用者確認 OCR 容錯 + code 現行 (d)(e) 無 tolerance 行為 |
| A1 | Decided | 絕對附加白名單的目標值 = S 潛最高檔（Q2），但比較方式沿用 `_OCR_TOLERANCE = 2` 容錯（`value + tolerance >= 門檻`），不採精確相等。原因：絕對附加保證 S 潛，OCR 容錯不會引入 FP；若用 `==` 則低解析度向上/向下誤讀會造成 FN | Q2 定義目標值 + 使用者後續確認沿用 OCR 容錯 — A1 更新 |
| A2 | Decided | Q4 明確：保留 `"絕對附加方塊 (僅洗兩排)"`，移除無後綴 `"絕對附加方塊"`（見 FR-19） | Q4 使用者明確答覆 — 從 Assumption 升格為 Decision |
| A3 | Decided | 本次為 **需求調整（spec change）**，非 bug fix — 即使現行 code 對部分邊界案例碰巧通過，新語意需以 FR + 新測試明確鎖定；UI / 說明文字同步更新 | Q1 使用者明確答覆 — 從 Open Question 升格為 Decision |
| A4 | Assumption | 個人自用工具，無多使用者 / 稽核 / 權限需求 | Project context |
| A5 | Assumption | 現有 mode 選擇**未**持久化在 config.json；mode 從 `use_preset` + `LineCondition.position` 欄位推導 | Phase 2 finding (condition_editor.py:461-466) — **推翻初版 A8 migration 假設** |
| A6 | Decided | 「同種主屬」（FR-12.1(a)）定義為**同一屬性名稱**（STR+STR、DEX+DEX 等），不接受 STR+DEX 這類「跨屬性同數值」組合 | Q3 使用者明確答覆 — 從 Open Question 升格為 Decision |
| A7 | Decided | Custom mode 任一排的數值下限 = `THRESHOLD_TABLE` 的「罕見」欄位（index [0][1]） | Q5 使用者明確答覆 — 從 Open Question 升格為 Decision |

## 8. Acceptance Signals

### 8.1 預設規則覆蓋

- **Signal 1.1**：手套 + 預設模式 + 目標「爆擊傷害 3%」，以下三組輸入皆輸出 `ConditionResult.passed = True`：
  - `[爆擊傷害 3%, STR 9%, STR 9%]` → pass
  - `[爆擊傷害 3%, 爆擊傷害 3%, STR 9%]` → pass
  - `[爆擊傷害 3%, 爆擊傷害 3%, 爆擊傷害 3%]` → pass
- **Signal 1.2**：帽子 + 預設模式 + 目標「技能冷卻時間 -1」，以下皆 pass：
  - `[冷卻 -1, STR 9%, 全屬 7%]` → pass
  - `[冷卻 -1, 冷卻 -1, 全屬 7%]` → pass
- **Signal 1.3**：珍貴方塊 + STR + 洗到 `[STR 9%, STR 9%, 全屬 7%]` → pass（對屬雙 S 不被排除）

### 8.2 Custom Mode 整併

- **Signal 2.1**：UI mode 下拉僅剩兩個選項（預設 / 自訂）
- **Signal 2.2**：Custom mode 第一個下拉（每 row）至少含「任一排 / 1 排 / 2 排 / 3 排」四個選項
- **Signal 2.3**：Custom mode 數值欄位在選擇屬性後自動限制下限；人工嘗試選 1% 應被 UI 拒絕或調整
- **Signal 2.4**：升級前以舊版 UI 儲存的 config（分別為 AND / OR 模式）在升級後載入，`_check_custom` 判定結果與升級前等價（透過 fixture 對比）

### 8.3 絕對附加白名單

- **Signal 3.1（永恆裝備）**：絕對附加 + 預設模式 + 裝備 = 永恆/光輝，以下皆 pass：
  - `[STR 9%, STR 9%]` / `[DEX 9%, DEX 9%]` / `[INT 9%, INT 9%]` / `[LUK 9%, LUK 9%]` → pass（同種主屬×2）
  - `[全屬 7%, 全屬 7%]` → pass
  - `[MaxHP 12%, MaxHP 12%]` → pass
- **Signal 3.2（一般裝備）**：絕對附加 + 預設模式 + 裝備 = 一般裝備，以下皆 pass：
  - `[STR 8%, STR 8%]`（同種主屬×2）
  - `[全屬 6%, 全屬 6%]`
  - `[MaxHP 11%, MaxHP 11%]`
- **Signal 3.3（手套/帽子 特殊屬性）**：
  - 手套 + 絕對附加 + `[爆擊傷害 3%, 爆擊傷害 3%]` → pass
  - 帽子 + 絕對附加 + `[冷卻 -1, 冷卻 -1]` → pass
- **Signal 3.4（FP 案例，必 fail — 篩選維度為「屬性類型 + 同名」，非數值）**：
  - 永恆 + `[STR 9%, DEX 9%]` → **fail**（Q3 同種定義 — 不同屬性名稱）
  - 永恆 + `[STR 9%, 全屬 7%]` → **fail**（跨類型雙 S — 屬性類別不同）
  - 永恆 + `[STR 9%, MaxHP 12%]` → **fail**（跨類型 — 即使各自達標）
- **Signal 3.5**：絕對附加 + 自訂模式 + 任意符合 row 條件組合 → 行為不受白名單限制（FR-14 保留）

### 8.4 說明文字差異化

- **Signal 4.1**：選擇「絕對附加方塊」時，`summary_label` 文字依 equipment_type 顯示對應白名單數值：
  - 裝備 = 永恆 / 光輝 或 手套(永恆) 或 帽子(永恆) → 含「99、77、12 12、-1 -1、雙爆手 3%+3%」對應條目
  - 裝備 = 一般裝備 或 手套(非永恆) 或 帽子(非永恆) → 含「88、66、11 11、-1 -1、雙爆手 3%+3%」對應條目
  - 非手套時不顯示「雙爆手」；非帽子時不顯示「-1 -1 冷卻」
- **Signal 4.2**：選擇「珍貴附加方塊」或「恢復附加方塊」時，`summary_label` 文字含「3S」、「雙 S」字樣
- **Signal 4.3**：裝備 = 帽子 + 一般方塊時，說明文字額外含「-2 冷卻」字樣
- **Signal 4.4**：裝備 = 手套 + 一般方塊時，說明文字含「雙爆」字樣，**但不含具體百分比數字**（FR-18）

### 8.5 測試與回歸

- **Signal 5.1**：`uv run pytest tests/test_condition.py` 全綠，升級前後無 regression（以升級前 pytest 結果為 baseline）
- **Signal 5.2**：新增測試涵蓋 FR-12.1 分級白名單 — 永恆 / 一般裝備各自的 (a)(b)(c)(d)(e) 5 類組合（pass）+ FR-13 至少 5 個 FP 案例（fail）
- **Signal 5.3**：新增測試涵蓋 FR-2、FR-3 的 N ∈ {1, 2, 3} 所有組合

## 9. Open Questions

### 9.1 Resolved (Q1–Q5)

Q1–Q5 已於 2026-04-12 由使用者答覆，結論整合至 FR / Assumptions：

| 原 Q | 原問題摘要 | 使用者答覆 | 整合位置 |
|------|-----------|-----------|----------|
| Q1 | Area 1 是 bug 還是文件更新？ | **需求調整（spec change）+ 文件更新也要做** | §1 Problem Statement、A3、FR-2..5（新測試鎖定）、FR-15..18（文件同步）|
| Q2 | 白名單數值是「恰好」還是「>=」？ | **目標值 = S 潛最高檔**（Q2 原意：game value 為精確值）；後續確認比較方式沿用 OCR 容錯（`value + tolerance >= 門檻`）避免低解析度 FN | FR-12 / FR-12.1 / FR-13、A1 |
| Q3 | 「同種主屬」定義？ | **同一屬性 × 2**（STR+STR ✓、STR+DEX ✗） | FR-12.1(a)、A6、Signal 3.4 |
| Q4 | 清理無後綴 `"絕對附加方塊"`？ | **保留有後綴的，移除無後綴** | FR-19、A2 |
| Q5 | Custom mode「任一排」下限？ | **`THRESHOLD_TABLE` 罕見欄**（永恆主屬 7、一般主屬 6、全屬 6/5、HP 9/8 等） | FR-8、A7 |

**裝備等級落差的普遍模式**（從 `condition.py:404-467 THRESHOLD_TABLE` 確認）：永恆 / 光輝 vs 一般裝備 的 S 潛 / 罕見 值皆有 **1% gap**（主屬 9 vs 8、全屬 7 vs 6、HP 12 vs 11），此模式已整合至 FR-8 / FR-12.1 具體對照表。

### 9.2 Unresolved

- [ ] **Q6（Solution-space — 建議 `/feasibility-study`）**：絕對附加白名單實作策略
  - 應以 (a) 新增 `_check_absolute_append()` 獨立函式、(b) 在 `_run_preset_any_pos` 中新增 `cube_type == 絕對附加` 分支、(c) 重構 `_check_line` 簽章支援多 cube_type 語意 — 三選一？
  - 此為方案比較，落入 `/feasibility-study` scope — 本文件不排序方案。

## 10. References

### 10.1 Code references（Phase 2 探索）

| 區域 | 檔案 | 重點行號 |
|------|------|----------|
| 門檻數值表 | `app/core/condition.py` | **`THRESHOLD_TABLE` 404-467** — FR-8（罕見欄）與 FR-12.1（S 潛欄）的數值來源；永恆/一般、手套/帽子永恆/非永恆、主武器/副手/萌獸皆在此定義 |
| 預設規則 | `app/core/condition.py` | `_check_line()` 556-578；`_run_preset_any_pos()` 581-620；`accept_crit3` / `accept_cooldown` flag 572-577 |
| 預設規則 | `app/core/condition.py` | `CUSTOM_SELECTABLE_ATTRIBUTES` 512-518；`EQUIPMENT_ATTRIBUTES` 473-481；`_STATS_WITH_ALL_STATS` 486；`ETERNAL_EQUIP_TYPES` 495；`_resolve_equip_type` 498-503 |
| Custom mode | `app/gui/condition_editor.py` | `_MODE_PRESET` / `_MODE_AND` / `_MODE_OR` 25-28；mode combo 105-113；`_refresh_position_combos` 237-256；`_on_mode_changed` 321-328 |
| Custom mode | `app/gui/condition_editor.py` | `load_from_config()` mode 推導 461-466 |
| Custom mode | `app/core/condition.py` | `_check_custom()` 977-1005 |
| 絕對附加 | `app/gui/settings_panel.py` | `CUBE_TYPES` 17；UI dropdown 36-39 |
| 絕對附加 | `app/core/condition.py` | `_TWO_LINE_CUBE_TYPES` 623；`get_num_lines()` 626-628；2-line summary 734-746 |
| 說明文字 | `app/gui/condition_editor.py` | `summary_label` 149-152 |
| 說明文字 | `app/core/condition.py` | `generate_condition_summary()` + helpers 674-815 |
| 測試 | `tests/test_condition.py` | `TestConditionCheckerGlove` class 1390；`TestConditionCheckerHat` class 1971；`TestPresetPermutationCheck` class 1803（FR-2/FR-3 核心：預設模式手套 / 帽子的 permutation 覆蓋）；`TestConditionCheckerCustomMode` class 1616；`TestConditionCheckerCustomAnyPosition` class 2235；`TestConditionCheckerCustomSummary` class 2118；`TestConditionCheckerDynamicRows` class 2178；2-line cube 實際測試：`TestConditionCheckerSubWeaponConvertible`（1164）2-row cases 1285-1335 + `TestAbsoluteCubeTwoLines` class 2379（絕對附加 2-line 專屬測試） |

### 10.2 Memory references

- `feedback_case_vs_inference.md` — cases-only methodology（C5 的依據）
- `project_custom_mode_merge_plan.md` — 2026-04-09 預告的 merge 計畫（本次需求正是啟動該計畫），由 Phase 2 驗證 `position=0` 語意確實已支援（A5 取代初版 A8）

### 10.3 建議後續流程

1. ~~使用者回覆 Q1–Q5~~ ✅ 已完成（2026-04-12）
2. **下一步**：執行 `/sd0x-dev-flow:feasibility-study condition-rules-v2` — 聚焦 Q6（絕對附加白名單實作策略三選一）
3. 執行 `/sd0x-dev-flow:tech-spec condition-rules-v2`
4. 執行 `/sd0x-dev-flow:feature-dev` 實作（含新測試覆蓋 FR-12.1 分級矩陣全部組合 + FR-13 FP 案例）
