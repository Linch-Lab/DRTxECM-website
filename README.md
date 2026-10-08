# DRTxECM 官方網站

**https://drtxecm.billlinch.com/**

[DRTxECM](https://github.com/Linch-Lab/DRTxECM) 的官方網站：繁體中文與英文雙語、
純靜態、**不使用 JavaScript**、不含任何追蹤碼。

網站與應用程式刻意分成兩個倉庫：

| 倉庫 | 內容 |
|---|---|
| **`Linch-Lab/DRTxECM-website`**（本倉庫） | 官網（本目錄即網站根目錄） |
| [`Linch-Lab/DRTxECM`](https://github.com/Linch-Lab/DRTxECM) | 應用程式原始碼、PyInstaller 打包設定、GitHub Actions 發佈流程 |

網站提供**兩種發行版本**，下載按鈕都指向應用程式倉庫的 GitHub Releases：

```
免安裝版   https://github.com/Linch-Lab/DRTxECM/releases/latest/download/DRTxECM-win64.zip
Python 版  https://github.com/Linch-Lab/DRTxECM/releases/latest/download/DRTxECM-python.zip
```

| | 免安裝版 | Python 版 |
|---|---|---|
| 大小 | 約 126 MB | 約 1.8 MB |
| 需要 Python | 不需要 | 3.10 或 3.11 |
| 第一次啟動 | 解壓即用 | 需下載約 150 MB 套件 |
| 電腦阻擋未簽章程式時 | 可能被擋 | 通常可以（`python.exe` 有簽章） |
| 學校封鎖 PyPI 時 | 可以 | 無法安裝 |

兩者在 `download.html` 與 `en/download.html` 上有並列的比較表。
`DRTxECM-python.zip` 由應用程式倉庫的 release workflow 產生，
內容與啟動器說明見該倉庫的 `packaging/README.md`。

> **注意**：在應用程式倉庫還沒有任何 Release 之前，這兩個網址都會回 404。
> 發佈順序請見 [部署網站.md](部署網站.md)。

---

## 專案結構

```
DRTxECM-website/                 ← 倉庫根目錄 = 網站根目錄
├── index.html                   首頁
├── download.html                下載
├── guide.html                   使用說明
├── method.html                  方法與原理
├── faq.html                     常見問題
├── cite.html                    引用與致謝
├── 404.html
├── favicon.ico                  網站圖示（瀏覽器會直接請求這個路徑）
├── .htaccess                    Apache 設定（Hostinger / cPanel）
├── robots.txt
├── sitemap.xml                  12 頁 + hreflang
├── latest.json                  應用程式更新檢查的來源
├── en/                          英文版（與中文同結構的六頁）
│   ├── index.html
│   ├── download.html
│   ├── guide.html
│   ├── method.html
│   ├── faq.html
│   └── cite.html
├── assets/
│   ├── style.css                全站共用樣式
│   ├── logo.svg                 頁首標誌（淺色底）
│   ├── logo-white.svg           深色底版本
│   ├── logo-mark.svg            只有圖標
│   ├── app.ico                  應用程式圖示（同步到應用程式倉庫）
│   ├── favicon-96.png           分頁／搜尋結果的網站圖示（96x96）
│   ├── apple-touch-icon.png     加到主畫面
│   ├── og-image.png             社群分享預覽（1200x630）
│   ├── twqr-donate.jpg          贊助頁的 TWQR 台灣Pay 收款碼
│   ├── screenshots/             真實介面截圖（四張）
│   └── README.txt
├── tools/
│   ├── make_assets.py           產生上面所有圖檔
│   ├── make_screenshots.py      啟動真實 GUI 產生介面截圖
│   ├── bump_version.py          同步全站版本號
│   └── check_site.py            網站一致性檢查
├── .gitignore
└── README.md / 部署網站.md
```

### 網站圖示（分頁與搜尋結果）

標誌的圖標就是網站圖示，三個路徑在所有頁面都以**站根絕對路徑**引用
（與姊妹專案 LinLingo 一致），這樣 `/en/` 底下的頁面不必改寫成
`../assets/`，搜尋引擎在任何頁面也都解析到同一個圖示：

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="96x96" href="/assets/favicon-96.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
```

`favicon-96.png` 選 96 是因為 Google 要求搜尋結果的 favicon 必須是
正方形、且邊長為 48 的倍數。`favicon.ico` 與 `app.ico` 是同一份多尺寸
圖示（16/24/32/48/64/128/256），應用程式倉庫的 `assets/DRTxECM.ico`
也是同一份，所以程式圖示與網站圖示永遠一致。

---

## 設計原則

| 原則 | 做法 |
|---|---|
| 不用 JavaScript | 沒有任何 `<script>`；下拉選單、導覽全部是純 HTML |
| 不追蹤 | 沒有 Google Analytics、沒有任何外部請求 |
| 不外連資源 | 樣式與圖檔全部在本站，字型用系統字型 |
| 雙語 | 中文在根目錄、英文在 `en/`，兩邊以 `hreflang` 互指 |
| 每頁獨立 SEO | 各自的 `title`、`meta description`、`canonical`、Open Graph |
| 好維護 | 全站只有一份 `style.css`，改一處全站生效 |

---

## 素材（assets/）

所有圖檔都由 `tools/make_assets.py` 產生，**請勿手動編輯**。
造型概念是「實軸 + 壓扁的 Nyquist 半圓弧」——壓扁半圓正是 CPE 相角
&alpha; &lt; 1 時 Nyquist 圖的實際樣貌，而「&alpha; 可自由擬合」是本工具的核心特色。

要調整顏色或造型，改腳本後重跑：

```bash
python tools/make_assets.py
```

## 介面截圖

`assets/screenshots/` 的四張圖是**實際啟動 GUI 產生**的，不是手繪 mockup：

```bash
python tools/make_screenshots.py
```

腳本會載入內附的 ZARC 範例資料、跑一次 DRT 與 Stage 2／Stage 3 兩次擬合，
再把視窗畫面存檔。**程式改版後重跑，截圖就會跟著更新。**
Qt 以 `offscreen` 平台外掛執行，因此不需要桌面環境。

---

## 版本號同步

網站頁首的版本號出現在 **14 個地方**（12 個 HTML 頁面的 `<span class="ver">`、
兩個下載頁的「目前版本」、以及 `latest.json`）。
為避免漏改，請用腳本同步：

```bash
python tools/bump_version.py 0.3.0
```

這個版本號必須與**應用程式倉庫的 `version.txt`** 一致，
因為 GitHub Release、Windows 檔案內容的版本資訊、以及網站顯示的版本
都應該指向同一個版本。

---

## 本機預覽

網站是純靜態檔案，直接用瀏覽器開啟 `index.html` 即可。
但 `.htaccess` 的 404 頁與 HTTPS 轉址需要伺服器才會生效，
要完整預覽可以用 Python 內建的伺服器：

```bash
python -m http.server 8000
```

再開啟 <http://localhost:8000/>。

---

## 部署

三種方式（Hostinger Git 匯入、手動上傳、GitHub Pages）與上線檢查清單，
請見 [部署網站.md](部署網站.md)。

---

## 改完網站請跑一次檢查

網站沒有建置步驟，改動就是直接改 HTML，很容易漏東西（某頁忘了改
`canonical`、導覽少了 `here` 標記、`sitemap.xml` 少一頁、版本號只改一半、
圖片路徑少一層 `../`）。這支腳本會全部檢查：

```bash
python tools/check_site.py
```

離開碼 0 表示通過。它會驗證：本機連結是否都存在、有沒有混進 JavaScript
或追蹤碼、每頁的 SEO 標註與 `hreflang`、導覽結構、`sitemap.xml` 與
`robots.txt`、全站版本號一致性（含與應用程式倉庫 `version.txt` 的比對）、
標籤是否成對、截圖是否存在。

若應用程式倉庫不在預設位置，可用環境變數指定：

```bash
set DRTXECM_REPO=C:\path\to\DRTxECM
python tools/check_site.py
```

---

## 授權

網站內容與 [DRTxECM](https://github.com/Linch-Lab/DRTxECM) 同為
[MIT License](https://github.com/Linch-Lab/DRTxECM/blob/master/LICENSE)。

DRTxECM 建構於 Ciucci Lab 的 [pyDRTtools](https://github.com/ciuccislab/pyDRTtools)
之上，引用資訊見網站的[引用與致謝](cite.html)頁。
