# Core: Preset Coverage + Absolute Whitelist + Cube Type Cleanup

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-12
> **Status**: Superseded
> **Superseded By**: [condition-rules-v3 R1 — Equipment Consolidation](../../condition-rules-v3/requests/2026-04-12-equipment-consolidation-r1.md)
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Requirements**: [1-requirements.md](../1-requirements.md)

> **Supersede note**: v2 的手套 / 帽子 equipment type 已於 v3 合併為 `是 gear + is_glove`/`is_hat` flag。本 ticket 的 FR-1..5（手套 / 帽子 preset coverage）在 v3 schema 下由 `ConditionChecker._is_glove`/`_is_hat` 配合 FR-3 縱深防禦實現，語意等價。FR-11..14.1（絕對附加白名單）與 FR-19（cube type cleanup）已於 PR #43 落地並持續在 v3 中維持。字面 AC 措辭與現行 schema 不對齊，故標記為 Superseded 而非 Completed。

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

- [x] AC-1: 手套 preset crit×1 / crit×2 / crit×3 + 主屬/全屬 組合皆 pass (FR-2, FR-4)
- [x] AC-2: 帽子 preset cooldown×1 / cooldown×2 / cooldown×3 + 主屬/全屬 組合皆 pass (FR-3, FR-4)
- [x] AC-3: 絕對附加白名單 5 類 × 2 裝備等級 (永恆/一般) 皆 pass (FR-12.1)
- [x] AC-4: 跨類型 (STR+全屬) / 跨屬性 (STR+DEX) / 非對應裝備 (非手套爆擊) 皆 fail (FR-13, FR-14.1)
- [x] AC-5: 爆擊傷害 1%+1% 不因 tolerance 通過 (FR-12.1(e) 不套用 tolerance)
- [x] AC-6: `_TWO_LINE_CUBE_TYPES` 僅含有後綴版本；舊 config `"絕對附加方塊"` 自動遷移為有後綴 (FR-19)
- [x] AC-7: `_classify_line` 抽取後行為等價 — 既有全部 tests 無 regression
- [x] AC-8: 所有屬性 + 絕對附加 同種 pass / 跨類型 fail (dispatch 互動)
- [x] Pass `/codex-review-fast`
- [x] Pass `/precommit-fast`

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | req-analyze + feasibility + tech-spec |
| Development | Done | Merged via PR #43 (commit `0117583`) |
| Testing | Done | Tests still pass in current v3 state (328 passed) |
| Acceptance | Candidate | All AC heuristically checked post-merge; v2 semantics preserved under v3 schema |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — Phase 1, 2, 5
- Sibling: [R2 — UI Mode Merge + Summary](./2026-04-12-ui-mode-merge-summary-r2.md)
