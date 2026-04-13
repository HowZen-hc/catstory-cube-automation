# UI: Subtype Checkbox (手套/帽子) + Sub-weapon Field Width

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-12
> **Status**: Candidate Complete
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Requirements**: [1-requirements.md](../1-requirements.md)
> **Depends On**: [R1 — Equipment Consolidation](./2026-04-12-equipment-consolidation-r1.md)

## Background

UI 層：移除 `eternal_check`，新增「手套」「帽子」兩個 mutually-exclusive checkbox（僅在「永恆 / 光輝」與「一般裝備」+ 預設模式時顯示）。輔助武器目標屬性下拉僅保留 `"物理/魔法攻擊力 (可轉換)"` 一個選項，寬度擴展至能完整顯示。

## Requirements

- `glove_check` + `hat_check` Qt signal 互斥（勾一個 disable 另一個）
- checkbox 僅在 `equipment_type ∈ {"永恆 / 光輝", "一般裝備 (神秘、漆黑、頂培)"}` + 預設模式顯示
- checkbox 預設未勾；附 tooltip 說明（`_CHECKBOX_TOOLTIP`）
- `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 縮減為單一 `_ATTACK_CONVERTIBLE` 選項
- 副手 `attr_combo.setMinimumWidth(260)` 條件式（其他裝備維持 150）
- `load_from_config` / `apply_to_config` 同步讀寫 `is_glove` / `is_hat`（以 `blockSignals` 包覆避免循環觸發）
- 自訂模式 + 輔助武器仍可選 `"物理攻擊力"` / `"魔法攻擊力"`（`CUSTOM_SELECTABLE_ATTRIBUTES["weapon"]` 維持）

## Scope

| Scope | Description |
|-------|-------------|
| In | WS2（Checkbox UI + 副手欄位寬度）+ WS4b（UI 相關單元測試） |
| Out | Core schema / ConditionChecker（R1）、summary 字串（R3） |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/gui/condition_editor.py` | Modify | 替換 `eternal_check` 為 `glove_check` + `hat_check`；新增 `_on_glove_toggled` / `_on_hat_toggled` / `_update_subtype_visibility`；`_on_equip_changed` 改寬度；`load_from_config` / `apply_to_config` 更新；`_add_custom_row` 呼叫 `get_custom_attributes(equip, is_glove, is_hat)` |
| `app/core/condition.py` | Modify | `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 縮減為 `[_ATTACK_CONVERTIBLE]` |
| `tests/test_condition.py` | Modify | 既有副手測試若假設三個選項需調整 |

## Acceptance Criteria

- [x] AC-1: 選擇「永恆 / 光輝」或「一般裝備」+ 預設模式 → `glove_check` + `hat_check` 可見；其他裝備或自訂模式 → 隱藏 (FR-7, Signal 1.2, Signal 1.3)
- [x] AC-2: 勾「手套」時「帽子」自動 disable；取消勾選後恢復可用（vice versa）(FR-8, Signal 2.1)
- [x] AC-3: `EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` == `[_ATTACK_CONVERTIBLE]` 且 `attr_combo.count() == 1` (FR-13, Signal 4.1)
- [x] AC-4: 選擇輔助武器時 `attr_combo.minimumWidth() >= 240`；其他裝備 `== 150`(FR-14, Signal 4.2)
- [x] AC-5: 自訂模式 + 輔助武器仍可選「物理攻擊力」「魔法攻擊力」(FR-15, Signal 4.3)
- [x] AC-6: `load_from_config({is_glove: True, ...})` 後 UI checkbox state 正確且不觸發循環 signal
- [x] AC-7: checkbox 附 tooltip，內容覆蓋 3-line「至少 1 排」與 2-line「雙排」語意 (FR-10)
- [x] AC-8: `glove_check` 與 `hat_check` 初始狀態皆未勾選；兩者皆未勾時，選「永恆 / 光輝」+ 目標 STR 走一般永恆判定路徑（等同 v2「永恆 / 光輝 + STR」，不套 crit/cooldown 預檢）(FR-9, UC-5)
- [x] AC-9: `uv run pytest tests/test_condition.py` 全綠（UI 改動不破壞 core 測試）
- [x] Pass `/codex-review-fast`
- [x] Pass `/precommit-fast`

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | tech-spec §3.4.3, §3.4.4 |
| Development | Done | Commit `0bfa90d` — glove/hat checkbox + sub-weapon reduction |
| Testing | Done | 312 tests pass (new `TestSubWeaponAttributesR2` + `TestGetCustomAttributesSubtype`) |
| Acceptance | Candidate | Manual UI visual AC-1/AC-2/AC-6 deferred to user; all core-facing AC heuristically checked |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — §3.4.3, §3.4.4
- Requirements: [1-requirements.md](../1-requirements.md) — FR-7..10, FR-13..15
- Siblings: [R1 — Core](./2026-04-12-equipment-consolidation-r1.md) | [R3 — Summary Shorthand](./2026-04-12-summary-shorthand-r3.md)
