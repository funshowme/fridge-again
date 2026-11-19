"""冰箱第二春 (FridgeAgain) Flask 後端服務與前端靜態檔案伺服器。"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any

from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from backend.ai import is_ai_configured, try_ai_recommend
from backend.db import (
    BASE_DIR,
    VALID_STATUSES,
    get_connection,
    get_stats,
    now_iso,
    resolve_emoji,
    serialize_item,
    serialize_recipe,
)
from backend.recommend import recommend_by_rules
from backend.seed import ensure_seeded, reset_and_seed

app = Flask(__name__, static_folder=None)
app.json.ensure_ascii = False

ensure_seeded()


def error_response(code: str, message: str, status_code: int) -> tuple[Response, int]:
    return jsonify({"error": {"code": code, "message": message}}), status_code


def _resolve_dist_dir() -> str:
    root_dist = os.path.join(BASE_DIR, "dist")
    if os.path.isfile(os.path.join(root_dist, "index.html")):
        return root_dist
    frontend_dist = os.path.join(BASE_DIR, "frontend", "dist")
    if os.path.isfile(os.path.join(frontend_dist, "index.html")):
        return frontend_dist
    return root_dist


def _validate_iso_date(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    clean = value.strip()
    try:
        date.fromisoformat(clean)
        return clean
    except ValueError:
        return None


@app.errorhandler(Exception)
def handle_unexpected_error(exc: Exception) -> tuple[Response, int]:
    if isinstance(exc, HTTPException):
        if exc.code == 404 and request.path.startswith("/api"):
            return error_response("NOT_FOUND", "找不到此 API 路徑", 404)
        if exc.code == 400:
            return error_response("BAD_REQUEST", "請求格式不正確", 400)
        if exc.code == 405 and request.path.startswith("/api"):
            return error_response("BAD_REQUEST", "不支援此 HTTP 方法", 400)
    return error_response("INTERNAL", f"伺服器內部錯誤：{exc}", 500)


@app.get("/api/health")
def api_health() -> tuple[Response, int]:
    ai_mode = "online" if is_ai_configured() else "offline"
    return jsonify({"ok": True, "ai": ai_mode}), 200


@app.get("/api/items")
def api_list_items() -> tuple[Response, int]:
    status_filter = request.args.get("status", "in_fridge").strip() or "in_fridge"
    if status_filter != "all" and status_filter not in VALID_STATUSES:
        return error_response("BAD_REQUEST", "無效的食材狀態篩選值", 400)

    conn = get_connection()
    try:
        cur = conn.cursor()
        if status_filter == "all":
            cur.execute("SELECT * FROM items ORDER BY expires_on ASC, id ASC")
        else:
            cur.execute(
                "SELECT * FROM items WHERE status = ? ORDER BY expires_on ASC, id ASC",
                (status_filter,),
            )
        items = [serialize_item(row) for row in cur.fetchall()]
        return jsonify({"items": items}), 200
    finally:
        conn.close()


@app.post("/api/items")
def api_create_item() -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        return error_response("BAD_REQUEST", "請提供 JSON 格式的食材資料", 400)

    name = str(data.get("name", "")).strip()
    if not name:
        return error_response("BAD_REQUEST", "食材名稱（name）為必填", 400)

    expires_on = _validate_iso_date(data.get("expires_on"))
    if not expires_on:
        return error_response("BAD_REQUEST", "到期日（expires_on）必填且須為 YYYY-MM-DD 格式", 400)

    raw_quantity = data.get("quantity", 1)
    try:
        quantity = float(raw_quantity)
        if quantity <= 0:
            return error_response("BAD_REQUEST", "數量（quantity）必須大於 0", 400)
    except (TypeError, ValueError):
        return error_response("BAD_REQUEST", "數量（quantity）必須是數字", 400)

    unit = str(data.get("unit", "個")).strip() or "個"
    owner = str(data.get("owner", "")).strip()

    raw_price = data.get("price", 0)
    try:
        price = int(raw_price)
        if price < 0:
            return error_response("BAD_REQUEST", "價格（price）不可為負數", 400)
    except (TypeError, ValueError):
        return error_response("BAD_REQUEST", "價格（price）必須為整數", 400)

    status = str(data.get("status", "in_fridge")).strip() or "in_fridge"
    if status not in VALID_STATUSES:
        return error_response("BAD_REQUEST", "無效的食材狀態", 400)

    emoji = resolve_emoji(name, data.get("emoji"))
    created_at = now_iso()

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO items (name, emoji, quantity, unit, expires_on, owner, price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, emoji, quantity, unit, expires_on, owner, price, status, created_at),
        )
        new_id = cur.lastrowid
        conn.commit()

        cur.execute("SELECT * FROM items WHERE id = ?", (new_id,))
        row = cur.fetchone()
        return jsonify({"item": serialize_item(row)}), 201
    finally:
        conn.close()


@app.patch("/api/items/<int:item_id>")
def api_update_item(item_id: int) -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict) or not data:
        return error_response("BAD_REQUEST", "請提供要更新的欄位", 400)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        existing = cur.fetchone()
        if not existing:
            return error_response("NOT_FOUND", "找不到這個食材", 404)

        updates: dict[str, Any] = {}

        if "name" in data:
            name = str(data["name"]).strip()
            if not name:
                return error_response("BAD_REQUEST", "食材名稱不可為空", 400)
            updates["name"] = name
            if "emoji" not in data:
                updates["emoji"] = resolve_emoji(name)

        if "emoji" in data:
            updates["emoji"] = resolve_emoji(updates.get("name", existing["name"]), data["emoji"])

        if "quantity" in data:
            try:
                qty = float(data["quantity"])
                if qty <= 0:
                    return error_response("BAD_REQUEST", "數量必須大於 0", 400)
                updates["quantity"] = qty
            except (TypeError, ValueError):
                return error_response("BAD_REQUEST", "數量必須是數字", 400)

        if "unit" in data:
            updates["unit"] = str(data["unit"]).strip() or "個"

        if "expires_on" in data:
            exp = _validate_iso_date(data["expires_on"])
            if not exp:
                return error_response("BAD_REQUEST", "到期日須為 YYYY-MM-DD 格式", 400)
            updates["expires_on"] = exp

        if "owner" in data:
            updates["owner"] = str(data["owner"] or "").strip()

        if "price" in data:
            try:
                price = int(data["price"])
                if price < 0:
                    return error_response("BAD_REQUEST", "價格不可為負數", 400)
                updates["price"] = price
            except (TypeError, ValueError):
                return error_response("BAD_REQUEST", "價格必須為整數", 400)

        if "status" in data:
            status = str(data["status"]).strip()
            if status not in VALID_STATUSES:
                return error_response("BAD_REQUEST", "無效的食材狀態", 400)
            updates["status"] = status

        if not updates:
            return jsonify({"item": serialize_item(existing)}), 200

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [item_id]
        cur.execute(f"UPDATE items SET {set_clause} WHERE id = ?", params)
        conn.commit()

        cur.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        updated_row = cur.fetchone()
        return jsonify({"item": serialize_item(updated_row)}), 200
    finally:
        conn.close()


@app.delete("/api/items/<int:item_id>")
def api_delete_item(item_id: int) -> tuple[Response, int]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM items WHERE id = ?", (item_id,))
        if not cur.fetchone():
            return error_response("NOT_FOUND", "找不到這個食材", 404)

        cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        return jsonify({"ok": True}), 200
    finally:
        conn.close()


@app.post("/api/suggestions")
def api_suggestions() -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        return error_response("BAD_REQUEST", "請提供 JSON 格式的請求內容", 400)

    raw_ids = data.get("item_ids")
    if not isinstance(raw_ids, list) or not (1 <= len(raw_ids) <= 5):
        return error_response("BAD_REQUEST", "請勾選 1 到 5 樣食材（item_ids）", 400)

    try:
        item_ids = [int(x) for x in raw_ids]
    except (TypeError, ValueError):
        return error_response("BAD_REQUEST", "item_ids 必須為整數陣列", 400)

    conn = get_connection()
    try:
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in item_ids)
        cur.execute(f"SELECT * FROM items WHERE id IN ({placeholders})", item_ids)
        found_rows = cur.fetchall()
        if not found_rows:
            return error_response("NOT_FOUND", "找不到勾選的食材", 404)

        row_map = {int(r["id"]): serialize_item(r) for r in found_rows}
        missing_ids = [iid for iid in item_ids if iid not in row_map]
        if missing_ids:
            return error_response("NOT_FOUND", f"找不到部分勾選的食材（ID: {missing_ids[0]}）", 404)

        selected_items = [row_map[iid] for iid in item_ids]

        cur.execute("SELECT * FROM items WHERE status = 'in_fridge' ORDER BY expires_on ASC, id ASC")
        all_fridge_items = [serialize_item(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM recipes ORDER BY id ASC")
        all_recipes = [serialize_recipe(r) for r in cur.fetchall()]

        ai_results = try_ai_recommend(selected_items, all_fridge_items, all_recipes)
        if ai_results is not None:
            return jsonify({"source": "ai", "recipes": ai_results}), 200

        rule_results = recommend_by_rules(selected_items, all_fridge_items, all_recipes, limit=5)
        return jsonify({"source": "rules", "recipes": rule_results}), 200
    finally:
        conn.close()


@app.post("/api/rescues")
def api_create_rescue() -> tuple[Response, int]:
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        return error_response("BAD_REQUEST", "請提供 JSON 格式的救援資料", 400)

    raw_ids = data.get("item_ids")
    if not isinstance(raw_ids, list) or len(raw_ids) == 0:
        return error_response("BAD_REQUEST", "請提供至少 1 個食材 ID（item_ids）", 400)

    try:
        item_ids = [int(x) for x in raw_ids]
    except (TypeError, ValueError):
        return error_response("BAD_REQUEST", "item_ids 必須為整數陣列", 400)

    action = str(data.get("action", "cooked")).strip() or "cooked"
    if action not in {"cooked", "shared"}:
        return error_response("BAD_REQUEST", "action 只能是 cooked 或 shared", 400)

    raw_recipe_id = data.get("recipe_id")
    recipe_id: int | None = None
    if raw_recipe_id is not None:
        try:
            recipe_id = int(raw_recipe_id)
        except (TypeError, ValueError):
            return error_response("BAD_REQUEST", "recipe_id 必須為整數", 400)
    elif action == "cooked":
        return error_response("BAD_REQUEST", "煮完料理需提供 recipe_id", 400)

    conn = get_connection()
    try:
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in item_ids)
        cur.execute(f"SELECT * FROM items WHERE id IN ({placeholders})", item_ids)
        rows = cur.fetchall()
        row_map = {int(r["id"]): r for r in rows}
        for iid in item_ids:
            if iid not in row_map:
                return error_response("NOT_FOUND", "找不到這個食材", 404)

        recipe_title = "分享給室友"
        if recipe_id is not None:
            cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
            recipe_row = cur.fetchone()
            if not recipe_row:
                return error_response("NOT_FOUND", "找不到這個食譜", 404)
            recipe_title = str(recipe_row["title"])

        ordered_rows = [row_map[iid] for iid in item_ids]
        saved_ntd = sum(int(r["price"] or 0) for r in ordered_rows)
        item_names = [str(r["name"]) for r in ordered_rows]

        new_status = "rescued" if action == "cooked" else "shared"
        cur.execute(
            f"UPDATE items SET status = ? WHERE id IN ({placeholders})",
            [new_status, *item_ids],
        )

        created_at = now_iso()
        cur.execute(
            """
            INSERT INTO rescues (item_ids, item_names, recipe_id, recipe_title, action, saved_ntd, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps(item_ids),
                json.dumps(item_names, ensure_ascii=False),
                recipe_id,
                recipe_title,
                action,
                saved_ntd,
                created_at,
            ),
        )
        rescue_id = int(cur.lastrowid)
        conn.commit()

        stats = get_stats(conn)
        rescue_obj = {
            "id": rescue_id,
            "item_ids": item_ids,
            "recipe_id": recipe_id,
            "action": action,
            "saved_ntd": saved_ntd,
            "created_at": created_at,
        }
        return jsonify({"rescue": rescue_obj, "stats": stats}), 201
    finally:
        conn.close()


@app.get("/api/stats")
def api_stats() -> tuple[Response, int]:
    conn = get_connection()
    try:
        return jsonify(get_stats(conn)), 200
    finally:
        conn.close()


@app.get("/api/recipes")
def api_list_recipes() -> tuple[Response, int]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM recipes ORDER BY id ASC")
        recipes = [serialize_recipe(r) for r in cur.fetchall()]
        return jsonify({"recipes": recipes}), 200
    finally:
        conn.close()


@app.get("/api/recipes/<int:recipe_id>")
def api_get_recipe(recipe_id: int) -> tuple[Response, int]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        row = cur.fetchone()
        if not row:
            return error_response("NOT_FOUND", "找不到這個食譜", 404)
        return jsonify({"recipe": serialize_recipe(row)}), 200
    finally:
        conn.close()


@app.post("/api/reset")
def api_reset() -> tuple[Response, int]:
    conn = get_connection()
    try:
        reset_and_seed(conn)
        return jsonify({"ok": True, "stats": get_stats(conn)}), 200
    finally:
        conn.close()


@app.route("/api/<path:subpath>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def api_not_found(subpath: str) -> tuple[Response, int]:
    return error_response("NOT_FOUND", f"找不到 API 路徑：/api/{subpath}", 404)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str) -> Response | tuple[str, int, dict[str, str]]:
    if path.startswith("api/") or path == "api":
        return error_response("NOT_FOUND", "找不到此 API 路徑", 404)

    dist_dir = _resolve_dist_dir()
    if path:
        candidate = os.path.join(dist_dir, path)
        if os.path.isfile(candidate):
            return send_from_directory(dist_dir, path)

    index_file = os.path.join(dist_dir, "index.html")
    if os.path.isfile(index_file):
        return send_from_directory(dist_dir, "index.html")

    fallback_html = (
        "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>"
        "<title>冰箱第二春 FridgeAgain</title></head>"
        "<body style='font-family:sans-serif;padding:2rem;'>"
        "<h1>冰箱第二春 FridgeAgain 後端服務運行中</h1>"
        "<p>前端建置檔（<code>dist/index.html</code>）尚未產生；"
        "API 已就緒：<a href='/api/health'>/api/health</a>、"
        "<a href='/api/items'>/api/items</a>、<a href='/api/stats'>/api/stats</a>。</p>"
        "</body></html>"
    )
    return fallback_html, 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
