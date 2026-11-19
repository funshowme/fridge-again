"""種子資料建立與重置工具（支援 `python -m backend.seed --reset`）。"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import timedelta
from typing import Any

from backend.db import (
    get_connection,
    init_schema,
    now_tw,
    resolve_emoji,
    today_tw,
)


def build_seed_items() -> list[dict[str, Any]]:
    today = today_tw()
    base_dt = now_tw().replace(hour=12, minute=0, second=0, microsecond=0)

    def exp(offset_days: int) -> str:
        return (today + timedelta(days=offset_days)).isoformat()

    def created(offset_days: int = -1) -> str:
        return (base_dt + timedelta(days=offset_days)).isoformat(timespec="seconds")

    # 16 樣在冰箱中的食材（ID 1..16）：
    # 食安原則：生鮮肉類、海鮮、乳製品、豆腐最少為今天到期（days_left >= 0）；
    # 唯一已過期（days_left = -1）展示品為「過熟還能烤蛋糕／做甜點」的香蕉。
    in_fridge_items = [
        {
            "name": "香蕉",
            "emoji": "🍌",
            "quantity": 2,
            "unit": "根",
            "expires_on": exp(-1),
            "owner": "阿哲",
            "price": 25,
            "status": "in_fridge",
            "created_at": created(-4),
        },
        {
            "name": "舒肥雞胸肉",
            "emoji": "🍗",
            "quantity": 1,
            "unit": "包",
            "expires_on": exp(0),
            "owner": "阿哲",
            "price": 59,
            "status": "in_fridge",
            "created_at": created(-3),
        },
        {
            "name": "牛奶",
            "emoji": "🥛",
            "quantity": 1,
            "unit": "瓶",
            "expires_on": exp(0),
            "owner": "小明",
            "price": 65,
            "status": "in_fridge",
            "created_at": created(-4),
        },
        {
            "name": "嫩豆腐",
            "emoji": "🧈",
            "quantity": 1,
            "unit": "盒",
            "expires_on": exp(0),
            "owner": "小美",
            "price": 25,
            "status": "in_fridge",
            "created_at": created(-2),
        },
        {
            "name": "雞蛋",
            "emoji": "🥚",
            "quantity": 3,
            "unit": "顆",
            "expires_on": exp(1),
            "owner": "小明",
            "price": 30,
            "status": "in_fridge",
            "created_at": created(-3),
        },
        {
            "name": "白飯",
            "emoji": "🍚",
            "quantity": 2,
            "unit": "碗",
            "expires_on": exp(1),
            "owner": "小美",
            "price": 30,
            "status": "in_fridge",
            "created_at": created(-1),
        },
        {
            "name": "蔥",
            "emoji": "🧅",
            "quantity": 1,
            "unit": "把",
            "expires_on": exp(2),
            "owner": "小明",
            "price": 20,
            "status": "in_fridge",
            "created_at": created(-2),
        },
        {
            "name": "金針菇",
            "emoji": "🍄",
            "quantity": 1,
            "unit": "包",
            "expires_on": exp(2),
            "owner": "小美",
            "price": 25,
            "status": "in_fridge",
            "created_at": created(-2),
        },
        {
            "name": "吐司",
            "emoji": "🍞",
            "quantity": 4,
            "unit": "片",
            "expires_on": exp(2),
            "owner": "阿哲",
            "price": 35,
            "status": "in_fridge",
            "created_at": created(-2),
        },
        {
            "name": "起司片",
            "emoji": "🧀",
            "quantity": 3,
            "unit": "片",
            "expires_on": exp(3),
            "owner": "小美",
            "price": 40,
            "status": "in_fridge",
            "created_at": created(-3),
        },
        {
            "name": "火腿",
            "emoji": "🥓",
            "quantity": 4,
            "unit": "片",
            "expires_on": exp(3),
            "owner": "小明",
            "price": 45,
            "status": "in_fridge",
            "created_at": created(-3),
        },
        {
            "name": "高麗菜",
            "emoji": "🥬",
            "quantity": 1,
            "unit": "顆",
            "expires_on": exp(4),
            "owner": "阿哲",
            "price": 50,
            "status": "in_fridge",
            "created_at": created(-2),
        },
        {
            "name": "番茄",
            "emoji": "🍅",
            "quantity": 2,
            "unit": "顆",
            "expires_on": exp(5),
            "owner": "小美",
            "price": 35,
            "status": "in_fridge",
            "created_at": created(-1),
        },
        {
            "name": "韓式泡菜",
            "emoji": "🌶️",
            "quantity": 1,
            "unit": "罐",
            "expires_on": exp(6),
            "owner": "小明",
            "price": 85,
            "status": "in_fridge",
            "created_at": created(-4),
        },
        {
            "name": "烏龍麵",
            "emoji": "🍜",
            "quantity": 2,
            "unit": "包",
            "expires_on": exp(7),
            "owner": "阿哲",
            "price": 50,
            "status": "in_fridge",
            "created_at": created(-2),
        },
        {
            "name": "冷凍水餃",
            "emoji": "🥟",
            "quantity": 15,
            "unit": "顆",
            "expires_on": exp(10),
            "owner": "小明",
            "price": 75,
            "status": "in_fridge",
            "created_at": created(-5),
        },
    ]

    # 歷史已救援（6 樣，共 NT$245）與已浪費（2 樣）食材
    historical_items = [
        {
            "name": "雞蛋",
            "emoji": "🥚",
            "quantity": 2,
            "unit": "顆",
            "expires_on": exp(-3),
            "owner": "小明",
            "price": 20,
            "status": "rescued",
            "created_at": created(-5),
        },
        {
            "name": "隔夜飯",
            "emoji": "🍚",
            "quantity": 1,
            "unit": "碗",
            "expires_on": exp(-3),
            "owner": "小明",
            "price": 20,
            "status": "rescued",
            "created_at": created(-5),
        },
        {
            "name": "板豆腐",
            "emoji": "🧈",
            "quantity": 1,
            "unit": "盒",
            "expires_on": exp(-2),
            "owner": "小美",
            "price": 25,
            "status": "rescued",
            "created_at": created(-4),
        },
        {
            "name": "韓式泡菜",
            "emoji": "🌶️",
            "quantity": 1,
            "unit": "份",
            "expires_on": exp(-2),
            "owner": "小美",
            "price": 45,
            "status": "rescued",
            "created_at": created(-4),
        },
        {
            "name": "鮮奶",
            "emoji": "🥛",
            "quantity": 1,
            "unit": "瓶",
            "expires_on": exp(-1),
            "owner": "阿哲",
            "price": 65,
            "status": "rescued",
            "created_at": created(-3),
        },
        {
            "name": "厚片吐司",
            "emoji": "🍞",
            "quantity": 3,
            "unit": "片",
            "expires_on": exp(-1),
            "owner": "阿哲",
            "price": 70,
            "status": "rescued",
            "created_at": created(-3),
        },
        {
            "name": "豆漿",
            "emoji": "🥛",
            "quantity": 1,
            "unit": "瓶",
            "expires_on": exp(-4),
            "owner": "小明",
            "price": 32,
            "status": "wasted",
            "created_at": created(-7),
        },
        {
            "name": "小白菜",
            "emoji": "🥬",
            "quantity": 1,
            "unit": "把",
            "expires_on": exp(-2),
            "owner": "阿哲",
            "price": 25,
            "status": "wasted",
            "created_at": created(-6),
        },
    ]

    return in_fridge_items + historical_items


SEED_RECIPES: list[dict[str, Any]] = [
    {
        "title": "電鍋滑嫩蒸蛋",
        "emoji": "🍮",
        "tool": "電鍋",
        "minutes": 15,
        "ingredients": ["雞蛋", "蔥", "醬油"],
        "optional": ["蔥", "醬油"],
        "steps": [
            "雞蛋打散，加入 1.5 倍溫水與少許醬油拌勻",
            "過篩或撈掉表面氣泡，撒上蔥花",
            "電鍋外鍋放半杯水，鍋蓋夾一根筷子留縫，蒸至跳起即可",
        ],
    },
    {
        "title": "電鍋黃金蛋炒飯（炊飯版）",
        "emoji": "🍛",
        "tool": "電鍋",
        "minutes": 20,
        "ingredients": ["白飯", "雞蛋", "火腿", "蔥", "醬油"],
        "optional": ["火腿", "蔥"],
        "steps": [
            "白飯撥散放入內鍋，淋上打散的蛋液與一匙醬油拌勻",
            "鋪上切丁的火腿，外鍋加半杯水按下電鍋",
            "開關跳起後撒上蔥花翻拌，免開火也能粒粒分明",
        ],
    },
    {
        "title": "微波起司牛奶燉飯",
        "emoji": "🧀",
        "tool": "微波爐",
        "minutes": 6,
        "ingredients": ["白飯", "牛奶", "起司片", "火腿"],
        "optional": ["火腿"],
        "steps": [
            "深碗放入白飯，倒入牛奶至淹過白飯約一半高度",
            "鋪上撕碎的火腿與起司片",
            "微波爐中強火加熱 4–5 分鐘至起司融化濃稠，拌勻即可",
        ],
    },
    {
        "title": "電鍋韓式泡菜豆腐鍋",
        "emoji": "🍲",
        "tool": "電鍋",
        "minutes": 20,
        "ingredients": ["嫩豆腐", "韓式泡菜", "金針菇", "雞蛋", "烏龍麵", "蔥"],
        "optional": ["金針菇", "雞蛋", "烏龍麵", "蔥"],
        "steps": [
            "內鍋放入切塊嫩豆腐、韓式泡菜與洗淨的金針菇，加水至七分滿",
            "外鍋加一杯水蒸煮，跳起前 5 分鐘可打入雞蛋或放入烏龍麵",
            "撒上蔥花即可熱騰騰享用",
        ],
    },
    {
        "title": "微波法式吐司布丁",
        "emoji": "🍞",
        "tool": "微波爐",
        "minutes": 5,
        "ingredients": ["吐司", "牛奶", "雞蛋"],
        "optional": [],
        "steps": [
            "雞蛋與牛奶在深碗或大馬克杯中打散拌勻",
            "吐司切成一口大小方塊，浸入蛋奶液吸飽湯汁",
            "微波爐中火加熱 3 分鐘至蛋液凝固、表面蓬鬆柔軟",
        ],
    },
    {
        "title": "微波起司火腿蛋吐司盒",
        "emoji": "🥪",
        "tool": "微波爐",
        "minutes": 4,
        "ingredients": ["吐司", "雞蛋", "起司片", "火腿"],
        "optional": ["火腿"],
        "steps": [
            "吐司中間用湯匙壓出凹槽，鋪上火腿與起司片",
            "在凹槽打入一顆雞蛋，用牙籤在蛋黃戳兩個小洞防爆",
            "微波爐中火加熱 2–3 分鐘至蛋白熟透即可",
        ],
    },
    {
        "title": "電鍋番茄滑蛋雞胸丼",
        "emoji": "🍅",
        "tool": "電鍋",
        "minutes": 20,
        "ingredients": ["番茄", "雞蛋", "舒肥雞胸肉", "白飯", "蔥"],
        "optional": ["舒肥雞胸肉", "白飯", "蔥"],
        "steps": [
            "番茄切塊放入內鍋，外鍋加半杯水先蒸軟出汁",
            "倒入蛋液與手撕舒肥雞胸肉，外鍋再加 1/4 杯水蒸熟",
            "淋在熱白飯上並撒上蔥花",
        ],
    },
    {
        "title": "微波金針菇蒸豆腐",
        "emoji": "🍄",
        "tool": "微波爐",
        "minutes": 6,
        "ingredients": ["嫩豆腐", "金針菇", "蔥", "醬油"],
        "optional": ["蔥", "醬油"],
        "steps": [
            "嫩豆腐切厚片排在深盤底，上面鋪滿洗淨的金針菇",
            "淋上一匙醬油與少許開水，加蓋或覆蓋微波保鮮膜留透氣孔",
            "微波爐強火加熱 5 分鐘，出爐撒上蔥花",
        ],
    },
    {
        "title": "電鍋高麗菜雞胸蒸餃鍋",
        "emoji": "🥟",
        "tool": "電鍋",
        "minutes": 20,
        "ingredients": ["冷凍水餃", "高麗菜", "舒肥雞胸肉", "雞蛋"],
        "optional": ["舒肥雞胸肉", "雞蛋"],
        "steps": [
            "內鍋底鋪滿手撕高麗菜，擺上冷凍水餃（不需退冰）",
            "淋上半碗水並放上切片舒肥雞胸肉，外鍋加一杯水",
            "跳起後高麗菜清甜、水餃Q彈不破皮",
        ],
    },
    {
        "title": "微波泡菜起司烏龍麵",
        "emoji": "🍜",
        "tool": "微波爐",
        "minutes": 7,
        "ingredients": ["烏龍麵", "韓式泡菜", "起司片", "雞蛋", "蔥"],
        "optional": ["起司片", "雞蛋", "蔥"],
        "steps": [
            "深碗放入烏龍麵、韓式泡菜與半碗熱水，微波 4 分鐘後拌開",
            "打入雞蛋（蛋黃戳洞）並鋪上起司片，再微波 2 分鐘",
            "撒上蔥花拌勻即可享用",
        ],
    },
    {
        "title": "電鍋牛奶高麗菜雞肉湯麵",
        "emoji": "🥣",
        "tool": "電鍋",
        "minutes": 20,
        "ingredients": ["牛奶", "高麗菜", "舒肥雞胸肉", "烏龍麵", "金針菇"],
        "optional": ["舒肥雞胸肉", "烏龍麵", "金針菇"],
        "steps": [
            "內鍋放入高麗菜、金針菇、烏龍麵與半碗水，外鍋一杯水蒸煮",
            "開關跳起後倒入牛奶與切片雞胸肉，利用餘溫悶 5 分鐘",
            "湯頭濃郁不油膩，適合宵夜暖胃",
        ],
    },
    {
        "title": "微波起司蒸餃佐泡菜",
        "emoji": "🥟",
        "tool": "微波爐",
        "minutes": 8,
        "ingredients": ["冷凍水餃", "起司片", "韓式泡菜"],
        "optional": ["韓式泡菜"],
        "steps": [
            "冷凍水餃放入深盤，加半碗熱水並加蓋，微波強火 5 分鐘至熟",
            "倒掉多餘水分，鋪上泡菜與起司片再微波 1 分鐘至起司融化",
            "免開火也能做出韓式牽絲煎餃風味",
        ],
    },
    {
        "title": "電鍋番茄蔬菜豆腐湯餃",
        "emoji": "🍅",
        "tool": "電鍋",
        "minutes": 25,
        "ingredients": ["番茄", "嫩豆腐", "高麗菜", "金針菇", "冷凍水餃", "蔥"],
        "optional": ["金針菇", "冷凍水餃", "蔥"],
        "steps": [
            "番茄切塊、嫩豆腐切丁、高麗菜撥片放入內鍋，可依食量加幾顆水餃",
            "加入兩碗水，外鍋一杯水按下電鍋",
            "跳起後撒上蔥花，清爽又有飽足感",
        ],
    },
    {
        "title": "微波手撕雞胸蔥油拌飯",
        "emoji": "🍗",
        "tool": "微波爐",
        "minutes": 4,
        "ingredients": ["舒肥雞胸肉", "白飯", "蔥", "雞蛋", "醬油"],
        "optional": ["蔥", "雞蛋", "醬油"],
        "steps": [
            "白飯與手撕舒肥雞胸肉放入深碗中",
            "淋上一匙醬油並撒上蔥花，加蓋微波 2 分鐘",
            "可搭配一顆微波水波蛋拌勻享用",
        ],
    },
    {
        "title": "電鍋火腿起司高麗菜炊飯",
        "emoji": "🍚",
        "tool": "電鍋",
        "minutes": 25,
        "ingredients": ["白飯", "火腿", "高麗菜", "起司片"],
        "optional": ["起司片"],
        "steps": [
            "白飯鋪底，放上切碎的高麗菜與火腿丁，加兩匙水",
            "電鍋外鍋半杯水蒸煮，讓高麗菜甜味滲入米飯",
            "跳起後趁熱鋪上起司片悶 2 分鐘拌勻",
        ],
    },
    {
        "title": "微波番茄起司吐司披薩",
        "emoji": "🍕",
        "tool": "微波爐",
        "minutes": 4,
        "ingredients": ["吐司", "番茄", "起司片", "火腿", "舒肥雞胸肉"],
        "optional": ["火腿", "舒肥雞胸肉"],
        "steps": [
            "番茄切薄片鋪在吐司上，放上火腿丁或雞胸肉絲",
            "最上層鋪滿起司片",
            "微波爐中強火加熱 2–3 分鐘至起司融化牽絲即可",
        ],
    },
    {
        "title": "微波香蕉牛奶馬克杯蛋糕",
        "emoji": "🍌",
        "tool": "微波爐",
        "minutes": 5,
        "ingredients": ["香蕉", "牛奶", "雞蛋", "吐司"],
        "optional": ["吐司"],
        "steps": [
            "過熟香蕉在馬克杯中用叉子壓成泥（越熟越甜，不用另外加糖）",
            "打入雞蛋與牛奶攪拌均勻，可撕入半片吐司增加蛋糕體口感",
            "微波爐中強火加熱 2–3 分鐘至表面澎起熟透即可享用",
        ],
    },
    {
        "title": "電鍋焦糖香蕉布丁吐司",
        "emoji": "🍮",
        "tool": "電鍋",
        "minutes": 15,
        "ingredients": ["香蕉", "吐司", "牛奶", "雞蛋"],
        "optional": [],
        "steps": [
            "吐司切丁鋪在深碗底，擺上切片的熟香蕉",
            "雞蛋與牛奶打勻過篩後倒入碗中，讓吐司吸飽蛋奶液",
            "電鍋外鍋加半杯水蒸至跳起，香蕉果香濃郁、口感綿密",
        ],
    },
    {
        "title": "微波溫熱香蕉蛋奶盅",
        "emoji": "🥣",
        "tool": "微波爐",
        "minutes": 4,
        "ingredients": ["香蕉", "牛奶", "雞蛋", "燕麥"],
        "optional": ["雞蛋", "燕麥"],
        "steps": [
            "熟香蕉切厚片放入深碗，倒入牛奶（可依喜好加燕麥或一顆打散的雞蛋）",
            "微波爐中火分兩段加熱共 3 分鐘，中間取出攪拌一次",
            "香蕉的自然甜味融入熱牛奶，適合當宿舍早餐或宵夜",
        ],
    },
]


def seed_database(conn: sqlite3.Connection) -> None:
    init_schema(conn)
    cur = conn.cursor()

    items_data = build_seed_items()
    for item in items_data:
        cur.execute(
            """
            INSERT INTO items (name, emoji, quantity, unit, expires_on, owner, price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["name"],
                item["emoji"] or resolve_emoji(item["name"]),
                item["quantity"],
                item["unit"],
                item["expires_on"],
                item["owner"],
                item["price"],
                item["status"],
                item["created_at"],
            ),
        )

    for rec in SEED_RECIPES:
        cur.execute(
            """
            INSERT INTO recipes (title, emoji, tool, minutes, ingredients, optional, steps)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec["title"],
                rec["emoji"],
                rec["tool"],
                rec["minutes"],
                json.dumps(rec["ingredients"], ensure_ascii=False),
                json.dumps(rec["optional"], ensure_ascii=False),
                json.dumps(rec["steps"], ensure_ascii=False),
            ),
        )

    base_dt = now_tw().replace(hour=19, minute=30, second=0, microsecond=0)
    seed_rescues = [
        {
            "item_ids": [17, 18],
            "item_names": ["雞蛋", "隔夜飯"],
            "recipe_id": 2,
            "recipe_title": "電鍋黃金蛋炒飯（炊飯版）",
            "action": "cooked",
            "saved_ntd": 40,
            "created_at": (base_dt - timedelta(days=3)).isoformat(timespec="seconds"),
        },
        {
            "item_ids": [19, 20],
            "item_names": ["板豆腐", "韓式泡菜"],
            "recipe_id": 4,
            "recipe_title": "電鍋韓式泡菜豆腐鍋",
            "action": "cooked",
            "saved_ntd": 70,
            "created_at": (base_dt - timedelta(days=2)).isoformat(timespec="seconds"),
        },
        {
            "item_ids": [21],
            "item_names": ["鮮奶"],
            "recipe_id": 3,
            "recipe_title": "微波起司牛奶燉飯",
            "action": "cooked",
            "saved_ntd": 65,
            "created_at": (base_dt - timedelta(days=1, hours=4)).isoformat(timespec="seconds"),
        },
        {
            "item_ids": [22],
            "item_names": ["厚片吐司"],
            "recipe_id": 5,
            "recipe_title": "微波法式吐司布丁",
            "action": "cooked",
            "saved_ntd": 70,
            "created_at": (base_dt - timedelta(days=1)).isoformat(timespec="seconds"),
        },
    ]

    for r in seed_rescues:
        cur.execute(
            """
            INSERT INTO rescues (item_ids, item_names, recipe_id, recipe_title, action, saved_ntd, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps(r["item_ids"]),
                json.dumps(r["item_names"], ensure_ascii=False),
                r["recipe_id"],
                r["recipe_title"],
                r["action"],
                r["saved_ntd"],
                r["created_at"],
            ),
        )

    conn.commit()


def ensure_seeded(conn: sqlite3.Connection | None = None) -> None:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        init_schema(conn)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM items")
        item_cnt = int(cur.fetchone()["cnt"])
        cur.execute("SELECT COUNT(*) AS cnt FROM recipes")
        recipe_cnt = int(cur.fetchone()["cnt"])
        if item_cnt == 0 and recipe_cnt == 0:
            seed_database(conn)
    finally:
        if close_after:
            conn.close()


def reset_and_seed(conn: sqlite3.Connection | None = None) -> None:
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True
    try:
        init_schema(conn)
        conn.executescript(
            """
            DELETE FROM rescues;
            DELETE FROM items;
            DELETE FROM recipes;
            DELETE FROM sqlite_sequence WHERE name IN ('items', 'recipes', 'rescues');
            """
        )
        conn.commit()
        seed_database(conn)
    finally:
        if close_after:
            conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="冰箱第二春 資料庫種子工具")
    parser.add_argument("--reset", action="store_true", help="清空並重新載入種子資料")
    args = parser.parse_args()

    if args.reset:
        reset_and_seed()
        print("已重置資料庫並寫入最新種子資料（16 樣在庫食材、19 道宿舍食譜、4 筆歷史救援紀錄）。")
    else:
        ensure_seeded()
        print("已確認資料庫種子資料就緒。")


if __name__ == "__main__":
    main()
