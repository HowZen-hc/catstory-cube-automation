# 實作順序與驗證方式

## Phase 1：基礎建設

- [x] uv 初始化專案、安裝依賴
- [x] 建立 docs/ 規劃文件
- [x] 建立專案目錄骨架

## Phase 2：核心模組

### 2.1 螢幕擷取（screen.py）

- [x] 使用 mss 擷取指定區域螢幕
- 驗證：擷取螢幕截圖並儲存為 PNG

### 2.2 OCR 引擎（ocr.py）

- [x] 封裝 PaddleOCR，設定繁體中文
- 驗證：對遊戲截圖進行 OCR，確認辨識結果

### 2.3 滑鼠控制（mouse.py）

- [x] 封裝 pyautogui，提供 move、click、delay
- 驗證：自動移動滑鼠到每指定座標並點擊

### 2.4 模板匹配（matcher.py）

- [x] OpenCV matchTemplate 找按鈕位置
- 驗證：對遊戲截圖匹配按鈕模板，回傳座標

### 2.5 條件判斷（condition.py）

- [x] 解析 OCR 文字，提取潛能屬性與數值
- [x] 比對使用者設定的目標條件
- 驗證：單元測試各種潛能文字

## Phase 3：方塊策略

### 3.1 策略基類（base.py）

- [x] 定義抽象介面 `execute_roll()`

### 3.2 簡單流程（simple_flow.py）

- [x] 實作珍貴/絕對/萌獸方塊的洗潛能流程

### 3.3 恢復方塊流程（compare_flow.py）

- [x] 實作前後比較的恢復方塊流程

## Phase 4：GUI

### 4.1 主視窗（main_window.py）

- [x] 基本佈局，整合各面板

### 4.2 區域框選（region_selector.py）

- [x] 透明覆蓋層，框選螢幕區域

### 4.3 條件編輯器（condition_editor.py）

- [x] 動態新增/刪除條件行

### 4.4 洗方塊紀錄（roll_log.py）

- [x] 滾動列表顯示歷史

### 4.5 設定面板（settings_panel.py）

- [x] 方塊類型、延遲、快捷鍵設定

## Phase 5：自動化迴圈

### 5.1 AutomationWorker（automation.py）

- [x] QThread 主迴圈
- [x] 整合所有模組
- [x] Signal 通知 GUI 更新

## Phase 6：整合與測試

- [x] 單元測試（condition parsing、config save/load，共 31 項）
- [x] 錯誤處理與邊界情況（automation worker try/except、啟動前驗證、error signal）
- [x] 設定檔儲存/載入（JSON 序列化/反序列化，啟動載入、關閉儲存）
- [ ] 端對端測試（需在 Windows 環境實測）
