DRTxECM 網站素材
=================

除了 twqr-donate.jpg 之外，本資料夾的圖檔全部由 tools/make_assets.py
產生，請勿手動編輯。要調整顏色或造型，改 tools/make_assets.py 之後重跑：

    python tools/make_assets.py

| 檔案 | 用途 | 來源 |
|---|---|---|
| logo.svg | 網站頁首標誌（淺色底） | 產生 |
| logo-white.svg | 深色底版本 | 產生 |
| logo-mark.svg | 只有圖標、無文字 | 產生 |
| app.ico | 應用程式圖示（同步到應用程式倉庫） | 產生 |
| favicon-96.png | 分頁與搜尋結果的網站圖示（96x96） | 產生 |
| apple-touch-icon.png | iOS／Android 加到主畫面的圖示 | 產生 |
| og-image.png | 社群分享預覽圖（1200x630） | 產生 |
| twqr-donate.jpg | 贊助頁的 TWQR 台灣Pay 收款碼 | 手動放入，不產生 |
| screenshots/ | 真實介面截圖 | tools/make_screenshots.py |

另外會在網站根目錄產生 favicon.ico，因為瀏覽器與搜尋引擎會直接
請求 /favicon.ico：

    /favicon.ico                              傳統與自動探索
    /assets/favicon-96.png                    48 的倍數，Google 搜尋結果採用
    /assets/apple-touch-icon.png              加到主畫面

三個路徑在所有頁面都以「站根絕對路徑」引用，這樣 /en/ 底下的頁面
不必改寫成 ../assets/，也保證搜尋引擎在任何頁面都能解析到同一個圖示。

造型說明：實軸 + 壓扁的 Nyquist 半圓弧。壓扁半圓正是 CPE 相角
α < 1 時 Nyquist 圖的實際樣貌，而「α 可自由擬合」是本工具的核心特色。
