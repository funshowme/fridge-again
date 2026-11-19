# 冰箱第二春 — API 介面（v1.1）

> v1.1：`POST /api/suggestions` 每筆加 `also_in_fridge`；冰箱裡已有的食材不再算 `missing`。

> 前後端依這份同時開工。要改欄位，先告訴 PM，由 PM 更新這份文件並通知雙方。

## 共通規則

- 所有路徑前綴 `/api`，請求與回應都是 JSON（`Content-Type: application/json`）。
- 前端呼叫時一律用**相對路徑** `/api/items`，**不要寫死 `http://localhost:5000`**；開發時用 Vite 的 proxy 把 `/api` 轉到本機後端。
- API 連不到（網站預覽網址沒有 Python）時，前端自動改用內建示範資料，回傳格式和本文件完全相同。
- 日期一律 `YYYY-MM-DD`（台灣時間，Asia/Taipei）；時間戳記用 ISO 8601，例如 `2026-12-05T14:30:00+08:00`。
- 金額單位：新台幣整數。
- 錯誤回應：HTTP 400 / 404 / 500，內容固定為
  ```json
  { "error": { "code": "NOT_FOUND", "message": "找不到這個食材" } }
  ```
  `code` 可用值：`BAD_REQUEST`、`NOT_FOUND`、`INTERNAL`。`message` 用中文，前端可直接顯示。

## 資料型別

### Item（食材）
```json
{
  "id": 3,
  "name": "雞蛋",
  "emoji": "🥚",
  "quantity": 2,
  "unit": "顆",
  "expires_on": "2026-12-06",
  "days_left": 1,
  "urgency": "red",
  "owner": "小明",
  "price": 20,
  "status": "in_fridge",
  "created_at": "2026-12-05T12:00:00+08:00"
}
```
- `days_left`：後端依今天計算，已過期為負數。
- `urgency`：`red`（days_left ≤ 1）、`yellow`（2–3）、`green`（≥ 4）。
- `owner`：室友名稱，可為空字串（不是帳號，不存任何個資）。
- `price`：估計價值，用來算「省下多少錢」，可為 0。
- `status`：`in_fridge`（在冰箱）、`rescued`（煮掉了）、`wasted`（丟掉了）、`shared`（選做：分享給室友）。

### Recipe（食譜）
```json
{
  "id": 7,
  "title": "電鍋蒸蛋",
  "emoji": "🍮",
  "tool": "電鍋",
  "minutes": 15,
  "ingredients": ["雞蛋", "蔥"],
  "optional": ["蔥"],
  "steps": ["蛋打散加 1.5 倍水", "外鍋放半杯水", "蒸到開關跳起"]
}
```
- `tool`：`電鍋` 或 `微波爐`（宿舍限定）。
- `optional`：可省略的食材，不算「缺少」。

---

## 端點

### 1. `GET /api/health`
確認服務活著、目前推薦模式。
```json
{ "ok": true, "ai": "offline" }
```
`ai`：`offline`（只用規則式）或 `online`（有金鑰且連得到 AI）。

### 2. `GET /api/items?status=in_fridge`
取得食材清單，依 `expires_on` 由近到遠排序。`status` 可省略，預設 `in_fridge`。
```json
{ "items": [ Item, Item ] }
```

### 3. `POST /api/items`
新增食材。
- 輸入：
  ```json
  { "name": "豆腐", "quantity": 1, "unit": "盒", "expires_on": "2026-12-07", "owner": "小美", "price": 25 }
  ```
  必填：`name`、`expires_on`。其他預設：`quantity` 1、`unit` "個"、`owner` ""、`price` 0。`emoji` 由後端依名稱對照，找不到用 `🥫`。
- 輸出（201）：`{ "item": Item }`

### 4. `PATCH /api/items/{id}`
改狀態或內容（例如標記丟掉）。
- 輸入（欄位都可選）：`{ "status": "wasted" }`
- 輸出：`{ "item": Item }`

### 5. `DELETE /api/items/{id}`
刪除輸入錯的食材（不計入統計）。輸出：`{ "ok": true }`

### 6. `POST /api/suggestions`
勾選食材 → 推薦食譜（核心功能）。
- 輸入：`{ "item_ids": [3, 5] }`（1–5 個）
- 輸出：
  ```json
  {
    "source": "rules",
    "recipes": [
      {
        "recipe": Recipe,
        "uses": ["雞蛋", "白飯"],
        "uses_item_ids": [3, 5],
        "also_in_fridge": [ { "id": 8, "name": "蔥", "days_left": 2 } ],
        "missing": ["醬油"],
        "score": 92,
        "reason": "用掉 2 樣快過期食材，其中雞蛋明天到期"
      }
    ]
  }
  ```
- `source`：`rules`（規則式）或 `ai`。
- `also_in_fridge`（v1.1 新增）：食譜需要、使用者**沒勾選**但冰箱裡（`in_fridge`）**有**的食材。這些**不可以**出現在 `missing`。前端顯示成「冰箱裡也有：蔥」。
- `missing`：冰箱裡真的沒有、也不是 optional 的食材。
- **食安規則（v1.2）**：`days_left < 0` 的肉類、海鮮、乳製品、豆腐不參與推薦（不列入 `uses`、`also_in_fridge`）；其他過期食材可推薦，但 `reason` 會加上「已過期，請先確認外觀氣味再使用」。
- **可能回傳空陣列**：如果勾選的食材全都是「過期且不安全」的，`recipes` 會是 `[]`（HTTP 200）。前端要顯示說明（例如「為了安全，過期的肉類、乳製品不建議再食用」），並提供「標記丟掉」按鈕（呼叫 `PATCH /api/items/{id}` `{ "status": "wasted" }`）。
- 回傳 3–5 筆，依 `score` 由高到低。至少要用到 1 個勾選的食材。
- 規則式計分（建議，後端可微調）：每用到 1 個勾選食材 +30；該食材 `days_left ≤ 1` 再 +10；每缺 1 樣非 optional 食材 −15；同時也會用到冰箱裡其他快過期食材 +5。分數夾在 0–100。
- 食材比對要能處理別名（例如「蛋」=「雞蛋」、「白飯」=「剩飯」）。

### 7. `POST /api/rescues`
「我煮了！」→ 記一筆救援，相關食材改成 `rescued`。
- 輸入：`{ "item_ids": [3, 5], "recipe_id": 7, "action": "cooked" }`
  - `action`：`cooked`（必做）或 `shared`（選做）
- 輸出（201）：
  ```json
  {
    "rescue": { "id": 12, "item_ids": [3, 5], "recipe_id": 7, "action": "cooked", "saved_ntd": 45, "created_at": "..." },
    "stats": Stats
  }
  ```

### 8. `GET /api/stats`
首頁上方的統計。
```json
{
  "rescued_count": 8,
  "saved_ntd": 320,
  "wasted_count": 2,
  "rescue_rate": 0.8,
  "recent": [
    { "id": 12, "recipe_title": "電鍋蒸蛋", "item_names": ["雞蛋"], "created_at": "..." }
  ]
}
```
- `rescue_rate` = rescued_count ÷ (rescued_count + wasted_count)，分母 0 時為 0。
- `recent` 最多 5 筆，新到舊。

### 9. `GET /api/recipes/{id}`（選用）
單一食譜詳情：`{ "recipe": Recipe }`。前端也可以直接用 suggestions 回傳的內容，不一定要呼叫。

---

## 種子資料要求（後端）

- 啟動時若資料庫是空的，自動放入：
  - 約 15 樣食材，**到期日用「今天 + N 天」產生**（N = −1 到 10），保證任何時候打開都有紅、黃、綠三種；分給 2–3 位虛構室友（例如「小明」「小美」）。
  - 約 15 道宿舍食譜，全部只用電鍋或微波爐。
  - 3–5 筆過去的救援紀錄，讓統計一開始就不是 0。
- 提供重置方式（例如 `python -m backend.seed --reset`），展示前可以恢復初始狀態。
