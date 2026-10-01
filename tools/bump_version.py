# -*- coding: utf-8 -*-
"""
同步全站版本號。

網站頁首的版本號散落在 12 個 HTML 頁面、兩個下載頁的「目前版本」說明，
以及 latest.json，一共 14 處。手改一定會漏，所以用這支腳本統一更新。

用法：
    python tools/bump_version.py 0.3.0

它只做字串替換，不會碰其他內容；重複執行同樣的版本號是安全的（不會有變化）。
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)

VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")

# 頁首的版本標籤
HEADER_RE = re.compile(r'(<span class="ver">v)([^<]*)(</span>)')
# 下載頁的「目前版本」／"Current version" 說明
LEAD_RE = re.compile(r"((?:目前版本|Current version)\s*<b>v)([^<]*)(</b>)",
                     re.IGNORECASE)


def html_files():
    """回傳所有需要更新版本號的 HTML 檔（不含 404，它沒有版本號）。"""
    names = ["index.html", "download.html", "guide.html",
             "method.html", "faq.html", "cite.html"]
    out = [os.path.join(SITE, n) for n in names]
    out += [os.path.join(SITE, "en", n) for n in names]
    return [p for p in out if os.path.exists(p)]


def _replace(pattern, text, version):
    """把 pattern 第 2 群組換成 version，並回傳（新字串, 實際變更數）。

    刻意只計算「值真的不一樣」的次數，這樣重跑同一個版本號會回報 0，
    而不是把每個符合的樣式都算成一次變更。
    """
    changes = 0

    def _sub(m):
        nonlocal changes
        if m.group(2) != version:
            changes += 1
        return f"{m.group(1)}{version}{m.group(3)}"

    return pattern.sub(_sub, text), changes


def update_html(path, version):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    original = text

    text, n1 = _replace(HEADER_RE, text, version)
    text, n2 = _replace(LEAD_RE, text, version)

    if text != original:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    return n1 + n2


def update_latest_json(version):
    path = os.path.join(SITE, "latest.json")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("version") == version:
        return 0
    data["version"] = version
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return 1


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.strip().splitlines()[-3].strip())

    version = sys.argv[1].strip()
    if not VERSION_RE.match(version):
        raise SystemExit(f"版本號格式不對：{version!r}（範例：0.2.0）")

    total = 0
    touched = 0
    for path in html_files():
        n = update_html(path, version)
        rel = os.path.relpath(path, SITE)
        if n:
            touched += 1
            print(f"  {rel}: 更新 {n} 處")
        total += n

    if update_latest_json(version):
        total += 1
        touched += 1
        print("  latest.json: 更新 version 欄位")

    print(f"\n版本 {version}：共更新 {total} 處、{touched} 個檔案。")

    # 提醒：這裡只改網站，應用程式倉庫的 version.txt 要自己同步
    print("\n提醒：請確認應用程式倉庫 Linch-Lab/DRTxECM 的 version.txt "
          f"也是 {version}，並推上對應的 v{version} 標籤。")


if __name__ == "__main__":
    main()
