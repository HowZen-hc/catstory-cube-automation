# Recovery Cube: Auto-Click on Match

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-14
> **Status**: Candidate Complete
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Requirements**: [1-requirements.md](../1-requirements.md)

## Background

恢復附加方塊命中後 AFK 期間若遊戲斷線會還原 before，目前依賴使用者手動進遊戲點「使用」。本 request 在 `MouseController` 新增 `click()`、於 `CompareFlowStrategy` 命中分支點一下 `potential_region` 中心後回傳 `matched=True`，由 worker 隨後結束自動化；不碰未命中路徑與既有快取。

## Requirements

- `MouseController` 新增 `click(x, y) -> bool`，與既有 `press_confirm` 同風格（前景檢查 + stop_flag 響應）
- 模組級 `_send_click()` 透過 `SendInput` 送出 `MOUSEEVENTF_LEFTDOWN/LEFTUP`
- `CompareFlowStrategy.execute_roll` 於 `matched=True` 時呼叫 `self.mouse.click(cx, cy)`，座標取 `potential_region` 中心
- 點擊失敗（`SetCursorPos` 回 0 或 `SendInput` < 2）→ `raise RuntimeError`，由 `AutomationWorker` 既有 try/except 轉成 `error_occurred`，**不得誤觸發 `target_reached`**
- 未命中路徑、初始命中分支（`automation.py:93-96`）、`_is_better` / `_last_lines` 皆不改動
- 新增 `tests/test_mouse.py`；擴充 `tests/test_compare_flow.py` 命中/未命中/座標/失敗四項

## Scope

| Scope | Description |
|-------|-------------|
| In | `MouseController.click` + `_send_click`；CompareFlow 命中分支插入 click + log + 失敗 raise；對應 unit tests |
| Out | SimpleFlow；`_is_better` / `_last_lines` 清理（另行 request）；初始潛能已命中路徑；斷線偵測；新 UI 設定 |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/core/mouse.py` | Modify | 新增常數 `_MOUSEEVENTF_LEFTDOWN` / `_MOUSEEVENTF_LEFTUP` / `_INPUT_MOUSE`；新增模組函式 `_send_click`；`MouseController` 新增 `click()` |
| `app/cube/compare_flow.py` | Modify | `execute_roll` 於 `matched=True` 先檢 `region.is_set()`（未設則 raise），再取中心座標 → `logger.info` → `self.mouse.click`，點擊失敗亦 raise `RuntimeError` |
| `tests/test_mouse.py` | New | 7 項：`_send_click` 回值、`click()` 呼叫順序、stop_flag 回 False、stop 路徑 silent（零 warning）、`SetCursorPos` 失敗、`SendInput` 完全失敗、`SendInput` 部分失敗（`side_effect=[1,0]`）；使用 `patch("app.core.mouse.ctypes.windll", fake, create=True)` 跨平台 mock |
| `tests/test_compare_flow.py` | Modify | 新增 5 項：`test_click_on_match`（含精確 log + `matched=True` 斷言）/ `test_no_click_on_miss` / `test_click_uses_region_center`（奇數 41x61 驗 `//2`）/ `test_match_raises_on_click_failure`（驗 `_is_better` short-circuit）/ `test_match_raises_when_region_unset`；既有 7 項測項全綠 |

## Acceptance Criteria

- [x] AC-1: `MouseController.click(x, y)` 存在且簽章為 `(self, x: int, y: int) -> bool`；呼叫時會先 `_ensure_game_foreground()`、再檢 `self.stopped`、再 `SetCursorPos`、再 `_send_click`（`test_mouse.py::test_click_calls_foreground_then_cursor_then_sendinput`）
- [x] AC-2: `click()` 的失敗路徑區分兩類——(a) stop_flag 已 set 時 silent 回 False（無 warning，語義同 `press_confirm`）；(b) `SetCursorPos` 回 0 或 `SendInput` < 2 時回 False 並 `logger.warning`（`test_mouse.py::test_click_respects_stop_flag`、`test_click_stop_flag_is_silent`、`test_click_returns_false_on_setcursorpos_failure`、`test_click_returns_false_on_sendinput_failure`、`test_click_returns_false_on_partial_sendinput`）
- [x] AC-3: `CompareFlowStrategy.execute_roll` 在 `checker.check=True` 時恰好呼叫 `mouse.click` 一次，座標為 `Region(x, y, w, h)` 的中心 `(x + w//2, y + h//2)`，並正常回 `RollResult(matched=True)`（`test_compare_flow.py::test_click_on_match`（含 `result.matched is True` 斷言）+ `test_click_uses_region_center`（奇數 41x61 驗 `//2`））
- [x] AC-4: `checker.check=False` 時 `mouse.click` 完全未被呼叫（`test_compare_flow.py::test_no_click_on_miss`）
- [x] AC-5: `mouse.click` 回 False 時，`execute_roll` 拋 `RuntimeError` 並 short-circuit `_is_better`（`test_compare_flow.py::test_match_raises_on_click_failure`）；新增 `test_match_raises_when_region_unset` 保護 `region.is_set()` 前置檢查
- [x] AC-6: 既有 `test_compare_flow.py` 全部測項繼續 pass（快取、seed、SimpleFlow no-op 等）；`uv run pytest` 全量 407 pass
- [x] AC-7: 命中事件至少產生一筆 log，格式為 `#%05d 命中 → 點擊 potential_region 中心 (%d, %d)`；以 `caplog` 斷言精確訊息存在於 records（`test_compare_flow.py::test_click_on_match`）
- [ ] AC-8: Manual E2E（UC-1）— 實機 AFK 跑到命中後回來，裝備為 after 潛能；`grep "命中 → 點擊" logs/*.log` 至少 1 筆，且後續 GUI 完成彈窗確實出現（以畫面為準）
- [x] AC-9: Pass `/codex-review-fast`（Codex loop ✅ Ready）
- [x] AC-10: Pass `/precommit`（`ruff check` all passed + `uv run pytest` 407 pass）

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | Requirements + Tech Spec 已 Mergeable |
| Development | Done | `MouseController.click` + CompareFlow 命中分支整合 + region.is_set() 防護 |
| Testing | Done | 新增 `test_mouse.py`（7 項）+ 擴充 `test_compare_flow.py`（+6 項）；`uv run pytest` 407 pass；`ruff` pass |
| Acceptance | Pending E2E | 除 AC-8 實機 AFK 驗收外，其餘 AC-1..AC-7、AC-9、AC-10 已以測試 + review 證實 |

**Status**: Pending / In Progress / Candidate Complete / Completed

## Verification Commands

```bash
# 單元測試（新增 + 擴充）
uv run pytest tests/test_mouse.py tests/test_compare_flow.py -v

# 全量回歸
uv run pytest

# 命中 log 檢查（E2E 後）
grep -n "命中 → 點擊" logs/*.log
```

## References

- Requirements: [1-requirements.md](../1-requirements.md)
- Tech Spec: [2-tech-spec.md](../2-tech-spec.md)
- 既有測試模式：`tests/test_compare_flow.py`（`_make_strategy` helper + `strategy` fixture）
- Windows API 參考：`app/core/mouse.py`（`_send_key` 可借鏡）
