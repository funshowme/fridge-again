"""端對端測試：核心 5 步（看清單 → 勾選 → 給它們第二次機會 → 看食譜 → 我煮了 → 統計更新）。
手機寬度 375px。需要：pip install playwright 且 playwright install chromium；先 build 出 dist/。

用法：
  python tests/e2e_core_flow.py                 兩種情況都跑（flask + static）
  python tests/e2e_core_flow.py --mode flask    只跑部署網址情況（Flask 送 dist + API）
  python tests/e2e_core_flow.py --mode static   只跑網站預覽情況（純靜態、沒有 API，前端要改用內建示範資料）
截圖放 release/screens/。Flask 模式測完會 seed --reset。結束碼 0 = 全部通過。
"""
import argparse
import functools
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "release", "screens")
os.makedirs(SHOTS, exist_ok=True)
VIEWPORT = {"width": 375, "height": 812}
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("  通過 " if ok else "  失敗 ") + name + (f"  → {detail}" if detail and not ok else ""))


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


def start_static(port):
    """純靜態伺服器：只送 dist/，/api/* 一律 404（模擬網站預覽沒有 Python）。"""
    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(H, directory=os.path.join(ROOT, "dist"))
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
    external = []
    page.on("request", lambda r: external.append(r.url) if not r.url.startswith(url.rstrip("/"))
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
    cards.nth(0).click()
    cards.nth(1).click()
    check(f"[{label}] 2 勾選後顯示已選 2/5", page.get_by_text(re.compile(r"已選 2/5")).count() > 0)
    shot("2-selected")

    # 3. 給它們第二次機會
    page.get_by_role("button", name="給它們第二次機會").click()
    page.wait_for_selector(".recipe-card", timeout=10000)
    rc = page.locator(".recipe-card").count()
    check(f"[{label}] 3 出現 3–5 道推薦食譜（{rc}）", 3 <= rc <= 5)
    body = page.inner_text("body")
    check(f"[{label}] 3 食譜標示電鍋或微波爐", ("電鍋" in body) or ("微波爐" in body))
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

    check(f"[{label}] 沒有 JS 錯誤", not errors, "; ".join(errors[:3]))
    check(f"[{label}] 沒有連外部網址", not external, ", ".join(external[:3]))
    ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["flask", "static", "both"], default="both")
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(ROOT, "dist", "index.html")):
        print("找不到 dist/index.html，請先 build 前端")
        sys.exit(2)
    flask_proc = None
    srv = None
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
        reset_db()
    bad = [r for r in results if not r[1]]
    print(f"\n結果：{len(results) - len(bad)} 通過，{len(bad)} 失敗；截圖在 release/screens/")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
