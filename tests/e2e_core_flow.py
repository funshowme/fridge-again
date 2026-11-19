"""端對端測試：核心 5 步（看清單 → 勾選 → 給它們第二次機會 → 看食譜 → 我煮了 → 統計更新）。
手機寬度 375px。需要：pip install playwright 且 playwright install chromium；先 build 出 dist/。

用法：
  python tests/e2e_core_flow.py                 三種情況都跑（flask + static + ghpages）
  python tests/e2e_core_flow.py --mode flask    只跑部署網址情況（Flask 送 dist + API）
  python tests/e2e_core_flow.py --mode static   只跑網站預覽情況（純靜態、沒有 API，前端要改用內建示範資料）
  python tests/e2e_core_flow.py --mode ghpages  模擬 GitHub Pages：dist 放在暫存資料夾的 fridge-again/ 子路徑，
                                                從暫存根目錄提供服務，/api/* 回 404（測完刪除暫存資料夾）
截圖放 release/screens/。Flask 模式測完會 seed --reset。結束碼 0 = 全部通過。
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

from datetime import date, timedelta

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "release", "screens")
os.makedirs(SHOTS, exist_ok=True)
VIEWPORT = {"width": 375, "height": 812}
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("  通過 " if ok else "  失敗 ") + name + (f"  → {detail}" if detail and not ok else ""))


def _force_remove(func, path, _exc):
    """Windows：複製自 OneDrive 的檔案可能帶唯讀屬性，先改成可寫再刪。"""
    try:
        os.chmod(path, 0o700)
        func(path)
    except OSError:
        pass


def reset_db():
    subprocess.run([sys.executable, "-m", "backend.seed", "--reset"], cwd=ROOT,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def start_flask(port):
    reset_db()
    env = dict(os.environ, PORT=str(port))
    for k in ("OPENAI_API_KEY", "AI_API_KEY", "GEMINI_API_KEY"):
        env.pop(k, None)
    p = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2)
            return p
        except Exception:
            time.sleep(0.2)
    p.kill()
    raise RuntimeError("Flask 沒啟動")


def start_static(port, directory=None):
    """純靜態伺服器：只送指定資料夾（預設 dist/），/api/* 一律 404（模擬網站預覽／GitHub Pages 沒有 Python）。"""
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(H, directory=directory or os.path.join(ROOT, "dist"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def read_stats(page):
    """從統計橫幅讀 (已救回樣數, 累計省下 NT$)。"""
    vals = page.locator(".stat-value").all_inner_texts()
    nums = [int(re.sub(r"[^\d]", "", v) or 0) for v in vals]
    return nums[0], nums[1]


def run_flow(browser, url, label):
    print(f"\n== {label}：{url} ==")
    ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error"
            and "404" not in m.text and "Failed to load resource" not in m.text else None)
    origin = "/".join(url.split("/")[:3])
    failed = []
    assets_ok = []
    def on_resp(r):
        u = r.url
        if "/api/" in u:
            return  # 靜態模式的 /api/* 404 是預期的
        if u.endswith((".js", ".css")):
            assets_ok.append((u, r.status))
        if r.status >= 400:
            failed.append(f"{r.status} {u}")
    page.on("response", on_resp)
    page.on("requestfailed", lambda r: failed.append(f"FAILED {r.url}") if "/api/" not in r.url else None)
    external = []
    page.on("request", lambda r: external.append(r.url) if not r.url.startswith(origin)
            and not r.url.startswith("data:") else None)

    def shot(n):
        page.screenshot(path=os.path.join(SHOTS, f"{label}-{n}.png"), full_page=False)

    def no_hscroll(step):
        w = page.evaluate("document.documentElement.scrollWidth")
        check(f"[{label}] {step}：375px 沒有橫向捲動", w <= VIEWPORT["width"] + 1, f"scrollWidth={w}")

    page.goto(url, wait_until="networkidle")
    # 1. 看清單
    page.wait_for_selector(".ingredient-list [role=checkbox]", timeout=10000)
    cards = page.locator(".ingredient-list [role=checkbox]")
    n = cards.count()
    check(f"[{label}] 1 清單有食材（{n} 樣）", n >= 8)
    check(f"[{label}] 1 紅黃綠急迫度標籤都在", page.locator(".urgency-astrx-badge").count() >= 3)
    rescued0, saved0 = read_stats(page)
    check(f"[{label}] 1 統計一開始不是 0（救回 {rescued0}、省 {saved0}）", rescued0 > 0 and saved0 > 0)
    no_hscroll("清單")
    shot("1-list")

    # 2. 勾選 2 樣
    cards.filter(has_text="舒肥雞胸肉").first.click()
    cards.filter(has_text="牛奶").first.click()
    check(f"[{label}] 2 勾選後顯示已選 2/5", page.get_by_text(re.compile(r"已選 2/5")).count() > 0)
    shot("2-selected")

    # 3. 給它們第二次機會
    page.get_by_role("button", name="給它們第二次機會").click()
    page.wait_for_selector(".recipe-card", timeout=10000)
    rc = page.locator(".recipe-card").count()
    check(f"[{label}] 3 出現 3–5 道推薦食譜（{rc}）", 3 <= rc <= 5)
    body = page.inner_text("body")
    check(f"[{label}] 3 食譜標示電鍋或微波爐", ("電鍋" in body) or ("微波爐" in body))
    dup = page.evaluate(r"""() => [...document.querySelectorAll('.recipe-card')].flatMap(c => {
        const t = c.innerText;
        const opt = (t.match(/可省略加分：([^\n]*)/) || [,''])[1].split('、').filter(Boolean);
        const fr = ((t.match(/冰箱裡也有\s*([\s\S]*?)還缺食材/) || [,''])[1]);
        const used = ((t.match(/用到[^\n]*/) || [''])[0]);
        const seen = new Set(); const bad = [];
        for (const o of opt) { if (seen.has(o) || fr.includes(o) || used.includes(o)) bad.push(o); seen.add(o); }
        return bad;
    })""")
    check(f"[{label}] 3 「可省略加分」沒有重複或已在清單中的項目", not dup, str(dup))
    no_hscroll("推薦")
    shot("3-suggestions")

    # 4. 看食譜
    page.locator(".recipe-card").first.click()
    cook = page.get_by_role("button", name=re.compile(r"我煮了"))
    cook.wait_for(timeout=10000)
    check(f"[{label}] 4 食譜詳情有步驟", "步驟" in page.inner_text("body"))
    no_hscroll("食譜詳情")
    shot("4-detail")

    # 5. 我煮了！
    cook.click()
    page.get_by_role("button", name="回到我的冰箱").wait_for(timeout=10000)
    check(f"[{label}] 5 成功畫面出現", True)
    shot("5-success")
    page.get_by_role("button", name="回到我的冰箱").click()
    page.wait_for_selector(".ingredient-list [role=checkbox]", timeout=10000)
    n2 = page.locator(".ingredient-list [role=checkbox]").count()
    check(f"[{label}] 5 食材從清單消失（{n} → {n2}）", n2 == n - 2)
    rescued1, saved1 = read_stats(page)
    check(f"[{label}] 5 統計更新（救回 {rescued0}→{rescued1}、省 {saved0}→{saved1}）",
          rescued1 == rescued0 + 2 and saved1 > saved0)
    shot("6-home-after")

    # 重新整理後狀態仍在（Flask 靠資料庫、static 靠 localStorage）
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".ingredient-list [role=checkbox]", timeout=10000)
    check(f"[{label}] 重新整理後狀態保留", page.locator(".ingredient-list [role=checkbox]").count() == n2)

    run_extras(page, label, shot, no_hscroll)

    reload_n = page.locator(".ingredient-list [role=checkbox]").count()
    page.reload(wait_until="networkidle")
    page.wait_for_selector(".ingredient-list [role=checkbox]", timeout=10000)
    check(f"[{label}] 額外操作後重新整理，清單數量保留（{reload_n}）",
          page.locator(".ingredient-list [role=checkbox]").count() == reload_n)

    check(f"[{label}] 沒有失敗的資源載入（非 /api）", not failed, "; ".join(failed[:3]))
    by_url = {}
    for u, st in assets_ok:
        by_url.setdefault(u, set()).add(st)
    # 每個 css/js 網址至少有一次 200（重新整理後的 304 是瀏覽器快取驗證，不算失敗）
    check(f"[{label}] css/js 都是 200（{len(by_url)} 個檔：{', '.join(u.rsplit('/', 1)[-1] for u in by_url)}）",
          by_url and all(200 in sts and sts <= {200, 304} for sts in by_url.values()), str(by_url))
    check(f"[{label}] 沒有 JS 錯誤", not errors, "; ".join(errors[:3]))
    check(f"[{label}] 沒有連外部網址", not external, ", ".join(external[:3]))
    ctx.close()


def wasted_count(page):
    t = page.locator(".stats-wasted-chip").inner_text()
    return int(re.sub(r"[^\d]", "", t) or 0)


def run_extras(page, label, shot, no_hscroll):
    """新增食材、食安提示、標記丟掉。"""
    cards = page.locator(".ingredient-list [role=checkbox]")
    n0 = cards.count()
    w0 = wasted_count(page)

    # 過期香蕉（水果）：卡片有「已過期」提醒，但可以勾選
    banana = cards.filter(has_text="香蕉")
    check(f"[{label}] 過期品香蕉有食安提醒文字", page.get_by_text(re.compile(r"已過期")).count() > 0)

    # 新增食材：過期的牛奶（乳製品，屬高風險）
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    page.get_by_role("button", name="新增食材").first.click()
    page.get_by_label("食材名稱").fill("牛奶")
    page.locator("input[type=date]").fill(yesterday)
    page.get_by_role("button", name="放入冰箱").click()
    page.wait_for_timeout(800)
    n1 = cards.count()
    check(f"[{label}] 新增食材成功（{n0} → {n1}）", n1 == n0 + 1)
    shot("7-added")
    no_hscroll("新增後清單")

    # 勾選過期牛奶 → 食安提示
    cards.filter(has_text="牛奶").first.click()
    check(f"[{label}] 清單上過期牛奶有高風險提示", page.get_by_text("過期生鮮不建議食用").count() > 0)
    page.get_by_role("button", name="給它們第二次機會").click()
    page.get_by_text(re.compile("為了安全")).first.wait_for(timeout=10000)
    check(f"[{label}] 勾選過期高風險品：顯示食安說明且沒有食譜", page.locator(".recipe-card").count() == 0)
    no_hscroll("食安畫面")
    shot("8-safety")
    page.get_by_role("button", name=re.compile(r"標記丟掉")).first.click()
    page.wait_for_selector(".ingredient-list [role=checkbox]", timeout=10000)
    page.wait_for_timeout(500)
    check(f"[{label}] 食安畫面標記丟掉後回冰箱，清單 {n1} → {cards.count()}", cards.count() == n1 - 1)
    check(f"[{label}] 丟掉統計 +1（{w0} → {wasted_count(page)}）", wasted_count(page) == w0 + 1)

    # 卡片上的「壞了，標記丟掉」
    target = page.locator("article.ingredient-card").filter(has_text="蔥").first
    target.get_by_role("button", name=re.compile("操作")).click()
    page.get_by_role("button", name="壞了，標記丟掉").first.click()
    page.wait_for_timeout(800)
    check(f"[{label}] 卡片標記丟掉：清單減 1、丟掉統計再 +1",
          cards.count() == n1 - 2 and wasted_count(page) == w0 + 2,
          f"cards={cards.count()} wasted={wasted_count(page)}")
    shot("9-after-wasted")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["flask", "static", "ghpages", "both"], default="both")
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(ROOT, "dist", "index.html")):
        print("找不到 dist/index.html，請先 build 前端")
        sys.exit(2)
    flask_proc = None
    srv = None
    srv2 = None
    tmp = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            if a.mode in ("flask", "both"):
                flask_proc = start_flask(8766)
                run_flow(browser, "http://127.0.0.1:8766/", "flask")
                st = json.loads(urllib.request.urlopen("http://127.0.0.1:8766/api/stats").read())
                check("[flask] 資料庫真的記到救援（API /api/stats 的 recent 有新紀錄）", len(st["recent"]) > 0)
            if a.mode in ("static", "both"):
                srv = start_static(8767)
                run_flow(browser, "http://127.0.0.1:8767/", "static")
            if a.mode in ("ghpages", "both"):
                tmp = tempfile.mkdtemp(prefix="ghpages_")
                shutil.copytree(os.path.join(ROOT, "dist"), os.path.join(tmp, "fridge-again"))
                srv2 = start_static(8768, tmp)
                with urllib.request.urlopen("http://127.0.0.1:8768/fridge-again/") as r:
                    check("[ghpages] /fridge-again/ 回 200", r.status == 200)
                try:
                    urllib.request.urlopen("http://127.0.0.1:8768/api/items")
                    check("[ghpages] /api/* 應為 404", False, "回了 200")
                except urllib.error.HTTPError as e:
                    check("[ghpages] /api/* 為 404（模擬 GitHub Pages）", e.code == 404)
                run_flow(browser, "http://127.0.0.1:8768/fridge-again/", "ghpages")
            browser.close()
    finally:
        if flask_proc:
            flask_proc.terminate()
            try:
                flask_proc.wait(5)
            except Exception:
                flask_proc.kill()
        if srv:
            srv.shutdown()
            srv.server_close()
        if srv2:
            srv2.shutdown()
            srv2.server_close()
        if tmp:
            for _ in range(10):
                shutil.rmtree(tmp, onerror=_force_remove)
                if not os.path.exists(tmp):
                    break
                time.sleep(1)
            print("暫存資料夾已刪除：", not os.path.exists(tmp))
        reset_db()
    bad = [r for r in results if not r[1]]
    print(f"\n結果：{len(results) - len(bad)} 通過，{len(bad)} 失敗；截圖在 release/screens/")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
