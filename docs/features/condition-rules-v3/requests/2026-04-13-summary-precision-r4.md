# Phase 2 Core: Summary 文案精準化 + UI Label「冷卻帽」

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-13
> **Status**: Completed
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md) — §3.6.1 row catalog + §3.6.2 label rename
> **Requirements**: [1-requirements.md](../1-requirements.md) — FR-7、FR-16..25、Signal 5.x / 6.x / 7.4

## Background

Phase 1（R1/R2/R3）已上線基礎 shorthand summary（99 力 / 77 全 / 12 12 HP / 33 爆 / -1 -1 冷卻），但與 2026-04-13 使用者重新要求的精準文案不一致：預設規則應以「結構性簡述」為主（不列裝備等級數值）、絕對附加應以「僅支援」明示封閉白名單、冷卻帽絕對附加需傳達「77 全 冷卻也接受、洗到主屬會洗掉」語意。同時 UI checkbox label「帽子」需改為「冷卻帽」以明示對應「想洗冷卻屬性的帽子」場景。

## Requirements

- 全面替換 `_PHASE2_PRESET_TEMPLATES` 與 `_generate_*_summary` 內字串，使其與 §3.6.1 row catalog 逐字一致（含全形標點、`77全` 無空格）
- `app/gui/condition_editor.py:111` 的 `QCheckBox("帽子")` 改為 `QCheckBox("冷卻帽")`
- `_CHECKBOX_TOOLTIP`（L34）內所有 user-visible「帽子」字樣改為「冷卻帽」，並新增「三排同屬會洗掉」警示句
- 既有 summary 測試斷言全面更新為 Phase 2 精準字串
- 新增測試覆蓋冷卻帽絕對附加「77 全 冷卻」白名單 summary 字串（注意「全」與「冷卻」之間有空格，與 FR-25 / §3.6.1 row A-HAT 逐字一致）

## Scope

| Scope | Description |
|-------|-------------|
| In | WS5（summary 文案精準化 + UI label rename）+ WS8a（測試斷言更新） |
| Out | GPU 區塊移除（R5）、主視窗 GUI Polish（R6）、底層判定邏輯（不變動） |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/core/condition.py` | Modify | `_generate_*_summary` 系列函式內字串替換為 §3.6.1 row catalog 逐字版本（含 `_PHASE2_PRESET_TEMPLATES` 模板表） |
| `app/gui/condition_editor.py` | Modify | L111 `QCheckBox("帽子")` → `QCheckBox("冷卻帽")`；L34 `_CHECKBOX_TOOLTIP` 內文「帽子」→「冷卻帽」並加「三排同屬會洗掉」字樣 |
| `tests/test_condition.py` | Modify | `TestSummaryShorthand` 全部斷言改為 Phase 2 精準字串；新增冷卻帽絕對附加 `77 全 冷卻` 白名單斷言 |
| `tests/test_condition_editor.py` | Modify | 新增 `assert hat_check.text() == "冷卻帽"` 斷言；tooltip token 斷言（爆擊 / 冷卻 / 三排 或 同屬） |

## Acceptance Criteria

- [x] AC-1: 珍貴方塊 + 永恆/光輝 或 一般裝備 + 目標 = 所有屬性 → `summary_label.text()` 等於 `支援 力 / 敏 / 智 / 幸、全屬、HP，包含 3S、雙 S 及全屬混搭` (FR-16, Signal 5.1)
- [x] AC-2: 珍貴方塊 + 永恆/光輝 + 目標 = 主屬之一 → 等於 `支援 3S、雙 S，包含全屬混搭`；目標 = 全屬性 → 等於 `包含 3S、雙 S 的情況` (FR-17, FR-18, Signal 5.2, 5.3)
- [x] AC-3: 珍貴方塊 + 勾選「手套」→ 等於 `必須符合一排為爆擊傷害 3%，支援雙爆、3S、雙 S`；勾選「冷卻帽」→ 等於 `必須符合一排為技能冷卻時間 -1 秒，支援 -2 冷卻、3S、雙 S` (FR-19, FR-20, Signal 5.4, 5.5)
- [x] AC-4: 珍貴 / 恢復方塊（3-line）+ 主武器/徽章 + 物理攻擊力 → 等於 `三物（支援 3S、雙 S）`；魔法攻擊力 → 等於 `三魔（支援 3S、雙 S）` (FR-21, Signal 5.6)
- [x] AC-5: 絕對附加 + 永恆/光輝 + 目標 = 所有屬性 → 等於 `僅支援 99 四屬、77全、12 12 HP`（注意 `77全` 無空格）；一般裝備對應 `僅支援 88 四屬、66全、11 11 HP` (FR-22, Signal 6.1)
- [x] AC-6: 絕對附加 + 目標 = 主屬 → 等於 `99 力`（無括號、無補充字樣，其他主屬類推）；目標 = HP → 等於 `12 12 HP`（永恆）/ `11 11 HP`（一般） (FR-23, FR-23.1, Signal 6.2, 6.3)
- [x] AC-7: 絕對附加 + 勾選「手套」→ 等於 `僅支援 33 爆`；勾選「冷卻帽」→ 等於 `支援 -1 -1 冷卻，也接受 77 全 冷卻；若洗到主屬會直接洗掉` (FR-24, FR-25, Signal 6.4, 6.5)
- [x] AC-8: `hat_check.text() == "冷卻帽"` 且 `glove_check.text() == "手套"`（widget text 斷言）；`_CHECKBOX_TOOLTIP` 文字含 `爆擊` AND `冷卻` AND (`三排` OR `同屬`) (FR-7, Signal 7.4, Signal 2.1.2)
- [x] `uv run pytest tests/test_condition.py tests/test_condition_editor.py` 全綠（366 tests pass）
- [x] Pass `/codex-review-fast`（heuristic review ✅ Ready；正式 `--verify-ac` 可於需要 Completed 狀態時執行）
- [x] Pass `/precommit-fast`（ruff ✅；pytest ✅ 366 passed）

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | tech-spec §3.6.1 + §3.6.2 已定案 |
| Development | Done | `app/core/condition.py` summary 重寫 + `app/gui/condition_editor.py` label/tooltip rename；移除 dead helper `_fmt_all_stats` / `_generate_gear_summary_3line` / `_generate_all_attrs_summary` / `_collect_gear_shorthand_parts` / `_ABSOLUTE_ALL_STATS_FALLBACK_NOTE` |
| Testing | Done | `tests/test_condition.py` `TestSummaryShorthand` Phase 2 重寫（AC-1..AC-7 逐字 + target=全屬性 edge）；`tests/test_condition_editor.py` 新增 `TestSubtypeCheckboxLabels`（AC-8 Signal 7.4 / 2.1.2）。全專案 366 tests pass |
| Acceptance | Done | `--verify-ac` Explore agent 2026-04-13 驗證：8/8 AC Complete + High confidence（逐字字串比對、檢查點覆蓋度、checkbox precedence dispatch 順序皆確認）；Codex review 兩輪收斂 ✅ Ready；precommit-fast ✅ All Pass |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — §3.6.1 (row catalog), §3.6.2 (label rename)
- Requirements: [1-requirements.md](../1-requirements.md) — FR-7, FR-16..25, Signal 5.1..5.8, Signal 6.1..6.7, Signal 7.4
- Siblings: [R5 — GPU Removal](./2026-04-13-gpu-removal-r5.md) | [R6 — Main Window Polish](./2026-04-13-main-window-polish-r6.md)
- Phase 1 predecessors: [R1](./2026-04-12-equipment-consolidation-r1.md) | [R2](./2026-04-12-subtype-checkbox-ui-r2.md) | [R3](./2026-04-12-summary-shorthand-r3.md)
