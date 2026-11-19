"""規則式食譜推薦引擎（含食材別名正規化、also_in_fridge 比對、食安過濾與到期優先計分）。"""

from __future__ import annotations

from typing import Any

ALIAS_GROUPS: dict[str, list[str]] = {
    "雞蛋": ["雞蛋", "蛋", "水煮蛋", "溏心蛋", "雞蛋液", "鮮蛋", "土雞蛋", "荷包蛋", "滷蛋"],
    "白飯": ["白飯", "剩飯", "隔夜飯", "飯", "米飯", "白米飯", "熟飯", "糙米飯", "紫米飯"],
    "牛奶": ["牛奶", "鮮奶", "鮮乳", "保久乳", "全脂牛奶", "低脂牛奶", "牛乳"],
    "嫩豆腐": ["嫩豆腐", "豆腐", "板豆腐", "百頁豆腐", "雞蛋豆腐", "傳統豆腐", "盒裝豆腐", "凍豆腐"],
    "舒肥雞胸肉": ["舒肥雞胸肉", "舒肥雞胸", "雞胸肉", "雞胸", "雞肉", "雞腿肉", "雞肉絲", "雞柳", "雞腿"],
    "蔥": ["蔥", "青蔥", "蔥花", "蔥段", "珠蔥", "三星蔥"],
    "金針菇": ["金針菇", "香菇", "鴻喜菇", "杏鮑菇", "秀珍菇", "菇", "舞菇", "雪白菇"],
    "吐司": ["吐司", "白吐司", "全麥吐司", "厚片吐司", "麵包", "餐包", "貝果"],
    "起司片": ["起司片", "起司", "起司絲", "乳酪", "乳酪絲", "芝士", "焗烤起司", "莫札瑞拉"],
    "火腿": ["火腿", "火腿片", "培根", "熱狗", "香腸", "德式香腸", "午餐肉"],
    "高麗菜": ["高麗菜", "青菜", "小白菜", "青江菜", "娃娃菜", "菠菜", "大陸妹", "空心菜", "地瓜葉"],
    "番茄": ["番茄", "牛番茄", "小番茄", "聖女番茄", "蕃茄"],
    "韓式泡菜": ["韓式泡菜", "泡菜", "辣泡菜", "黃金泡菜"],
    "烏龍麵": ["烏龍麵", "泡麵", "王子麵", "科學麵", "麵條", "意麵", "拉麵", "冬粉", "寬粉", "關廟麵", "麵"],
    "冷凍水餃": ["冷凍水餃", "水餃", "熟水餃", "煎餃", "餛飩", "雲吞", "蒸餃"],
    "香蕉": ["香蕉", "熟香蕉", "芭蕉"],
    "燕麥": ["燕麥", "燕麥片", "即食燕麥", "麥片"],
    "醬油": ["醬油", "醬油膏", "薄鹽醬油"],
    "豬肉": ["豬肉", "豬肉片", "梅花豬", "五花肉", "絞肉", "肉片"],
    "牛肉": ["牛肉", "牛肉片", "牛五花", "牛絞肉"],
    "海鮮": ["海鮮", "蝦", "蝦仁", "魚", "魚片", "鮭魚", "鯛魚", "蛤蜊", "透抽", "小卷", "花枝"],
    "玉米": ["玉米", "玉米粒", "玉米罐頭", "玉米筍"],
    "馬鈴薯": ["馬鈴薯", "洋芋", "地瓜", "番薯"],
}

ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in ALIAS_GROUPS.items():
    ALIAS_TO_CANONICAL[canonical] = canonical
    for alias in aliases:
        ALIAS_TO_CANONICAL[alias] = canonical

# 食安高風險類別：肉類、海鮮、乳製品、豆腐（days_left < 0 時不可推薦，不列入 uses 與 also_in_fridge）
HIGH_RISK_CANONICALS: set[str] = {
    "舒肥雞胸肉",
    "豬肉",
    "牛肉",
    "火腿",
    "海鮮",
    "牛奶",
    "起司片",
    "嫩豆腐",
}

HIGH_RISK_KEYWORDS: tuple[str, ...] = (
    "雞肉",
    "雞胸",
    "雞腿",
    "豬",
    "牛",
    "羊",
    "鴨",
    "鵝",
    "肉",
    "火腿",
    "培根",
    "香腸",
    "熱狗",
    "魚",
    "蝦",
    "蛤",
    "蚵",
    "蟹",
    "海鮮",
    "透抽",
    "花枝",
    "小卷",
    "牛奶",
    "鮮奶",
    "鮮乳",
    "牛乳",
    "優格",
    "優酪乳",
    "起司",
    "乳酪",
    "芝士",
    "鮮奶油",
    "豆腐",
    "豆花",
    "豆漿",
)


def normalize_ingredient(name: str) -> str:
    clean = (name or "").strip()
    if not clean:
        return ""
    if clean in ALIAS_TO_CANONICAL:
        return ALIAS_TO_CANONICAL[clean]
    for alias, canonical in sorted(ALIAS_TO_CANONICAL.items(), key=lambda x: len(x[0]), reverse=True):
        if len(alias) >= 2 and (alias in clean or clean in alias):
            return canonical
    return clean


def is_high_risk_perishable(name: str) -> bool:
    clean = (name or "").strip()
    if not clean:
        return False
    # 「雞蛋豆腐」含「豆腐」，屬於豆腐類；純「雞蛋／蛋」非此四類
    can = normalize_ingredient(clean)
    if can in HIGH_RISK_CANONICALS:
        return True
    return any(kw in clean for kw in HIGH_RISK_KEYWORDS)


def is_expired_unsafe(item: dict[str, Any]) -> bool:
    return int(item.get("days_left", 0)) < 0 and is_high_risk_perishable(str(item.get("name", "")))


def ingredients_match(name_a: str, name_b: str) -> bool:
    can_a = normalize_ingredient(name_a)
    can_b = normalize_ingredient(name_b)
    if not can_a or not can_b:
        return False
    if can_a == can_b:
        return True
    if len(can_a) >= 2 and len(can_b) >= 2 and (can_a in can_b or can_b in can_a):
        return True
    return False


def _format_urgency_note(item: dict[str, Any], recipe: dict[str, Any]) -> str:
    days_left = int(item.get("days_left", 99))
    name = item.get("name", "食材")
    if days_left < 0:
        return f"其中{name}已過期 {abs(days_left)} 天（已過期，請先確認外觀氣味再使用）"
    if days_left == 0:
        return f"其中{name}今天到期"
    if days_left == 1:
        return f"其中{name}明天到期"
    if days_left <= 3:
        return f"其中{name}剩 {days_left} 天到期"
    return f"只用{recipe['tool']} {recipe['minutes']} 分鐘即可完成"


def recommend_by_rules(
    selected_items: list[dict[str, Any]],
    all_fridge_items: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    # 食安過濾：days_left < 0 的肉類、海鮮、乳製品、豆腐不參與推薦（不列入 uses 與 also_in_fridge）
    safe_selected_items = [it for it in selected_items if not is_expired_unsafe(it)]
    if not safe_selected_items:
        return []

    selected_ids = {int(it["id"]) for it in selected_items}
    other_fridge_items = [
        it
        for it in all_fridge_items
        if int(it["id"]) not in selected_ids
        and it.get("status") == "in_fridge"
        and not is_expired_unsafe(it)
    ]

    scored_results: list[tuple[tuple[int, int, int, int], dict[str, Any]]] = []
    used_recipe_ids: set[int] = set()

    for recipe in recipes:
        recipe_ings = list(recipe.get("ingredients", []))
        optional_ings = list(recipe.get("optional", []))

        matched_selected: list[dict[str, Any]] = []
        uses: list[str] = []
        uses_item_ids: list[int] = []

        for s_item in safe_selected_items:
            if any(ingredients_match(s_item["name"], r_ing) for r_ing in recipe_ings):
                matched_selected.append(s_item)
                uses_item_ids.append(int(s_item["id"]))
                if s_item["name"] not in uses:
                    uses.append(s_item["name"])

        if not matched_selected:
            continue

        also_in_fridge: list[dict[str, Any]] = []
        also_in_fridge_ids: set[int] = set()
        missing: list[str] = []
        matched_other_expiring: list[dict[str, Any]] = []

        for r_ing in recipe_ings:
            if any(ingredients_match(s_item["name"], r_ing) for s_item in matched_selected):
                continue

            other_matches = [
                o_item for o_item in other_fridge_items if ingredients_match(o_item["name"], r_ing)
            ]
            if other_matches:
                for o_item in other_matches:
                    oid = int(o_item["id"])
                    if oid not in also_in_fridge_ids:
                        also_in_fridge.append(
                            {
                                "id": oid,
                                "name": str(o_item["name"]),
                                "days_left": int(o_item["days_left"]),
                            }
                        )
                        also_in_fridge_ids.add(oid)
                    if int(o_item.get("days_left", 99)) <= 3 and o_item not in matched_other_expiring:
                        matched_other_expiring.append(o_item)
                continue

            is_optional = any(ingredients_match(opt, r_ing) for opt in optional_ings)
            if not is_optional:
                missing.append(r_ing)

        raw_score = 27 + 30 * len(matched_selected)
        for s_item in matched_selected:
            d_left = int(s_item.get("days_left", 99))
            if d_left <= 1:
                raw_score += 10
            elif d_left <= 3:
                raw_score += 5

        raw_score -= 15 * len(missing)
        raw_score += 5 * len(matched_other_expiring)
        score = max(0, min(100, raw_score))

        sorted_matched = sorted(matched_selected, key=lambda x: int(x.get("days_left", 99)))
        most_urgent = sorted_matched[0]
        urgency_note = _format_urgency_note(most_urgent, recipe)

        has_expiring_selected = any(int(x.get("days_left", 99)) <= 3 for x in matched_selected)
        if has_expiring_selected:
            reason = f"用掉 {len(matched_selected)} 樣快過期食材，{urgency_note}"
        else:
            reason = f"用掉 {len(matched_selected)} 樣勾選食材，{urgency_note}"

        if matched_other_expiring:
            extra_names = "、".join(it["name"] for it in matched_other_expiring[:2])
            reason += f"（還能順便用掉冰箱裡的{extra_names}）"

        has_expired_used = any(int(x.get("days_left", 0)) < 0 for x in matched_selected) or any(
            int(x.get("days_left", 0)) < 0 for x in also_in_fridge
        )
        if has_expired_used and "已過期，請先確認外觀氣味再使用" not in reason:
            reason += "（已過期，請先確認外觀氣味再使用）"

        entry = {
            "recipe": recipe,
            "uses": uses,
            "uses_item_ids": uses_item_ids,
            "also_in_fridge": also_in_fridge,
            "missing": missing,
            "score": score,
            "reason": reason,
        }
        sort_key = (
            score,
            len(matched_selected),
            -len(missing),
            -int(recipe.get("minutes", 30)),
        )
        scored_results.append((sort_key, entry))
        used_recipe_ids.add(int(recipe["id"]))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    top_entries = [item[1] for item in scored_results[:limit]]

    if len(top_entries) < 3 and safe_selected_items:
        fallback_titles = [
            "電鍋韓式泡菜豆腐鍋",
            "電鍋番茄蔬菜豆腐湯餃",
            "微波泡菜起司烏龍麵",
            "電鍋黃金蛋炒飯（炊飯版）",
        ]
        primary_item = sorted(safe_selected_items, key=lambda x: int(x.get("days_left", 99)))[0]
        for recipe in recipes:
            if len(top_entries) >= 3:
                break
            if int(recipe["id"]) in used_recipe_ids:
                continue
            if recipe["title"] not in fallback_titles and len(recipes) >= 3:
                continue

            fb_also: list[dict[str, Any]] = []
            fb_also_ids: set[int] = set()
            for r_ing in recipe.get("ingredients", []):
                for o_item in other_fridge_items:
                    oid = int(o_item["id"])
                    if oid not in fb_also_ids and ingredients_match(o_item["name"], r_ing):
                        fb_also.append(
                            {
                                "id": oid,
                                "name": str(o_item["name"]),
                                "days_left": int(o_item["days_left"]),
                            }
                        )
                        fb_also_ids.add(oid)

            urgency_note = _format_urgency_note(primary_item, recipe)
            fb_reason = f"百搭宿舍{recipe['tool']}料理，可加入{primary_item['name']}一起烹調（{urgency_note}）"
            if (
                int(primary_item.get("days_left", 0)) < 0
                or any(int(x.get("days_left", 0)) < 0 for x in fb_also)
            ) and "已過期，請先確認外觀氣味再使用" not in fb_reason:
                fb_reason += "（已過期，請先確認外觀氣味再使用）"

            top_entries.append(
                {
                    "recipe": recipe,
                    "uses": [primary_item["name"]],
                    "uses_item_ids": [int(primary_item["id"])],
                    "also_in_fridge": fb_also,
                    "missing": [],
                    "score": max(55, 65 - len(top_entries) * 5),
                    "reason": fb_reason,
                }
            )
            used_recipe_ids.add(int(recipe["id"]))

    return top_entries[:limit]
