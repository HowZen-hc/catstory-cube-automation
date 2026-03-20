# 架構設計

## 模組總覽

```
app/
├── core/          # 底層工具：截圖、OCR、滑鼠、模板匹配
├── cube/          # 方塊策略：不同方塊的洗潛能流程
├── gui/           # PyQt6 介面
├── models/        # 資料模型與設定
└── assets/        # 模板圖片等靜態資源
```

## 核心模組（core/）

| 模組 | 類別 | 職責 |
|------|------|------|
| screen.py | ScreenCapture | mss 螢幕擷取，回傳 numpy array |
| ocr.py | OCREngine | PaddleOCR 封裝，繁體中文辨識 |
| mouse.py | MouseController | pyautogui 滑鼠移動與點擊 |
| matcher.py | TemplateMatcher | OpenCV 模板匹配，定位按鈕位置 |
| condition.py | ConditionChecker | 判斷 OCR 結果是否符合目標條件 |
| automation.py | AutomationWorker | QThread 主迴圈，協調所有模組 |

## 方塊策略（cube/）

| 模組 | 類別 | 說明 |
|------|------|------|
| base.py | CubeStrategy (ABC) | 抽象基類，定義 `execute_roll()` 介面 |
| simple_flow.py | SimpleFlowStrategy | Flow A：珍貴/絕對/萌獸方塊，直接洗 |
| compare_flow.py | CompareFlowStrategy | Flow B：恢復方塊，需前後比較決定保留 |

### Flow A — 簡單流程（珍貴/絕對/萌獸方塊）

```
使用方塊 → 等待結果 → OCR 讀取潛能 → 判斷條件
  → 符合：停止
  → 不符合：繼續洗
```

### Flow B — 恢復方塊流程

```
OCR 讀取當前潛能 → 使用方塊 → 等待結果 → OCR 讀取新潛能
  → 新潛能較好：點「使用」
  → 新潛能較差：點「取消」（恢復原潛能）
  → 達成目標：停止
```

## GUI 模組（gui/）

| 模組 | 類別 | 說明 |
|------|------|------|
| main_window.py | MainWindow | 主視窗，整合所有面板 |
| region_selector.py | RegionSelector | 透明覆蓋層，讓使用者框選螢幕區域 |
| condition_editor.py | ConditionEditor | 目標潛能條件編輯器 |
| roll_log.py | RollLog | 洗方塊歷史紀錄顯示 |
| settings_panel.py | SettingsPanel | 延遲、方塊類型、快捷鍵設定 |

## 資料模型（models/）

| 模組 | 類別 | 說明 |
|------|------|------|
| potential.py | PotentialLine | 單行潛能資料（等級、屬性、數值） |
| potential.py | RollResult | 一次洗方塊的完整結果 |
| config.py | AppConfig | 應用程式設定 dataclass |

## 資料流

```
[螢幕] → ScreenCapture → numpy array
       → TemplateMatcher → 按鈕座標
       → OCREngine → 文字結果
       → ConditionChecker → 是否達標
       → CubeStrategy → 決定下一步
       → MouseController → 執行操作
```

## 執行緒模型

- **主執行緒**：PyQt6 GUI 事件迴圈
- **工作執行緒**：AutomationWorker（QThread），執行自動化迴圈
- **通訊方式**：Qt Signal/Slot，工作緒透過 signal 更新 GUI
