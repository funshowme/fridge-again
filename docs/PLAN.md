# 冰箱第二春 — 時程與分工

> 以正式比賽 28 小時換算（T+0 = 開始開發）。這次是賽前演練，用同樣的節奏跑。

## 分工

| 角色 | 負責 | 交付物 |
|---|---|---|
| 專案管理員（PM） | 規格、API、時程、追進度、整合檢查、展示稿 | `docs/*`、`README.md`、`DEMO.md`、`AI_COLLABORATION.md` 彙整 |
| 前端工程師 | React + Vite + Astryx 介面、手機版面、先用 mock 開發再接 API、離線備案（必做） | `frontend/`、根目錄 `dist/` |
| 後端管理員 | Flask + SQLite、9 個 API、規則式推薦、種子資料、送出 `dist/`、`.env.example`、部署計畫檢查 | `app.py`、`backend/`、`requirements.txt`、`.env.example` |
| 測試和部屬工程師 | API 自動測試、端對端測試（兩種網址情境、375px）、金鑰與打包檢查、zip 產出；只回報 bug，不改程式 | `tests/`、`scripts/`、zip 檔 |

專案位置：本 repo 根目錄（所有檔案都放這裡）

## 時程與檢查點

| 時段 | 要完成的事 | 誰 |
|---|---|---|
| T+0 – T+1 | 規格、API 定案，全員確認 | PM（已完成初版） |
| T+1 – T+6 | 後端：資料表、種子資料、items / stats API；前端：首頁冰箱清單 + 統計（mock） | 前、後 |
| T+6 – T+12 | 後端：suggestions、rescues；前端：推薦頁、詳情頁、救援成功畫面 | 前、後 |
| **T+12** | **第一次整合**：前端接真 API，核心流程 5 步能從頭跑到尾 | 全員 |
| T+12 – T+22 | 新增食材表單、美化、修 bug；選做功能依 SPEC 順序 | 前、後 |
| **T+22** | **功能凍結**，只修 bug | 全員 |
| T+22 – T+26 | 打包 zip、部署測試、金鑰掃描、離線測試 | 後端主導、PM 檢查 |
| T+26 – T+28 | README、DEMO、AI_COLLABORATION 定稿，最後上傳 | PM |

## 回報方式

- 每完成一個檢查點，回報 PM：做好了什麼、怎麼啟動測試、還卡在哪。
- 要改 API 欄位 → 先告訴 PM，不要直接改。
- 每人在 `AI_COLLABORATION.md` 自己的段落記下：做了什麼、遇到的問題與解法。

## 打包前檢查清單

- [ ] 核心流程 5 步從頭操作到尾，沒有卡住
- [ ] 375px 手機寬度正常
- [ ] zip 裡沒有 `.env`、沒有寫死的金鑰（`grep -ri "sk-\|api_key\s*=" .` 只該出現 `.env.example` 的空變數）
- [ ] 拔網路後仍能操作主要功能（規則式推薦）
- [ ] 打開就有種子資料
- [ ] 根目錄 `dist/` 有放進 zip，`data/*.db` 沒放
- [ ] **網站預覽網址**：只開 `dist/index.html`（不跑 Python）也能走完核心流程（內建示範資料）
- [ ] **部署網址**：打開就是完整作品，API 有回應
- [ ] **部署計畫**：python312、工作目錄 = 根目錄、`pip install -r requirements.txt`、`gunicorn -b 0.0.0.0:$PORT app:app`；不對就手動改
- [ ] 前端程式裡搜尋 `localhost` 應該只出現在 `vite.config.js` 的 proxy 設定
- [ ] README 說得出「如何給快過期食材第二次機會」
