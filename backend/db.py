"""SQLite 資料庫管理、時間計算與資料型別序列化。"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from typing import Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW_TZ = timezone(timedelta(hours=8))

VALID_STATUSES = {"in_fridge", "rescued", "wasted", "shared"}

EMOJI_MAP: list[tuple[tuple[str, ...], str]] = [
    (("雞蛋", "水煮蛋", "溏心蛋", "鹹蛋", "皮蛋", "蛋"), "🥚"),
    (("牛奶", "鮮奶", "鮮乳", "保久乳", "豆漿", "燕麥奶"), "🥛"),
    (("白飯", "剩飯", "隔夜飯", "糙米飯", "紫米飯", "飯"), "🍚"),
    (("嫩豆腐", "板豆腐", "百頁豆腐", "雞蛋豆腐", "豆腐"), "🧈"),
    (("舒肥雞胸肉", "舒肥雞胸", "雞胸肉", "雞腿", "雞肉"), "🍗"),
    (("豬肉", "牛肉", "肉片", "絞肉", "梅花豬", "五花肉"), "🥩"),
    (("火腿", "培根", "香腸", "熱狗"), "🥓"),
    (("起司片", "起司絲", "起司", "乳酪", "芝士"), "🧀"),
    (("吐司", "麵包", "貝果", "餐包"), "🍞"),
    (("金針菇", "香菇", "鴻喜菇", "杏鮑菇", "秀珍菇", "菇"), "🍄"),
    (("高麗菜", "青江菜", "小白菜", "菠菜", "大陸妹", "娃娃菜", "青菜"), "🥬"),
    (("青蔥", "蔥花", "洋蔥", "蔥"), "🧅"),
    (("牛番茄", "小番茄", "番茄", "蕃茄"), "🍅"),
    (("韓式泡菜", "泡菜", "辣椒"), "🌶️"),
    (("烏龍麵", "泡麵", "王子麵", "科學麵", "意麵", "拉麵", "麵"), "🍜"),
    (("冷凍水餃", "水餃", "煎餃", "餛飩", "雲吞"), "🥟"),
    (("玉米筍", "玉米粒", "玉米"), "🌽"),
    (("紅蘿蔔", "胡蘿蔔"), "🥕"),
    (("馬鈴薯", "地瓜", "番薯"), "🥔"),
    (("貢丸", "魚丸", "丸子", "火鍋料", "甜不辣"), "🍢"),
    (("布丁", "優格"), "🍮"),
    (("蘋果",), "🍎"),
    (("香蕉",), "🍌"),
    (("檸檬",), "🍋"),
]


def get_db_path() -> str:
    env_path = os.environ.get("FRIDGE_DB_PATH", "").strip()
    if env_path:
        if os.path.isabs(env_path):
            return env_path
        return os.path.join(BASE_DIR, env_path)
    return os.path.join(BASE_DIR, "data", "fridge.db")


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def now_tw() -> datetime:
    return datetime.now(TW_TZ)


def today_tw() -> date:
    return now_tw().date()


def now_iso() -> str:
    return now_tw().isoformat(timespec="seconds")


def resolve_emoji(name: str, custom_emoji: str | None = None) -> str:
    if custom_emoji and str(custom_emoji).strip():
        return str(custom_emoji).strip()
    clean = (name or "").strip()
    for keywords, emoji in EMOJI_MAP:
        for kw in keywords:
            if kw == clean:
                return emoji
    for keywords, emoji in EMOJI_MAP:
        for kw in keywords:
            if kw in clean:
                return emoji
    return "🥫"


def compute_days_left_and_urgency(expires_on: str, ref_date: date | None = None) -> tuple[int, str]:
    base_date = ref_date or today_tw()
    exp_date = date.fromisoformat(expires_on)
    days_left = (exp_date - base_date).days
    if days_left <= 1:
        urgency = "red"
    elif days_left <= 3:
        urgency = "yellow"
    else:
        urgency = "green"
    return days_left, urgency


def format_quantity(val: Any) -> int | float:
    try:
        f_val = float(val)
        if f_val.is_integer():
            return int(f_val)
        return round(f_val, 2)
    except (TypeError, ValueError):
        return 1


def serialize_item(row: sqlite3.Row | dict[str, Any], ref_date: date | None = None) -> dict[str, Any]:
    expires_on = str(row["expires_on"])
    days_left, urgency = compute_days_left_and_urgency(expires_on, ref_date=ref_date)
    return {
        "id": int(row["id"]),
        "name": str(row["name"]),
        "emoji": str(row["emoji"]),
        "quantity": format_quantity(row["quantity"]),
        "unit": str(row["unit"]),
        "expires_on": expires_on,
        "days_left": days_left,
        "urgency": urgency,
        "owner": str(row["owner"] or ""),
        "price": int(row["price"] or 0),
        "status": str(row["status"]),
        "created_at": str(row["created_at"]),
    }


def serialize_recipe(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    ingredients = row["ingredients"]
    if isinstance(ingredients, str):
        ingredients = json.loads(ingredients)
    optional = row["optional"]
    if isinstance(optional, str):
        optional = json.loads(optional)
    steps = row["steps"]
    if isinstance(steps, str):
        steps = json.loads(steps)
    return {
        "id": int(row["id"]),
        "title": str(row["title"]),
        "emoji": str(row["emoji"]),
        "tool": str(row["tool"]),
        "minutes": int(row["minutes"]),
        "ingredients": list(ingredients),
        "optional": list(optional),
        "steps": list(steps),
    }


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            emoji TEXT NOT NULL DEFAULT '🥫',
            quantity REAL NOT NULL DEFAULT 1,
            unit TEXT NOT NULL DEFAULT '個',
            expires_on TEXT NOT NULL,
            owner TEXT NOT NULL DEFAULT '',
            price INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'in_fridge',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            emoji TEXT NOT NULL DEFAULT '🍲',
            tool TEXT NOT NULL,
            minutes INTEGER NOT NULL,
            ingredients TEXT NOT NULL,
            optional TEXT NOT NULL DEFAULT '[]',
            steps TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rescues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_ids TEXT NOT NULL,
            item_names TEXT NOT NULL,
            recipe_id INTEGER,
            recipe_title TEXT NOT NULL,
            action TEXT NOT NULL DEFAULT 'cooked',
            saved_ntd INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def get_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total_price "
        "FROM items WHERE status IN ('rescued', 'shared')"
    )
    rescued_row = cur.fetchone()
    rescued_count = int(rescued_row["cnt"]) if rescued_row else 0
    saved_ntd = int(rescued_row["total_price"]) if rescued_row else 0

    cur.execute("SELECT COUNT(*) AS cnt FROM items WHERE status = 'wasted'")
    wasted_row = cur.fetchone()
    wasted_count = int(wasted_row["cnt"]) if wasted_row else 0

    denom = rescued_count + wasted_count
    rescue_rate = round(rescued_count / denom, 2) if denom > 0 else 0

    cur.execute(
        "SELECT id, recipe_title, item_names, created_at "
        "FROM rescues ORDER BY id DESC LIMIT 5"
    )
    recent = []
    for row in cur.fetchall():
        raw_names = row["item_names"]
        names = json.loads(raw_names) if isinstance(raw_names, str) else list(raw_names)
        recent.append(
            {
                "id": int(row["id"]),
                "recipe_title": str(row["recipe_title"]),
                "item_names": names,
                "created_at": str(row["created_at"]),
            }
        )

    return {
        "rescued_count": rescued_count,
        "saved_ntd": saved_ntd,
        "wasted_count": wasted_count,
        "rescue_rate": rescue_rate,
        "recent": recent,
    }
