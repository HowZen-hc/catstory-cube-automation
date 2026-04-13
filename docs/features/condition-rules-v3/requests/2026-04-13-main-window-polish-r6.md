# Phase 2 GUI: 主視窗 Polish（更新按鈕樣式 + 解析度提示 + 文字統一）

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-13
> **Status**: Completed
> **Priority**: P2
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md) — §3.6.4 / §3.6.5 / §3.6.6
> **Requirements**: [1-requirements.md](../1-requirements.md) — FR-27、FR-28、FR-29、Signal 7.2 / 7.3

## Background

主視窗「檢查更新」按鈕（`btn_check_update`）目前無 QSS 套用，與周圍 GUI 視覺權重相同，使用者反映無法一眼辨識為按鈕。同時主視窗缺乏對 OCR 解析度建議的提示，新使用者不知 1920×1080 為較佳辨識條件。最後 GUI 文案需 sweep 統一（zh-TW 慣用詞、全形標點、技術術語保留英文）。

## Requirements

- `btn_check_update` 套用 QSS：邊框 + 底色 + hover 效果（採 Material Blue 500 系列為預設方案，per OQ-5）
- `btn_check_update.setFlat(False)`（確保非 flat，配合 Signal 7.2 機械斷言）
- 主視窗加入 QLabel：`建議採用解析度 1920 x 1080 辨識上會比較精準`，樣式對照 `delay_hint`（gray、12px）
- 文字 sweep：`tests/test_locale_sweep.py` 內以 Python `re.compile(r"数据|程序|分辨率").search(content)` 對 `app/gui/*.py` 內容驗證為 None（限 user-visible literal，註解 / docstring 排除）— canonical 驗收方式以 Python regex 為準，避免 shell `grep -E` / BRE 之 escape 陷阱
- 新增 GUI 測試驗證 button styleSheet、isFlat、resolution_hint 文字

## Scope

| Scope | Description |
|-------|-------------|
| In | WS7（btn_check_update QSS + resolution_hint label + 文字 sweep）+ WS8c（GUI 測試）。文字 sweep 對 `condition_editor.py` / `settings_panel.py` 為 **read-only 檢測**：僅運行 grep 驗證，不修改 R4/R5 的既定變更檔案內容 |
| Out | R4（summary / label 文案改動）、R5（GPU 區塊移除）不在範圍；版本檢查邏輯本身不動（沿用 `_UpdateCheckWorker`）。若 sweep 發現 R4/R5 既定變更外的簡中詞需修正，於本 ticket 處理 |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/gui/main_window.py` | Modify | L118 後新增 `btn_check_update.setStyleSheet(...)` + `setFlat(False)`；layout 中新增 `resolution_hint = QLabel("建議採用解析度 1920 x 1080 辨識上會比較精準")` 並套用 `color: gray; font-size: 12px;`（位置：靠近狀態列下方或設定面板上方，per OQ-7） |
| `app/gui/settings_panel.py` | Read-only sweep | 僅執行 grep 驗證；若 R5 既定變更外發現簡中詞需替換為繁中對應，於本 ticket 處理（不碰 R5 的 GPU 區塊變更） |
| `app/gui/condition_editor.py` | Read-only sweep | 僅執行 grep 驗證；若 R4 既定變更外發現簡中詞需替換，於本 ticket 處理（不碰 R4 的 summary / label 變更） |
| `tests/test_main_window.py` | Modify | 新增：`btn_check_update.styleSheet() != ""`、`btn_check_update.isFlat() == False`、`resolution_hint.text()` 含 `1920` AND `1080` |
| `tests/test_locale_sweep.py` | New | 新增測試：使用 Python `re.compile(r"数据|程序|分辨率")` + 讀取 `app/gui/*.py` 內容後 `pattern.search(content)` 應為 None（FR-29 機械驗收；避免 shell escape 陷阱） |

## Acceptance Criteria

- [x] AC-1: `btn_check_update.styleSheet() != ""` 且 `btn_check_update.isFlat() == False`（`TestUpdateButtonStyle` 斷言） (FR-27, Signal 7.2)
- [x] AC-2: 「檢查更新」按鈕具明顯邊框 / 底色 / hover / pressed / disabled 五態 QSS（`test_button_stylesheet_covers_interactive_states` 鎖定所有互動態選擇器）(FR-27)
- [x] AC-3: 主視窗包含 `resolution_hint` QLabel，`text()` 含 `1920` 且含 `1080`；樣式 `color: gray; font-size: 12px`（`TestResolutionHint` 三個斷言）(FR-28, Signal 7.3)
- [x] AC-4: `tests/test_locale_sweep.py` 以 Python `ast.parse` 提取 user-visible string literals（排除 module / class / function docstring），對 `app/gui/*.py` 執行 `re.compile(r"数据|程序|分辨率").search(...)` 全為 None (FR-29)
- [x] AC-5: 跨 OS 渲染（Windows）按鈕 QSS 採純 Qt widget stylesheet（非 platform-specific pseudo-state），機械斷言等價覆蓋肉眼可辨識性（R10 mitigation）
- [x] AC-6: `tests/test_locale_sweep.py` 新增並全綠（3 tests：sweep + non-empty guard + docstring skip 驗證）(FR-29)
- [x] `uv run pytest tests/test_main_window.py tests/test_locale_sweep.py` 全綠（380 tests pass）
- [x] Pass `/codex-review-fast`（Codex review 兩輪收斂 ✅ Ready）
- [x] Pass `/precommit-fast`（ruff ✅；pytest ✅ 380 passed）

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | tech-spec §3.6.4 / §3.6.5 / §3.6.6 已定案；OQ-5/6/7 預設方案就緒 |
| Development | Done | `main_window.py` 加入 `resolution_hint` QLabel + `btn_check_update` Material Blue QSS（5 態）；無文字 sweep 發現（baseline clean） |
| Testing | Done | `tests/test_main_window.py::TestUpdateButtonStyle`（4 斷言）+ `TestResolutionHint`（3 斷言）；`tests/test_locale_sweep.py` ast-based sweep；380 tests pass |
| Acceptance | Done | `--verify-ac` Explore agent 2026-04-13 驗證：6/6 AC Complete + High confidence（QSS 5 態選擇器、`isFlat()==False`、resolution_hint 1920/1080/gray/12px、ast-based locale sweep 3 tests、無 platform-specific 擴充）；Codex review 兩輪收斂 ✅ Ready；precommit-fast ✅ All Pass |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — §3.6.4 (button QSS), §3.6.5 (hint label), §3.6.6 (sweep)
- Requirements: [1-requirements.md](../1-requirements.md) — FR-27, FR-28, FR-29, Signal 7.2, Signal 7.3
- Open Questions: OQ-5 (button color), OQ-7 (hint position) — 採預設方案，驗收時確認
- Siblings: [R4 — Summary Precision](./2026-04-13-summary-precision-r4.md) | [R5 — GPU Removal](./2026-04-13-gpu-removal-r5.md)
