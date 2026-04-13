# Requirements: 條件規則系統 v3（裝備類型收斂 + 說明文字精簡）

> **Created**: 2026-04-12
> **Last Updated**: 2026-04-13（新增 §5.7 GUI Polish；FR-16..25 改寫；UI label「帽子→冷卻帽」）
> **Tier**: standard
> **Previous Feature**: [condition-rules-v2](../condition-rules-v2/1-requirements.md) — 2026-04-12 合併（PR #43）
> **Tech Spec**: [2-tech-spec.md](./2-tech-spec.md)（需同步更新以涵蓋 §5.7 與 FR-16..29 改寫）

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
| 說明文字精簡：預設規則 summary 傳達「結構性組合」（3S、雙 S、全屬混搭、雙爆、-2 冷卻），不列出裝備等級數值 | 變更成功判定邏輯本身 |
| 絕對附加說明明確以「僅支援」表達封閉白名單；手套 / 冷卻帽 checkbox 勾選時傳達「洗到主屬會洗掉」語意 | 改變 v2 絕對附加白名單的門檻值 |
| 直接移除 `is_eternal` 欄位與「手套 / 帽子」equipment_type，採用全新 schema | 為舊 config.json 做 migration（發布方式為整包重下載，每次都是全新 config — 見 A3） |
| UI label 改用「冷卻帽」而非「帽子」以明示 checkbox 對應「想洗冷卻屬性的帽子」情境 | 變更內部識別符 `is_hat`（仍維持原名） |
| 設定面板移除 GPU 加速 checkbox（短期不實作，避免誤導） | 移除 `AppConfig.use_gpu` dataclass 欄位（保留以避免 OCR 引擎破壞） |
| 主視窗「檢查更新」按鈕具明顯按鈕外觀；新增 1920×1080 解析度建議提示 | 變更版本檢查邏輯本身 |

## 3. Stakeholders

| Stakeholder | Role | Key Concern |
|-------------|------|-------------|
| 使用者（單一） | User + Developer + Operator | 選單更短、checkbox 直觀、說明一眼看懂、升級零破壞 |
| `app/core/condition.py` | Dependent (code) | `EQUIPMENT_TYPES` / `EQUIPMENT_ATTRIBUTES` 保持 v3 縮減後形態；`GEAR_EQUIP_TYPES`（v3 既有 frozenset）作為 gear 判定；v2 本檔符號 `ETERNAL_EQUIP_TYPES` / `GLOVE_TYPES` / `HAT_TYPES` / `_resolve_equip_type` 已在先前 v3 工單移除；`ConditionChecker` 以 `is_glove` / `is_hat` flag 驅動 `accept_crit3` / `accept_cooldown`；`generate_condition_summary` 文案須依 FR-16..25 改寫 |
| `app/gui/condition_editor.py` | Dependent (code) | 移除 `eternal_check`，新增 `glove_check` + `hat_check`（mutually exclusive、UI label `冷卻帽`）；checkbox 僅對永恆 / 光輝 + 一般裝備顯示；副手目標屬性欄位寬度增加；`_on_equip_changed` / `load_from_config` 邏輯調整；summary_label 文案對照 FR-16..25 改寫 |
| `app/gui/settings_panel.py` | Dependent (code) | 完全移除 `gpu_checkbox` 區塊（L78-85）及 `apply_to_config` / `load_persistent_from_config` 中的 GPU 讀寫（L92, L102） |
| `app/gui/main_window.py` | Dependent (code) | 「檢查更新」按鈕（`btn_check_update`）樣式調整（QSS 差異化）；新增解析度提示 label |
| `app/models/config.py` | Dependent (config) | `is_glove: bool` / `is_hat: bool` 已存在（L43-44）；`is_eternal` 已移除；v2 的 `_OLD_EQUIP_MIGRATION` 表已移除；`__post_init__` 互斥歸零邏輯（L55-61）已實作，對應 Signal 3.4 |
| `tests/test_condition.py` | Dependent (tests) | `TestConditionCheckerGlove` / `TestConditionCheckerHat` / `TestAbsoluteCubeTwoLines` 既有案例需重構（改用新 schema），行為斷言保持等價 |
| `app/cube/*.py`（compare_flow, simple_flow） | Dependent (code) | 不變動（讀取 `ConditionChecker` 結果的介面保持不變） |
| `docs/features/condition-rules-v2` | Reference | v2 FR-2 / FR-3 / FR-12.1 / FR-16 的語意必須在 v3 仍成立（行為不變，只改變入口 / 說明） |

## 4. Use Cases

| # | Actor | Action | Expected Outcome |
|---|-------|--------|-----------------|
| UC-1 | 使用者 | 打開裝備類型下拉 | 僅看到 4 個選項：永恆 / 光輝、一般裝備、主武器 / 徽章、輔助武器（不再有獨立的手套 / 帽子 / 萌獸亦維持 v2 動態注入行為） |
| UC-2 | 使用者 | 選「永恆 / 光輝」 | UI 出現「手套」與「冷卻帽」兩個 checkbox（二擇一，預設皆未勾）；勾其中一個會 disable 另一個 |
| UC-3 | 使用者 | 勾「手套」checkbox、目標 = STR | 判定要求「任一排為爆擊傷害 3%」為必要條件，其餘兩排為 STR / 全屬性 / HP 達標（行為等價於 v2 的「手套 + 目標 STR」）；三排同主屬無任何爆擊 → 判定失敗 |
| UC-4 | 使用者 | 勾「冷卻帽」checkbox、目標 = STR | 判定要求「任一排為技能冷卻時間 -1 秒」為必要條件（支援 -2 冷卻）；三排同主屬無任何冷卻 → 判定失敗 |
| UC-5 | 使用者 | 選「永恆 / 光輝」但不勾任何 checkbox、目標 = STR | 等同 v2 的「永恆 / 光輝 + STR」；不套用爆擊 / 冷卻預檢（對應「要洗主屬帽子」情境 — 此時不勾「冷卻帽」） |
| UC-6 | 使用者 | 選「輔助武器」 | 目標屬性下拉僅顯示「物理 / 魔法攻擊力 (可轉換)」一個選項；欄位寬度足以完整顯示全名 |
| UC-7 | 使用者 | 選「永恆 / 光輝」+ 目標 = 所有屬性 + cube = 珍貴方塊 | `summary_label` 顯示 `支援 力 / 敏 / 智 / 幸、全屬、HP，包含 3S、雙 S 及全屬混搭` |
| UC-8 | 使用者 | 選「永恆 / 光輝」+ 目標 = STR + cube = 絕對附加 | `summary_label` 顯示 `99 力`（無括號、無補充字樣） |
| UC-9 | 使用者 | 選「永恆 / 光輝」+ 勾「手套」 + cube = 絕對附加 | `summary_label` 顯示 `僅支援 33 爆` |
| UC-10 | 使用者 | 選「永恆 / 光輝」+ 勾「冷卻帽」 + cube = 絕對附加 | `summary_label` 顯示 `支援 -1 -1 冷卻，也接受 77 全 冷卻；若洗到主屬會直接洗掉` |
| UC-11 | 使用者 | 下載新版整包並首次啟動 | 以預設 config 啟動（全新 schema，無 `is_eternal` 欄位、無「手套 / 帽子」equipment_type）；使用者重新設定一次即可 |
| UC-12 | 使用者 | 打開設定面板 | 不再看到「啟用 GPU 加速」checkbox（FR-26 區塊移除） |
| UC-13 | 使用者 | 打開主視窗 | 狀態列右側「檢查更新」按鈕具明顯按鈕外觀（邊框 + 底色 + hover 效果），並於主視窗內可見「建議採用解析度 1920 x 1080 辨識上會比較精準」提示文字 |

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
| FR-7 | UI 必須新增「手套」與「冷卻帽」兩個 checkbox，僅在 `equipment_type ∈ {"永恆 / 光輝", "一般裝備 (神秘、漆黑、頂培)"}` 且 `mode == 預設規則` 時顯示；切換到其他 equipment 或自訂模式時整組 checkbox 隱藏。UI label 採用「冷卻帽」而非「帽子」以明確表達此 checkbox 對應「想洗冷卻屬性的帽子」場景；若使用者要洗主屬帽子則不勾選（對應 UC-5） | Must | v2 `eternal_check` 的可見度規則類比沿用；User 2026-04-13 追加要求 UI label 從「帽子」改為「冷卻帽」 |
| FR-8 | 兩個 checkbox mutually exclusive：勾「手套」時，「冷卻帽」自動 disable 且視覺灰化（vice versa）；取消勾選後對方恢復可用 | Must | User 明確要求；避免使用者同時勾兩個產生語意衝突 |
| FR-9 | Checkbox 預設皆為未勾選；使用者可選擇不勾任一個（對應 UC-5，例：要洗主屬帽子 → 不勾「冷卻帽」） | Must | User 明確指出帽子類職業不一定需要冷卻；要洗主屬帽子時不應勾選 |
| FR-10 | UI 必須在 checkbox 附近顯示說明性提示（tooltip 或 label）。**3-line cube（珍貴 / 恢復）** 勾選後規則：**至少 1 排**必須符合對應特殊條件（手套 = 爆擊傷害 3% / 冷卻帽 = 冷卻 -1 秒，含更高減冷如 -2 秒），其餘排依主屬 / 全屬 / HP 判定（允許 2 排或 3 排皆為特殊條件）。若三排皆為主屬 / 全屬 / HP 而無任何特殊條件，判定為不合格（洗掉）。若不勾選則無特殊條件預檢。**2-line cube（絕對附加）** 勾選後規則：以 §5.6（FR-22..25）之白名單為權威定義，FR-10 僅提供「不勾選 = 無預檢」之基線補充，不規定 2-line 接受組合（避免與 FR-25 冷卻帽可接受 `77 全 + 冷卻` 之規則相互矛盾） | Must | User 明確要求以說明文字處理「某些帽子職業不需勾」的情境；User 2026-04-13 追加強調「洗到三排同屬會洗掉」語意；3-line 為「至少 1 排」（v2 FR-2 / FR-3 明定 N ∈ {1, 2, 3}）；2-line 規則權威交由 §5.6 以解決早期版本 FR-10「雙排皆特殊」與 FR-25「77 全接受」的語意衝突（codex 2026-04-13 指出） |

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

### 5.5 說明文字（預設規則 summary 精簡）

**設計原則**（User 2026-04-13）：說明文字傳達「支援哪些結果」，預設門檻（99 力 / 77 全 / 12 12 HP 等）內建於永恆 / 光輝或一般裝備的閾值，無須在說明中列出數值；只描述「結構性組合」（3S、雙 S、全屬混搭、雙爆、-2 冷卻）。

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-16 | **永恆 / 光輝 + 一般裝備，cube = 珍貴 / 恢復（3-line），目標 = 所有屬性** → `summary_label` 採用：`支援 力 / 敏 / 智 / 幸、全屬、HP，包含 3S、雙 S 及全屬混搭` | Must | User 2026-04-13 明確指定文字 |
| FR-17 | **永恆 / 光輝 + 一般裝備，cube = 珍貴 / 恢復（3-line），目標 = 主屬（力 / 敏 / 智 / 幸）之一** → `summary_label` 採用：`支援 3S、雙 S，包含全屬混搭`（不加括號、不列 99 / 77 數值） | Must | User 2026-04-13 明確指定；數值內建於裝備等級 |
| FR-18 | **永恆 / 光輝 + 一般裝備，cube = 珍貴 / 恢復（3-line），目標 = 全屬性** → `summary_label` 採用：`包含 3S、雙 S 的情況`（不加「全屬混搭」，因本身就是全屬） | Must | User 2026-04-13 明確指定 |
| FR-19 | **永恆 / 光輝 + 一般裝備，cube = 珍貴 / 恢復（3-line），勾選「手套」checkbox** → `summary_label` 採用：`必須符合一排為爆擊傷害 3%，支援雙爆、3S、雙 S`（不論目標為主屬 / 全屬 / HP，均以此文案覆蓋） | Must | User 2026-04-13 明確指定；手套預檢語意蓋過一般 summary |
| FR-20 | **永恆 / 光輝 + 一般裝備，cube = 珍貴 / 恢復（3-line），勾選「冷卻帽」checkbox** → `summary_label` 採用：`必須符合一排為技能冷卻時間 -1 秒，支援 -2 冷卻、3S、雙 S` | Must | User 2026-04-13 明確指定；冷卻帽預檢語意蓋過一般 summary |
| FR-21 | **主武器 / 徽章（3-line），目標 = 物理攻擊力** → `summary_label` 採用：`三物（支援 3S、雙 S）`；**目標 = 魔法攻擊力** → 採用：`三魔（支援 3S、雙 S）` | Must | User 2026-04-13 明確指定；單一屬性目標，不含跨物 / 魔合稱 |
| FR-21.1 | **輔助武器（副手，3-line）** 說明維持 v2 行為：`三物 / 三魔（副手可於遊戲內進行物魔日冕）`；**副手 2-line（絕對附加）** 保留 v2 結尾註解 `(副手可於遊戲內進行物魔日冕)` | Should | v2 行為保留；日冕轉換為副手專屬語意，不受 FR-21 影響 |
| FR-21.2 | 一般裝備與永恆 / 光輝的 summary 文案**完全相同**（FR-16..20）；兩者差別僅在背後裝備屬性 % 數（永恆 = 9 / 9 / 7 / 7 / 12 / 12，一般 = 8 / 8 / 6 / 6 / 11 / 11），不在說明文字中區分 | Must | User 2026-04-13 明確說明「畢竟他們只有裝備屬性%數不一樣而已」 |

### 5.6 絕對附加說明（2-line cube）

**設計原則**（User 2026-04-13）：絕對附加白名單嚴格有限，說明必須用「僅支援」明示封閉集；勾選手套 / 冷卻帽時，若洗到主屬會直接失敗（洗掉），說明需傳達此語意。

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-22 | **絕對附加 + 目標 = 所有屬性** → `summary_label` 採用：`僅支援 99 四屬、77全、12 12 HP`（永恆 / 光輝；一般裝備對應 `88 四屬、66全、11 11 HP`）。注意：`77全` 不含空格 | Must | User 2026-04-13 明確指定：加「僅支援」、`77全` 無空格 |
| FR-23 | **絕對附加 + 目標 = 主屬（力 / 敏 / 智 / 幸）之一** → `summary_label` 採用：`99 力` / `99 敏` / `99 智` / `99 幸`（依目標），不含括號說明文字（例：不再附加「(也接受 77 全屬)」等括號）。一般裝備對應 `88 力` 等 | Must | User 2026-04-13 明確指定：四屬情境不要括號 |
| FR-23.1 | **絕對附加 + 目標 = HP** → `summary_label` 採用：`12 12 HP`（永恆 / 光輝）或 `11 11 HP`（一般裝備） | Must | 同 FR-23 格式一致性 |
| FR-24 | **絕對附加 + 勾選「手套」checkbox** → `summary_label` 採用：`僅支援 33 爆`（覆蓋一般 summary；意指兩排皆爆擊傷害 3%，若洗到主屬則判定失敗即洗掉） | Must | User 2026-04-13 明確指定 |
| FR-25 | **絕對附加 + 勾選「冷卻帽」checkbox** → `summary_label` 採用：`支援 -1 -1 冷卻，也接受 77 全 冷卻；若洗到主屬會直接洗掉` | Must | User 2026-04-13 明確指定；冷卻帽絕對附加接受「雙冷卻」或「77 全 + 冷卻」兩種白名單組合 |

### 5.7 GUI Polish（設定面板與主視窗）

User 2026-04-13 追加的 GUI 層級調整，與條件規則邏輯無直接關聯，但屬同一發布範圍。

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-26 | `app/gui/settings_panel.py` 必須**完全移除** GPU 加速 checkbox 區塊（`gpu_checkbox`、對應 `row4` layout、`apply_to_config` 中的 `config.use_gpu` 寫入、`load_persistent_from_config` 中的 `self.gpu_checkbox.setChecked(...)`）。`AppConfig.use_gpu` 欄位可保留（若仍被 OCR 引擎參考），但 UI 不再顯露此選項 | Must | User 2026-04-13 明確要求：「短時間不會需要，直接移除」 |
| FR-27 | 主視窗「檢查更新」按鈕（`btn_check_update`）必須在視覺上**可辨識為按鈕**——使用者能於主視窗初見即判斷其為可點擊元件，而非僅是文字標籤。具體呈現手段（邊框、底色、hover 效果、icon 等）由 `/tech-spec` 階段決議（見 §9.1 OQ-2），本 FR 僅規範可觀察的結果 | Must | User 2026-04-13 明確指出：目前顏色與周圍 GUI 完全相同，容易誤認為文字標籤（保持 problem-space，將 QSS 細節下放至 tech-spec） |
| FR-28 | 主視窗必須加入一段可見的補充提示文字，語意為：建議採用 1920 x 1080 解析度以獲得較佳 OCR 辨識精準度。位置與精確樣式由 tech-spec 決定，建議對照既有 hint label 樣式（例：`settings_panel.py` 中 `delay_hint` 的灰色小字模式） | Must | User 2026-04-13 明確要求；幫助新使用者理解 OCR 辨識準度受解析度影響 |
| FR-29 | 所有 UI 可見文字（checkbox label、summary_label、tooltip、hint label）須整體檢視一致性：相同語意採用相同詞彙；繁中寫作符合台灣慣用（`資料` 非 `数据`、`程式` 非 `程序`、`解析度` 非 `分辨率`）；技術術語保留英文（OCR、GPU、HP）；標點符號統一採用全形中文標點 | Should | User 2026-04-13 要求「文字在幫我統一優化」；對齊 `@rules/docs-writing.md` locale 規則 |

## 6. Non-Functional Requirements

| ID | Category | Requirement | Metric |
|----|----------|-------------|--------|
| NFR-1 | Reliability | 既有 `tests/test_condition.py` 所有測試（手套 / 帽子 / 絕對附加 classes）必須經 schema 改寫後全綠；行為斷言等價 v2；新增測試僅需覆蓋 Signal 3.3 防呆 + Signal 3.4 invalid config | `uv run pytest tests/test_condition.py` 全綠 |
| NFR-2 | Maintainability | `EQUIPMENT_TYPES` 縮減後，相關 dict keys（`EQUIPMENT_ATTRIBUTES`、`_EQUIP_TO_CUSTOM_CATEGORY`、`THRESHOLD_TABLE`）必須保持一致；不得有 legacy equipment_type dispatch 路徑（`grep -n "_resolve_equip_type\\|GLOVE_TYPES\\|HAT_TYPES\\|ETERNAL_EQUIP_TYPES" app/core/condition.py` 結果 = 0）；此檢查不涵蓋註解或 summary 字串中的「手套 / 帽子」描述語 | grep 結果 = 0 |
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
| A6 | Decided | UI checkbox label「帽子」改為「冷卻帽」；內部 `is_hat` 識別符不變（避免破壞 schema） | User 2026-04-13 |
| A7 | Decided | `AppConfig.use_gpu` dataclass 欄位**保留**（避免 OCR 引擎引用點破壞），僅移除 UI 顯露 | 推論：cases-only 原則，未證實 OCR 是否仍引用 → 保留欄位，僅斷尾 UI |
| A8 | Open → OQ-2 | 「檢查更新」按鈕的具體 QSS 配色由 tech-spec 階段選擇（建議參照 `btn_start` ▶ 開始按鈕視覺權重）。問題本身列於 §9.1 OQ-2 | 待 `/tech-spec` 階段決議 |

## 8. Acceptance Signals

### 8.1 裝備類型收斂

- **Signal 1.1**：`EQUIPMENT_TYPES` 去除「手套」與「帽子」後長度為 4（不含萌獸動態注入）
- **Signal 1.2**：UI 裝備類型下拉在非萌獸 cube 下僅列 4 個選項；選擇「永恆 / 光輝」或「一般裝備」才顯示「手套 / 冷卻帽」checkbox 群組
- **Signal 1.3**：選擇「主武器 / 徽章」或「輔助武器」時 checkbox 群組隱藏

### 8.2 Checkbox 互斥、預設與判定等價

- **Signal 2.1**：勾「手套」→「冷卻帽」checkbox 進入 disabled 狀態；取消勾選後「冷卻帽」恢復可用（vice versa）
- **Signal 2.1.1（FR-9 預設未勾）**：開啟編輯器預設狀態下 `glove_check.isChecked() == False` 且 `hat_check.isChecked() == False`
- **Signal 2.1.2（FR-10 提示文案覆蓋）**：checkbox 的 tooltip（或鄰近 label）文字經 lowercase 後同時包含以下三個 token（逐字比對）：`爆擊`、`冷卻`、`三排` 或 `同屬`；以 `in` 運算子測試斷言
- **Signal 2.2**：`equipment_type = "永恆 / 光輝"` + `is_glove = True` + 目標 = STR，對以下 OCR lines 判定為 pass（行為等價 v2 FR-2）：
  - `[爆擊傷害 3%, STR 9%, STR 9%]`
  - `[爆擊傷害 3%, 爆擊傷害 3%, STR 9%]`
  - `[爆擊傷害 3%, 爆擊傷害 3%, 爆擊傷害 3%]`
- **Signal 2.3**：同條件但 `is_glove = False, is_hat = False` 時，以上第一組 fail 若第 1 排非目標屬性（行為等價 v2 的「永恆 / 光輝 + STR」預檢缺席）
- **Signal 2.4**：`equipment_type = "一般裝備"` + `is_hat = True` + 目標 = STR，對 `[冷卻 -1, STR 8%, 全屬 6%]` 判定為 pass（行為等價 v2 FR-3 一般等級）

### 8.3 Schema 清理（無 Migration）

- **Signal 3.1**：`AppConfig` dataclass 不含 `is_eternal` 欄位（`grep -n "is_eternal" app/models/config.py` 結果為 0）
- **Signal 3.2**：`_OLD_EQUIP_MIGRATION` 表（若仍存在）中「手套 / 帽子」四個 legacy entries 不得保留；若整表已移除，此 Signal 自動滿足
- **Signal 3.3（舊 config 防呆 — 單一行為）**：載入內容為 `{"equipment_type": "手套", ...}` 的 config.json 時，`AppConfig.load()` 必須：(a) 將 `equipment_type` fallback 為 `"永恆 / 光輝"`、(b) 透過 logging.warning 記錄含 `equipment_type` 字樣的警告、(c) 不 raise；必須有單元測試覆蓋三項行為
- **Signal 3.4（invalid config — 單一行為）**：若載入到 `is_glove = True` 且 `is_hat = True` 的 config，`AppConfig.load()`（或 `__post_init__`）必須將兩者同時歸零並透過 logging.warning 記錄含 `is_glove` 與 `is_hat` 字樣的警告；**不** raise ValueError（配合現況 `app/models/config.py:55-61` 已實作的互斥歸零行為）；必須有單元測試覆蓋
- **Signal 3.5（FR-3 非 gear 忽略 subtype flag）**：當 `equipment_type ∈ {"主武器 / 徽章 (米特拉)", "輔助武器 (副手)"}` 時，即使 config 含 `is_glove = True` 或 `is_hat = True`，`ConditionChecker._is_glove` 與 `_is_hat` 必須為 `False`（驗證 `app/core/condition.py:1007-1009` 的 `is_gear = equip in GEAR_EQUIP_TYPES` 閘道）
- **Signal 3.6（FR-5 無 legacy resolve 路徑）**：`app/core/condition.py` 中無 `_resolve_equip_type` 符號；`THRESHOLD_TABLE` 的 key 直接為 `equipment_type` 值（`grep -n "_resolve_equip_type" app/core/condition.py` 結果為 0）

### 8.4 副手欄位簡化

- **Signal 4.1**：選擇「輔助武器」時 `attr_combo.count() == 1` 且 text = `"物理/魔法攻擊力 (可轉換)"`
- **Signal 4.2**：`attr_combo` 寬度 ≥ 240px（或 OS 預設字型下 full text 不截斷）
- **Signal 4.3**：自訂模式 + 輔助武器仍可選擇「物理攻擊力」或「魔法攻擊力」（FR-15 保留）

### 8.5 說明文字（預設規則 3-line）

- **Signal 5.1**：珍貴方塊 + 永恆 / 光輝（或一般裝備）+ 目標 = 所有屬性 → `summary_label` 等於 `支援 力 / 敏 / 智 / 幸、全屬、HP，包含 3S、雙 S 及全屬混搭`
- **Signal 5.2**：珍貴方塊 + 永恆 / 光輝（或一般裝備）+ 目標 = 主屬（STR / DEX / INT / LUK 之一）→ `summary_label` 等於 `支援 3S、雙 S，包含全屬混搭`（不含括號、不含 99 / 77 / 88 / 66 數值）
- **Signal 5.3**：珍貴方塊 + 永恆 / 光輝（或一般裝備）+ 目標 = 全屬性 → `summary_label` 等於 `包含 3S、雙 S 的情況`
- **Signal 5.4**：珍貴方塊 + 勾選「手套」checkbox → `summary_label` 等於 `必須符合一排為爆擊傷害 3%，支援雙爆、3S、雙 S`（覆蓋 Signal 5.1..5.3 文案）
- **Signal 5.5**：珍貴方塊 + 勾選「冷卻帽」checkbox → `summary_label` 等於 `必須符合一排為技能冷卻時間 -1 秒，支援 -2 冷卻、3S、雙 S`
- **Signal 5.6**：珍貴方塊 + 主武器 / 徽章 + 目標 = 物理攻擊力 → `summary_label` 等於 `三物（支援 3S、雙 S）`；目標 = 魔法攻擊力 → 等於 `三魔（支援 3S、雙 S）`
- **Signal 5.7**：珍貴方塊 + 副手（3-line）→ `summary_label` 含 `三物 / 三魔` 且含 `日冕` 字樣
- **Signal 5.8**：永恆 / 光輝 與一般裝備（不含子類別 checkbox）在相同目標屬性下，summary 文字**完全相等**（FR-21.2）

### 8.6 絕對附加說明（2-line）

- **Signal 6.1**：絕對附加 + 永恆 / 光輝 + 目標 = 所有屬性 → `summary_label` 等於 `僅支援 99 四屬、77全、12 12 HP`（注意 `77全` 無空格）；一般裝備對應 `僅支援 88 四屬、66全、11 11 HP`
- **Signal 6.2**：絕對附加 + 永恆 / 光輝 + 目標 = STR → `summary_label` 等於 `99 力`（不含括號、不含「也接受」字樣）；其他三主屬類推
- **Signal 6.3**：絕對附加 + 目標 = HP → `summary_label` 等於 `12 12 HP`（永恆）或 `11 11 HP`（一般）
- **Signal 6.4**：絕對附加 + 勾選「手套」→ `summary_label` 等於 `僅支援 33 爆`
- **Signal 6.5**：絕對附加 + 勾選「冷卻帽」→ `summary_label` 等於 `支援 -1 -1 冷卻，也接受 77 全 冷卻；若洗到主屬會直接洗掉`
- **Signal 6.6**：絕對附加 summary 全體不含 `9 7 雙 S 混搭` 或類似跨類型組合描述
- **Signal 6.7**：副手 2-line 說明保留 v2 的 `(副手可於遊戲內進行物魔日冕)` 結尾

### 8.7 GUI Polish

- **Signal 7.1.a（GPU UI 移除）**：`grep -n "gpu_checkbox" app/gui/settings_panel.py` 結果為 0；開啟設定面板不再出現「啟用 GPU 加速」字樣
- **Signal 7.1.b（GPU config 讀寫移除）**：`apply_to_config` / `load_persistent_from_config` / `load_from_config` 三處不再對 `config.use_gpu` 做讀或寫（`grep -n "use_gpu" app/gui/settings_panel.py` 結果為 0）；此 Signal 對應 FR-26 第二半
- **Signal 7.2（更新按鈕可辨識為按鈕）**：機械驗收 —— `btn_check_update.styleSheet() != ""`（套用非預設 QSS）**且** `btn_check_update.isFlat() == False`；主觀驗收（可選）：新使用者盲測能於 3 秒內判斷其為按鈕。具體 QSS 內容由 tech-spec 決定（OQ-2）
- **Signal 7.3（解析度提示）**：主視窗 GUI 包含 label 文字 `建議採用解析度 1920 x 1080 辨識上會比較精準`（或等義），樣式對照 `delay_hint`（gray、12px）
- **Signal 7.4（UI label widget 斷言）**：`hat_check.text() == "冷卻帽"` 且 `glove_check.text() == "手套"`（以 widget text 直接斷言，避免 grep 誤觸註解 / 內部字串 / summary 文案中的「帽子」描述語）；內部識別符 `is_hat` 維持不變

### 8.8 測試與回歸

- **Signal 8.1**：`uv run pytest tests/test_condition.py` 全綠（以 v2 綠燈為 baseline）
- **Signal 8.2**：新增測試覆蓋 FR-11 舊 equipment_type 防呆（Signal 3.3）、Signal 3.4 invalid config、FR-16..25 的 summary 字串斷言（逐字比對文案）
- **Signal 8.3**：v2 的 `TestConditionCheckerGlove` / `TestConditionCheckerHat` 測試類別經測試參數更新（equipment_type + is_glove/is_hat flag 改寫）後全綠
- **Signal 8.4（GUI 測試）**：擴充既有 `tests/test_condition_editor.py`（Signal 7.4 widget label）與 `tests/test_main_window.py`（Signal 7.1.a/7.1.b GPU 移除、Signal 7.2 按鈕樣式、Signal 7.3 解析度提示），可用 Qt offscreen fixture

## 9. Open Questions

### 9.1 Unresolved

| OQ | 問題 | 擬解決階段 |
|----|------|-----------|
| OQ-2 | 「檢查更新」按鈕之具體 QSS 配色（邊框顏色、底色、hover 色）如何選擇以同時符合視覺可辨識性與整體 GUI 色調？建議參考既有 `btn_start` ▶ 開始按鈕的視覺權重 | `/tech-spec` 階段決議（對應 A8；FR-27 的實作層） |

### 9.2 Resolved

| 原 OQ | 原問題 | 使用者答覆 | 整合位置 |
|-------|--------|-----------|----------|
| OQ-1 | 「所有屬性」欄位是否改名？ | 維持不變 | A4 |

> **Note**: checkbox 狀態的資料結構（`is_glove` / `is_hat` 兩個 bool，mutually exclusive）已於 FR-2 定案。enum 替代方案（`sub_type: Literal[...]`）屬實作細節，若 `/feasibility-study` 判斷 enum 對 serialization / 測試較佳，可在 tech-spec 階段以等價 shape 調整，但對外 FR 契約不變（UI 呈現「兩個 mutually-exclusive checkboxes」）。

## 10. References

### 10.1 Code references（Phase 2 探索）

> **Anchor policy**: 下列行號為 2026-04-13 re-anchor 後的現況（v3 部分重構已 merge，v2 符號 `GLOVE_TYPES` / `HAT_TYPES` / `ETERNAL_EQUIP_TYPES` / `_resolve_equip_type` / `_OLD_EQUIP_MIGRATION` / `is_eternal` / `eternal_check` 已不存在）；若 code 後續變動，請以符號名稱為準，行號僅為輔助。

| 區域 | 檔案 | 符號 + 行號（2026-04-13） |
|------|------|----------|
| 裝備類型定義 | `app/core/condition.py` | `_ATTACK_CONVERTIBLE` L444、`EQUIPMENT_ATTRIBUTES` L447、`EQUIPMENT_TYPES` L455 |
| `THRESHOLD_TABLE` 對照 | `app/core/condition.py` | `THRESHOLD_TABLE` L410（永恆 / 一般 / 主武器 / 副手分段） |
| 判定 flag 路徑 | `app/core/condition.py` | `accept_crit3` / `accept_cooldown` 參數 L534-535 / L559-560 / L578-579；匹配分支 L546-549、L601-602；`self._is_glove` / `self._is_hat` 屬性 L1008-1009 |
| 副手屬性 | `app/core/condition.py` | `_ATTACK_CONVERTIBLE` L444、`EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` L451 |
| 自訂模式分類 | `app/core/condition.py` | `GEAR_EQUIP_TYPES` L462、`CUSTOM_SELECTABLE_ATTRIBUTES` L474、`_EQUIP_TO_CUSTOM_CATEGORY` L483、`get_custom_attributes` L492（含 L502 `is_gear = equipment_type in GEAR_EQUIP_TYPES`、L504-508 子類別分支） |
| Summary 生成 | `app/core/condition.py` | `generate_condition_summary` L753-（含 `_ATTACK_CONVERTIBLE` 分支 L774、`THRESHOLD_TABLE.get(equip)` L777 / L809 / L826 / L868 / L897 / L941 / L959；FR-16..25 文案撰改點） |
| UI checkbox（需重命名 label） | `app/gui/condition_editor.py` | `glove_check` L107-110、`hat_check` L111-114（L111 `QCheckBox("帽子")` 必須改為 `QCheckBox("冷卻帽")`，FR-7）；`_on_glove_toggled` / `_on_hat_toggled` L379 / L382；`_toggle_subtype_mutex` L384；`_sync_subtype_checks` L396-407；`_update_subtype_visibility` 呼叫點 L347 / L369 |
| 副手欄位寬度 | `app/gui/condition_editor.py` | `attr_combo.setMinimumWidth(150)` L139；切換分支 `_DEFAULT_ATTR_WIDTH` L365、`_SUB_WEAPON_ATTR_WIDTH` L363（需確認 ≥ 240px） |
| Config schema | `app/models/config.py` | `AppConfig` dataclass L37-；`is_glove` L43、`is_hat` L44、`use_gpu` L48；互斥驗證 `__post_init__` L55-61（已實作，對應 Signal 3.4）；`save()` L63；`load()` L74（含 `is_glove=` L90、`is_hat=` L91、`use_gpu=` L95） |
| GPU 區塊（FR-26 待移除） | `app/gui/settings_panel.py` | `gpu_checkbox` L78-85；`apply_to_config` 中 `config.use_gpu = self.gpu_checkbox.isChecked()` L92；`load_persistent_from_config` L100-102 |
| 檢查更新按鈕（FR-27） | `app/gui/main_window.py` | `btn_check_update` L118；文字更新 L284 / L302；`_UpdateCheckWorker` L30-38 |
| Hint label 樣式參考（FR-28） | `app/gui/settings_panel.py` | `delay_hint` L67-68（gray、`font-size: 12px`） |
| 測試 | `tests/test_condition.py` | `TestGetCustomAttributesSubtype` L1190、`TestConditionCheckerSubWeaponConvertible` L1227、`TestConditionCheckerGlove` L1451、`TestConditionCheckerHat` L2126、`TestAbsoluteCubeTwoLines` L2796 |

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
