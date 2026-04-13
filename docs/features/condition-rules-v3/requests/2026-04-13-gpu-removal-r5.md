# Phase 2 GUI: 移除 GPU 加速區塊

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-13
> **Status**: Pending
> **Priority**: P2
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md) — §3.6.3
> **Requirements**: [1-requirements.md](../1-requirements.md) — FR-26、Signal 7.1.a / 7.1.b

## Background

設定面板「啟用 GPU 加速」checkbox 目前 disabled 且 tooltip 標示「目前已停用此選項」，短期內不會實作 GPU 加速；保留會誤導使用者，使用者要求直接移除。`AppConfig.use_gpu` dataclass 欄位**保留**（per 1-requirements A7），避免破壞潛在 OCR 引擎引用。

## Requirements

- `app/gui/settings_panel.py:78-85` 的 GPU checkbox 區塊（`row4` 整段）刪除
- `apply_to_config` (L92) 的 `config.use_gpu = self.gpu_checkbox.isChecked()` 刪除
- `load_persistent_from_config` (L100-102) 的 method body 中 `self.gpu_checkbox.setChecked(...)` 刪除；若該 method 整體無其他用途則整 method 刪除（同時 sweep `app/gui/main_window.py` 移除 caller）
- `AppConfig.use_gpu` 欄位**保留**（不變動 `app/models/config.py:48`）
- 新增 GUI 測試驗證 `gpu_checkbox` 屬性已不存在於 `SettingsPanel`

## Scope

| Scope | Description |
|-------|-------------|
| In | WS6（settings_panel.py GPU 移除 + caller sweep）+ WS8b（GUI 測試） |
| Out | `AppConfig.use_gpu` 欄位刪除（保留以避免 OCR 引擎引用點破壞，per A7）；R4 / R6 不在範圍 |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/gui/settings_panel.py` | Modify | 刪除 L78-85（`gpu_checkbox` 區塊與 `row4` layout）；刪除 L92（`apply_to_config` 內 `config.use_gpu` 寫入）；處理 L100-102（`load_persistent_from_config` body 或整 method） |
| `app/gui/main_window.py` | Modify | grep `load_persistent_from_config` caller；若 method 已刪除則同步移除呼叫；若僅修改則保持呼叫不變 |
| `tests/test_main_window.py` | Modify | 新增 `getattr(settings_panel, "gpu_checkbox", None) is None` 斷言；驗證 `apply_to_config` / `load_persistent_from_config`（如保留）不再讀寫 `config.use_gpu` |

## Acceptance Criteria

- [ ] AC-1: `grep -n "gpu_checkbox" app/gui/settings_panel.py` 結果為 0 (FR-26, Signal 7.1.a)
- [ ] AC-2: `grep -n "use_gpu" app/gui/settings_panel.py` 結果為 0 (FR-26, Signal 7.1.b)
- [ ] AC-3: 載入 `SettingsPanel`，`getattr(panel, "gpu_checkbox", None) is None`（GUI 測試）(Signal 7.1.a)
- [ ] AC-4: `app/models/config.py` 仍保留 `use_gpu: bool = False` 欄位（FR-26 boundary，per A7 — 不刪除 dataclass field 以避免破壞潛在 OCR 引擎引用）
- [ ] AC-5: `app/gui/main_window.py` 對 `load_persistent_from_config` 的呼叫（若有）不會 AttributeError（FR-26 caller sweep；R9 mitigation）
- [ ] AC-6: 啟動 GUI 開啟設定面板，視覺上不再出現「啟用 GPU 加速」字樣（FR-26, Signal 7.1.a 手動驗證）
- [ ] `uv run pytest tests/test_main_window.py` 全綠
- [ ] Pass `/codex-review-fast`
- [ ] Pass `/precommit-fast`

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | tech-spec §3.6.3 已定案；R9 風險識別（caller sweep） |
| Development | - | |
| Testing | - | |
| Acceptance | - | |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — §3.6.3, §4.2 R9
- Requirements: [1-requirements.md](../1-requirements.md) — FR-26, A7, Signal 7.1.a, Signal 7.1.b
- Siblings: [R4 — Summary Precision](./2026-04-13-summary-precision-r4.md) | [R6 — Main Window Polish](./2026-04-13-main-window-polish-r6.md)
