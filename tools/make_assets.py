# -*- coding: utf-8 -*-
"""
DRTxECM 視覺識別產生器 —— 產生網站與應用程式所需的圖示素材。

設計概念
    DRTxECM 的核心創新是「CPE 相角 α 作為自由擬合參數」。當 α < 1 時，
    Nyquist 圖上的半圓會偏離理想半圓而形成「壓扁半圓（depressed
    semicircle）」。因此標誌就是：實軸 + 壓扁的 Nyquist 半圓弧。
    這是對該工具核心能力最直接的視覺轉譯，而且線條極簡，
    在 16px 的 favicon 尺寸下依然清楚可辨。

輸出
    assets/logo.svg            網站頁首（淺色底）
    assets/logo-white.svg      深色底版本（README 深色模式）
    assets/logo-mark.svg       只有圖標、無文字
    assets/app.ico             分頁圖示 + 應用程式圖示（多尺寸）
    assets/apple-touch-icon.png
    assets/og-image.png        社群分享預覽（1200x630）

用法
    python tools/make_assets.py

本腳本不依賴網路與外部資源，重跑即可完整重建所有素材。
幾何全部定義在 64x64 的設計格上，再依需求等比縮放。
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

# ---- 品牌色 ----
INK = "#0f2c5c"         # 主要深藍（文字）
BLUE = "#0b57d0"        # 主要色（與 LinLingo 同色系，維持家族感）
BLUE_DARK = "#0b3c8f"   # 漸層起點
BLUE_LIGHT = "#1b7ae0"  # 漸層終點
TEAL = "#0ea5a4"        # 強調色（"x" 與分隔線）

# ---- 字型 ----
FONT_DIR = r"C:\Windows\Fonts"
F_LATIN_B = os.path.join(FONT_DIR, "segoeuib.ttf")
F_LATIN = os.path.join(FONT_DIR, "segoeui.ttf")
F_CJK_B = os.path.join(FONT_DIR, "msjhbd.ttc")
F_CJK = os.path.join(FONT_DIR, "msjh.ttc")

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")

# ---- 幾何（64x64 設計格）----
GRID = 64.0
CHORD_X0, CHORD_X1 = 12.0, 52.0   # 半圓弧的兩個端點（落在實軸上）
BASE_Y = 42.0                     # 實軸高度
SAG = 17.0                        # 弧頂高度（< 半弦長 → 壓扁半圓）
AXIS_X0, AXIS_X1 = 8.0, 56.0      # 實軸線段範圍
ARC_W = 6.0                       # 弧線粗細
AXIS_W = 2.6                      # 實軸粗細


def arc_geometry():
    """由弦長與弧頂高推算圓心與半徑（壓扁半圓的幾何）。"""
    a = (CHORD_X1 - CHORD_X0) / 2.0
    r = (a * a + SAG * SAG) / (2.0 * SAG)
    cx = (CHORD_X0 + CHORD_X1) / 2.0
    cy = BASE_Y + (r - SAG)
    return cx, cy, r


CX, CY, R = arc_geometry()
# 弧的起迄角（Pillow 慣例：以 3 點鐘為 0，順時針增加；y 軸向下）
T0 = math.degrees(math.atan2(BASE_Y - CY, CHORD_X0 - CX))
T1 = math.degrees(math.atan2(BASE_Y - CY, CHORD_X1 - CX))
# 弧所張的角度（用於 SVG 的 large-arc-flag 判斷）
SPAN_DEG = abs(T1 - T0)


def draw_mark(draw, scale, offset=(0.0, 0.0), color="#ffffff"):
    """把 Nyquist 標誌畫進 draw，可指定縮放與位移。"""
    ox, oy = offset

    def p(v, axis):
        return v * scale + (ox if axis == "x" else oy)

    # 實軸
    draw.line(
        [p(AXIS_X0, "x"), p(BASE_Y, "y"), p(AXIS_X1, "x"), p(BASE_Y, "y")],
        fill=color, width=max(1, round(AXIS_W * scale)),
    )
    # 壓扁半圓弧
    draw.arc(
        [p(CX - R, "x"), p(CY - R, "y"), p(CX + R, "x"), p(CY + R, "y")],
        start=T0, end=T1, fill=color, width=max(1, round(ARC_W * scale)),
    )


def gradient(size, c1, c2):
    """對角線線性漸層。"""
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    a = tuple(int(c1[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(h):
        for x in range(w):
            t = (x / max(1, w - 1) + y / max(1, h - 1)) / 2.0
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return img


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def make_app_icon(px=256, bg=True):
    """應用程式圖示／favicon。bg=False 時回傳透明底的藍色標誌。"""
    if bg:
        icon = gradient((px, px), BLUE_DARK, BLUE_LIGHT).convert("RGBA")
        icon.putalpha(rounded_mask((px, px), round(px * 0.22)))
        color = "#ffffff"
    else:
        icon = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        color = BLUE
    draw_mark(ImageDraw.Draw(icon), px / GRID, color=color)
    return icon


# ---------------------------------------------------------------- 文字工具

def dsize(font, text):
    box = font.getbbox(text)
    return box[2] - box[0], box[3] - box[1]


def fit_font(path, text, max_w, start, minimum=10):
    """由大到小尋找能塞進 max_w 的字級。"""
    size = start
    while size > minimum:
        f = ImageFont.truetype(path, size)
        if dsize(f, text)[0] <= max_w:
            return f
        size -= 1
    return ImageFont.truetype(path, minimum)


def make_og_image():
    """社群分享預覽圖 1200x630。"""
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#ffffff")
    d = ImageDraw.Draw(img)

    # 頂部漸層色帶
    img.paste(gradient((W, 12), BLUE_DARK, BLUE_LIGHT), (0, 0))

    # 左側標誌（標誌本體是寬扁形，用 210 寬的方框配合垂直置中）
    box = 210
    scale = box / GRID
    # 標誌在設計格中的垂直中心約為 (BASE_Y - SAG/2 + BASE_Y)/2
    mark_cy = (BASE_Y - SAG + BASE_Y) / 2.0
    draw_mark(d, scale, offset=(30.0, 315.0 - mark_cy * scale), color=BLUE)

    x0 = 330
    f_title = ImageFont.truetype(F_LATIN_B, 86)
    d.text((x0, 168), "DRTxECM", font=f_title, fill=INK)
    tw = dsize(f_title, "DRTxECM")[0]
    d.line([x0, 288, x0 + tw, 288], fill=TEAL, width=6)

    line_cjk = "CPE 相角自由擬合的等效電路建模工具"
    f_sub = fit_font(F_CJK_B, line_cjk, W - x0 - 80, 40)
    d.text((x0, 320), line_cjk, font=f_sub, fill="#333333")

    line_en = ("DRT deconvolution → Gaussian peak decomposition "
               "→ CNLS circuit fitting")
    f_en = fit_font(F_LATIN, line_en, W - x0 - 80, 28)
    d.text((x0, 384), line_en, font=f_en, fill="#555555")

    f_foot = ImageFont.truetype(F_CJK, 26)
    d.text((x0, 470), "開源免費 ｜ MIT License ｜ Windows 免安裝版",
           font=f_foot, fill=BLUE)
    f_url = ImageFont.truetype(F_LATIN, 26)
    d.text((x0, 516), "drtxecm.billlinch.com", font=f_url, fill="#888888")

    return img


# ---------------------------------------------------------------- SVG 產生

LOGO_FONT = ("'Segoe UI',system-ui,-apple-system,'Microsoft JhengHei',"
             "'PingFang TC',sans-serif")


def mark_svg(color, size=64.0, ox=0.0, oy=0.0):
    """把 Nyquist 標誌輸出成 SVG。

    半圓弧以 A（elliptical arc）指令表示；sweep-flag=1 在 SVG 座標系
    （y 軸向下）代表順時針，即由左端點往右端點畫出上方的弧。
    """
    s = size / GRID
    x0, x1 = CHORD_X0 * s + ox, CHORD_X1 * s + ox
    by = BASE_Y * s + oy
    r = R * s
    ax0, ax1 = AXIS_X0 * s + ox, AXIS_X1 * s + ox
    aw, asw = ARC_W * s, AXIS_W * s
    large = 1 if SPAN_DEG > 180 else 0
    return (
        f'<g fill="none" stroke="{color}" stroke-linecap="round">'
        f'<line x1="{ax0:.2f}" y1="{by:.2f}" x2="{ax1:.2f}" y2="{by:.2f}" '
        f'stroke-width="{asw:.2f}"/>'
        f'<path d="M {x0:.2f} {by:.2f} A {r:.2f} {r:.2f} 0 {large} 1 '
        f'{x1:.2f} {by:.2f}" stroke-width="{aw:.2f}"/>'
        f'</g>'
    )


def logo_svg(ink, accent, mark_color, width=336, height=64):
    """含文字的橫式標誌。"""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="DRTxECM">\n'
        f'  <title>DRTxECM</title>\n'
        f'  {mark_svg(mark_color)}\n'
        f'  <text x="72" y="44" font-family="{LOGO_FONT}" font-size="36" '
        f'font-weight="700" letter-spacing="-0.6">'
        f'<tspan fill="{ink}">DRT</tspan>'
        f'<tspan fill="{accent}">x</tspan>'
        f'<tspan fill="{ink}">ECM</tspan></text>\n'
        f'</svg>\n'
    )


def mark_only_svg(color, size=64):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}" role="img" aria-label="DRTxECM">\n'
        f'  <title>DRTxECM</title>\n'
        f'  {mark_svg(color)}\n'
        f'</svg>\n'
    )


ASSETS_README = """DRTxECM 網站素材
=================

本資料夾的圖檔全部由 tools/make_assets.py 產生，請勿手動編輯。
要調整顏色或造型，改 tools/make_assets.py 之後重跑：

    python tools/make_assets.py

| 檔案 | 用途 |
|---|---|
| logo.svg | 網站頁首標誌（淺色底） |
| logo-white.svg | 深色底版本 |
| logo-mark.svg | 只有圖標、無文字 |
| app.ico | 分頁圖示（favicon）＋應用程式圖示 |
| apple-touch-icon.png | iOS／Android 加到主畫面的圖示 |
| og-image.png | 社群分享預覽圖（1200x630） |

造型說明：實軸 + 壓扁的 Nyquist 半圓弧。壓扁半圓正是 CPE 相角
α < 1 時 Nyquist 圖的實際樣貌，而「α 可自由擬合」是本工具的核心特色。
"""


def main():
    os.makedirs(ASSETS, exist_ok=True)

    def out(name):
        return os.path.join(ASSETS, name)

    icon = make_app_icon(256)
    icon.save(out("app.ico"), format="ICO",
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                     (128, 128), (256, 256)])
    print("wrote app.ico")

    make_app_icon(180).save(out("apple-touch-icon.png"))
    print("wrote apple-touch-icon.png")

    make_og_image().save(out("og-image.png"))
    print("wrote og-image.png")

    with open(out("logo.svg"), "w", encoding="utf-8") as f:
        f.write(logo_svg(INK, TEAL, BLUE))
    with open(out("logo-white.svg"), "w", encoding="utf-8") as f:
        f.write(logo_svg("#ffffff", "#5eead4", "#ffffff"))
    with open(out("logo-mark.svg"), "w", encoding="utf-8") as f:
        f.write(mark_only_svg(BLUE))
    print("wrote logo.svg / logo-white.svg / logo-mark.svg")

    with open(out("README.txt"), "w", encoding="utf-8") as f:
        f.write(ASSETS_README)
    print("wrote README.txt")

    print(f"\ngeometry: chord {CHORD_X0}-{CHORD_X1}, base_y {BASE_Y}, "
          f"sag {SAG}, R {R:.2f}, arc span {SPAN_DEG:.1f} deg")


if __name__ == "__main__":
    main()
