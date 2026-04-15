# OCR Bug Fix Log

## 2026-04-15 `全壓性` → `全屬性`

| 現象 | Root Cause | Fix | 測試 |
|------|-----------|-----|------|
| `全壓性+7%` 未辨識 | `_OCR_FIXES` 缺少 `全壓性` 映射（屬 → 壓 誤讀） | `("全壓性", "全屬性")` | `test_ocr_fix_all_stats_ya` |

RAW 範例：`['全壓性+7%', '全屬性+7%']`（同次 OCR 兩行輸出，L1 未辨識、L2 正常）。

## 2026-03-26 Batch Fix (Bug #1-8)

### Fixed

| # | 現象 | Root Cause | Fix | 測試 |
|---|------|-----------|-----|------|
| 1 | `全屬性` → `全屋性` | `_OCR_FIXES` 缺少映射 | `("全屋性", "全屬性")` | `test_ocr_fix_all_stats_wu` |
| 2 | `LUK+6%6` 未辨識 | `%` 後殘留數字 | `_TRAILING_AFTER_PERCENT` regex 清除 `%\d+$` | `test_ocr_fix_trailing_digit_after_percent` |
| 3 | `INT` → `IT` | `_OCR_FIXES` 缺少映射 | `_OCR_INT_FIXES` regex（lookbehind 避免誤改 CRIT 等詞）| `test_ocr_fix_int_as_it` |
| 4 | `+6%6` 多處出現 | 同 #2 | 同 #2 | `test_ocr_fix_trailing_digit_str` |
| 5 | `全國性+6%` 未辨識 | `全國性`/`全慶性` 不在修正表 | `("全國性", "全屬性")`, `("全慶性", "全屬性")` | `test_ocr_fix_all_stats_guo`, `_qing` |
| 6 | `全属性+79` 未辨識 | `%` 被 OCR 誤讀為 `9` | `_PERCENT_AS_NINE` regex：僅在無 `%` 時將尾部 `9` 替換為 `%` | `test_ocr_fix_percent_as_nine` |
| 6b | `axHP+121` 未辨識 | `MaxHP` 的 `M` 被吃掉 | `("axHP", "MaxHP")`, `("axMP", "MaxMP")` | `test_ocr_fix_maxhp_ax` |
| 7 | `1NT`/`1IT`/`1TT`/`IIT` | I↔1 + N↔T 混淆 | `_OCR_INT_FIXES` regex 統一處理所有 INT 誤讀變體 | `test_ocr_fix_int_as_1nt`, `_1it`, `_1tt`, `_iit` |

### 暫不處理（Option A）

| # | 現象 | 原因 | 備註 |
|---|------|------|------|
| 8 | `DEX +996`（實際 DEX +9%）| OCR 模型完全吃掉 `%`，數值嚴重失真 | 這類 case 罕見且難以安全修正。目前標為「未辨識」。未來若採用字元級混淆映射（Option E）可能改善。|

### Known Risks

| 修正 | 風險 | 緩解 |
|------|------|------|
| `_PERCENT_AS_NINE`（9→%） | 平值屬性（如 `MaxHP +199`）可能被誤改為 `MaxHP +19%` | 僅在文字中完全沒有 `%` 時才套用；平值屬性不參與條件判斷，誤判只會造成多洗一次（false positive），不會洗掉好潛能（false negative）|
| `_OCR_INT_FIXES` | 包含 `IT` 的其他英文詞（如 `LIMIT`）可能被誤改 | lookbehind `(?<![A-Za-z0-9])` 限制前方不能有字母數字；遊戲截圖中不會出現這類英文詞 |

### Domain Knowledge

- 全屬性永遠帶 `%`，不會有平值
- 爆擊傷害、屬性%、攻擊力% 都是 % 類屬性，平值版本通常不是目標
- 帽子的「技能冷卻時間 -N 秒」是唯一重要的非 % 屬性
- 洗兩排潛能使用絕對附加方塊，相關實作可能需要另外調整

### Future Improvement

- 考慮重構為字元級混淆映射（feasibility study Option E），減少維護成本
- 絕對附加方塊的兩排潛能實作待調整
