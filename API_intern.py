# this document is the internal API of the code
# it will do some continuous update on your dashboards
# all data will be stored in Excel files in the API_data/ folder
# this program needs to be inserted in the task scheduler of your computer
# and needs to run on business days — once every morning is sufficient

import yfinance as yf
import pandas as pd
import datetime
import time
import os

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "API_data")
os.makedirs(DATA_DIR, exist_ok=True)


today = datetime.date.today()


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance >= 0.2 returns a MultiIndex — flatten it to simple column names."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() for col in df.columns]
    else:
        df.columns = [col.lower() for col in df.columns]
    return df


# ==================
# USD/EUR Rate  —  data extracted from yfinance
# ==================

day_fx = today - datetime.timedelta(days=14)

print(f"[{datetime.datetime.now():%H:%M:%S}] Downloading EURUSD=X  ({day_fx} -> {today}) ...")
try:
    df_fx = yf.download("EURUSD=X", start=day_fx, end=today, auto_adjust=True, progress=False)
    df_fx = flatten_columns(df_fx)
    df_fx = df_fx[["open", "high", "low", "close"]].copy()
    df_fx.index.name = "date"

    out_fx = os.path.join(DATA_DIR, "FX.xlsx")
    df_fx.to_excel(out_fx)
    print(f"  -> saved {len(df_fx)} rows to {out_fx}")
except Exception as e:
    print(f"  [ERROR] EURUSD download failed: {e}")


time.sleep(3)

# ==================
# Sugar #11 continuous front month  (SB=F)  —  data extracted from yfinance
# ==================

beg_vol = today - datetime.timedelta(days=365)

print(f"[{datetime.datetime.now():%H:%M:%S}] Downloading SB=F  ({beg_vol} -> {today}) ...")
try:
    df_vol = yf.download("SB=F", start=beg_vol, end=today, auto_adjust=True, progress=False)
    df_vol = flatten_columns(df_vol)
    df_vol = df_vol[["open", "high", "low", "close"]].copy()
    df_vol.index.name = "date"

    
    df_vol["rets"] = df_vol["close"].pct_change()

    
    df_vol["vol_CtoC_20d"] = df_vol["rets"].rolling(20).std() * (252 ** 0.5)

    out_vol = os.path.join(DATA_DIR, "HistVolSB.xlsx")
    df_vol.to_excel(out_vol)
    print(f"  -> saved {len(df_vol)} rows to {out_vol}")
except Exception as e:
    print(f"  [ERROR] SB=F download failed: {e}")


print(f"[{datetime.datetime.now():%H:%M:%S}] API update complete.")
