# Requirements: Recovery Cube Auto-Commit on Match

> **Doc class**: Lifecycle — Phase 1 requirements (per `@rules/docs-numbering.md`). Feature-level problem-space analysis. **Not** a task tracking ticket; for per-task progress tracking see `requests/*.md` (created via `/create-request`).
> **Created**: 2026-04-14
> **Updated**: 2026-04-14
> **Tier**: quick
> **Tech Spec**: [2-tech-spec.md](./2-tech-spec.md)

## 1. Problem Statement

目前恢復附加方塊命中目標後，腳本會直接跳出「完成」GUI 彈窗，等使用者回到電腦再手動進入遊戲點「使用」並確認。這段等待期間內若發生遊戲斷線，遊戲會預設還原為 before，AFK 的使用者回來時才發現命中的潛能沒留下。

解法很單純：使用者已經在設定裡框選好潛能欄位區域，命中當下腳本——

1. 在潛能區域執行滑鼠點擊
2. 立刻跳出腳本側「完成」GUI 彈窗，結束自動化

腳本的職責止於送出點擊；遊戲端後續的確認流程由遊戲自行處理，不再等待、不按空白，也不偵測遊戲彈窗。只要點擊在命中當下送出去，就達成目的。

### 5-Why Trace

1. Surface：命中後希望腳本自動把潛能「落袋」，不要讓使用者手動操作。
2. Why：現在命中後是停下等使用者操作，這段空窗期遊戲斷線就會還原 before。
3. Root：只要命中當下立刻送出「選擇該側潛能」的點擊，AFK 空窗就消失，斷線問題也一併解決。

## 2. Goals / Non-Goals

| Goals | Non-Goals |
|-------|-----------|
| 命中當下由腳本在潛能區域執行一次滑鼠點擊後即結束自動化 | 不等待、不送出空白鍵，不偵測遊戲後續彈窗 |
| 讓 AFK 使用者回來時，裝備已確實留下命中的潛能 | 不做斷線偵測、重連、畫面狀態判定等守護機制 |
| 限定恢復附加方塊（CompareFlow）| 其他方塊類型不在此次範圍；不調整既有 OCR / 比較 / 快取邏輯 |

## 3. Stakeholders

| Stakeholder | Role | Key Concern |
|-------------|------|-------------|
| 掛機洗裝使用者 | User | 命中就是命中，不必再擔心 AFK 期間被還原 |
| 現場使用者 | User | 自動化動作不要造成額外誤點或干擾 |
| 腳本維護者 | Developer | 新增的點擊動作整潔加入 CompareFlow 命中分支，不影響未命中路徑 |

## 4. Use Cases

| # | Actor | Action | Expected Outcome |
|---|-------|--------|-----------------|
| UC-1 | 使用者 | 開啟自動洗方塊後離開電腦 | 命中時腳本自行完成落袋，使用者回來看到的就是 after 潛能 |
| UC-2 | 使用者 | 命中當下本人在電腦前 | 點擊自動完成，腳本立即跳出完成彈窗；遊戲端後續的確認流程仍可由使用者即時接手（或由遊戲自行完成）|

## 5. Functional Requirements

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-1 | CompareFlow 判定命中後，腳本須在使用者已框選的潛能區域內執行一次滑鼠點擊；區域內任一點即可（區域本身比實際可點擊範圍小，座標策略無額外要求）| Must | 這是命中當下送出「使用」動作、避免 AFK 被還原的核心操作 |
| FR-2 | 點擊完成後，腳本立即觸發「完成」GUI 彈窗並結束自動化；不等待、不送出額外按鍵、不輪詢遊戲後續彈窗 | Must | 遊戲端點擊已把「使用」送出，後續是遊戲流程；腳本不需耦合到遊戲彈窗 |
| FR-3 | 上述動作只在命中（`result.matched=True`）時觸發；未命中輪次維持既有流程 | Must | 未命中不能誤按「使用」，否則會把差的結果變成成品 |
| FR-4 | 命中與點擊動作須寫入 log，至少包含 roll_number、點擊座標來源（region 名稱）、時間 | Should | 方便事後追溯，對齊既有 `logger.info("#%05d ...")` 風格 |

## 6. Non-Functional Requirements

| ID | Category | Requirement | Metric |
|----|----------|-------------|--------|
| NFR-1 | Reliability | 命中後點擊不得漏做或在錯誤時機觸發 | UC-1 / UC-2 情境下，命中 10 次，10 次皆有對應點擊；未命中 0 次誤觸發 |
| NFR-2 | Usability | 使用者不需為此功能新增額外設定（沿用既有潛能區域）| 預設啟用，無新設定欄位 |
| NFR-3 | Performance | 命中到點擊送出與完成彈窗觸發的腳本端耗時 | p95 < 500 ms（不含遊戲端後續動畫/彈窗）|

## 7. Constraints & Assumptions

| Type | Description | Source |
|------|-------------|--------|
| Constraint | 範圍限定恢復附加方塊（Flow B / CompareFlow）| 使用者對話 |
| Constraint | 以「點擊使用者已框選的潛能區域」作為觸發動作；不引入新的區域設定 | 使用者對話 |
| Fact | 遊戲中實際可選取的潛能介面比使用者框選的區域大，故框選區域內任一座標都能觸發「選擇該側潛能」；無需中心點 / 隨機化等特殊策略 | 使用者已於實機實測確認 |
| Fact | 在遊戲畫面仍停留於比較 UI 時，於潛能區域內執行一次滑鼠點擊，遊戲端會視為「選擇該側潛能（使用）」；腳本不需額外送空白或等待後續彈窗 | 使用者已於實機實測確認 |
| Fact | 若使用者未框選 `potential_region`，既有流程的 OCR 會直接回空、`checker.check([])` 不會命中，因此本需求的點擊分支自然不會觸發 | `app/cube/compare_flow.py:66-67` 現況 |
| Assumption | 命中當下遊戲畫面仍停留在比較 UI；既有流程在 after OCR 後尚未切換畫面 | `app/cube/compare_flow.py:42-57` 現況 |
| Assumption | 點擊動作仍須先確保遊戲視窗為前景（沿用既有前景檢查機制，具體重用方式歸 `/tech-spec` 決定）| 現況鍵盤路徑即有此保護 |

## 8. Acceptance Signals

- Signal 1（FR-1 / FR-2 / NFR-1）：UC-1 實測 — AFK 跑到命中後回來，裝備已是 after 潛能，log 可看到點擊事件並立即接著完成彈窗觸發。
- Signal 2（FR-3）：單一連續執行中，未命中輪次的 log 不得出現命中路徑的點擊動作。
- Signal 3（NFR-3）：命中當下到腳本完成彈窗觸發之間的耗時 p95 < 500 ms。
- Signal 4（FR-4）：命中事件的 log 包含 `roll_number`、點擊座標來源（region 名稱）、時間戳，可逐筆檢閱。

## 9. Open Questions

（無；Phase 1 所有開放問題已由使用者回覆或實測釐清，詳見 §7 Facts。）

## 10. References

- 程式現況：
  - `app/cube/compare_flow.py:12-97` — CompareFlow 流程、命中判定、`_last_lines` 快取規則與「使用 / 取消」TODO
  - `app/core/automation.py:20-124` — `AutomationWorker` 主迴圈、`target_reached` 訊號
  - `app/core/mouse.py:116-192` — `press_confirm`、`_ensure_game_foreground`、`bind_stop_flag`
- 相關規則：`@.claude/rules/docs-writing.md`、`@.claude/rules/docs-numbering.md`
