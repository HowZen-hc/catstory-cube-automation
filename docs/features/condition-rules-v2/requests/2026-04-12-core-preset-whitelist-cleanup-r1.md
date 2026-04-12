# Core: Preset Coverage + Absolute Whitelist + Cube Type Cleanup

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-12
> **Status**: In Progress
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Requirements**: [1-requirements.md](../1-requirements.md)

## Background

條件規則系統 v2 的核心邏輯層改動：預設規則需覆蓋手套/帽子所有合法結果（FR-1..5）、絕對附加白名單限縮為同種×2 五類組合（FR-11..14.1）、清理無後綴 cube type 字串（FR-19）。

## Requirements

- 預設規則以「目標屬性達成」為核心，手套 crit×N / 帽子 cooldown×N 全組合 pass
- 絕對附加方塊白名單：同種主屬×2、全屬×2、MaxHP×2、冷卻×2（帽子）、爆擊×2（手套），依裝備等級差異化
- 白名單 (d)(e) 不套用 `_OCR_TOLERANCE`
- 移除 `_TWO_LINE_CUBE_TYPES` 無後綴字串 + config migration

## Scope

| Scope | Description |
|-------|-------------|
| In | Area 1 (preset test lockdown) + Area 3 (classifier + whitelist) + Area 5 (cube type cleanup + migration) |
| Out | Area 2 (UI mode merge) — see R2; Area 4 (summary text) — see R2 |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/core/condition.py` | Modify | `_classify_line` extraction, `_WhitelistCombo`, `_build_whitelist`, `_check_absolute_append`, dispatch reorder, `_TWO_LINE_CUBE_TYPES` cleanup |
| `app/models/config.py` | Modify | Cube type migration (unsuffixed → suffixed) |
| `tests/test_condition.py` | Modify | +6 lockdown tests, +18 whitelist tests, test fixture updates |
| `tests/test_config.py` | Modify | Migration assertion updates |

## Acceptance Criteria

- [ ] AC-1: 手套 preset crit×1 / crit×2 / crit×3 + 主屬/全屬 組合皆 pass (FR-2, FR-4)
- [ ] AC-2: 帽子 preset cooldown×1 / cooldown×2 / cooldown×3 + 主屬/全屬 組合皆 pass (FR-3, FR-4)
- [ ] AC-3: 絕對附加白名單 5 類 × 2 裝備等級 (永恆/一般) 皆 pass (FR-12.1)
- [ ] AC-4: 跨類型 (STR+全屬) / 跨屬性 (STR+DEX) / 非對應裝備 (非手套爆擊) 皆 fail (FR-13, FR-14.1)
- [ ] AC-5: 爆擊傷害 1%+1% 不因 tolerance 通過 (FR-12.1(e) 不套用 tolerance)
- [ ] AC-6: `_TWO_LINE_CUBE_TYPES` 僅含有後綴版本；舊 config `"絕對附加方塊"` 自動遷移為有後綴 (FR-19)
- [ ] AC-7: `_classify_line` 抽取後行為等價 — 既有全部 tests 無 regression
- [ ] AC-8: 所有屬性 + 絕對附加 同種 pass / 跨類型 fail (dispatch 互動)
- [ ] Pass `/codex-review-fast`
- [ ] Pass `/precommit-fast`

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | req-analyze + feasibility + tech-spec |
| Development | Done | Phase 1 (lockdown) + Phase 2 (whitelist) + Phase 5 (cleanup) implemented |
| Testing | In Progress | 287 condition + 9 config tests passing; review gate pending |
| Acceptance | Pending | AC verification pending |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — Phase 1, 2, 5
- Sibling: [R2 — UI Mode Merge + Summary](./2026-04-12-ui-mode-merge-summary-r2.md)
