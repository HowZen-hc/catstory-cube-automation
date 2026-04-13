# Summary: Community Shorthand Rewrite + Absolute Tightening

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-12
> **Status**: Candidate Complete
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Requirements**: [1-requirements.md](../1-requirements.md)
> **Depends On**: [R1 — Equipment Consolidation](./2026-04-12-equipment-consolidation-r1.md)
>
> **Recommended order**: 實作順序建議最後（R1 → R2 → R3），避免 summary 改寫期間與 UI 狀態呈現不一致（見 tech-spec §5 建議 commit order）

## Background

`summary_label` 全面改寫為社群慣用超短標記法（`99 力`、`77 全`、`12 12 HP`、`33 爆`、`-1 -1 冷卻`、`三物 / 魔`）。絕對附加 summary 緊縮為白名單對應條目，主屬 / HP 路徑加註「7 7 全屬也接受」。

## Requirements

- 新 helper：`_STAT_TO_ZH` 對照表、`_fmt_stat_shorthand` / `_fmt_all_stats` / `_fmt_hp`
- `generate_condition_summary` + 四個 `_generate_*_summary` 依 tech-spec §3.4.2 row catalog 改寫
- 主武器 / 徽章 → `三物 / 魔（3S、雙 S）`
- 副手 3-line → `三物 / 三魔（副手可於遊戲內進行物魔日冕）`；副手 2-line → 保留 v2 `(副手可於遊戲內進行物魔日冕)` 結尾
- 絕對附加 + 主屬 / HP 目標 → 加註「7 7 全屬（也接受，非全屬職業可於遊戲內轉換裝備職業）」
- 絕對附加 + `is_glove=True` → 含 `33 爆`；+ `is_hat=True` → 含 `-1 -1 冷卻`
- 絕對附加 summary 不含 `9 7 雙 S 混搭` 或類似跨類型描述

## Scope

| Scope | Description |
|-------|-------------|
| In | WS3（Summary 全面改寫）+ WS4c（summary 字串斷言測試） |
| Out | Core schema（R1）、UI checkbox（R2） |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/core/condition.py` | Modify | 新增 `_STAT_TO_ZH` + 格式化 helpers；重寫 `generate_condition_summary` / `_generate_absolute_summary` / `_generate_absolute_all_attrs_summary` / `_generate_all_attrs_summary`；新增 `_generate_weapon_summary` / `_generate_gear_summary`（依 §3.4.2 decision tree） |
| `tests/test_condition.py` | Modify | 新增 `TestSummaryShorthand` — 18 row catalog 的字串斷言（每 row 1 case） |

## Acceptance Criteria

- [x] AC-1: 珍貴 + 永恆 + 所有屬性 summary 含 `99 力`、`99 敏`、`99 智`、`99 幸`、`77 全`、`12 12 HP`（FR-16, FR-17, FR-18, Signal 5.1, Row 3-ET-AS）
- [x] AC-2: 珍貴 + 一般 + STR summary 含 `88 力`、`66 全`，不含 `99` / `77`（FR-16, FR-17, Signal 5.2, Row 3-NM-S）
- [x] AC-3: 絕對附加 + 永恆 + 主屬 / HP 目標 summary 含對應 shorthand（`99 力` / `12 12 HP`）+ 加註 `7 7 全屬（也接受，非全屬職業可於遊戲內轉換裝備職業）`（FR-22, FR-23, FR-24, Signal 5.3, Row A-ET-S / A-ET-HP）
- [x] AC-4: 絕對附加 + 一般 + `is_glove=True` summary 含 `33 爆`；+ `is_hat=True` summary 含 `-1 -1 冷卻`（FR-24, Signal 5.4, Signal 5.5, Row A-NM-*-G / A-*-H）
- [x] AC-5: 珍貴 + 永恆 + `is_hat=True` summary 含「-2 冷卻」字樣；珍貴 + 永恆 + `is_glove=True` summary 含「雙爆」但**不含具體 3% 數字**（FR-19, Row 3-ET-S-G / 3-ET-S-H）
- [x] AC-6: 珍貴 + 主武器 summary 不論選物攻或魔攻皆含 `三物 / 魔`（FR-20, Signal 5.6, Row 3-W）
- [x] AC-7: 絕對附加 summary 不含 `9 7 雙 S 混搭` 或跨類型組合字樣（FR-22, Signal 5.7）
- [x] AC-8: 副手 3-line summary 含 `三物 / 三魔` + 「日冕」；2-line summary 保留 v2 結尾 `(副手可於遊戲內進行物魔日冕)`（FR-21, Signal 5.8, Row 3-SW / A-SW）
- [x] Pass `/codex-review-fast`
- [x] Pass `/precommit-fast`

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | tech-spec §3.4.2 row catalog 共 18 rows |
| Development | Done | Commit `1554ddc` — shorthand helpers + rewrite |
| Testing | Done | 328 tests pass (new `TestSummaryShorthand` — 16 cases + 6 updated summary tests) |
| Acceptance | Candidate | All AC heuristically checked; awaiting `--verify-ac` for closure-grade |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — §3.4.2 row catalog + decision tree
- Requirements: [1-requirements.md](../1-requirements.md) — FR-16..24
- Siblings: [R1 — Core](./2026-04-12-equipment-consolidation-r1.md) | [R2 — Checkbox UI](./2026-04-12-subtype-checkbox-ui-r2.md)
