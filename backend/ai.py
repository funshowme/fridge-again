"""選做：線上 AI 食譜推薦（只從環境變數讀取金鑰，沒網路或失敗時自動退回規則式，並強制套用食安規則）。"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from backend.recommend import ingredients_match, is_expired_unsafe


def get_ai_token() -> str:
    for env_var in ("AI_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val
    return ""


def is_ai_configured() -> bool:
    return bool(get_ai_token())


def _normalize_ai_entries(
    entries: list[dict[str, Any]],
    safe_selected_items: list[dict[str, Any]],
    all_fridge_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected_ids = {int(it["id"]) for it in safe_selected_items}
    other_fridge_items = [
        it
        for it in all_fridge_items
        if int(it["id"]) not in selected_ids
        and it.get("status") == "in_fridge"
        and not is_expired_unsafe(it)
    ]
    normalized: list[dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("recipe"), dict):
            continue
        recipe = item["recipe"]
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
        also_ids: set[int] = set()
        missing: list[str] = []

        for r_ing in recipe_ings:
            if any(ingredients_match(s["name"], r_ing) for s in matched_selected):
                continue
            other_matches = [
                o for o in other_fridge_items if ingredients_match(o["name"], r_ing)
            ]
            if other_matches:
                for o in other_matches:
                    oid = int(o["id"])
                    if oid not in also_ids:
                        also_in_fridge.append(
                            {
                                "id": oid,
                                "name": str(o["name"]),
                                "days_left": int(o["days_left"]),
                            }
                        )
                        also_ids.add(oid)
                continue
            if not any(ingredients_match(opt, r_ing) for opt in optional_ings):
                missing.append(r_ing)

        reason = str(item.get("reason", "")).strip()
        has_expired_used = any(int(x.get("days_left", 0)) < 0 for x in matched_selected) or any(
            int(x.get("days_left", 0)) < 0 for x in also_in_fridge
        )
        if has_expired_used and "已過期，請先確認外觀氣味再使用" not in reason:
            reason = f"{reason}（已過期，請先確認外觀氣味再使用）" if reason else "已過期，請先確認外觀氣味再使用"

        item["uses"] = uses
        item["uses_item_ids"] = uses_item_ids
        item["also_in_fridge"] = also_in_fridge
        item["missing"] = missing
        item["reason"] = reason
        normalized.append(item)
    return normalized


def try_ai_recommend(
    selected_items: list[dict[str, Any]],
    all_fridge_items: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    """嘗試呼叫外部 AI 產生或排序推薦；若無金鑰、沙箱無網路或格式異常，回傳 None 由規則式接手。"""
    token = get_ai_token()
    if not token:
        return None

    safe_selected_items = [it for it in selected_items if not is_expired_unsafe(it)]
    if not safe_selected_items:
        return []

    endpoint = os.environ.get(
        "AI_BASE_URL", "https://api.openai.com/v1/chat/completions"
    ).strip()
    model_name = os.environ.get("AI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

    selected_summary = [
        {
            "id": int(it["id"]),
            "name": it["name"],
            "days_left": int(it["days_left"]),
        }
        for it in safe_selected_items
    ]
    fridge_summary = [
        {"id": int(it["id"]), "name": it["name"], "days_left": int(it["days_left"])}
        for it in all_fridge_items
        if it.get("status") == "in_fridge" and not is_expired_unsafe(it)
    ]

    prompt = (
        "你是宿舍料理助手。請根據勾選食材與冰箱現有食材，從候選食譜挑選最適合的 3 到 5 道"
        "只用電鍋或微波爐的料理，回傳 JSON 陣列（每筆含 recipe, uses, uses_item_ids, "
        "also_in_fridge: [{id, name, days_left}], missing, score, reason）。"
        "若使用到 days_left < 0 的食材，reason 必須加上「已過期，請先確認外觀氣味再使用」。"
        f"\n勾選食材: {json.dumps(selected_summary, ensure_ascii=False)}"
        f"\n冰箱食材: {json.dumps(fridge_summary, ensure_ascii=False)}"
        f"\n候選食譜: {json.dumps(recipes, ensure_ascii=False)}"
    )

    payload = json.dumps(
        {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "只回傳合法 JSON，不要加 Markdown。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if isinstance(parsed, list) and 3 <= len(parsed) <= 5:
            normalized = _normalize_ai_entries(parsed, safe_selected_items, all_fridge_items)
            if 3 <= len(normalized) <= 5:
                return normalized
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError, OSError):
        return None

    return None
