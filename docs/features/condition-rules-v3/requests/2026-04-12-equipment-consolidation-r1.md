# Core: Equipment Consolidation + `is_glove`/`is_hat` Flag Rewiring

> **Doc class**: Request ticket (date-prefixed non-lifecycle — per `@rules/docs-numbering.md`). Per-task work breakdown unit for progress tracking. **Not** a feature-level requirements doc — for that see `../1-requirements.md` (created via `/req-analyze`).
> **Created**: 2026-04-12
> **Status**: Candidate Complete
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Requirements**: [1-requirements.md](../1-requirements.md)

## Background

`EQUIPMENT_TYPES` 收斂：移除獨立「手套 / 帽子」，合併到「永恆 / 光輝」與「一般裝備」。`is_eternal` 欄位由 `is_glove` / `is_hat` 兩個 mutually-exclusive bool 取代。ConditionChecker 的 crit / cooldown 判定改由 config flag 驅動（附 FR-3 非 gear 防禦）。

## Requirements

- `EQUIPMENT_TYPES` 從 6→4 項（移除「手套」「帽子」）
- `GLOVE_TYPES` / `HAT_TYPES` / `ETERNAL_EQUIP_TYPES` / `_resolve_equip_type` 刪除
- `AppConfig` 移除 `is_eternal`，新增 `is_glove` + `is_hat`（`__post_init__` 互斥驗證）
- `ConditionChecker` 的 `_is_glove` / `_is_hat` 改由 `config.is_glove and is_gear` / `config.is_hat and is_gear` 驅動（FR-3 縱深防禦）
- `CUSTOM_SELECTABLE_ATTRIBUTES` keys 中文→英文（`gear` / `gear_glove` / `gear_hat` / `weapon` / `beast`）
- `AppConfig.load()` 對舊 `equipment_type == "手套" / "帽子"` 防呆 fallback + log
- `_OLD_EQUIP_MIGRATION` 表中「手套 (永恆)」「手套 (非永恆)」「帽子 (永恆)」「帽子 (非永恆)」四行移除

## Scope

| Scope | Description |
|-------|-------------|
| In | WS1（裝備類型收斂 + ConditionChecker 改線）+ WS4a（core 測試改 schema 回綠） |
| Out | UI checkbox / 副手寬度（R2）、summary 改寫（R3） |

## Related Files

| File | Action | Description |
|------|--------|-------------|
| `app/core/condition.py` | Modify | 刪 `GLOVE_TYPES`/`HAT_TYPES`/`ETERNAL_EQUIP_TYPES`/`_resolve_equip_type`；縮減 `EQUIPMENT_ATTRIBUTES`；rename `CUSTOM_SELECTABLE_ATTRIBUTES` keys；`get_custom_attributes` 新簽章；`ConditionChecker.__init__` FR-3 gated flag |
| `app/models/config.py` | Modify | 刪 `is_eternal`；加 `is_glove` + `is_hat` + `__post_init__`；`load()` legacy fallback；清理 `_OLD_EQUIP_MIGRATION` |
| `tests/test_condition.py` | Modify | 所有 `AppConfig(is_eternal=...)` 改為 `is_glove=` / `is_hat=`；既有行為斷言保留 |
| `tests/test_config.py`（if exists） | Modify | 新增 `__post_init__` 互斥驗證 + legacy fallback 測試 |

## Acceptance Criteria

- [x] AC-1: `EQUIPMENT_TYPES` 長度為 4（不含動態注入的「萌獸」）(FR-1, Signal 1.1)
- [x] AC-2: `grep -n "GLOVE_TYPES\|HAT_TYPES\|ETERNAL_EQUIP_TYPES\|_resolve_equip_type\|is_eternal" app/core/condition.py app/models/config.py` 結果為 0 (FR-5, FR-6, NFR-2)
- [x] AC-3: `grep -n '"手套"\|"帽子"' app/core/condition.py` 結果為 0 (NFR-2)
- [x] AC-4: `AppConfig.__post_init__` 對 `is_glove=True` 且 `is_hat=True` 自動歸零並記 warning (Signal 3.4)
- [x] AC-5: ~~`AppConfig.load()` 讀到 legacy equipment_type 時 fallback~~ — **已撤銷**：每次安裝皆整包重新下載（A3 決策），不支援舊 config 遷移，fallback 程式碼已移除
- [x] AC-6: `ConditionChecker` 在 `equipment_type ∈ {"主武器 / 徽章", "輔助武器"}` + `is_glove=True` 時，`self._is_glove` 必為 False（FR-3 縱深防禦測試）
- [x] AC-7: 行為等價 + 正反案例：
  - 正案例（Signal 2.2）：`equipment_type="永恆 / 光輝"` + `is_glove=True` + 目標 STR → 三組 `[爆擊 3%, STR 9%, STR 9%]` / `[爆擊 3%, 爆擊 3%, STR 9%]` / `[爆擊 3%, 爆擊 3%, 爆擊 3%]` 皆 pass
  - 反案例（Signal 2.3）：同 equipment + `is_glove=False` + `is_hat=False` → 以上第一組若第 1 排非目標屬性則 fail（無 crit 預檢）
  - 一般等級（Signal 2.4）：`equipment_type="一般裝備 (神秘、漆黑、頂培)"` + `is_hat=True` + 目標 STR + `[冷卻 -1, STR 8%, 全屬 6%]` → pass
- [x] AC-8: `_OLD_EQUIP_MIGRATION` 整個移除 + `grep '手套\|帽子' app/models/config.py` = 0（FR-12, Signal 3.2）— 配合 A3 決策（整包重新下載）所有 legacy migration 程式碼已刪除
- [x] AC-9: `uv run pytest tests/test_condition.py tests/test_config.py` 全綠
- [x] Pass `/codex-review-fast`
- [x] Pass `/precommit-fast`

## Progress

| Phase | Status | Note |
|-------|--------|------|
| Analysis | Done | req-analyze + tech-spec |
| Development | Done | Commit `4f9e62e` — schema + FR-3 defense |
| Testing | Done | 305 tests pass (tests/test_condition.py + tests/test_config.py) |
| Acceptance | Candidate | All AC heuristically checked; awaiting `--verify-ac` for closure-grade |

## References

- Tech Spec: [2-tech-spec.md](../2-tech-spec.md) — §3.2, §3.4.1, §3.4.5
- Requirements: [1-requirements.md](../1-requirements.md) — FR-1..6, FR-11, FR-12
- Siblings: [R2 — Checkbox UI](./2026-04-12-subtype-checkbox-ui-r2.md) | [R3 — Summary Shorthand](./2026-04-12-summary-shorthand-r3.md)
