# UI: Custom Mode Merge + Summary Text

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-12
> **Status**: Candidate Complete
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Requirements**: [1-requirements.md](../1-requirements.md)
> **Depends On**: [R1 — Core Preset + Whitelist + Cleanup](./2026-04-12-core-preset-whitelist-cleanup-r1.md)

## Background

條件規則系統 v2 的 UI 層改動：合併 `_MODE_AND` + `_MODE_OR` 為單一 `_MODE_CUSTOM`、position combo 加入「任一排」選項、summary 文字依 cube_type + equip_type 差異化。

## Requirements

- Mode 下拉僅保留「預設規則 / 自訂條件」兩個選項
- per-row position combo 含「任一排」(position=0) + 指定排 (1/2/3)
- `apply_to_config` / `load_from_config` 簡化（不再推導 AND/OR mode）
- 絕對附加 summary 顯示白名單 5 類具體數值
- 一般方塊 summary 補充 3S/雙 S、帽子 -2 冷卻、手套雙爆（不含 %）

## Scope

| Scope | Description |
|-------|-------------|
| In | Area 2 (custom mode merge) + Area 4 (summary text differentiation) |
| Out | Area 1/3/5 (core logic) — see R1 |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/gui/condition_editor.py` | Modify | `_MODE_CUSTOM` rename, position combo with "任一排", `apply_to_config`/`load_from_config` simplified, `_on_position_changed` excludes position=0 swap |
| `app/core/condition.py` | Modify | `_generate_absolute_summary` new function, 3-line summary supplements (雙爆/-2 冷卻/3S 雙 S) |
| `tests/test_condition.py` | Modify | Summary snapshot tests updated |

## Acceptance Criteria

- [x] AC-1: UI mode 下拉僅有「預設規則 / 自訂條件」兩個選項 (FR-6, NFR-2)
- [x] AC-2: Custom mode position combo 含「任一排 / 第 1 排 / 第 2 排 / 第 3 排」(FR-7)
- [x] AC-3: 舊 config (AND mode / OR mode 存檔) 載入後行為等價 (FR-10, NFR-3)
- [x] AC-4: 絕對附加 summary 依裝備等級顯示白名單數值 (FR-15, FR-16)
- [x] AC-5: 一般方塊 summary 含「3S、雙 S」、帽子含「-2 冷卻」、手套含「雙爆」不含 % (FR-17, FR-18)
- [x] AC-6: `grep -r "_MODE_OR\|_MODE_AND" app/gui/` 結果為 0 (NFR-2)
- [x] AC-7: position swap 邏輯排除「任一排」互換 (Q11 from tech-spec)
- [x] Pass `/codex-review-fast`
- [x] Pass `/precommit-fast`

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | req-analyze + feasibility + tech-spec |
| Development | Done | Phase 3 (mode merge) + Phase 4 (summary) implemented |
| Testing | Done | Tests still pass in current v3 state (328 passed) |
| Acceptance | Candidate | All AC heuristically checked post-merge (PR #43); v3 summary-shorthand superseded v2 text (AC-5 "雙爆"/"-2 冷卻" now emitted by R3 helpers) |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — Phase 3, 4
- Sibling: [R1 — Core Preset + Whitelist + Cleanup](./2026-04-12-core-preset-whitelist-cleanup-r1.md)
