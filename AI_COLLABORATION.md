# AI 協作紀錄 — 冰箱第二春

> 評審會問「怎麼和 AI 協作」。每個 Agent 在自己的段落記錄：做了什麼、遇到什麼問題、怎麼解決。用條列、附時間。

## 團隊組成

| Agent | 角色 | 負責範圍 |
|---|---|---|
| 專案管理員 | PM | 點子選定、規格、API 介面、時程、整合、展示稿 |
| 前端工程師 | 前端 | React + Vite 介面、手機版面、mock 與 API 串接 |
| 後端管理員 | 後端 | Flask + SQLite、推薦引擎、種子資料、部署 |
| 測試和部屬工程師 | 測試／部署 | API 與端對端測試、手機版面、離線預覽、金鑰掃描、打包 zip、部署前檢查 |

人類隊員 Sean：提供比賽簡報、做最後決策、現場展示。

## 協作流程

1. Sean 把比賽簡報交給 PM。
2. PM 提出 3 個點子，用評分比重加權比較，選定「冰箱第二春」（見 `docs/SPEC.md`）。
3. PM 先寫好 API 介面（`docs/API.md`），前後端依同一份文件**同時**開工；前端先用假資料。
4. 要改介面時一律回到 PM，更新文件後再通知雙方，避免兩邊對不上。

## 專案管理員

- [T+0] 讀完簡報，比較 3 個點子（冰箱第二春 4.63 / 計畫復活所 3.55 / 物品接力站 3.30），選定冰箱第二春。關鍵考量：部署沙箱沒有網路，所以核心推薦改用規則式，AI 只當加分。
- [T+0] 寫好 SPEC.md、API.md、PLAN.md，分派前後端任務。
- [T+0] Sean 補充平台行為（網站預覽只跑網頁、部署才跑 Python），PM 修改規格：離線備案改為必做、前端建置輸出改到根目錄 `dist/`、API 一律 `/api/` 相對路徑、加入部署計畫檢查；UI 改用 Astryx。
- [T+8] 自行啟動後端抽查 API，發現推薦把冰箱裡已有的「雞蛋」列為缺少 → API 升 v1.1，新增 `also_in_fridge` 欄位，分派後端修正、通知前端顯示。
- [T+9] 再次抽查發現推薦第一名使用「已過期 1 天的雞胸肉」，有食安疑慮（起因是 PM 規格寫了「到期日 −1 到 10 天」）→ API 升 v1.2 加入食安規則：過期肉類／海鮮／乳製品／豆腐不推薦，唯一過期展示品改為香蕉；補上「全部不安全時回傳空推薦」的畫面需求。
- [T+9] 判斷前端工作量雖重但核心已完成，不加派第二位前端（避免同檔案衝突），改由新加入的測試和部屬工程師分擔驗證。
- [T+10] 從測試截圖發現推薦卡片「可省略加分」與「用到你選的」重複 → 分派前端過濾。
- [T+14] 建立 `.gitignore`、掃描金鑰與私人路徑（移除文件中的本機完整路徑），推送 GitHub `main`；測試工程師驗證 `/fridge-again/` 子路徑無後端情境 31/31 通過後，發布 `gh-pages`，並用瀏覽器在真實網址走完核心流程。
- [T+15] 撰寫 `README.md`、`DEMO.md`（1 分鐘簡報＋3 分鐘示範＋評審問答）。

## 前端工程師

- [T+2] 依 `docs/SPEC.md` 與 `docs/API.md` 建立 React 19 + Vite 前端專案架構、設計 Token 與核心 5 步流程元件（首頁冰箱清單與統計橫幅、勾選浮動列、推薦食譜卡片、食譜詳情互動步驟清單、救援成功慶祝畫面，以及含常用食材快填的新增食材表單）。
- [T+4] 收到 PM 搬家與 UI 規格更新，將 `frontend/` 遷移至新的專案根目錄並刪除舊目錄；導入 Meta Astryx（`@astryxdesign/core` 0.7.16、`@astryxdesign/theme-neutral` 0.7.16、`@stylexjs/stylex`），改寫全部介面使用 `Theme`、`Button`、`IconButton`、`Card`、`ClickableCard`、`Badge`、`Banner`、`Dialog`、`DialogHeader`、`SegmentedControl`、`Token`、`TextInput`、`Field`、`StatusDot`、`EmptyState`、`Skeleton` 元件，並以 CSS Token 客製溫暖奶油與救援綠主題。
- [T+6] 調整 Vite 建置輸出為 `base: './'`、`build.outDir: '../dist'`（建到專案根目錄 `dist/`），所有 API 改用 `/api/...` 相對路徑並移除程式碼與註解中所有 `localhost` 字眼（僅保留 `vite.config.js` 的 dev proxy）；實作必做離線備案（自動偵測 `/api/health`，連不到時無縫切換內建示範資料 + `localStorage` 持久化 + 右上角資料來源切換／一鍵重置開關）。
- [T+11] 對齊 `docs/API.md` v1.1/v1.2 與後端 `backend/seed.py`、`backend/recommend.py`：(1) 完整同步 16 樣庫存食材（含唯一過期展示品「香蕉」`days_left = -1`）、19 道電鍋／微波爐食譜（含 3 道香蕉料理）與初始戰績（已救回 6 樣、累計省下 NT$245、丟掉 2 樣、救援率 75%）；(2) 推薦卡片新增「冰箱裡也有」顯示列，並過濾 `optional` 中已出現在 `uses` 或 `also_in_fridge` 的重複食材；(3) 實作過期食材明顯標示與食安攔截（全選過期肉類／海鮮／乳製品／豆腐時顯示食安說明與一鍵「標記丟掉」按鈕，非高風險過期食材於推薦理由與詳情頁顯示食安提醒）。
- [T+12] 修正 Windows + OneDrive 下 Node 24 呼叫 `fs.rmSync` 造成建置中斷的問題（新增 `frontend/build.mjs` 安全清檔），並以 375px 手機視窗實測 Flask 部署模式與純靜態示範模式皆正常渲染、零橫向捲動、零 JS 錯誤且兩邊初始數據完全一致。
- [T+13] 因應 GitHub Pages 子路徑（`/fridge-again/`、無後端）發布需求，強化 `frontend/src/services/api.js` 對 404 HTML、405、5xx 與非規格 JSON 404 的自動備援切換並重新建置 `dist/`；以本機模擬 `/fridge-again/` 子路徑＋`/api/*` 回傳 404 HTML 實測全流程與子路徑重新整理皆 100% 通過（純 React state 路由不觸發 404），`frontend/src` 與 `dist` 金鑰掃描皆為 0 筆。

## 後端管理員

- [T+1] 依 `docs/API.md` 與 `docs/SPEC.md` 建立 SQLite 資料庫結構（`backend/db.py`）與種子工具（`backend/seed.py`）：啟動時若資料庫為空自動塞入 15 樣在冰箱食材（到期日相對「今天 + N 天」動態計算，涵蓋紅／黃／綠三種緊急度）、16 道只用電鍋或微波爐的宿舍食譜、以及 4 筆歷史救援紀錄（6 樣已救援、2 樣已丟棄，初始救援率 0.75、省下 NT$245）；並提供 `python -m backend.seed --reset` 一鍵重置。
- [T+3] 收到 PM 搬家與部署規格更新，將 `app.py`、`backend/`、`requirements.txt`、`.env.example`、`Procfile` 搬移至新的專案根目錄並清除舊目錄檔案；Flask 靜態檔案路由改為優先送出根目錄 `dist/index.html` 與靜態資源（`dist` 未產生時回傳友善提示頁，不讓服務崩潰）。
- [T+6] 完成實作全部 9 個 API 端點（`GET /api/health`、`GET /api/items`、`POST /api/items`、`PATCH /api/items/{id}`、`DELETE /api/items/{id}`、`POST /api/suggestions`、`POST /api/rescues`、`GET /api/stats`、`GET /api/recipes/{id}`）及規則式推薦引擎（`backend/recommend.py`），支援別名正規化（如「蛋=雞蛋」「隔夜飯=剩飯=白飯」「鮮奶=牛奶」「板豆腐=嫩豆腐=豆腐」等）與到期優先加權計分；並實作選做線上 AI 推薦（`backend/ai.py`），只從環境變數讀取金鑰，無金鑰或沙箱無網路時 100% 自動退回規則式。
- [T+8] 以 `PORT=8000` 啟動後端服務並以 `curl.exe` 完整驗證全部 9 個端點、錯誤回應格式（`BAD_REQUEST` / `NOT_FOUND` / `INTERNAL`）與金鑰掃描檢查（確認 `sk-|api_key\s*=` 只出現在 `.env.example` 空變數）。
- [T+9] 配合 PM 抽查與 `docs/API.md` v1.1 規格升級，更新 `backend/recommend.py` 與 `backend/ai.py`：針對食譜需要、使用者未勾選但冰箱中現有（`in_fridge`）的食材，以別名比對後放入新增欄位 `also_in_fridge: [{id, name, days_left}]`，並從 `missing` 中排除（`missing` 僅保留冰箱真正沒有且非 `optional` 的食材），以 `{"item_ids": [1, 2]}` 驗證通過後重置種子資料。
- [T+11] 依 PM 食安修正調整 `backend/seed.py`、`backend/recommend.py` 與 `backend/ai.py`：(1) 種子資料中所有肉類、乳製品、豆腐（舒肥雞胸肉、牛奶、嫩豆腐）的 `days_left` 最少為 0（今天到期），唯一 `days_left = -1` 展示品改為過熟仍可做甜點的「香蕉」（id 1），並新增 3 道香蕉電鍋／微波爐食譜；(2) 推薦引擎（規則式與 AI 備案）排除 `days_left < 0` 的肉類、海鮮、乳製品、豆腐（不列入 `uses` 與 `also_in_fridge`），其他過期食材推薦時於 `reason` 自動加上「已過期，請先確認外觀氣味再使用」；通過 `tests/test_api.py` 14 項測試並重置種子資料。

## 測試和部屬工程師

- [T+9] 讀完簡報、SPEC、API v1.1、PLAN 的打包前檢查清單。確認不修改 `app.py`、`backend/`、`frontend/`，發現問題只回報 PM。
- [T+9] 寫 `tests/test_api.py`（只用標準庫 unittest，自己啟動 Flask、測完自動 `seed --reset`）：9 個端點的正常情況和 `BAD_REQUEST` / `NOT_FOUND` 錯誤格式、v1.1 的 `missing` 不含冰箱已有食材。結果 14 項全過。
- [T+9] 寫 `scripts/check_and_pack.py`：掃描真實金鑰與 `.env`、前端不得出現 localhost（`vite.config.js` 例外）、檢查 dist／Procfile／requirements，打包 `release/fridge-again.zip`（含 `dist/`，排除 `data/*.db`、`__pycache__`、`node_modules`、`.git`、`.env`），並檢查檔案數與大小、驗證 zip 內容。
- [T+10] 寫 `tests/e2e_core_flow.py`（Playwright，375px 手機寬度）：核心 5 步各跑兩種情況（Flask 部署網址、純靜態網站預覽），並檢查沒有橫向捲動、沒有 JS 錯誤、沒有連外部網址、重新整理後狀態保留。兩種情況 33 項全過，截圖放 `release/screens/`。
- 遇到的問題：`frontend/src/services/api.js` 註解寫了 localhost 字眼，會被「前端不得出現 localhost」的掃描命中。解法：檢查腳本把「只在註解」降為警告，並建議前端改字眼。
- 遇到的問題：離線示範資料的初始「累計省下」是 NT$215，後端種子是 NT$245，兩種網址的畫面數字不一致。已回報 PM。

- [T+14] GitHub Pages 發布前驗證：把 e2e 勾選組合改成「舒肥雞胸肉＋牛奶」（會一起入菜），新增 `--mode ghpages`（dist 放暫存資料夾的 `fridge-again/` 子路徑、`/api/*` 回 404、測完刪除暫存資料夾），並加入新增食材、過期高風險品食安提示、標記丟掉、css/js 200、無失敗資源載入等檢查。flask 30、static 29、ghpages 31，共 90 項全過。新增 `check_and_pack.py --scan-dist` 掃描 dist 沒有金鑰、token、localhost。
- 遇到的問題：ghpages 暫存資料夾刪不掉（Windows 錯誤 5），原因是從 OneDrive 複製來的檔案帶唯讀屬性；解法：刪除時先改成可寫再刪。另外 css/js 的重新整理後 304 一開始被誤判為失敗，改成「每個檔至少一次 200，其餘只允許 304」。

## 遇到的問題與解法

| 問題 | 誰發現 | 解法 |
|---|---|---|
| 部署沙箱沒有對外網路，AI 服務叫不到 | PM | 核心改用規則式推薦，AI 列為選做並自動退回規則式 |
| 網站預覽網址不跑 Python，API 會失效 | Sean | 前端內建示範資料備案改為必做；建置結果放根目錄 `dist/` 讓預覽找得到 |
| Windows 或精簡 Linux 容器可能缺少 IANA `tzdata` 套件導致 `ZoneInfo("Asia/Taipei")` 失敗 | 後端管理員 | 改用 Python 標準庫 `timezone(timedelta(hours=8))` 處理台灣時間與 `days_left` 計算，零外部依賴且跨平台穩定 |
| 使用者新增罕見自訂食材或輸入同義詞時可能比對不到食譜 | 後端管理員 | 建立 19 組宿舍常見食材別名正規化字典與子字串比對，並加上百搭宿舍鍋物／炊飯保底機制，確保 `POST /api/suggestions` 永遠回傳 3–5 道可用食譜 |
| 平台上傳時掃描 `sk-\|api_key\s*=` 可能誤判程式碼變數名稱 | 後端管理員 | 在 `backend/ai.py` 避免使用 `api_key =` 變數命名，實測掃描只會命中 `.env.example` 的空變數 |
| 使用者未勾選但冰箱裡有的食材（如雞蛋）被誤列為 `missing` | PM | API 升級至 v1.1，後端推薦引擎（含規則式與 AI 備案）新增 `also_in_fridge: [{id, name, days_left}]` 並將該食材自 `missing` 移除 |
| 種子資料中肉類過期（`days_left = -1`）還被推薦入菜，易引發評審食安疑慮 | PM | 肉類／海鮮／乳製品／豆腐種子資料最少設為今天到期（`days_left >= 0`），過期展示品改為過熟香蕉並配香蕉甜點食譜；推薦引擎攔截已過期的高風險生鮮食材，其他過期食材於 `reason` 加上「已過期，請先確認外觀氣味再使用」 |
| 推薦卡片「可省略加分」列出已出現在「用到你選的／冰箱裡也有」的食材，造成語意矛盾 | PM | 前端推薦卡片改以別名比對過濾 `optional`，僅顯示未出現於 `uses` 與 `also_in_fridge` 的加分食材，過濾後為空則整行隱藏 |
| Astryx `ClickableCard` 內層內容遮擋內建 `<button>` 的自動化點擊命中 | 前端工程師 | 為 `.recipe-card-inner` 加上 `pointer-events: none`，讓卡片任意區域點擊皆直接導向按鈕 |
| Windows + OneDrive 同步目錄下 Node 24 執行 Vite `emptyOutDir`（內部呼叫 `fs.rmSync`）偶發觸發 `0xC0000409` 崩潰 | 前端工程師 | 改以 `frontend/build.mjs` 透過 `readdirSync + unlinkSync + rmdirSync` 安全清空根目錄 `dist/` 後再執行 Vite build，並設 `emptyOutDir: false` |
