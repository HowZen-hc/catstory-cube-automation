# Requirements: 條件規則系統 v3（裝備類型收斂 + 說明文字精簡）

> **Created**: 2026-04-12
> **Tier**: standard
> **Previous Feature**: [condition-rules-v2](../condition-rules-v2/1-requirements.md) — 2026-04-12 合併（PR #43）
> **Tech Spec**: （尚未建立，建議後續執行 `/feasibility-study` → `/tech-spec`）

## 1. Problem Statement

condition-rules-v2（PR #43）剛完成四個區域（預設覆蓋、custom 整併、絕對附加白名單、說明差異化）。實際使用後發現四個 UX 層面的摩擦：

1. **裝備類型選單過於冗長**：`EQUIPMENT_TYPES` 中手套、帽子分別獨立為兩個選項，但他們的主屬 / 全屬 / HP 判定邏輯與「永恆 / 光輝」、「一般裝備」完全相同，差別只在多一個「可接受爆擊傷害 3%」或「可接受冷卻 -1 秒」的判定路徑。使用者每次要選「手套」還是「永恆 / 光輝」要多想一次，且選錯會走到不同的 summary / threshold 分支。
2. **`is_eternal` 是多餘維度**：目前只有手套 / 帽子會出現 `永恆/非永恆` checkbox；若把手套 / 帽子合併進「永恆 / 光輝」與「一般裝備」，等級資訊已從裝備類型本身攜帶，`is_eternal` 變成重複的 UI state。
3. **副手的目標屬性欄位重複**：`輔助武器 (副手)` 目前提供三個目標屬性選項（可轉換、物攻、魔攻），但實務上只用第一個（可轉換）——遊戲內副手可整件轉換物 / 魔攻，單獨列物攻 / 魔攻欄位沒有使用情境；且目前欄位寬度不足導致文字被截斷。
4. **說明文字仍不夠精簡**：v2 已依 cube_type 差異化，但說明冗長（例：「全屬性 7% × 2」、「每排需符合以下任一 / 支援 3S、雙 S」），使用者希望改為社群慣用的超短標記法（`77 全`、`12 12 HP`、`99 力 / 敏 / 智 / 幸`）。同時絕對附加不再支援「9 7 雙 S 混搭」這類組合，但目前說明沒有明確排除；以及「當目標屬性為主屬或 HP 時，77 全屬其實也是可接受結果」這個資訊目前沒傳達給使用者。

### 5-Why Trace

| # | 層次 | 內容 |
|---|------|------|
| 1 | 表面需求 | 合併手套 / 帽子到現有裝備類型；改 checkbox 驅動爆擊 / 冷卻預檢；簡化副手目標屬性；重寫 summary 為社群標記法 |
| 2 | 為什麼現況不夠 | 裝備類型選項過多且部分重複；`is_eternal` checkbox 與「手套 / 帽子」選項疊加；副手三個選項只用一個；說明過於冗長且與使用者心智模型不一致 |
| 3 | 為什麼會這樣設計 | v2 把「是否為手套 / 帽子」視為裝備類型本身的一個維度，而非「裝備屬性」的一個修飾；v2 說明文字以工具語言生成（threshold 值 × 排數），非以社群語言表達 |
| 4 | 為什麼影響大 | 每次選裝備要重複選擇兩次（等級 + 手套 / 帽子）；配置複雜增加誤選風險；副手無效欄位影響寬度與一致性；冗長說明讓使用者分心、要重新解讀 |
| 5 | 根因 | 裝備類型抽象層次錯誤 — 應以「裝備等級（永恆 / 光輝 vs 一般裝備）」為主軸，「手套 / 帽子」退化為「可疊加預檢條件」的修飾 flag；說明文字的輸出格式應服務使用者的閱讀習慣，而非內部 threshold 結構 |

## 2. Goals / Non-Goals

| Goals | Non-Goals |
|-------|-----------|
| `EQUIPMENT_TYPES` 收斂為 4 類（永恆 / 光輝、一般裝備、主武器 / 徽章、輔助武器），移除獨立的手套 / 帽子 | 變更主武器 / 徽章的判定邏輯 |
| 以 checkbox（手套 / 帽子 二擇一）表達裝備子類別；checkbox 僅對永恆 / 光輝 + 一般裝備出現 | 變更 `THRESHOLD_TABLE` 的數值 |
| 移除 `is_eternal` UI state（等級改由裝備類型本身表達） | 新增除手套 / 帽子以外的子類別 checkbox |
| 副手目標屬性欄位僅保留「物理 / 魔法攻擊力 (可轉換)」單一選項，欄位寬度足以完整顯示 | 重寫副手判定邏輯（維持 v2 的轉換判定） |
| 說明文字改為社群標記法（`77 全`、`99 力`、`12 12 HP`、`33 爆`、`-1 -1 冷卻`） | 變更成功判定邏輯本身 |
| 絕對附加說明明確表達：僅支援 `99 四屬 / 77 全 / 12 12 HP / 33 爆（手套）/ -1 -1 冷卻（帽子）`，且主屬 / HP 路徑下加註 `7 7 全屬也接受` | 改變 v2 絕對附加白名單的門檻值 |
| 直接移除 `is_eternal` 欄位與「手套 / 帽子」equipment_type，採用全新 schema | 為舊 config.json 做 migration（發布方式為整包重下載，每次都是全新 config — 見 A3） |

## 3. Stakeholders

| Stakeholder | Role | Key Concern |
|-------------|------|-------------|
| 使用者（單一） | User + Developer + Operator | 選單更短、checkbox 直觀、說明一眼看懂、升級零破壞 |
| `app/core/condition.py` | Dependent (code) | `EQUIPMENT_TYPES` / `EQUIPMENT_ATTRIBUTES` 縮減；`ETERNAL_EQUIP_TYPES` / `GLOVE_TYPES` / `HAT_TYPES` 語意重寫；`_resolve_equip_type` 改用 `is_glove` / `is_hat` flag；`ConditionChecker` 以 flag 驅動 `accept_crit3` / `accept_cooldown`；`generate_condition_summary` 全面改寫輸出格式 |
| `app/gui/condition_editor.py` | Dependent (code) | 移除 `eternal_check`，新增 `glove_check` + `hat_check`（mutually exclusive）；checkbox 僅對永恆 / 光輝 + 一般裝備顯示；副手目標屬性欄位寬度增加；`_on_equip_changed` / `load_from_config` 邏輯調整 |
| `app/models/config.py` | Dependent (config) | 新增 `is_glove: bool` / `is_hat: bool`；直接刪除 `is_eternal` 欄位；清理 `_OLD_EQUIP_MIGRATION` 中「手套 / 帽子」legacy entries |
| `tests/test_condition.py` | Dependent (tests) | `TestConditionCheckerGlove` / `TestConditionCheckerHat` / `TestAbsoluteCubeTwoLines` 既有案例需重構（改用新 schema），行為斷言保持等價 |
| `app/cube/*.py`（compare_flow, simple_flow） | Dependent (code) | 不變動（讀取 `ConditionChecker` 結果的介面保持不變） |
| `docs/features/condition-rules-v2` | Reference | v2 FR-2 / FR-3 / FR-12.1 / FR-16 的語意必須在 v3 仍成立（行為不變，只改變入口 / 說明） |

## 4. Use Cases

| # | Actor | Action | Expected Outcome |
|---|-------|--------|-----------------|
| UC-1 | 使用者 | 打開裝備類型下拉 | 僅看到 4 個選項：永恆 / 光輝、一般裝備、主武器 / 徽章、輔助武器（不再有獨立的手套 / 帽子 / 萌獸亦維持 v2 動態注入行為） |
| UC-2 | 使用者 | 選「永恆 / 光輝」 | UI 出現「手套」與「帽子」兩個 checkbox（二擇一，預設皆未勾）；勾其中一個會 disable 另一個 |
| UC-3 | 使用者 | 勾「手套」checkbox、目標 = STR | 判定要求「任一排為爆擊傷害 ≥ 3%」為必要條件，其餘兩排為 STR / 全屬性 / HP 達標（行為等價於 v2 的「手套 + 目標 STR」） |
| UC-4 | 使用者 | 勾「帽子」checkbox、目標 = STR | 判定要求「任一排為技能冷卻時間 -1 秒」為必要條件（行為等價於 v2 的「帽子 + 目標 STR」） |
| UC-5 | 使用者 | 選「永恆 / 光輝」但不勾任何 checkbox、目標 = STR | 等同 v2 的「永恆 / 光輝 + STR」；不套用爆擊 / 冷卻預檢（例：帽子裝備但職業不需冷卻的情境） |
| UC-6 | 使用者 | 選「輔助武器」 | 目標屬性下拉僅顯示「物理 / 魔法攻擊力 (可轉換)」一個選項；欄位寬度足以完整顯示全名 |
| UC-7 | 使用者 | 選「永恆 / 光輝」+ 目標 = 所有屬性 + cube = 珍貴附加 | `summary_label` 顯示精簡標記法（例：`支援 99 力 / 敏 / 智 / 幸、77 全、12 12 HP（3S、雙 S 通過）`） |
| UC-8 | 使用者 | 選「永恆 / 光輝」+ 目標 = STR + cube = 絕對附加 | `summary_label` 顯示：`99 力`（對應 STR）+ `77 全屬（也接受，非全屬職業可於遊戲內轉換）` |
| UC-9 | 使用者 | 選「永恆 / 光輝」+ 勾「手套」 + cube = 絕對附加 | `summary_label` 含 `33 爆擊傷害` 項目 |
| UC-10 | 使用者 | 下載新版整包並首次啟動 | 以預設 config 啟動（全新 schema，無 `is_eternal` 欄位、無「手套 / 帽子」equipment_type）；使用者重新設定一次即可 |

## 5. Functional Requirements

### 5.1 裝備類型收斂（Equipment Type Consolidation）

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-1 | `EQUIPMENT_TYPES` 必須移除 `"手套"` 與 `"帽子"` 作為獨立裝備類型；保留 `"永恆 / 光輝"`、`"一般裝備 (神秘、漆黑、頂培)"`、`"主武器 / 徽章 (米特拉)"`、`"輔助武器 (副手)"`。`"萌獸"` 維持 v2 的動態注入行為，不在此列 | Must | User 要求；符合 root cause（裝備子類別是修飾 flag，非獨立類型） |
| FR-2 | `AppConfig` 必須新增 `is_glove: bool` 與 `is_hat: bool` 兩個欄位；兩者 mutually exclusive（同時為 True 視為 config 錯誤，預設皆為 False） | Must | 表達手套 / 帽子子類別；二擇一確保 UI / 判定語意一致 |
| FR-3 | `is_glove` / `is_hat` 僅在 `equipment_type ∈ {"永恆 / 光輝", "一般裝備 (神秘、漆黑、頂培)"}` 時具有語意；其他裝備類型忽略兩個 flag | Must | 其他裝備類型不會有手套 / 帽子形態 |
| FR-4 | `ConditionChecker` 的 `accept_crit3` flag 必須改由 `is_glove` 驅動（取代 v2 的 `equip in GLOVE_TYPES`）；`accept_cooldown` 改由 `is_hat` 驅動 | Must | 子類別資訊來源切換；判定結果必須與 v2 等價 |
| FR-5 | `_resolve_equip_type` 不再需要處理 `"手套" / "帽子"` → `"手套 (永恆) / ..."` 的後綴轉換，因為等級資訊已由 `equipment_type` 本身攜帶；`THRESHOLD_TABLE` 的對應 key 直接使用 `"永恆 / 光輝"` 或 `"一般裝備 (神秘、漆黑、頂培)"` | Must | `THRESHOLD_TABLE` 中「手套 (永恆) / 帽子 (永恆)」與「永恆 / 光輝」的數值等價（確認來源：`condition.py:404-467`，使用者聲明「光輝跟一般留意一下裝備 % 數有差別」— 此差別對應永恆 / 一般兩類，與手套 / 帽子無關）— **驗證任務**：Implementation 前需對照 `THRESHOLD_TABLE` 確認 `手套 (永恆)` = `永恆 / 光輝`、`帽子 (非永恆)` = `一般裝備` 的主屬 / 全屬 / HP 數值完全相同。若發現差異，以「永恆 / 光輝」與「一般裝備」為準（user 2026-04-12 聲明） |
| FR-6 | `is_eternal` 欄位必須從 UI 與 `AppConfig` dataclass 雙雙移除（直接刪除欄位宣告）；`app/models/config.py:64-96` 的 `_OLD_EQUIP_MIGRATION` 表中關於「手套 / 帽子」的 entries 亦可一併清除。發布模式為「整包重下載，每次全新 config」（A3），無需保留任何 backward-compat 讀取路徑 | Must | 發布模式決定無 migration 負擔；直接移除欄位最簡潔 |

### 5.2 Checkbox UI 互斥機制

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-7 | UI 必須新增「手套」與「帽子」兩個 checkbox，僅在 `equipment_type ∈ {"永恆 / 光輝", "一般裝備 (神秘、漆黑、頂培)"}` 且 `mode == 預設規則` 時顯示；切換到其他 equipment 或自訂模式時整組 checkbox 隱藏 | Must | v2 `eternal_check` 的可見度規則類比沿用 |
| FR-8 | 兩個 checkbox mutually exclusive：勾「手套」時，「帽子」自動 disable 且視覺灰化（vice versa）；取消勾選後對方恢復可用 | Must | User 明確要求；避免使用者同時勾兩個產生語意衝突 |
| FR-9 | Checkbox 預設皆為未勾選；使用者可選擇不勾任一個（對應 UC-5，例：帽子裝備但職業不需冷卻） | Must | User 明確指出帽子類職業不一定需要冷卻 |
| FR-10 | UI 必須在 checkbox 附近顯示說明性提示（tooltip 或 label），文字語意必須同時覆蓋 3-line 與 2-line cube：<br>**3-line cube（珍貴 / 恢復）**：勾選後，**至少 1 排**必須符合對應特殊條件（手套 = 爆擊傷害 ≥ 3% / 帽子 = 冷卻 -1 秒，含更高減冷如 -2 秒），其餘排依主屬 / 全屬 / HP 判定（允許 2 排或 3 排皆為特殊條件，參照 v2 FR-2 / FR-3）<br>**2-line cube（絕對附加）**：勾選後必須兩排皆為對應特殊條件（爆擊 3% × 2 或 冷卻 -1 × 2，對應 v2 FR-12.1 (d)(e)）<br>若不勾選，視為一般永恆 / 光輝或一般裝備判定（無特殊條件預檢） | Must | User 明確要求以說明文字處理「某些帽子職業不需勾」的情境；3-line 為「至少 1 排」（v2 FR-2 / FR-3 明定 N ∈ {1, 2, 3}），2-line 為「雙排」（v2 FR-12.1 明定 × 2） |

### 5.3 發布模式與 Schema 清理

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-11 | 本次發布採「整包重下載」模式（A3），不需 runtime migration；但為防呆：`AppConfig.load()` 讀到無法識別的舊 `equipment_type`（例：`"手套"`、`"帽子"`）時，必須 fallback 為預設值（`"永恆 / 光輝"`）並記錄 warning，不得讓程式 crash | Should | 防止使用者誤用舊 config 時白屏；但不承諾行為等價（重新設定即可） |
| FR-12 | `app/models/config.py` 中針對「手套 / 帽子」的 legacy migration entries（`_OLD_EQUIP_MIGRATION` 表的 `"手套 (永恆)"` / `"手套 (非永恆)"` / `"帽子 (永恆)"` / `"帽子 (非永恆)"` 四行）可一併移除，簡化維護 | Should | 發布模式決定不需這些 legacy key；降低 cognitive load |

### 5.4 副手欄位簡化

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-13 | `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 必須縮減為 `["物理/魔法攻擊力 (可轉換)"]` 單一選項（移除 `"物理攻擊力"`、`"魔法攻擊力"`） | Must | User 明確要求；其他兩個選項無使用情境 |
| FR-14 | `attr_combo` 於 equipment = 副手 時必須將最小寬度擴展到足以顯示 `"物理/魔法攻擊力 (可轉換)"` 全文（目前被截斷）；建議最小寬度 ≥ 240px（以 condition_editor.py 目前 150px 基準加上字元計算） | Must | User 明確提到「字被蓋到了」 |
| FR-15 | 副手 + 自訂模式仍允許使用者選擇 `"物理攻擊力"` 或 `"魔法攻擊力"` 作為單排條件（`CUSTOM_SELECTABLE_ATTRIBUTES["武器"]` 維持不變） | Should | 自訂模式保留彈性；v2 行為保留 |

### 5.5 說明文字社群標記法

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-16 | `summary_label` 必須改寫為社群慣用超短標記法：<br>• 主屬：`99 力` / `99 敏` / `99 智` / `99 幸`（對應 STR / DEX / INT / LUK，永恆 / 光輝）；一般裝備對應 `88 力` ... | Must | User 明確要求；社群慣用（`99 力` = 9% + 9% STR） |
| FR-17 | 全屬性記法：`77 全`（永恆 / 光輝）、`66 全`（一般裝備）；HP 記法：`12 12 HP`（永恆）、`11 11 HP`（一般）；爆擊：`33 爆` 或 `33 爆擊傷害`；冷卻：`-1 -1 冷卻` | Must | User 明確要求 |
| FR-18 | **一般方塊（珍貴 / 恢復，3-line）** 說明：以「目標屬性」+ 支援組合標示，不列出 `each line threshold` 的冗長文字。範例：<br>• 目標 = 主屬 STR：`支援 99 力（3S、雙 S）、77 全（混搭）`<br>• 目標 = 所有屬性：`支援 99 力 / 敏 / 智 / 幸、77 全、12 12 HP（3S、雙 S 含全屬混搭）`<br>• 目標 = HP：`支援 12 12 HP、77 全（混搭）` | Must | User 明確要求以壓縮說明 |
| FR-19 | **一般方塊 + 帽子** 說明保留 v2 的「支援 -2 冷卻」字樣（因 3-line cube 允許冷卻多於 1 排）；**一般方塊 + 手套** 說明保留「雙爆」但仍不列具體 `3%`（維持 v2 FR-18 的作用域切分） | Must | v2 行為保留；避免絕對附加語意混淆 |
| FR-20 | **主武器 / 徽章（3-line cube）** 說明：不論選物理或魔法，改為 `三物 / 魔（3S、雙 S）`（表達「攻擊力達標即可，物 / 魔同權」） | Must | User 明確要求 |
| FR-21 | **輔助武器（3-line cube）** 說明：`三物 / 三魔（副手可於遊戲內進行物魔日冕）`；2-line 副手說明保留 v2 現有結尾註解：`(副手可於遊戲內進行物魔日冕)` | Must | User 明確要求保留日冕提示 |

### 5.6 絕對附加說明緊縮

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-22 | **絕對附加 (`2-line cube, cube_type == "絕對附加方塊 (僅洗兩排)"`)** 說明：明確表達「僅支援 `99 四屬 / 77 全 / 12 12 HP`」等白名單；不列出 `9 7 雙 S 混搭` 這類非白名單描述 | Must | User 明確要求避免誤導 |
| FR-23 | **絕對附加 + 目標 = 主屬 或 HP**：說明必須加註 `7 7 全屬（也接受，非全屬職業可於遊戲內以遊戲幣轉換裝備職業）` | Must | User 明確要求；傳達遊戲內轉換可讓非全屬裝備有等值價值 |
| FR-24 | **絕對附加 + 目標 = 主屬 STR / DEX / INT / LUK** 單條標記：`99 力` / `99 敏` / `99 智` / `99 幸`；**+ 目標 = HP**：`12 12 HP`；**+ 目標 = 全屬性**：`77 全`；**+ 手套 (glove checkbox)**：`3% + 3%` 改為 `33 爆`；**+ 帽子 (hat checkbox)**：`-1 -1 冷卻` | Must | User 明確指定新格式；等級對應由 equipment 類型（永恆 vs 一般）決定，呈現 99 / 88、77 / 66、12 12 / 11 11 的差異 |

## 6. Non-Functional Requirements

| ID | Category | Requirement | Metric |
|----|----------|-------------|--------|
| NFR-1 | Reliability | 既有 `tests/test_condition.py` 所有測試（手套 / 帽子 / 絕對附加 classes）必須經 schema 改寫後全綠；行為斷言等價 v2；新增測試僅需覆蓋 Signal 3.3 防呆 + Signal 3.4 invalid config | `uv run pytest tests/test_condition.py` 全綠 |
| NFR-2 | Maintainability | `EQUIPMENT_TYPES` 縮減後，相關 dict keys（`EQUIPMENT_ATTRIBUTES`、`_EQUIP_TO_CUSTOM_CATEGORY`、`THRESHOLD_TABLE`）必須保持一致；`grep -n '"手套"' app/core/condition.py` 結果 = 0（全面移除，無 runtime dispatch / 無 legacy path） | grep 結果 = 0 |
| NFR-3 | Compatibility | 舊版 config.json（非預期被使用者手動保留的情境）載入時不得 crash（Signal 3.3）；新版 save 路徑寫出的 json 不含 `"is_eternal"` key | fixture 驗證 |
| NFR-4 | Usability | 裝備類型下拉選項數目必須從 v2 的 6 項（含獨立手套 / 帽子）減為 4 項（主 / 輔 / 永恆 / 一般；萌獸維持動態注入） | UI snapshot 驗證 |
| NFR-5 | Usability | 副手目標屬性欄位完整顯示（字元不被截斷）；以 macOS / Windows 系統字型 1080p 解析度目視驗證 | 手動 UI 驗證 |
| NFR-6 | Correctness | 說明文字改寫後必須保留 v2 的事實正確性（不得因壓縮產生與判定邏輯不一致的文字，例：不可說「支援 77 全」但實際判定門檻為 66） | 說明對照 `THRESHOLD_TABLE` 的單元測試（至少 permissive 3 組合 × 永恆 / 一般 = 6 案例） |

## 7. Constraints & Assumptions

| # | Type | Description | Source |
|---|------|-------------|--------|
| C1 | Constraint | 不得改變 `THRESHOLD_TABLE` 數值與絕對附加白名單的實質判定邏輯（僅改變輸入端：equipment_type + is_glove / is_hat flag） | Goals / Non-Goals |
| C2 | Constraint | 不得改變 `LineCondition.position` 欄位語意與自訂模式邏輯 | v2 C1 繼承 |
| C3 | Constraint | 萌獸方塊維持 v2 的特殊分支（動態注入 equipment_type、特殊判定路徑），不受 FR-1 縮減影響 | v2 邊界條件 |
| C4 | Constraint | 遵守 `feedback_case_vs_inference.md`（cases-only methodology）— 僅處理使用者提供的實際案例，不為未觀察到的情境（例：未來可能的「腰帶 / 肩膀」子類別）預寫 defensive code | Memory + project convention |
| A1 | Decided | 使用者確認 `THRESHOLD_TABLE` 中「手套 (永恆)」與「永恆 / 光輝」的主屬 / 全屬 / HP 數值等價（`光輝跟一般留意一下裝備 % 數有差別` — 僅指永恆 vs 一般等級差，非指手套 vs 非手套） | 使用者 2026-04-12 補充 |
| A2 | Decided | Checkbox 預設為未勾選；使用者不勾即視為一般裝備判定路徑（對應 UC-5） | User message |
| A3 | Decided | 發布模式為「整包重下載」：每次版本更新使用者下載完整新包，**不保留舊 `config.json`**。此決定消除所有 migration 負擔，允許直接移除欄位而非寫 compat 程式碼 | User 2026-04-12 決議 |
| A4 | Decided | 「所有屬性」欄位名稱維持不變，保留 `"所有屬性"` label（2026-04-12 使用者追加確認） | User 2026-04-12 決議 |
| A5 | Constraint | v2 FR-16 的絕對附加 summary 分級（永恆 99 / 77 / 12 12 vs 一般 88 / 66 / 11 11）必須在 v3 仍成立（只改表達格式，不改數值） | v2 carry-over |

## 8. Acceptance Signals

### 8.1 裝備類型收斂

- **Signal 1.1**：`EQUIPMENT_TYPES` 去除「手套」與「帽子」後長度為 4（不含萌獸動態注入）
- **Signal 1.2**：UI 裝備類型下拉在非萌獸 cube 下僅列 4 個選項；選擇「永恆 / 光輝」或「一般裝備」才顯示手套 / 帽子 checkbox 群組
- **Signal 1.3**：選擇「主武器 / 徽章」或「輔助武器」時 checkbox 群組隱藏

### 8.2 Checkbox 互斥 + 判定等價

- **Signal 2.1**：勾「手套」→ 「帽子」checkbox 進入 disabled 狀態；取消勾選後「帽子」恢復可用（vice versa）
- **Signal 2.2**：`equipment_type = "永恆 / 光輝"` + `is_glove = True` + 目標 = STR，對以下 OCR lines 判定為 pass（行為等價 v2 FR-2）：
  - `[爆擊傷害 3%, STR 9%, STR 9%]`
  - `[爆擊傷害 3%, 爆擊傷害 3%, STR 9%]`
  - `[爆擊傷害 3%, 爆擊傷害 3%, 爆擊傷害 3%]`
- **Signal 2.3**：同條件但 `is_glove = False, is_hat = False` 時，以上第一組 fail 若第 1 排非目標屬性（行為等價 v2 的「永恆 / 光輝 + STR」預檢缺席）
- **Signal 2.4**：`equipment_type = "一般裝備"` + `is_hat = True` + 目標 = STR，對 `[冷卻 -1, STR 8%, 全屬 6%]` 判定為 pass（行為等價 v2 FR-3 一般等級）

### 8.3 Schema 清理（無 Migration）

- **Signal 3.1**：`AppConfig` dataclass 不含 `is_eternal` 欄位（`grep -n "is_eternal" app/models/config.py` 結果為 0）
- **Signal 3.2**：`_OLD_EQUIP_MIGRATION` 表中「手套 / 帽子」四個 legacy entries 已移除
- **Signal 3.3（舊 config 防呆）**：載入內容為 `{"equipment_type": "手套", ...}` 的 config.json 時，`AppConfig.load()` 不得 crash；行為可為 (a) fallback 為預設值 + log warning，或 (b) 忽略該欄位 — 具體由 tech-spec 決定，但必須有單元測試覆蓋
- **Signal 3.4（invalid config fail-fast）**：若載入到 `is_glove=True` 且 `is_hat=True` 的 config（人工編輯錯誤），`AppConfig.load()` 必須以可觀察方式處理（拋出 ValueError 或自動將兩者歸零並記錄 warning）— 具體選擇由 `/feasibility-study` 與 `/tech-spec` 決定，但必須有單元測試覆蓋此 case

### 8.4 副手欄位簡化

- **Signal 4.1**：選擇「輔助武器」時 `attr_combo.count() == 1` 且 text = `"物理/魔法攻擊力 (可轉換)"`
- **Signal 4.2**：`attr_combo` 寬度 ≥ 240px（或 OS 預設字型下 full text 不截斷）
- **Signal 4.3**：自訂模式 + 輔助武器仍可選擇「物理攻擊力」或「魔法攻擊力」（FR-15 保留）

### 8.5 說明文字

- **Signal 5.1**：珍貴方塊 + 永恆 / 光輝 + 目標 = 所有屬性 → `summary_label` 含字串 `99 力` AND `99 敏` AND `99 智` AND `99 幸` AND `77 全` AND `12 12 HP`
- **Signal 5.2**：珍貴方塊 + 一般裝備 + 目標 = STR → `summary_label` 含 `88 力` AND `66 全`（不含 99 / 77）
- **Signal 5.3**：絕對附加 + 永恆 / 光輝 + 目標 = STR → `summary_label` 含 `99 力` 且含 `7 7 全屬` 類提示
- **Signal 5.4**：絕對附加 + 一般裝備 + `is_glove = True` → `summary_label` 含 `33 爆`
- **Signal 5.5**：絕對附加 + `is_hat = True` → `summary_label` 含 `-1 -1 冷卻`
- **Signal 5.6**：珍貴方塊 + 主武器 / 徽章 → `summary_label` 含 `三物 / 魔` 類字樣
- **Signal 5.7**：絕對附加 summary 不含 `9 7 雙 S 混搭` 或類似跨類型組合的描述
- **Signal 5.8**：副手 3-line 說明含 `三物 / 三魔` 及「日冕」字樣；副手 2-line 說明保留 v2 的 `(副手可於遊戲內進行物魔日冕)` 結尾

### 8.6 測試與回歸

- **Signal 6.1**：`uv run pytest tests/test_condition.py` 全綠（以 v2 綠燈為 baseline）
- **Signal 6.2**：新增測試覆蓋 FR-11 舊 equipment_type 防呆（Signal 3.3）、Signal 3.4 invalid config、FR-16..24 的 summary 字串斷言
- **Signal 6.3**：v2 的 `TestConditionCheckerGlove` / `TestConditionCheckerHat` 測試類別經測試參數更新（equipment_type + is_glove/is_hat flag 改寫）後全綠

## 9. Open Questions

### 9.1 Unresolved

（無 — OQ-1 已於 2026-04-12 由使用者決議為「維持『所有屬性』」，見 A4）

### 9.2 Resolved

| 原 OQ | 原問題 | 使用者答覆 | 整合位置 |
|-------|--------|-----------|----------|
| OQ-1 | 「所有屬性」欄位是否改名？ | 維持不變 | A4 |

> **Note**: checkbox 狀態的資料結構（`is_glove` / `is_hat` 兩個 bool，mutually exclusive）已於 FR-2 定案。enum 替代方案（`sub_type: Literal[...]`）屬實作細節，若 `/feasibility-study` 判斷 enum 對 serialization / 測試較佳，可在 tech-spec 階段以等價 shape 調整，但對外 FR 契約不變（UI 呈現「兩個 mutually-exclusive checkboxes」）。

## 10. References

### 10.1 Code references（Phase 2 探索）

> **Anchor policy**: 下列行號為本文件撰寫時（2026-04-12）的對應位置；若 code 後續變動，請以符號名稱（class / function / 常數）為準，行號僅為輔助。

| 區域 | 檔案 | 符號 + 行號（2026-04-12） |
|------|------|----------|
| 裝備類型定義 | `app/core/condition.py` | `EQUIPMENT_ATTRIBUTES` L479-487、`EQUIPMENT_TYPES` L489、`GLOVE_TYPES` L495、`HAT_TYPES` L498、`ETERNAL_EQUIP_TYPES` L501、`_resolve_equip_type` L504-509 |
| `THRESHOLD_TABLE` 對照 | `app/core/condition.py` | L404-467 — FR-5 等價確認 |
| 判定 flag 路徑 | `app/core/condition.py` | `accept_crit3` / `accept_cooldown` 參數宣告 L567-568、匹配分支 L579-582；`_is_glove` / `_is_hat` 屬性 L959-960；dispatch 使用 `accept_crit3=self._is_glove` / `accept_cooldown=self._is_hat` L1061-1062、L1176-1177 |
| 副手屬性 | `app/core/condition.py` | `_ATTACK_CONVERTIBLE` L476、`EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` L483 |
| 自訂模式分類 | `app/core/condition.py` | `CUSTOM_SELECTABLE_ATTRIBUTES` L518-524、`_EQUIP_TO_CUSTOM_CATEGORY` L527-535 |
| Summary 生成 | `app/core/condition.py` | `generate_condition_summary` L704-809、`_generate_absolute_summary` L812-851、`_generate_absolute_all_attrs_summary` L854-876、`_generate_all_attrs_summary` L879-928 |
| UI checkbox / 寬度 | `app/gui/condition_editor.py` | `eternal_check` L95-98、`_update_eternal_visibility` L350-354；預設模式 `attr_combo.setMinimumWidth(150)` L122-123（副手需擴展至 ≥ 240px，FR-14） |
| Config schema | `app/models/config.py` | `AppConfig` dataclass L36-51（`is_eternal` 欄位 L43）；`save()` 使用 `asdict(self)` L53-61；`load()` + migration 表 `_OLD_EQUIP_MIGRATION` L64-96 |
| 測試 | `tests/test_condition.py` | `TestConditionCheckerSubWeaponConvertible` L1164、`TestConditionCheckerGlove` L1390、`TestConditionCheckerHat` L2015、`TestAbsoluteCubeTwoLines` L2467 |

### 10.2 Doc references

- [condition-rules-v2 1-requirements.md](../condition-rules-v2/1-requirements.md) — v2 FR-2 / FR-3 / FR-12.1 / FR-16 行為繼承基準
- [condition-rules-v2 2-tech-spec.md](../condition-rules-v2/2-tech-spec.md) — dispatch 順序與 `_build_whitelist` 結構
- [sub-weapon-attack-convertible 2-tech-spec.md](../sub-weapon-attack-convertible/2-tech-spec.md) — 副手可轉換判定邏輯（FR-13 / FR-21 不改動此部分）

### 10.3 Memory references

- `feedback_case_vs_inference.md` — cases-only methodology（C4 的依據）
- `project_sub_weapon_attrs.md` — 副手僅洗物 / 魔攻、整件轉換（FR-13 的歷史脈絡）
- `project_custom_mode_merge_plan.md` — 自訂模式合併計畫（v2 已完成，v3 不動）

### 10.4 Requests directory

- `./requests/` — 本 feature 產出的 per-task 工單將存於此（非 lifecycle 文件）

### 10.5 建議後續流程

1. 執行 `/sd0x-dev-flow:feasibility-study condition-rules-v3` — 聚焦 FR-11 防呆策略與 invalid config 處理方式（Signal 3.3 / 3.4）
2. 執行 `/sd0x-dev-flow:tech-spec condition-rules-v3`
3. 執行 `/sd0x-dev-flow:create-request` 拆分 3 個工單（裝備類型收斂 / Checkbox UI / Summary 改寫）
4. 執行 `/sd0x-dev-flow:feature-dev` 實作（含新測試）
