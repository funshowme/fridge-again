"""安全檢查 + 打包 zip（只用標準庫）。
用法：
  python scripts/check_and_pack.py            只檢查（不打包）
  python scripts/check_and_pack.py --pack     檢查通過後打包到 release/fridge-again.zip
結束碼：0 = 全部通過（可有警告）；1 = 有錯誤。
"""
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "release")
ZIP_PATH = os.path.join(OUT_DIR, "fridge-again.zip")
MAX_FILES, MAX_BYTES = 5000, 300 * 1024 * 1024

EXCLUDE_DIRS = {"node_modules", ".git", "__pycache__", "release", ".venv", "venv", ".pytest_cache"}
EXCLUDE_FILE = re.compile(r"(^|/)(\.env(\..*)?|.*\.db|.*\.db-(wal|shm|journal)|.*\.sqlite3?|.*\.pyc|\.DS_Store)$")
KEEP_FILE = {".env.example"}

SECRET_PATTERNS = [
    ("sk- 金鑰", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}")),
    ("私鑰", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Bearer token", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("api_key 指派真實值", re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[=:]\s*['\"][A-Za-z0-9_\-./+]{12,}['\"]")),
]
TEXT_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css", ".md", ".txt", ".yml", ".yaml",
            ".toml", ".cfg", ".ini", ".example", ".env", ""}

errors, warnings = [], []


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def walk(include_excluded=False):
    for d, dirs, files in os.walk(ROOT):
        if not include_excluded:
            dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
        for f in files:
            yield os.path.join(d, f)


def is_text(path):
    return os.path.splitext(path)[1].lower() in TEXT_EXT or os.path.basename(path) == "Procfile"


def read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def check_env_files():
    for p in walk():
        n = os.path.basename(p)
        if n.startswith(".env") and n not in KEEP_FILE:
            errors.append(f"發現 env 檔：{rel(p)}（不可打包）")
    ex = os.path.join(ROOT, ".env.example")
    if os.path.isfile(ex):
        for i, line in enumerate(read(ex).splitlines(), 1):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                if re.search(r"KEY|SECRET|TOKEN|PASSWORD", k, re.I) and v.strip():
                    errors.append(f".env.example 第 {i} 行 {k} 不是空值")
    else:
        warnings.append("沒有 .env.example")


def check_secrets():
    for p in walk():
        if not is_text(p) or os.path.getsize(p) > 5 * 1024 * 1024:
            continue
        txt = read(p)
        for name, pat in SECRET_PATTERNS:
            for m in pat.finditer(txt):
                line = txt.count("\n", 0, m.start()) + 1
                snippet = m.group(0)[:6] + "…"
                errors.append(f"疑似{name}：{rel(p)}:{line}（{snippet}）")


def check_localhost():
    targets = [os.path.join(ROOT, "frontend", "src"), os.path.join(ROOT, "dist"),
               os.path.join(ROOT, "frontend", "index.html")]
    pat = re.compile(r"localhost|127\.0\.0\.1|0\.0\.0\.0:\d+")
    n = 0
    for t in targets:
        files = [t] if os.path.isfile(t) else [p for p in (walk_dir(t) if os.path.isdir(t) else [])]
        for p in files:
            if os.path.basename(p) == "vite.config.js" or not is_text(p):
                continue
            n += 1
            txt = read(p)
            for m in pat.finditer(txt):
                ln = txt.count(chr(10), 0, m.start())
                line_txt = txt.splitlines()[ln].strip()
                msg = f"前端出現 {m.group(0)}：{rel(p)}:{ln + 1}"
                if line_txt.startswith(("*", "//", "/*", "#", "<!--")):
                    warnings.append(msg + "（只在註解，建議改掉字眼以免被掃描誤判）")
                else:
                    errors.append(msg)
    if not os.path.isdir(os.path.join(ROOT, "dist")):
        pass
    return n


def walk_dir(d):
    for dd, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
        for f in files:
            yield os.path.join(dd, f)


def check_required():
    for f in ("app.py", "requirements.txt", "Procfile"):
        if not os.path.isfile(os.path.join(ROOT, f)):
            errors.append(f"缺少 {f}")
    if not os.path.isdir(os.path.join(ROOT, "backend")):
        errors.append("缺少 backend/")
    pf = read(os.path.join(ROOT, "Procfile"))
    if "gunicorn" not in pf or "app:app" not in pf:
        errors.append("Procfile 不是 gunicorn ... app:app")
    req = read(os.path.join(ROOT, "requirements.txt")).lower()
    for pkg in ("flask", "gunicorn"):
        if pkg not in req:
            errors.append(f"requirements.txt 缺 {pkg}")
    idx = os.path.join(ROOT, "dist", "index.html")
    if not os.path.isfile(idx):
        errors.append("缺少 dist/index.html（前端還沒建置）")
    else:
        html = read(idx)
        if re.search(r"""(src|href)=["']/(?!/)""", html):
            warnings.append("dist/index.html 有以 / 開頭的絕對路徑資源，網站預覽若放在子路徑可能載入失敗（vite base 應為 './'）")
        for m in re.finditer(r"""(?:src|href)=["']([^"']+)["']""", html):
            u = m.group(1)
            if u.startswith(("http://", "https://", "//")):
                warnings.append(f"dist/index.html 引用外部資源 {u}（沙箱／離線可能載入失敗）")
            elif not u.startswith(("data:", "#")):
                if not os.path.isfile(os.path.join(ROOT, "dist", u.lstrip("./").split("?")[0])):
                    errors.append(f"dist/index.html 引用的檔案不存在：{u}")


def collect_files():
    out = []
    for p in walk():
        r = rel(p)
        if os.path.basename(p) in KEEP_FILE or not EXCLUDE_FILE.search(r):
            out.append((p, r))
    return out


def check_size(files):
    n = len(files)
    total = sum(os.path.getsize(p) for p, _ in files)
    if n > MAX_FILES:
        errors.append(f"檔案數 {n} 超過 {MAX_FILES}")
    if total > MAX_BYTES:
        errors.append(f"大小 {total / 1e6:.1f}MB 超過 300MB")
    return n, total


def pack(files):
    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for p, r in files:
            z.write(p, r)
    # 驗證 zip 內容
    with zipfile.ZipFile(ZIP_PATH) as z:
        names = z.namelist()
    bad = [n for n in names if EXCLUDE_FILE.search(n) and not n.endswith(".env.example")
           or re.search(r"(^|/)(node_modules|\.git|__pycache__)/", n)]
    if bad:
        errors.append(f"zip 含不該有的檔案：{bad[:5]}")
    if "dist/index.html" not in names:
        errors.append("zip 沒有 dist/index.html")
    size = os.path.getsize(ZIP_PATH)
    print(f"zip：{rel(ZIP_PATH)}，{len(names)} 個檔案，{size / 1e6:.2f}MB")


def main():
    do_pack = "--pack" in sys.argv
    check_env_files()
    check_secrets()
    n = check_localhost()
    check_required()
    files = collect_files()
    cnt, total = check_size(files)
    print(f"[資訊] 將打包 {cnt} 個檔案，約 {total / 1e6:.2f}MB（上限 5000 檔 / 300MB）；前端掃描 {n} 個檔案")
    if do_pack and not errors:
        pack(files)
    elif do_pack:
        print("有錯誤，未打包")
    for w in warnings:
        print("[警告]", w)
    for e in errors:
        print("[錯誤]", e)
    print("結果：", "通過" if not errors else f"失敗（{len(errors)} 個錯誤）")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
