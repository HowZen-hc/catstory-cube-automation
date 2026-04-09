# 副手雙攻擊力（可轉換）預設條件選項

> **Created**: 2026-04-10
> **Status**: Completed
> **Priority**: P1
> **Tech Spec**: [2-tech-spec.md](../2-tech-spec.md)
> **Feasibility Study**: [0-feasibility-study.md](../0-feasibility-study.md)

## Background

副手（輔助武器）在遊戲內可透過「防具轉換」把物理攻擊力整件互換為魔法攻擊力（反之亦然）。既有工具在預設模式只能單選物攻或魔攻作為停手目標，導致洗到「可轉換後同樣可用」的好卷會被繼續洗掉，造成 false negative 漏停（成本極高）。

## Requirements

- 副手預設模式新增「物理/魔法攻擊力 (可轉換)」目標屬性，且作為切換到副手時的預設值
- 三排全物攻 **或** 三排全魔攻（含 OCR 容錯 2）達門檻即視為合格停手條件
- 混合洗出（例：2 物 1 魔）必須拒絕 — 對齊「整件轉換」語意（D1）
- 同時支援 3 排方塊與 2 排絕對附加方塊
- D2 強制防線：即便手改 `config.json` 把主武器或防具配上新屬性字串，也必須被 checker + summary 雙重拒絕
- 既有 `config.json`（舊 `target_attribute` 為「物理攻擊力」或「魔法攻擊力」）零遷移即相容

## Scope

| Scope | Description |
| ----- | ----------- |
| In    | `app/core/condition.py` 預設模式判定；`generate_condition_summary` 摘要；18 個新測試 case |
| In    | T2 重構：把 `_check_preset_any_pos` 的核心邏輯抽成 module-level 純函式 `_run_preset_any_pos`（為新路徑避免狀態污染）|
| Out   | 自訂模式（「逐排指定」／「符合任一」）— 由使用者未來的「自訂模式合併」重構處理（D3）|
| Out   | 主武器 / 徽章（米特拉）同步支援 — 遊戲內主武器不可轉換（D2）|
| Out   | UI 層修改 — 透過既有 `EQUIPMENT_ATTRIBUTES` 機制自動生效，`condition_editor.py` 0 行改動 |
| Out   | `AppConfig` schema 變更 — `target_attribute` 是字串，無需 migration |
| Out   | `CHANGELOG.md` 與 release notes 更新 — 留待 PR 階段處理 |

## Related Files

| File | Action | Description |
| ---- | ------ | ----------- |
| `app/core/condition.py` | Modify | `_ATTACK_CONVERTIBLE` 常數、`EQUIPMENT_ATTRIBUTES["輔助武器 (副手)"]` 列首新增、`_run_preset_any_pos` 純函式（T2）、`ConditionChecker.__init__` D2 guard + 防禦性初始化、`check()` 分派、`_check_attack_convertible` 方法、`generate_condition_summary` 新分支含 equip guard |
| `tests/test_condition.py` | Modify | 新增 `TestConditionCheckerSubWeaponConvertible` 類（18 個 test case，含 3 排純物／純魔 pass、混合 reject、容錯邊界對稱測試、OCR 非法屬性防呆、2 排方塊 pass/reject、summary 精確快照、D2 主武器 + 防具負向測試）|

## Acceptance Criteria

- [x] 新選項在副手下拉可見，且為裝備切換時的預設值（D6）
- [x] 3 排純物攻 / 3 排純魔攻且達門檻（含 OCR 容錯 2）可停手
- [x] 3 排混合洗出拒絕；低於門檻拒絕；容錯邊界（真實最小 pass 與 just-below reject）都覆蓋
- [x] 2 排方塊（絕對附加方塊）的純物攻 / 純魔攻 / 混合 / 低於門檻情境皆正確判定
- [x] OCR 誤判出非副手屬性（如 STR%）時 checker 自然拒絕，不 crash
- [x] D2 強制防線：主武器 + 新選項、永恆 / 光輝 + 新選項皆 `_valid = False` 且 summary 回傳錯誤訊息
- [x] 條件預覽摘要對 3 排與 2 排方塊各自顯示正確語意（含「混合洗出不算合格」警告）
- [x] 既有 `config.json`（舊 `target_attribute`）零遷移即載入，行為不變
- [x] Pass `/codex-test-review`
- [x] Pass `/codex-review-fast`
- [x] Pass `/precommit-fast`
- [x] Pass `/codex-review-doc`（feasibility study + tech spec doc sync 皆綠）

## Progress

| Phase | Status | Note |
| ----- | ------ | ---- |
| Feasibility | ✅ Done | `/feasibility-study` — 6 方案比較、Codex 雙輪討論、D1-D6 決定鎖定、Gate ✅ Mergeable |
| Analysis (Tech Spec) | ✅ Done | `/tech-spec` — Option A 完整虛擬碼 + 18 case 測試矩陣；Codex 3 輪審查找到 D2 規避漏洞與 line drift，修補後 Gate ✅ Mergeable |
| Development | ✅ Done | T1-T6 依 tech spec 落地：`app/core/condition.py` +143/-21 行（`git diff --numstat HEAD` 於 working tree 量測，基準 = `96b4acb`）|
| Testing | ✅ Done | T7 新增 18 個測試 case：`tests/test_condition.py` +226/-0 行；`uv run pytest tests/ --ignore=tests/test_main_window.py -q` → **257 passed**（`test_main_window.py` 為既有 WSL2 PyQt 環境崩潰，git stash 驗證為與本次改動無關）|
| Review | ✅ Done | `/codex-test-review` + `/codex-review-fast` 雙審查；第一輪 4 P2 + 2 Nit，P2/Nit 批次修補後第二輪 ✅ Ready（全維度 5⭐）|
| Precommit | ✅ Done | `/precommit-fast`：`ruff check --fix` 無需修改；`pytest` 257 passed |
| Doc Sync | ✅ Done | `/update-docs` 同步 tech spec 行號與虛擬碼；safety valve 驗證 code hash 前後一致 |
| Acceptance | ✅ Done | 所有 AC 已驗證 |

**Status**: Completed

## Deviations from Tech Spec

實作過程中由 Codex 審查推動的偏離，皆已回寫 tech spec（§3.3.3 / §3.3.5 / §6.1 / §5 實際落地）：

| # | 偏離項 | 觸發原因 |
|---|--------|---------|
| 1 | `ConditionChecker.__init__` 新增防禦性預設值 `self._is_attack_convertible = False` | T9 Code Review Nit — 避免未來重構觸發 `AttributeError` |
| 2 | 摘要文案「三排全物攻 或 三排全魔攻」→「全物攻 或 全魔攻」 | T9 Code Review Nit — 避免「兩排／三排」重複 |
| 3 | 新增 C6c / C6d 魔攻對稱容錯邊界測試 | T9 Test Review P2 — 證明容錯對稱套用到魔攻路徑 |
| 4 | 新增 C10b 2 排方塊低於門檻 reject 測試 | T9 Test Review P2 — 2 排方塊邊界覆蓋 |
| 5 | 新增 C13b 防具（永恆 / 光輝）+ 新屬性 D2 負向測試 | T9 Test Review P2 — 防止 guard 被誤寫成僅阻擋武器 |
| 6 | C11 改為精確列表快照（`assert summary == [...]`）| T9 Test Review P2 — 強化回歸偵測 |

原初 tech spec 預估 13 個測試 case → 實際落地 **18 個測試 case**（D1-D6 決策來源為 [feasibility §8.1](../0-feasibility-study.md)，tech spec 前言同步引用）。

## References

- [Feasibility Study](../0-feasibility-study.md) — 決定紀錄 D1-D6 與方案比較
- [Tech Spec](../2-tech-spec.md) — 完整實作路徑、測試矩陣、風險表、D2 雙層 guard 設計
