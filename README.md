# 冰箱第二春 FridgeAgain

> 勾選冰箱裡快過期的食材，30 秒找到只用電鍋或微波爐就能做的救援料理。

吃客松 Haquaso 賽前演練作品，主題「再來一次 Second Chance」。

- **線上示範（純前端示範模式）**：https://funshowme.github.io/fridge-again/

## 解決什麼問題

住宿舍、共用冰箱的大學生常常買了食材忘記吃，或不知道剩下那幾樣能煮什麼，最後只好丟掉。冰箱第二春讓這些**快被丟掉的食材得到第二次機會**：

1. 打開就看到冰箱清單，依到期日排序，紅、黃、綠標示急迫程度
2. 勾選 1–3 樣快過期的食材，按「給它們第二次機會」
3. 系統推薦只用電鍋或微波爐的料理，標出「用到你選的／冰箱裡也有／還缺」
4. 看步驟，按「我煮了！」
5. 食材從清單消失，「已救回幾樣、省下多少錢」的統計跟著更新

**食安規則**：過期的肉類、海鮮、乳製品、豆腐不會被推薦，改為提示「標記丟掉」；其他過期食材會附上「請先確認外觀氣味再使用」的提醒。

## 技術架構

```
瀏覽器（React 19 + Vite + Astryx）
        │  fetch("/api/...")；連不到就自動改用內建示範資料（localStorage）
        ▼
Python Flask（app.py）── 同時送出前端建置檔 dist/
        ├─ SQLite（啟動時自動放入示範用種子資料）
        └─ 推薦引擎：規則式（不需網路）／AI（選用，失敗自動退回規則式）
```

| 資料夾 | 內容 |
|---|---|
| `app.py`、`backend/` | Flask API、SQLite、規則式推薦、種子資料 |
| `frontend/` | React + Vite 原始碼，建置輸出到根目錄 `dist/` |
| `tests/`、`scripts/` | API 測試、端對端測試、金鑰掃描與打包檢查 |
| `docs/` | 規格（SPEC）、API 介面（API）、時程分工（PLAN） |

## 怎麼啟動

需要 Python 3.12 與 Node.js。

```bash
# 1. 建置前端（輸出到根目錄 dist/）
cd frontend
npm install
npm run build
cd ..

# 2. 啟動後端（同時送出前端網頁）
pip install -r requirements.txt
python app.py            # 預設 http://localhost:5000，可用環境變數 PORT 改連接埠
```

正式部署：`gunicorn -b 0.0.0.0:$PORT app:app`（見 `Procfile`）。

重置示範資料：`python -m backend.seed --reset`

前端開發模式：`cd frontend && npm run dev`（`/api` 會轉到本機後端）。

## 環境變數

複製 `.env.example` 成 `.env` 再填值。**所有變數都是選用的**，不填也能完整運作（推薦會使用規則式）。repo 裡不包含任何真實金鑰。

## 測試

```bash
python tests/test_api.py                    # 後端 API 測試
python tests/e2e_core_flow.py --mode static # 端對端測試（需 playwright + chromium）
python scripts/check_and_pack.py            # 金鑰掃描與打包檢查
```

## AI 協作

本作品由人類隊員與四個 AI Agent（專案管理員、前端工程師、後端管理員、測試和部屬工程師）分工完成，過程記錄在 [`AI_COLLABORATION.md`](AI_COLLABORATION.md)。
