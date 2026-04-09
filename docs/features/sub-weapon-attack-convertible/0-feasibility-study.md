# 副手雙攻擊力（可轉換）條件可行性研究

## 1. 問題本質

### 1.1 表面需求

副手（輔助武器）在 CatStory 遊戲內可進行「防具轉換」，把洗出的魔法攻擊力轉成物理攻擊力，反之亦然。目前這支自動化工具在預設模式下只能指定「物理攻擊力」**或**「魔法攻擊力」單一目標，導致洗到另一種攻擊力時會被判定為不合格而繼續洗掉。使用者希望這兩種攻擊力都能被視為合格停手條件。

### 1.2 核心問題（5 Why）

1. 為什麼要改？ — 副手可在遊戲內互轉物攻／魔攻，玩家不想先鎖死一種。
2. 為什麼現況不夠？ — 預設模式的 `target_attribute` 是單一字串，判定只會套到一種屬性。
3. 為什麼造成痛點？ — 好卷（可轉換後可用）會被繼續洗掉，浪費方塊成本極高。
4. 為什麼風險高？ — 判定錯誤的代價不對稱：**false negative（本來是好卷但被判為不合格 → 工具繼續洗，覆蓋掉原本該停手的好卷）** 的代價 **遠高於** **false positive（壞卷被誤判為合格 → 工具停手，玩家手動按一次再洗即可）**。設計上必須優先降低 FN。
5. 根因 — 目前條件模型沒有「可互轉等價屬性群組」概念。自訂模式的「符合任一」雖可湊出近似效果，但語意是「任一排命中一條」而非「三排皆達標且屬性一致」。

### 1.3 成功標準

- 副手選用新選項後，以下情境必須正確：
  - ✅ 三排都達到物理攻擊力門檻 → 通過
  - ✅ 三排都達到魔法攻擊力門檻 → 通過
  - ❌ 三排都是攻擊力但未達門檻（含 OCR 容錯）→ 不通過
  - ❌ 三排屬性混搭（例：2 物 1 魔）→ **不通過**（整件轉換語意，見 §8 決定紀錄 D1）
- 既有「只想要物攻」或「只想要魔攻」的使用者不受影響（原選項保留）。
- 條件摘要（UI 顯示）能清楚描述新語意。
- 不需要使用者手動改 `config.json`；必須在 UI 下拉中可發現。
- 不破壞既有測試（217 tests）。

### 1.4 範圍限制（由使用者確認）

- **僅處理副手（輔助武器）**：主武器 / 徽章在遊戲內不支援防具轉換（D2），本次不擴充。
- **僅動預設模式**：自訂模式（「逐排指定」與「符合任一」）本次不碰；相關改動留給後續的「自訂模式整併」重構（D3）。
- **副手屬性封閉集合**：遊戲內副手潛能只會出現物理攻擊力與魔法攻擊力，不會出現 STR/DEX/INT/LUK/MaxHP 等屬性。此假設簡化了邊界處理，但仍需在測試中保留「非法屬性出現時拒絕」的防呆案例。

## 2. 約束條件

| 類型 | 約束 | 來源 | 彈性 |
|------|------|------|:----:|
| 業務 | 誤判漏停代價極高（浪費方塊）| 專案 README／既有設計註解 | 無 |
| 技術 | 預設模式 `target_attribute` 是單一字串，條件摘要由 `generate_condition_summary` 硬字串拼出 | `app/core/condition.py:614-730` | 低 |
| 技術 | UI `attr_combo` 完全由 `EQUIPMENT_ATTRIBUTES[equip_type]` 灌入，擴充點集中 | `app/gui/condition_editor.py:332-345` | 高 |
| 技術 | `_check_所有屬性` 的語意是「三排全部用同一屬性鍵通過」，不接受混合 | `app/core/condition.py:824-855` | 高 |
| 相容 | 舊 `config.json` 需無痛讀取（不得刪欄位） | `app/models/config.py:64-112` | 無 |
| 資源 | 個人專案，偏好最小改動、最少新欄位 | — | 中 |

## 3. 現有能力盤點

### 3.1 相關模組

| 檔案:行 | 作用 |
|---------|------|
| `app/core/condition.py:410-413` | `THRESHOLD_TABLE["輔助武器 (副手)"]` 已同時包含 `物理攻擊力` 與 `魔法攻擊力`（均為 `((12, 9), None)`） |
| `app/core/condition.py:459` | `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 只列 `["物理攻擊力", "魔法攻擊力"]`，無「雙接受」選項 |
| `app/core/condition.py:801-822` | `_check_preset_any_pos` — 以單一 `target_key` 在所有排列組合中找合格分配 |
| `app/core/condition.py:824-855` | `_check_所有屬性` — 對 `_equip_thresholds` 中每個屬性分別跑「與 `_check_preset_any_pos` 同型的內嵌排列檢查邏輯」（非直接呼叫，而是行內複製 `permutations` + `_check_line` 的迴圈），任一屬性能把三排完整覆蓋即通過 |
| `app/core/condition.py:614-730` | `generate_condition_summary` + `_generate_all_attrs_summary` — 條件摘要硬編碼 STR/DEX/INT/LUK/全屬性/MaxHP，對武器類屬性沒有對應分支 |
| `app/gui/condition_editor.py:332-345` | `_on_equip_changed` — 依裝備類型填入 `attr_combo`，切換時自動觸發 |
| `app/models/config.py:64-112` | `AppConfig.load` — 已有舊設定欄位遷移區塊，可無痛加欄位（`data.get(..., default)`） |

### 3.2 已有的設計模式

- **「所有屬性」模式**：對防具已運作，邏輯模型正是「列舉所有可接受主屬性，任一能覆蓋三排即通過」。
- **條件摘要分派**：`generate_condition_summary` 依 `target_attribute` 字串分支。新增字串等於新增一條摘要分支。
- **OCR 容錯**：`_NO_TOLERANCE_EQUIP` 白名單保證副手會套用 `_OCR_TOLERANCE=2`，直接適用新條件。

### 3.3 Tech Debt

- `_generate_all_attrs_summary` 只列主屬系（STR/DEX/INT/LUK/全屬/MaxHP），對副手的 `所有屬性` 會印出空摘要（確認：見 `_generate_all_attrs_summary` 第 689-714 行）。若改以「重用所有屬性」路徑，必須同步補這裡。
- 測試覆蓋不足：副手只有一個預設模式測試（`test_sub_weapon` at `tests/test_condition.py:923`），沒有「混合拒絕」或「雙接受」案例。

## 4. 可能方案

### Option A：新增預設目標屬性字串「物理/魔法攻擊力 (可轉換)」

**核心**：在 `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 加一個新字串，`ConditionChecker` 偵測到後內部跑「物攻為目標」與「魔攻為目標」兩次 `_check_preset_any_pos`，任一通過即合格。

**實作路徑**：

1. `app/core/condition.py`
   - 定義 `_ATTACK_CONVERTIBLE = "物理/魔法攻擊力 (可轉換)"`
   - 在 `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 列首加入該字串
   - `ConditionChecker.__init__` 偵測到該屬性時：
     - 設 `self._is_attack_convertible = True`
     - 預先儲存兩組門檻 `self._phys_thresholds = THRESHOLD_TABLE[resolved]["物理攻擊力"]`、`self._magic_thresholds = THRESHOLD_TABLE[resolved]["魔法攻擊力"]`
     - **重要**：不得覆蓋／共用 `self._target_key`、`self._s_val` 等既有欄位，避免誤影響其他模式
   - 在 `ConditionChecker.check()` 的分派鏈（緊接 `_is_雙終被` / `_is_所有屬性` 分支之前或之後）新增：
     ```python
     if self._is_attack_convertible:
         return self._check_attack_convertible(lines)
     ```
   - 新增 `_check_attack_convertible(lines)`：實作成**參數化** helper，分別以 (`物理攻擊力%`, phys_thresholds) 與 (`魔法攻擊力%`, magic_thresholds) 為參數呼叫同一個純函式；任一 True 即回傳 True。兩次檢查之間**不得共用可變狀態**（避免 target/threshold 殘留造成誤判）。建議把既有 `_check_preset_any_pos` 的核心迴圈抽成接受 `(target_key, s_val, r_val)` 三個參數的 helper，原方法改為 thin wrapper 呼叫該 helper，新路徑亦呼叫同一 helper。
   - `generate_condition_summary` 新增分支（需同時支援 2 排與 3 排方塊，對齊既有 `num_lines == 2` 分支的格式）：
     - 3 排方塊：`["每排需符合以下任一:", "  · 物理攻擊力 12% or 9%", "  · 魔法攻擊力 12% or 9%", "(副手可於遊戲內互轉)"]`
     - 2 排方塊（絕對附加方塊）：`["兩排需符合以下任一:", "  · 物理攻擊力 12%", "  · 魔法攻擊力 12%", "(副手可於遊戲內互轉)"]`
     - 實作上建議在 `generate_condition_summary` 的 `num_lines == 2` 分支前後，各加一個 `attr == _ATTACK_CONVERTIBLE` 早退（early-return）分支，避免污染既有路徑
2. `app/gui/condition_editor.py` — 無需修改（`attr_combo` 會自動顯示新選項）
3. `tests/test_condition.py`
   - 新增 `TestConditionCheckerSubWeaponConvertible`：
     - 3 排純物攻通過、3 排純魔攻通過
     - 混合（2 物 1 魔、1 物 2 魔）拒絕
     - 未達門檻拒絕（含 OCR 容錯邊界 = S潛-2、-3）
     - 2 排方塊（絕對附加方塊）×{物/魔}通過、混合拒絕、未達門檻拒絕
     - 摘要文字快照（2 排 & 3 排各一）
4. `app/models/config.py` — 無需加欄位；新舊 `config.json` 皆自動相容（`target_attribute` 是字串）

> **範圍註記**：主武器 / 徽章（米特拉）在遊戲內**不**支援防具轉換（見 §8.1 D2），故**不**同步擴充該裝備類型。

**可行性評估**：

| 維度 | 評級 | 說明 |
|------|:----:|------|
| 技術可行性 | 🟢 | 100% 重用 `_check_preset_any_pos`；無新演算法 |
| 工作量 | 🟢 | 約 1.5-2.5 人天（程式 + 測試 + 摘要文案） |
| 風險 | 🟢 | 改動集中在 condition.py 的新分支；不動既有路徑 |
| 延展性 | 🟢 | 主武器／徽章未來要加同功能：加 1 行到 `EQUIPMENT_ATTRIBUTES` |
| 可發現性 | 🟢 | 下拉選單首項，不必讀文件 |
| 命名清晰度 | 🟢 | 「(可轉換)」直接對應遊戲用語 |
| 維護成本 | 🟢 | 新分支獨立，耦合低 |

**Cost**：

- 約 45-90 行程式 + 測試
- 需補 `generate_condition_summary` 分支（12-25 行）
- 無 schema migration

---

### Option B：把副手掛到既有「所有屬性」模式

**核心**：直接把 `"所有屬性"` 字串加進 `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]`，`ConditionChecker._check_所有屬性` 會自動以 `THRESHOLD_TABLE["輔助武器 (副手)"]` 的兩個鍵（物攻／魔攻）當候選，三排全物或全魔才過。

**實作路徑**：

1. `app/core/condition.py` — `EQUIPMENT_ATTRIBUTES` 加一個字串
2. `_generate_all_attrs_summary` **必須**改為泛化版本（或加武器分支），否則副手選「所有屬性」會印幾乎空白的條件摘要
3. `tests/test_condition.py` — 補副手 `所有屬性` 的 pass/fail/mixed/摘要案例

**可行性評估**：

| 維度 | 評級 | 說明 |
|------|:----:|------|
| 技術可行性 | 🟢 | 判定引擎 0 行改動，直接跑通 |
| 工作量 | 🟢 | 約 0.5-1.0 人天（判定）+ 修摘要 |
| 風險 | 🟡 | `_generate_all_attrs_summary` 泛化可能波及既有防具摘要行為 |
| 延展性 | 🟡 | 主武器要同功能必須承襲「所有屬性」命名 |
| 可發現性 | 🟡 | 使用者需猜測「副手的『所有屬性』是什麼意思」 |
| 命名清晰度 | 🔴 | 「所有屬性」在副手語境是誤導；副手只有兩個屬性不是「所有」 |
| 維護成本 | 🟡 | 命名負債會隨未來裝備擴張而放大 |

**Cost**：

- 程式 2-5 行（judge）+ 20-45 行（摘要泛化）+ 測試
- 無 schema migration
- **長期 UX 債**：命名語意錯誤，新使用者會誤解

---

### Option C：新增 `accept_both_attack_types` config 旗標 + UI checkbox

**核心**：`AppConfig` 增加布林欄位，副手預設模式下若 `target_attribute` 是物攻或魔攻且此旗標為 True，則判定時雙方向皆接受。UI 在副手模式多顯示一個 checkbox。

**實作路徑**：

1. `app/models/config.py` — 新增欄位 + `load()` 用 `data.get("accept_both_attack_types", False)` 相容舊檔
2. `app/core/condition.py` — `ConditionChecker` 讀取旗標，在 `_check_preset_any_pos` 前後包裝「雙向嘗試」
3. `app/gui/condition_editor.py` — 副手（或武器類）+ 預設模式時顯示 checkbox；切換裝備時隱藏重置
4. `generate_condition_summary` — 摘要需反映旗標狀態
5. `tests/test_condition.py` + `tests/test_config.py` — 新欄位、遷移、雙接受、混合拒絕、UI checkbox 互動

**可行性評估**：

| 維度 | 評級 | 說明 |
|------|:----:|------|
| 技術可行性 | 🟢 | 單純布林 flag |
| 工作量 | 🟡 | 約 1-2 人天，觸及 config + UI + 判定三層 |
| 風險 | 🟡 | UI 狀態管理（切換裝備時重置旗標）容易漏邊界 |
| 延展性 | 🟢 | 未來主武器轉換：同旗標擴張 |
| 可發現性 | 🟡 | checkbox 貼在哪、顯示條件都需設計 |
| 命名清晰度 | 🟢 | 「接受物／魔互轉」文案清楚 |
| 維護成本 | 🟡 | 一個 config 欄位 + UI 條件顯示 |

**Cost**：

- 約 90-170 行
- 輕量 migration（`.get()` 預設值）
- UI 狀態機略複雜

---

### Option D（拒絕）：資料層 alias — 把物攻／魔攻統一成 `攻擊力`

會影響主武器／徽章／萌獸／log／custom mode 多處，回歸面太大。且會喪失「只要物攻不要魔攻」的精準表達能力。

### Option E（拒絕）：只改文件，建議用自訂「符合任一」模式

自訂符合任一的語意是「有任一排命中任一條件即可」，與「三排達標」不等價，會誤判漏停風險更大。此外使用者已明確說找不到選項，僅改文件無法解決可發現性問題。

### Option F（拒絕）：手動改 `config.json` 加隱藏 key

`main_window._load_config_to_ui` 刻意不把下拉選單從 config 載回 UI（`app/gui/main_window.py:148-154`，註解明寫「下拉選單保持 UI 預設值」），且 `_on_start` 會執行 `apply_to_config` + `config.save()` 把當下 UI 狀態寫回磁碟（`app/gui/main_window.py:158-169`）。因此手改 `config.json` 會在啟動流程完全被覆蓋；且完全不可發現。

## 5. Codex 深度討論記錄

### 5.1 討論過程

| 回合 | 主題 | Codex 關鍵觀點 |
|------|------|----------------|
| 1 | 初次方案枚舉 | 獨立研究代碼後指出 `_generate_all_attrs_summary` 硬編碼問題（主動發現的盲點） |
| 1 | 建議方案 | 推薦 **C（新 config 旗標）** 為主、**B（重用所有屬性）**為備 |
| 2 | A/B/C 深度比較 | 重新評估後，在「假設 mixed roll 拒絕」前提下翻轉為推薦 **A** |
| 2 | 摘要函式 gap | 確認 A 需補 12-25 行、B 必改 20-45 行、C 需補 10-20 行 |

### 5.2 Codex 指出的風險／議題

- **`_generate_all_attrs_summary` 盲點**：若走 Option B（重用所有屬性），此 helper 對副手會回傳幾乎空白的摘要，必須同步泛化或加武器分支，否則條件預覽 UI 會壞掉。
- **`main_window` 會覆寫 config**：手改 config.json（Option F）不可行，啟動後就被 UI 值覆寫。
- **副手預設模式測試單薄**：目前只有一個 `test_sub_weapon`，不足以保護新邏輯。需補至少 4-5 個 case。
- **命名風險**：「所有屬性」套到副手會讓使用者困惑（副手只有兩個屬性）。

### 5.3 Claude 與 Codex 的差異與整合

| 觀點 | Claude 初判 | Codex 初判 | 最終採納 |
|------|-------------|------------|---------|
| 主推方案 | Option B（重用所有屬性，最少改動） | Option C（新 flag，語意最準） | **Option A**（Codex 二輪翻轉，Claude 同意） |
| 拒絕混合卷 | 預設拒絕，列開放問題 | 同 | 一致 |
| 摘要函式盲點 | 初期未發現 | 主動指出 | Codex 加分，採納修補 |
| 主武器是否同步擴充 | 未提 | 列為延展性加分 | 列為選配（見 §9） |

### 5.4 整合結論

Codex 的獨立研究發現了 `_generate_all_attrs_summary` 的硬編碼問題，使「重用所有屬性」（B）的隱藏成本浮上檯面。兩輪討論後雙方都翻到同一結論：**Option A** 在語意清晰、可發現性、與改動集中度三方面都勝出；B 的速度優勢被命名債抵消；C 對目前需求過度設計。

## 6. 方案比較

| 維度 | Option A | Option B | Option C |
|------|:--------:|:--------:|:--------:|
| 技術可行性 | 🟢 | 🟢 | 🟢 |
| 工作量（人天）| 1.5-2.5 | 0.5-1.0 + 摘要泛化 | 1-2 |
| 回歸風險 | 🟢 | 🟡（摘要函式改動波及防具）| 🟡（三層改動）|
| 可發現性 | 🟢 | 🟡 | 🟡 |
| 命名清晰度 | 🟢 | 🔴 | 🟢 |
| 延展性（主武器轉換）| 🟢 | 🟡 | 🟢 |
| Config schema 變動 | 無 | 無 | 新欄位 + migration |
| 摘要函式工作 | +12-25 行分支 | +20-45 行泛化 | +10-20 行 |
| 維護成本 | 🟢 | 🟡 | 🟡 |

## 7. 推薦方案

**推薦**：**Option A — 新增預設目標屬性「物理/魔法攻擊力 (可轉換)」**

**理由**：

- **符合約束**：無 schema migration、改動集中在 `condition.py`、UI 無需手動修改（`_on_equip_changed` 會自動灌入）。
- **語意正確**：新分支內部呼叫兩次 `_check_preset_any_pos` 就能精準表達「三排全物 OR 三排全魔」，且預設自然拒絕混合，對齊保守假設。
- **UX 勝出**：下拉選單首項，文案自帶「(可轉換)」就不需讀文件；不污染「所有屬性」命名。
- **Codex 同步**：兩輪獨立研究後雙方都翻到同一結論，方案收斂可信度高。
- **延展性**：若日後主武器／徽章也支援轉換，只需在 `EQUIPMENT_ATTRIBUTES` 再加一行。

**備選**：**Option B（重用所有屬性）**

**適用場景**：若要把工期壓到極限（半天內落地），且接受短期 UX 命名債，可快速上 B，待 v2 再重命名遷移。但不建議作為正式方案。

**拒絕**：D/E/F（理由見 §4）。C 雖然延展性和正確性都不錯，但對目前「只有副手一個場景」的需求來說，新增 config 欄位與 UI checkbox 屬於過度設計；在主武器也開放轉換時再升級到 C 更划算。

## 8. 決定紀錄 & 剩餘開放問題

### 8.1 已確認決定（2026-04-09，由使用者回覆）

| ID | 議題 | 決定 | 對實作的影響 |
|----|------|------|--------------|
| D1 | 防具轉換語意 | **整件統一互換** | 混合洗出（例：2 物 1 魔）必須**拒絕**。Option A 預設行為即為此語意，不需加 `allow_mixed` 參數，但函式仍應寫成易讀易測的純函式（便於日後若遊戲規則改變時擴充）。 |
| D2 | 主武器 / 徽章是否同步支援 | **不支援**（遊戲內主武器／徽章無防具轉換功能）| 只動 `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]`，不碰 `主武器 / 徽章 (米特拉)`。 |
| D3 | 本次是否動自訂模式 | **不動**（預設模式 only）| 不修改 `condition_editor.py` 的自訂模式相關 widget 或 `get_custom_attributes` / `CUSTOM_SELECTABLE_ATTRIBUTES["武器"]`。使用者未來會把「逐排指定」與「符合任一」重構為單一模式，此功能屬於該重構的前置需求之外。 |
| D4 | 副手屬性集合假設 | **僅物理攻擊力 / 魔法攻擊力**，副手不會出現 STR/DEX/INT/LUK/MaxHP 等屬性 | 簡化 `_check_attack_convertible` 邏輯：不必支援「全屬性」fallback。但測試仍應涵蓋「非法屬性出現時拒絕」的防呆案例（OCR 誤判防線）。 |
| D5 | 新選項的中文命名 | **`物理/魔法攻擊力 (可轉換)`** | `_ATTACK_CONVERTIBLE = "物理/魔法攻擊力 (可轉換)"`；UI 下拉文案、條件摘要、測試快照皆以此字串為準。 |
| D6 | 是否取代原「物理攻擊力」作為副手預設值 | **是**（Option A：列表首位且為預設）| `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"] = ["物理/魔法攻擊力 (可轉換)", "物理攻擊力", "魔法攻擊力"]`。`_on_equip_changed` 切換到副手時，`attr_combo` 預設值自動為第一項。原「物理攻擊力」「魔法攻擊力」保留給想鎖死單一屬性的使用者。 |

### 8.2 剩餘開放問題

- [ ] **O1**：是否需要在 `CHANGELOG.md` 和 release notes 標註這是新功能？
  - 建議：是（CHANGELOG `### Added`、release notes「副手新增雙攻擊力可轉換條件（可接受物／魔任一種）」）
  - 本題留待 PR 階段處理，不阻擋進入 `/tech-spec`。

## 9. 下一步

所有阻擋性決定已鎖定（D1-D6），可直接進入技術規格階段：

1. `/tech-spec` — 依 Option A 寫出完整技術規格，含：
   - `_ATTACK_CONVERTIBLE = "物理/魔法攻擊力 (可轉換)"` 常數與分派點
   - `_check_attack_convertible` 函式簽章與演算法（整件轉換語意，拒絕混合卷）
   - `generate_condition_summary` 新分支範本（2 排 + 3 排）
   - `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 新順序（新選項置於列首作為預設值）
   - 測試清單（≥ 8 個 case，含 OCR 非法屬性防呆）
2. `/feature-dev` — 實作 → `/verify` → `/codex-review-fast` + `/codex-test-review` → `/precommit`
3. 文件同步 — 更新 `docs/potential-system.md`（若有提到副手條件）
4. PR 階段 — 處理 §8.2 O1（CHANGELOG / release notes 標註）

## 10. 驗收指標

| 項目 | 指標 |
|------|------|
| 功能（3 排方塊）| 新選項在副手下拉可見，三排純物攻／純魔攻可停手；混合與低於門檻拒絕 |
| 功能（2 排方塊）| 絕對附加方塊選新選項時，兩排純物攻／純魔攻可停手；混合與低於門檻拒絕 |
| 相容 | 既有 `config.json`（舊 `target_attribute`）零遷移即載入 |
| 測試 | 新增 ≥ 8 個測試 case（3 排 pass phys / pass magic / reject mixed / reject low-tolerance-edge；2 排 pass phys / pass magic / reject mixed；摘要快照 3 排 + 2 排）|
| UI | 條件預覽摘要正確顯示雙接受語意（2 排與 3 排格式皆正確）|
| 回歸 | 既有 217 tests 全數通過 |
