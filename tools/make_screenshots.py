# -*- coding: utf-8 -*-
"""
用真實的 DRTxECM 介面產生網站用的截圖。

不是手繪的 mockup —— 這支腳本會實際啟動 GUI、載入範例 EIS 資料、
跑一次 DRT，然後把視窗畫面存成 PNG。所以網站上的截圖永遠與程式一致。

用法（必須用跑得動 DRTxECM 的 Python 環境）：

    python tools/make_screenshots.py

輸出到 assets/screenshots/：
    01-eis-loaded.png     主視窗，已匯入 EIS 資料
    02-drt-result.png     主視窗，DRT 計算完成
    03-stage2-peaks.png   Stage 2 高斯峰分解
    04-stage3-ecm.png     Stage 3 等效電路擬合

Qt 以 offscreen 平台外掛執行，因此不需要桌面環境（可在 CI 或遠端執行）。
"""

import math
import os
import re
import sys
import traceback

# ---- 設定（可用環境變數覆寫）----
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
APP_REPO = os.environ.get(
    "DRTXECM_REPO", os.path.join(os.path.dirname(SITE), "app-repo"))
OUT_DIR = os.path.join(SITE, "assets", "screenshots")

# 用哪一組範例資料（ZARC = 壓扁半圓，最能展現 CPE 的 α）
SAMPLE = os.path.join(APP_REPO, "EIS data", "text files", "zarc_data.txt")

# 必須在 import PyQt5 之前設定
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# offscreen 平台外掛不使用 Windows 的字型後端，Qt 本身又已不再附字型，
# 因此若不指定字型目錄，所有元件的文字都會是空白的（只有 matplotlib
# 畫出來的圖有字）。QT_QPA_FONTDIR 讓 Qt 的基本字型資料庫去掃系統字型。
if not os.environ.get("QT_QPA_FONTDIR"):
    for _d in (r"C:\Windows\Fonts", "/usr/share/fonts", "/System/Library/Fonts"):
        if os.path.isdir(_d):
            os.environ["QT_QPA_FONTDIR"] = _d
            break

sys.path.insert(0, APP_REPO)

import numpy as np  # noqa: E402
from PyQt5 import QtCore, QtWidgets  # noqa: E402


def load_sample(path):
    """讀入三欄資料（頻率、Z'、Z''），容忍表頭與逗號分隔。"""
    last = None
    for delimiter in (None, ",", "\t"):
        for skip in range(0, 6):
            try:
                arr = np.loadtxt(path, skiprows=skip, delimiter=delimiter)
            except Exception as exc:  # noqa: BLE001
                last = exc
                continue
            if arr.ndim == 2 and arr.shape[1] >= 3 and arr.shape[0] > 5:
                return arr[:, :3]
    raise RuntimeError(f"無法解析範例資料 {path}: {last}")


def grab(widget, name, app):
    """把 widget 目前的外觀存成 PNG。"""
    widget.repaint()
    for _ in range(8):
        app.processEvents()
    path = os.path.join(OUT_DIR, name)
    ok = widget.grab().save(path)
    print(f"  {'wrote' if ok else 'FAILED'} {name}")
    return ok


def install_fonts(app):
    """為 offscreen 平台裝上系統字型並指定預設字型家族。

    只設 QT_QPA_FONTDIR 是不夠的：Qt 會掃到整個字型目錄，然後挑到一個
    不合適的預設家族（畫面上會出現一堆亂碼般的字符）。這裡明確載入
    Segoe UI 並設為應用程式字型，畫面才會跟實際執行時一致。
    """
    from PyQt5 import QtGui  # noqa: WPS433

    for fname in ("segoeui.ttf", "segoeuib.ttf"):
        path = os.path.join(r"C:\Windows\Fonts", fname)
        if os.path.exists(path):
            QtGui.QFontDatabase.addApplicationFont(path)

    try:
        families = QtGui.QFontDatabase().families()
    except Exception:  # noqa: BLE001
        families = []

    for cand in ("Segoe UI", "Microsoft JhengHei", "DejaVu Sans"):
        if cand in families:
            app.setFont(QtGui.QFont(cand, 9))
            print(f"  font: {cand}")
            return
    print("  font: (none found, using Qt default)")


def silence_message_boxes():
    """把 QMessageBox 的靜態方法換成 no-op。

    Stage 2／Stage 3 的擬合在成功與失敗時都會彈出 modal 訊息框。
    在 offscreen 模式下這些框會卡住腳本；而「從 timer 去關掉 modal 視窗」
    會在 Qt 的巢狀事件圈裡造成 access violation（0xC0000005）而讓行程崩潰。
    直接讓訊息框不要出現，既安全又不需要人工介入。這是測試腳本的常見做法。
    """
    QtWidgets.QMessageBox.information = staticmethod(lambda *a, **k: None)
    QtWidgets.QMessageBox.warning = staticmethod(lambda *a, **k: None)
    QtWidgets.QMessageBox.critical = staticmethod(lambda *a, **k: None)
    QtWidgets.QMessageBox.question = staticmethod(
        lambda *a, **k: QtWidgets.QMessageBox.No)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    from pyDRTtools.GUI import GUI
    from pyDRTtools.runs import EIS_object
    from pyDRTtools import extensions

    app = QtWidgets.QApplication([])
    install_fonts(app)
    silence_message_boxes()

    # 安全網：offscreen 模式下若有任何 modal 視窗彈出，會讓腳本卡死。
    # 這個 timer 會自動把它們關掉。
    def close_modals():
        w = app.activeModalWidget()
        if w is not None:
            print(f"  (auto-closing modal: {type(w).__name__})")
            w.close()

    watchdog = QtCore.QTimer()
    watchdog.timeout.connect(close_modals)
    watchdog.start(500)

    print("launching GUI (offscreen)...")
    win = GUI()
    win.resize(1500, 950)
    win.show()
    app.processEvents()

    # ---- 1. 匯入範例資料 ----
    arr = load_sample(SAMPLE)
    print(f"sample: {SAMPLE}")
    print(f"        {arr.shape[0]} points, "
          f"freq {arr[:, 0].min():.3g} .. {arr[:, 0].max():.3g} Hz")
    win.data = EIS_object(arr[:, 0], arr[:, 1], arr[:, 2])
    win.inductance_callback()
    app.processEvents()
    grab(win, "01-eis-loaded.png", app)

    # ---- 2. 跑一次 DRT（用介面預設值：Gaussian / GCV）----
    print("running DRT (Simple Run / GCV) - this can take a while...")
    try:
        win.simple_run_callback()
        app.processEvents()
        print(f"  gamma computed: {hasattr(win.data, 'gamma')}")
        grab(win, "02-drt-result.png", app)
    except Exception:  # noqa: BLE001
        print("  DRT run FAILED:")
        traceback.print_exc()

    # ---- 3. Stage 2：高斯峰分解（實際執行擬合）----
    dlg2 = None
    try:
        win.ui.peak_num_entry.setText("3")
        dlg2 = extensions.Stage2Window(win, win.data, 3)
        dlg2.resize(1250, 800)
        dlg2.show()
        app.processEvents()
        # 執行真正的多高斯擬合（成功時會彈出 modal 訊息框，由 watchdog 關掉）
        dlg2.run_fitting()
        app.processEvents()
        grab(dlg2, "03-stage2-peaks.png", app)
    except Exception:  # noqa: BLE001
        print("  Stage 2 capture FAILED:")
        traceback.print_exc()

    # ---- 4. Stage 3：等效電路擬合（實際執行 CNLS 優化）----
    try:
        # 用 Stage 2 擬合出來的峰，套用程式自己的換算公式當作初始值：
        #   R = A·σ·√(2π)、τ = exp(μ)、Q = τ/R、α = 1
        params, _ = dlg2.get_params()
        triplets = [params[i:i + 3] for i in range(0, len(params), 3)]
        triplets.sort(key=lambda t: t[1])
        peaks = []
        for amp, cen, wid in triplets:
            r_ohm = float(amp * wid * math.sqrt(2 * math.pi))
            tau = float(math.exp(cen))
            peaks.append({
                "R": r_ohm,
                "Q": (tau / r_ohm) if r_ohm else 1e-6,
                "alpha": 1.0,
            })

        dlg3 = extensions.Stage3Window(win, win.data, dlg2.ohmic_R,
                                      dlg2.inductance_L, peaks)
        dlg3.resize(1500, 900)
        dlg3.show()
        app.processEvents()

        # 放開 R、Q（設成 ±10%），α 維持 <= 1，讓 CNLS 真的有東西可優化，
        # 這樣截圖上才會出現 Error / Error% 與更新後的 RMSE。
        # 注意：下拉選單的項目字串是 ASCII 的 "Free +-10%"，不是 "Free ±10%"。
        for key, w in dlg3.param_widgets.items():
            if re.match(r"^[RQ]_\d+$", key):
                w["mode"].setCurrentText("Free +-10%")
        app.processEvents()

        print("running CNLS fitting...")
        dlg3.run_fitting()
        app.processEvents()
        grab(dlg3, "04-stage3-ecm.png", app)
    except Exception:  # noqa: BLE001
        print("  Stage 3 capture FAILED:")
        traceback.print_exc()

    watchdog.stop()
    print("\ndone ->", OUT_DIR)


if __name__ == "__main__":
    main()
