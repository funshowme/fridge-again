"""後端 API 自動測試（照 docs/API.md v1.1）。只用標準庫，不需安裝 pytest。
執行：python tests/test_api.py   （會自己啟動 Flask，測完自動 seed --reset）
可用環境變數 TEST_PORT 改埠號（預設 8765）。
"""
import json
import os
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("TEST_PORT", "8765"))
BASE = f"http://127.0.0.1:{PORT}"
proc = None


def call(method, path, body=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, txt


def reset():
    subprocess.run([sys.executable, "-m", "backend.seed", "--reset"], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def setUpModule():
    global proc
    reset()
    env = dict(os.environ, PORT=str(PORT))
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AI_API_KEY"):
        env.pop(k, None)
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            call("GET", "/api/health")
            return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("Flask 沒有啟動")


def tearDownModule():
    if proc:
        proc.terminate()
        try:
            proc.wait(5)
        except Exception:
            proc.kill()
    reset()


def assert_err(tc, res, code, http):
    st, b = res
    tc.assertEqual(st, http, b)
    tc.assertIsInstance(b, dict)
    tc.assertEqual(set(b.keys()), {"error"}, b)
    tc.assertEqual(b["error"]["code"], code)
    tc.assertTrue(b["error"]["message"])


ITEM_KEYS = {"id", "name", "emoji", "quantity", "unit", "expires_on", "days_left",
             "urgency", "owner", "price", "status", "created_at"}


class T(unittest.TestCase):
    def setUp(self):
        reset()

    def _pick(self, n):
        return [i["id"] for i in call("GET", "/api/items")[1]["items"][:n]]

    def test_01_health(self):
        st, b = call("GET", "/api/health")
        self.assertEqual(st, 200)
        self.assertIs(b["ok"], True)
        self.assertIn(b["ai"], ("offline", "online"))

    def test_02_items_list(self):
        st, b = call("GET", "/api/items")
        self.assertEqual(st, 200)
        items = b["items"]
        self.assertGreaterEqual(len(items), 12)
        for it in items:
            self.assertTrue(ITEM_KEYS <= set(it), set(it) ^ ITEM_KEYS)
            self.assertEqual(it["status"], "in_fridge")
            d = it["days_left"]
            exp = (date.fromisoformat(it["expires_on"]) - date.today()).days
            self.assertLessEqual(abs(d - exp), 1)
            self.assertEqual(it["urgency"], "red" if d <= 1 else "yellow" if d <= 3 else "green")
        self.assertEqual([i["expires_on"] for i in items], sorted(i["expires_on"] for i in items))
        self.assertEqual({i["urgency"] for i in items}, {"red", "yellow", "green"})
        st, b = call("GET", "/api/items?status=rescued")
        self.assertEqual(st, 200)
        self.assertTrue(all(i["status"] == "rescued" for i in b["items"]))
        assert_err(self, call("GET", "/api/items?status=bogus"), "BAD_REQUEST", 400)

    def test_03_items_create(self):
        exp = (date.today() + timedelta(days=5)).isoformat()
        st, b = call("POST", "/api/items", {"name": "豆腐", "quantity": 1, "unit": "盒",
                                             "expires_on": exp, "owner": "小美", "price": 25})
        self.assertEqual(st, 201, b)
        it = b["item"]
        self.assertTrue(ITEM_KEYS <= set(it))
        self.assertEqual((it["name"], it["unit"], it["owner"], it["price"], it["status"]),
                         ("豆腐", "盒", "小美", 25, "in_fridge"))
        st, b = call("POST", "/api/items", {"name": "神秘食材XYZ", "expires_on": exp})
        self.assertEqual(st, 201)
        it = b["item"]
        self.assertEqual((it["quantity"], it["unit"], it["owner"], it["price"], it["emoji"]),
                         (1, "個", "", 0, "🥫"))
        assert_err(self, call("POST", "/api/items", {"expires_on": exp}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/items", {"name": "x"}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/items", {"name": "x", "expires_on": "2026/12/01"}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/items", raw=b"not json"), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/items", {"name": "x", "expires_on": exp, "price": -5}), "BAD_REQUEST", 400)

    def test_04_items_patch(self):
        iid = self._pick(1)[0]
        st, b = call("PATCH", f"/api/items/{iid}", {"status": "wasted"})
        self.assertEqual(st, 200)
        self.assertEqual(b["item"]["status"], "wasted")
        self.assertNotIn(iid, self._pick(100))
        assert_err(self, call("PATCH", "/api/items/999999", {"status": "wasted"}), "NOT_FOUND", 404)
        assert_err(self, call("PATCH", f"/api/items/{iid}", {"status": "nope"}), "BAD_REQUEST", 400)

    def test_05_items_delete(self):
        exp = (date.today() + timedelta(days=5)).isoformat()
        before = call("GET", "/api/stats")[1]
        iid = call("POST", "/api/items", {"name": "輸錯", "expires_on": exp})[1]["item"]["id"]
        self.assertEqual(call("DELETE", f"/api/items/{iid}"), (200, {"ok": True}))
        self.assertEqual(call("GET", "/api/stats")[1], before)
        assert_err(self, call("DELETE", f"/api/items/{iid}"), "NOT_FOUND", 404)

    def test_06_suggestions(self):
        ids = self._pick(2)
        st, b = call("POST", "/api/suggestions", {"item_ids": ids})
        self.assertEqual(st, 200, b)
        self.assertIn(b["source"], ("rules", "ai"))
        rs = b["recipes"]
        self.assertTrue(3 <= len(rs) <= 5, len(rs))
        scores = [r["score"] for r in rs]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for r in rs:
            for k in ("recipe", "uses", "uses_item_ids", "also_in_fridge", "missing", "score", "reason"):
                self.assertIn(k, r)
            self.assertTrue(0 <= r["score"] <= 100)
            self.assertIn(r["recipe"]["tool"], ("電鍋", "微波爐"))
            self.assertTrue(set(r["uses_item_ids"]) & set(ids), "至少用到 1 個勾選食材")
            self.assertTrue(r["reason"])
            for a in r["also_in_fridge"]:
                self.assertTrue({"id", "name", "days_left"} <= set(a))
                self.assertNotIn(a["id"], ids)
        self.assertEqual(call("POST", "/api/suggestions", {"item_ids": self._pick(5)})[0], 200)
        assert_err(self, call("POST", "/api/suggestions", {"item_ids": []}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/suggestions", {"item_ids": list(range(1, 7))}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/suggestions", {}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/suggestions", {"item_ids": ["a"]}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/suggestions", {"item_ids": [999999]}), "NOT_FOUND", 404)

    def test_07_missing_not_in_fridge(self):
        """v1.1：missing 不可含冰箱（in_fridge）已有的食材名稱。"""
        items = call("GET", "/api/items")[1]["items"]
        fridge_names = {i["name"] for i in items}
        for it in items[:6]:
            rs = call("POST", "/api/suggestions", {"item_ids": [it["id"]]})[1]["recipes"]
            for r in rs:
                for m in r["missing"]:
                    self.assertNotIn(m, fridge_names,
                                     f"勾 {it['name']} → {r['recipe']['title']} 的 missing 含冰箱已有的 {m}")
                for m in r["missing"]:
                    self.assertNotIn(m, {a["name"] for a in r["also_in_fridge"]})

    def test_08_rescues(self):
        before = call("GET", "/api/stats")[1]
        ids = self._pick(2)
        prices = {i["id"]: i["price"] for i in call("GET", "/api/items")[1]["items"]}
        rid = call("POST", "/api/suggestions", {"item_ids": ids})[1]["recipes"][0]["recipe"]["id"]
        st, b = call("POST", "/api/rescues", {"item_ids": ids, "recipe_id": rid, "action": "cooked"})
        self.assertEqual(st, 201, b)
        r = b["rescue"]
        self.assertEqual((r["item_ids"], r["recipe_id"], r["action"]), (ids, rid, "cooked"))
        self.assertEqual(r["saved_ntd"], sum(prices[i] for i in ids))
        s = b["stats"]
        self.assertEqual(s["rescued_count"], before["rescued_count"] + 2)
        self.assertEqual(s["saved_ntd"], before["saved_ntd"] + r["saved_ntd"])
        left = self._pick(100)
        for i in ids:
            self.assertNotIn(i, left)
        self.assertEqual(call("GET", "/api/stats")[1], s)
        self.assertLessEqual(len(s["recent"]), 5)
        self.assertEqual(s["recent"][0]["id"], r["id"])
        assert_err(self, call("POST", "/api/rescues", {"item_ids": [], "recipe_id": rid, "action": "cooked"}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/rescues", {"item_ids": self._pick(1), "recipe_id": rid, "action": "x"}), "BAD_REQUEST", 400)
        assert_err(self, call("POST", "/api/rescues", {"item_ids": [999999], "recipe_id": rid, "action": "cooked"}), "NOT_FOUND", 404)
        assert_err(self, call("POST", "/api/rescues", {"item_ids": self._pick(1), "recipe_id": 999999, "action": "cooked"}), "NOT_FOUND", 404)

    def test_08b_rescues_shared(self):
        st, b = call("POST", "/api/rescues", {"item_ids": self._pick(1), "action": "shared"})
        self.assertEqual(st, 201, b)
        self.assertEqual(b["rescue"]["action"], "shared")

    def test_09_stats(self):
        st, s = call("GET", "/api/stats")
        self.assertEqual(st, 200)
        for k in ("rescued_count", "saved_ntd", "wasted_count", "rescue_rate", "recent"):
            self.assertIn(k, s)
        self.assertGreater(s["rescued_count"], 0)
        tot = s["rescued_count"] + s["wasted_count"]
        self.assertAlmostEqual(s["rescue_rate"], s["rescued_count"] / tot if tot else 0, places=2)
        self.assertLessEqual(len(s["recent"]), 5)
        for r in s["recent"]:
            self.assertTrue({"id", "recipe_title", "item_names", "created_at"} <= set(r))

    def test_10_recipe_detail(self):
        rid = call("POST", "/api/suggestions", {"item_ids": self._pick(1)})[1]["recipes"][0]["recipe"]["id"]
        st, b = call("GET", f"/api/recipes/{rid}")
        self.assertEqual(st, 200)
        for k in ("id", "title", "emoji", "tool", "minutes", "ingredients", "optional", "steps"):
            self.assertIn(k, b["recipe"])
        self.assertIn(b["recipe"]["tool"], ("電鍋", "微波爐"))
        assert_err(self, call("GET", "/api/recipes/999999"), "NOT_FOUND", 404)

    def test_11_unknown_api_path(self):
        assert_err(self, call("GET", "/api/nope"), "NOT_FOUND", 404)

    def test_12_seed_recipes_dorm_only(self):
        recipes = []
        for i in range(1, 40):
            st, b = call("GET", f"/api/recipes/{i}")
            if st == 200:
                recipes.append(b["recipe"])
        self.assertGreaterEqual(len(recipes), 15)
        self.assertTrue(all(r["tool"] in ("電鍋", "微波爐") for r in recipes))

    def test_13_root_serves_html(self):
        with urllib.request.urlopen(BASE + "/", timeout=10) as r:
            self.assertEqual(r.status, 200)
            self.assertIn("text/html", r.headers.get("Content-Type", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
