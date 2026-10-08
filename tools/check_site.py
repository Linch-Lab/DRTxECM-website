# -*- coding: utf-8 -*-
"""
網站一致性檢查。

這個網站沒有建置步驟，改動就是直接改 HTML，因此很容易在複製貼上時漏掉東西：
某頁忘了改 canonical、導覽少了「here」標記、sitemap 少一頁、
版本號只改了一半、圖片路徑少一層 ../。

這支腳本把這些檢查全部自動化，改完網站跑一次就知道有沒有漏。

用法（在網站根目錄）：

    python tools/check_site.py

離開碼 0 = 全部通過，1 = 有錯誤（可直接用在 CI 或 pre-commit）。

檢查項目
    1. 所有本機連結（href / src）都指向存在的檔案
    2. 沒有 JavaScript、inline 事件處理、追蹤碼、http:// 或外部 CDN
    3. 每頁都有 title / description / canonical / hreflang / Open Graph /
       Twitter Card，且語言切換指回同一頁
    4. 每頁都有完整的六項導覽，且只有一個「目前頁面」標記
    5. sitemap.xml 是合法 XML、頁數正確、每個網址都有對應檔案；
       robots.txt 指向 sitemap
    6. 全站版本號一致，且 latest.json 與應用程式倉庫的 version.txt 相符
    7. og:image 是絕對網址且檔案存在
    8. 標籤成對、每頁都以 </html> 結尾
    9. 截圖檔案存在，並統計被引用次數
"""

import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

# 應用程式倉庫（可選）。預設往上一層找 app-repo，也可以用環境變數指定。
APP_REPO = os.environ.get("DRTXECM_REPO",
                          os.path.join(os.path.dirname(SITE), "app-repo"))

DOMAIN = "https://drtxecm.billlinch.com"
PAGES = ["index.html", "download.html", "guide.html", "method.html",
         "faq.html", "cite.html"]
SCREENSHOTS = ["01-eis-loaded.png", "02-drt-result.png",
               "03-stage2-peaks.png", "04-stage3-ecm.png"]
EXTRA_PAGES = ["404.html"]

# 網站圖示（分頁與搜尋結果）與贊助 QR。這些以前都出現過少檔或路徑寫錯的
# 情況，所以獨立檢查：檔案要在、每一頁都要用站根絕對路徑引用。
ICON_FILES = [("favicon.ico", "favicon at the site root"),
              ("assets/favicon-96.png", "96x96 PNG favicon"),
              ("assets/apple-touch-icon.png", "apple-touch-icon")]
ICON_LINKS = ['href="/favicon.ico"', 'href="/assets/favicon-96.png"',
              'href="/assets/apple-touch-icon.png"']
QR_FILE = "assets/twqr-donate.jpg"
QR_LINK = 'src="/assets/twqr-donate.jpg"'
QR_PAGES = ["cite.html", "en/cite.html"]

fails, oks = [], []


def F(m):
    fails.append(m)


def O(m):
    oks.append(m)


def read(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def html_pages():
    out = [os.path.join(SITE, p) for p in PAGES]
    out += [os.path.join(SITE, "en", p) for p in PAGES]
    out += [os.path.join(SITE, p) for p in EXTRA_PAGES]
    return [p for p in out if os.path.exists(p)]


def rel(path):
    return os.path.relpath(path, SITE).replace(os.sep, "/")


def check_pages_exist():
    pages = html_pages()
    expect = (len(PAGES) * 2) + len(EXTRA_PAGES)
    if len(pages) != expect:
        F(f"expected {expect} HTML pages, found {len(pages)}")
    return pages


def check_links(pages):
    """所有本機連結都必須指向存在的檔案。"""
    pattern = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')
    broken = []
    for page in pages:
        base = os.path.dirname(page)
        for url in pattern.findall(read(page)):
            if url.startswith(("http://", "https://", "mailto:", "//", "#")):
                continue
            target = url.split("#")[0].split("?")[0]
            if not target:
                continue
            if target.startswith("/"):
                path = os.path.join(SITE, target.lstrip("/"))
            else:
                path = os.path.normpath(os.path.join(base, target))
            if not os.path.exists(path):
                broken.append(f"{rel(page)} -> {url}")
    if broken:
        for item in broken:
            F(f"broken local link: {item}")
    else:
        O(f"all local links resolve ({len(pages)} pages)")


def check_no_js(pages):
    """網站必須是純靜態：無 JS、無追蹤、無外部資源、無不安全網址。"""
    bad = False
    for page in pages:
        html = read(page)
        name = rel(page)
        if re.search(r"<script", html, re.I):
            F(f"{name}: contains <script>")
            bad = True
        if re.search(r"\son(click|load|error|change|submit|mouseover)\s*=",
                     html, re.I):
            F(f"{name}: contains an inline event handler")
            bad = True
        if re.search(r"google-analytics|gtag\(|googletagmanager|hotjar",
                     html, re.I):
            F(f"{name}: contains tracking code")
            bad = True
        if "http://" in html:
            F(f"{name}: contains an insecure http:// URL")
            bad = True
        if re.search(r'<(link|script)[^>]+(fonts\.googleapis|cdn\.|unpkg|jsdelivr)',
                     html, re.I):
            F(f"{name}: loads an external resource")
            bad = True
    if not bad:
        O("static-only: no JavaScript, no handlers, no tracking, no CDNs")


def check_head(pages):
    """每頁的 SEO 與語言標註。"""
    bad = False
    for page in pages:
        name = rel(page)
        if name == "404.html":
            continue
        html = read(page)
        is_en = name.startswith("en/")
        zh = name[3:] if is_en else name
        en = ("en/" + name) if not is_en else name

        for needle, label in (("<title>", "title"),
                              ('name="description"', "meta description"),
                              ('rel="canonical"', "canonical"),
                              ('hreflang="zh-Hant"', "hreflang zh-Hant"),
                              ('hreflang="en"', "hreflang en"),
                              ('hreflang="x-default"', "hreflang x-default"),
                              ('name="twitter:card"', "twitter:card")):
            if needle not in html:
                F(f"{name}: missing {label}")
                bad = True
        for prop in ("og:type", "og:url", "og:title", "og:description",
                     "og:image"):
            if prop not in html:
                F(f"{name}: missing {prop}")
                bad = True

        expect = f"{DOMAIN}/en/{name[3:]}" if is_en else f"{DOMAIN}/{name}"
        if name.endswith("index.html"):
            expect = expect.replace("index.html", "")
        if f'rel="canonical" href="{expect}"' not in html:
            F(f"{name}: canonical is not {expect}")
            bad = True

        want_lang = "en" if is_en else "zh-Hant"
        if f'lang="{want_lang}"' not in html:
            F(f"{name}: wrong <html lang>")
            bad = True

        # 語言切換必須指回同一頁
        switch = f'href="../{name[3:]}"' if is_en else f'href="en/{name}"'
        if switch not in html:
            F(f"{name}: language switch does not point to {switch}")
            bad = True

        # 交叉檢查：該檔案確實存在
        for counterpart in (zh, en):
            if not os.path.exists(os.path.join(SITE, counterpart.replace("/", os.sep))):
                F(f"{name}: hreflang counterpart missing on disk: {counterpart}")
                bad = True
    if not bad:
        O("every page has SEO head tags, hreflang and a working language switch")


def check_nav(pages):
    """六項導覽 + 剛好一個 here。"""
    bad = False
    for page in pages:
        name = rel(page)
        if name == "404.html":
            continue
        match = re.search(r'<nav class="site">(.*?)</nav>', read(page), re.S)
        if not match:
            F(f"{name}: no <nav class=\"site\">")
            bad = True
            continue
        body = match.group(1)
        count = len(re.findall(r'class="here"', body))
        if count != 1:
            F(f"{name}: nav has {count} 'here' markers, expected 1")
            bad = True
        for target in PAGES:
            if f'href="{target}"' not in body:
                F(f"{name}: nav missing link to {target}")
                bad = True
    if not bad:
        O("every page has the full 6-item nav with exactly one current marker")


def check_sitemap():
    """sitemap 合法、頁數正確、每個網址都有檔案。"""
    sm_path = os.path.join(SITE, "sitemap.xml")
    try:
        root = ET.fromstring(read(sm_path))
    except ET.ParseError as exc:
        F(f"sitemap.xml is not valid XML: {exc}")
        return
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [e.text for e in root.findall(".//s:loc", ns)]
    expect = len(PAGES) * 2
    if len(locs) != expect:
        F(f"sitemap has {len(locs)} URLs, expected {expect}")
    for loc in locs:
        tail = loc.replace(DOMAIN + "/", "")
        if not tail or tail.endswith("/"):
            tail += "index.html"
        if not os.path.exists(os.path.join(SITE, tail.replace("/", os.sep))):
            F(f"sitemap URL has no file on disk: {loc}")

    robots = read(os.path.join(SITE, "robots.txt"))
    if f"{DOMAIN}/sitemap.xml" not in robots:
        F("robots.txt does not point at the sitemap")
    O(f"sitemap.xml valid with {len(locs)} URLs, all present; robots.txt points to it")


def check_version(pages):
    """全站版本號一致，且與應用程式倉庫相符。"""
    pattern = re.compile(r'<span class="ver">v([^<]+)</span>')
    found = {}
    for page in pages:
        match = pattern.search(read(page))
        if match:
            found.setdefault(match.group(1), []).append(rel(page))
    if len(found) != 1:
        F(f"inconsistent header versions: "
          f"{ {k: len(v) for k, v in found.items()} }")
        return
    version = list(found)[0]
    O(f"header version consistent across {len(list(found.values())[0])} pages: "
      f"v{version}")

    latest_path = os.path.join(SITE, "latest.json")
    latest = json.loads(read(latest_path))
    if latest.get("version") != version:
        F(f"latest.json version {latest.get('version')} != page version {version}")

    version_txt = os.path.join(APP_REPO, "version.txt")
    if os.path.exists(version_txt):
        app_version = read(version_txt).strip()
        if app_version != version:
            F(f"app version.txt ({app_version}) != website ({version})")
        else:
            O(f"website version matches the app repo's version.txt ({app_version})")
    else:
        print(f"  note  app repo not found at {APP_REPO}; skipped the "
              f"version.txt cross-check")


def check_og_image(pages):
    bad = False
    for page in pages:
        name = rel(page)
        for url in re.findall(r'og:image" content="([^"]+)"', read(page)):
            if not url.startswith(DOMAIN):
                F(f"{name}: og:image is not absolute ({url})")
                bad = True
                continue
            local = url.replace(DOMAIN + "/", "").replace("/", os.sep)
            if not os.path.exists(os.path.join(SITE, local)):
                F(f"{name}: og:image file missing ({url})")
                bad = True
    if not bad:
        O("og:image is absolute and present on disk on every page")


def check_tag_balance(pages):
    bad = False
    for page in pages:
        name = rel(page)
        html = read(page)
        for tag in ("html", "head", "body", "nav", "table", "figure", "div"):
            opens = len(re.findall(rf"<{tag}[\s>]", html))
            closes = len(re.findall(rf"</{tag}>", html))
            if opens != closes:
                F(f"{name}: <{tag}> opened {opens}x but closed {closes}x")
                bad = True
        if not html.rstrip().endswith("</html>"):
            F(f"{name}: does not end with </html>")
            bad = True
    if not bad:
        O("all tags balanced; every page ends with </html>")


def check_screenshots(pages):
    for name in SCREENSHOTS:
        if not os.path.exists(os.path.join(SITE, "assets", "screenshots", name)):
            F(f"missing screenshot {name}")
    used = sum(read(p).count("screenshots/") for p in pages)
    if used == 0:
        F("screenshots exist but are not referenced by any page")
    else:
        O(f"{len(SCREENSHOTS)} screenshots present, referenced {used} times")


def check_icons_and_qr(pages):
    """分頁／搜尋結果的圖示，以及贊助 QR。"""
    bad = False

    for relpath, label in ICON_FILES:
        if not os.path.exists(os.path.join(SITE, relpath.replace("/", os.sep))):
            F(f"missing {label} ({relpath})")
            bad = True
    if not os.path.exists(os.path.join(SITE, QR_FILE.replace("/", os.sep))):
        F(f"missing sponsor QR ({QR_FILE})")
        bad = True

    for page in pages:
        name = rel(page)
        html = read(page)
        for needle in ICON_LINKS:
            if needle not in html:
                F(f"{name}: missing {needle}")
                bad = True
        # 舊寫法（相對路徑的 app.ico）不該再出現
        if "assets/app.ico" in html:
            F(f"{name}: still references the old assets/app.ico")
            bad = True

    for name in QR_PAGES:
        path = os.path.join(SITE, name.replace("/", os.sep))
        if not os.path.exists(path):
            F(f"missing page {name}")
            bad = True
            continue
        if QR_LINK not in read(path):
            F(f"{name}: the sponsor QR image is not referenced")
            bad = True

    if not bad:
        O("favicon trio present and referenced on every page; sponsor QR wired up")


def check_app_repo():
    """應用程式倉庫的打包檔案是否齊全（找不到就跳過）。"""
    if not os.path.isdir(APP_REPO):
        return
    wanted = ["version.txt", "DRTxECM.spec", "build.bat",
              "packaging/make_version_info.py",
              "packaging/requirements-build.txt",
              "packaging/README.md", "releases/README.md",
              "assets/DRTxECM.ico",
              "packaging/extras/診斷.cmd",
              "packaging/extras/使用前必讀.txt",
              ".github/workflows/release.yml"]
    bad = False
    for item in wanted:
        if not os.path.exists(os.path.join(APP_REPO, item.replace("/", os.sep))):
            F(f"app repo missing {item}")
            bad = True
    gitignore = read(os.path.join(APP_REPO, ".gitignore"))
    if "!DRTxECM.spec" not in gitignore:
        F("app .gitignore does not un-ignore DRTxECM.spec")
        bad = True
    # .bat 必須是純 ASCII，否則 cmd.exe 會讀錯前面的行
    with open(os.path.join(APP_REPO, "build.bat"), "rb") as handle:
        raw = handle.read()
    if any(b > 127 for b in raw):
        F("build.bat contains non-ASCII bytes (cmd.exe will misparse it)")
        bad = True
    if not bad:
        O("app repo packaging files complete; build.bat is pure ASCII")


def main():
    pages = check_pages_exist()
    print(f"pages: {len(pages)}")

    check_links(pages)
    check_no_js(pages)
    check_head(pages)
    check_nav(pages)
    check_sitemap()
    check_version(pages)
    check_og_image(pages)
    check_tag_balance(pages)
    check_screenshots(pages)
    check_icons_and_qr(pages)
    check_app_repo()

    print()
    for message in oks:
        print(f"  OK    {message}")
    for message in fails:
        print(f"  FAIL  {message}")
    print(f"\n{len(oks)} passed, {len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
