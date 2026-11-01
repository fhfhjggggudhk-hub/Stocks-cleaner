"""
⚡ AI Stock Screener Pro — NSE + BSE সব স্টক, Weekly + Daily Higher Low স্ক্যানার  (একটাই ফাইল)

  ⭐ আজকের সেরা স্টক : রোজ বিকেলে GitHub Action স্ক্যান করে data/picks.json বানায়; অ্যাপ খুললেই ফল দেখা যায়
  🔍 লাইভ স্ক্যানার  : নিজে ফিল্টার বদলে স্ক্যান + যেকোনো স্টকের ১৫-পয়েন্ট ডিপ অ্যানালাইসিস

অ্যাপ চালাতে:      streamlit run app.py
রোজকার স্ক্যান:     python -c "import app; app.run_job()"      (GitHub Action এটাই চালায়)
এটি শুধু শিক্ষামূলক টুল, আর্থিক পরামর্শ নয়। কোনো কৌশলেই লাভের নিশ্চয়তা নেই।
"""
import io
import json
import os
import random
import re
import sys
import time
from datetime import date, datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

IST = ZoneInfo("Asia/Kolkata")
MARKET_CLOSE = pd.Timedelta(hours=15, minutes=30)
BATCH_SIZE = 100

NSE_EQUITY_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"

TIMEFRAMES = {
    "1 Day (Daily)": dict(period="1y", interval="1d", weekly=False),
    "1 Week (Weekly)": dict(period="3y", interval="1wk", weekly=True),
}

STATUS_MID = "🟢 In Range (₹500 - ₹2,000)"
STATUS_HIGH = "🔴 Above ₹2,000"
STATUS_LOW = "🟡 Below ₹500"

W_OFF = "বন্ধ (ফিল্টার নেই)"
W_UP = "Weekly Uptrend (EMA20 > EMA50)"
W_HL = "Weekly Higher Low"
W_BOTH = "Weekly Uptrend + Higher Low"
WEEKLY_HL_PARAMS = dict(n=2, min_rise_pct=1.0, min_swing_pct=3.0, max_age=8, max_dist_pct=30.0)

UNI_ALL = "সব NSE স্টক (অটো ডাউনলোড)"
UNI_BUILTIN = "বাছাই করা লিকুইড স্টক (বিল্ট-ইন)"
UNI_UPLOAD = "নিজের টিকার ফাইল আপলোড (.txt / .csv)"

# নেটওয়ার্ক সমস্যা হলে এই ছোট তালিকা ব্যবহার হবে। ভুল টিকার থাকলে "ডেটা না পাওয়া" তালিকায় দেখাবে।
FALLBACK_TICKERS = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL",
    "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO",
    "BAJFINANCE", "NESTLEIND", "WIPRO", "HCLTECH", "M&M", "NTPC", "POWERGRID", "TATASTEEL",
    "JSWSTEEL", "ONGC", "COALINDIA", "ADANIENT", "ADANIPORTS", "BAJAJFINSV", "TECHM", "GRASIM",
    "HINDALCO", "DRREDDY", "CIPLA", "EICHERMOT", "BRITANNIA", "APOLLOHOSP", "DIVISLAB",
    "HEROMOTOCO", "BPCL", "INDUSINDBK", "TATACONSUM", "SBILIFE", "HDFCLIFE", "BAJAJ-AUTO",
    "SHRIRAMFIN", "TRENT", "BEL", "HAL", "IRCTC", "DMART", "PIDILITIND", "DLF", "GAIL", "IOC",
    "VEDL", "SIEMENS", "ABB", "TATAPOWER", "PNB", "BANKBARODA", "CANBK", "UNIONBANK",
    "FEDERALBNK", "IDFCFIRSTB", "AUBANK", "PFC", "RECLTD", "IRFC", "RVNL", "NHPC", "SUZLON",
    "YESBANK", "IDEA", "TVSMOTOR", "ASHOKLEY", "BHARATFORG", "MOTHERSON", "POLYCAB", "HAVELLS",
    "DIXON", "VOLTAS", "LUPIN", "AUROPHARMA", "TORNTPHARM", "ZYDUSLIFE", "MAXHEALTH", "FORTIS",
    "NAUKRI", "PERSISTENT", "COFORGE", "MPHASIS", "JINDALSTEL", "SAIL", "NMDC", "AMBUJACEM",
    "SHREECEM", "DABUR", "GODREJCP", "MARICO", "COLPAL", "PAGEIND", "BOSCHLTD", "CUMMINSIND",
    "INDIGO", "JIOFIN", "LICI", "HINDPETRO", "BHEL", "MAZDOCK", "COCHINSHIP", "BSE", "ANGELONE",
]


# ───────────────────────── স্টক তালিকা ─────────────────────────
def _dedupe(seq):
    return list(dict.fromkeys(seq))


def parse_uploaded_tickers(uploaded):
    text = uploaded.read().decode("utf-8", errors="ignore")
    out = []
    for tok in re.split(r"[,\s;]+", text):
        tok = tok.strip().strip('"').strip("'")
        if not tok or tok.upper() in {"SYMBOL", "TICKER", "NAME", "STOCK"}:
            continue
        if not re.fullmatch(r"[A-Za-z0-9&\-\.]+", tok):
            continue
        out.append(tok.upper() if "." in tok else tok.upper() + ".NS")
    return _dedupe(out)



# ───────────────────────── ডেটা ডাউনলোড ─────────────────────────
def _download(tickers, period, interval):
    try:
        raw = yf.download(
            list(tickers), period=period, interval=interval, group_by="ticker",
            auto_adjust=False, threads=True, progress=False,
        )
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    if raw is None or raw.empty:
        return out
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = set(raw.columns.get_level_values(0))
        for t in tickers:
            if t in level0:
                d = raw[t].dropna(how="all")
                if not d.empty:
                    out[t] = d
    elif len(tickers) == 1:
        d = raw.dropna(how="all")
        if not d.empty:
            out[tickers[0]] = d
    return out


_CACHE = {}


def _cached_download(tickers, period, interval):
    key = (tickers, period, interval)
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    out = _download(tickers, period, interval)
    if not out:
        raise ValueError("empty")  # খালি ফলাফল ক্যাশ হবে না
    if len(_CACHE) >= 30:
        _CACHE.pop(min(_CACHE, key=lambda k: _CACHE[k][0]))
    _CACHE[key] = (time.time(), out)
    return out


def download_batch(tickers, period, interval):
    for _ in range(2):
        try:
            return _cached_download(tuple(tickers), period, interval)
        except Exception:  # noqa: BLE001
            time.sleep(1.5)
    return {}


def prepare_frame(df, cfg=None):
    return df.dropna(subset=["Open", "High", "Low", "Close"])


def drop_forming_candle(df, cfg):
    """চলমান (অসম্পূর্ণ) শেষ ক্যান্ডেল বাদ দেয়: দৈনিক = ১৫:৩০-এর আগে, সাপ্তাহিক = শুক্রবার ১৫:৩০-এর আগে।"""
    if df.empty:
        return df
    if cfg.get("weekly"):
        return drop_forming_weekly(df)
    last = df.index[-1]
    if last.tzinfo is None:
        last = last.tz_localize(IST)
    end = last.normalize() + MARKET_CLOSE
    return df if end <= datetime.now(IST) else df.iloc[:-1]


# ───────────────────────── Higher Low ─────────────────────────
def _swing_lows(L, n):
    idx = []
    for i in range(n, len(L) - n):
        if L[i] < L[i - n:i].min() and L[i] <= L[i + 1:i + n + 1].min():
            idx.append(i)
    return idx


def _swing_highs(H, n):
    idx = []
    for i in range(n, len(H) - n):
        if H[i] > H[i - n:i].max() and H[i] >= H[i + 1:i + n + 1].max():
            idx.append(i)
    return idx


def check_higher_low(df, n=3, min_rise_pct=0.3, min_swing_pct=1.0, max_age=10, max_dist_pct=5.0):
    """df = শুধু বন্ধ-হওয়া ক্যান্ডেল। Higher Low পেলে dict, নাহলে None।"""
    if len(df) < 2 * n + 10:
        return None
    L = df["Low"].to_numpy(float)
    H = df["High"].to_numpy(float)
    C = df["Close"].to_numpy(float)
    sl = _swing_lows(L, n)
    if len(sl) < 2:
        return None
    i1, i2 = sl[-2], sl[-1]
    low1, low2 = L[i1], L[i2]
    if low2 <= low1 * (1 + min_rise_pct / 100):
        return None  # Higher Low নয়
    if (H[i1:i2 + 1].max() - low1) / low1 * 100 < min_swing_pct:
        return None  # দুই লো-এর মাঝে আসল উঠা-নামা হয়নি
    age = len(df) - 1 - i2
    if age > max_age:
        return None  # পুরনো
    last_close = C[-1]
    if last_close < low2:
        return None  # HL ভেঙে গেছে
    dist = (last_close - low2) / low2 * 100
    if dist > max_dist_pct:
        return None  # দাম HL থেকে অনেক উপরে চলে গেছে
    recent = [L[i] for i in sl[-5:]]
    count = 1
    for a, b in zip(recent[-2::-1], recent[:0:-1]):
        if b > a:
            count += 1
        else:
            break
    return dict(idx=i2, hl=float(low2), prev=float(low1), age=age, dist=float(dist),
                count=count, time=df.index[i2])


# ───────────────────────── ক্যান্ডেল প্যাটার্ন ─────────────────────────
def bullish_shape(O, H, L, C, j, loose=False):
    """j-তম ক্যান্ডেলে শেষ হওয়া বুলিশ প্যাটার্ন → (নাম, প্যাটার্নের সর্বনিম্ন Low) বা None।"""
    if j < 2:
        return None
    o1, h1, l1, c1 = O[j], H[j], L[j], C[j]
    o2, h2, l2, c2 = O[j - 1], H[j - 1], L[j - 1], C[j - 1]
    o3, h3, l3, c3 = O[j - 2], H[j - 2], L[j - 2], C[j - 2]
    rng1 = h1 - l1
    if rng1 <= 0:
        return None
    b1, b2, b3 = abs(c1 - o1), abs(c2 - o2), abs(c3 - o3)
    lower1 = min(o1, c1) - l1
    upper1 = h1 - max(o1, c1)
    g1, r2, r3 = c1 > o1, c2 < o2, c3 < o3
    if r3 and (h3 - l3) > 0 and b3 >= 0.5 * (h3 - l3) and b2 <= 0.3 * (h2 - l2) and g1 and c1 > (o3 + c3) / 2:
        return "🌟 Morning Star", min(l1, l2, l3)
    if r2 and g1 and c1 >= o2 and o1 <= c2 and b1 > b2:
        return "🔥 Bullish Engulfing", min(l1, l2)
    if r2 and g1 and o1 < c2 and c1 > (o2 + c2) / 2 and c1 < o2:
        return "⚡ Piercing Line", min(l1, l2)
    if r2 and g1 and abs(l1 - l2) <= 0.1 * rng1 and b2 > 0:
        return "🪜 Tweezer Bottom", min(l1, l2)
    if r2 and g1 and o1 > c2 and c1 < o2 and b2 >= 0.5 * (h2 - l2):
        return "🤰 Bullish Harami", min(l1, l2)
    if b1 > 0 and lower1 >= 2 * b1 and upper1 <= 0.2 * b1:
        return ("🔨 Green Hammer" if g1 else "🔨 Hammer (Red)"), l1
    if g1 and b1 > 0 and upper1 >= 2 * b1 and lower1 <= 0.2 * b1:
        return "🙃 Inverted Hammer", l1
    if b1 <= 0.1 * rng1 and lower1 >= 0.6 * rng1 and upper1 <= 0.1 * rng1:
        return "🐉 Dragonfly Doji", l1
    if loose and b1 <= 0.1 * rng1:
        return "➕ Doji", l1
    return None


def bearish_shape(O, H, L, C, j):
    """বেয়ারিশ প্যাটার্ন → (নাম, প্যাটার্নের সর্বোচ্চ High) বা None।"""
    if j < 2:
        return None
    o1, h1, l1, c1 = O[j], H[j], L[j], C[j]
    o2, h2, l2, c2 = O[j - 1], H[j - 1], L[j - 1], C[j - 1]
    o3, h3, l3, c3 = O[j - 2], H[j - 2], L[j - 2], C[j - 2]
    rng1 = h1 - l1
    if rng1 <= 0:
        return None
    b1, b2, b3 = abs(c1 - o1), abs(c2 - o2), abs(c3 - o3)
    lower1 = min(o1, c1) - l1
    upper1 = h1 - max(o1, c1)
    r1, g2, g3 = c1 < o1, c2 > o2, c3 > o3
    if g3 and (h3 - l3) > 0 and b3 >= 0.5 * (h3 - l3) and b2 <= 0.3 * (h2 - l2) and r1 and c1 < (o3 + c3) / 2:
        return "🌩️ Evening Star", max(h1, h2, h3)
    if g2 and r1 and c1 <= o2 and o1 >= c2 and b1 > b2:
        return "❄️ Bearish Engulfing", max(h1, h2)
    if g2 and r1 and o1 > c2 and c1 < (o2 + c2) / 2 and c1 > o2:
        return "🌧️ Dark Cloud Cover", max(h1, h2)
    if r1 and b1 > 0 and upper1 >= 2 * b1 and lower1 <= 0.2 * b1:
        return "🌠 Shooting Star", h1
    if r1 and b1 > 0 and lower1 >= 2 * b1 and upper1 <= 0.2 * b1:
        return "🪢 Hanging Man", h1
    if b1 <= 0.1 * rng1 and upper1 >= 0.6 * rng1 and lower1 <= 0.1 * rng1:
        return "🪦 Gravestone Doji", h1
    return None


# ───────────────────────── একটি স্টকের বিশ্লেষণ ─────────────────────────
def price_status(price):
    if price < 500:
        return STATUS_LOW
    return STATUS_MID if price <= 2000 else STATUS_HIGH


def analyze_stock(df, p):
    """df = শুধু বন্ধ-হওয়া ক্যান্ডেল। কিছু না মিললে None।"""
    n = len(df)
    if n < 30:
        return None
    O = df["Open"].to_numpy(float)
    H = df["High"].to_numpy(float)
    L = df["Low"].to_numpy(float)
    C = df["Close"].to_numpy(float)
    vol = df["Volume"].fillna(0).to_numpy(float) if "Volume" in df else np.zeros(n)
    if vol[-20:].mean() < p["min_vol"]:
        return None

    pc = np.roll(C, 1)
    pc[0] = C[0]
    tr = np.maximum.reduce([H - L, np.abs(H - pc), np.abs(L - pc)])
    atr = pd.Series(tr).rolling(14, min_periods=5).mean().to_numpy()
    ema20 = pd.Series(C).ewm(span=20, adjust=False).mean().to_numpy()
    ema50 = pd.Series(C).ewm(span=50, adjust=False).mean().to_numpy()

    def tol(j, mult=0.5):
        return mult * atr[j] if np.isfinite(atr[j]) else 0.005 * C[j]

    price = float(C[-1])
    rng = H[-1] - L[-1]
    res = dict(
        price=round(price, 2), status=price_status(price),
        up=bool(C[-1] > ema50[-1] and ema20[-1] > ema50[-1]),
        buyer=round((C[-1] - L[-1]) / rng * 100, 1) if rng > 0 else 50.0,
        seller=round((H[-1] - C[-1]) / rng * 100, 1) if rng > 0 else 50.0,
        hl=None, hl_pattern=None, sr_type=None, sr_pattern=None,
    )

    # ১) Higher Low + HL-এর কাছে বুলিশ ক্যান্ডেল
    hl = check_higher_low(df, p["n"], p["min_rise"], p["min_swing"], p["max_age"], p["max_dist"])
    if hl:
        i2 = hl["idx"]
        for j in range(i2, min(i2 + 4, n)):
            found = bullish_shape(O, H, L, C, j, loose=True)
            if found and abs(found[1] - hl["hl"]) <= tol(j, 1.0):
                res["hl_pattern"] = found[0]
                break
        # HL কোন সাপোর্টে টিকেছে?
        a = tol(i2, 2.0)  # = 1 ATR
        zones = []
        if abs(hl["hl"] - ema20[i2]) <= a:
            zones.append("EMA20")
        if abs(hl["hl"] - ema50[i2]) <= a:
            zones.append("EMA50")
        old_highs = [H[k] for k in _swing_highs(H[:i2 - 2], 3)]
        if any(abs(hl["hl"] - h) <= a for h in old_highs):
            zones.append("পুরনো রেজিস্ট্যান্স")
        hl["support"] = " + ".join(zones) if zones else "—"
        stop = hl["hl"]
        risk = price - stop
        hl.update(stop=round(stop, 2), risk_pct=round(risk / price * 100, 2),
                  target=round(price + 2 * risk, 2))
        res["hl"] = hl

    # ২) শেষ ক্যান্ডেলে সাপোর্ট/রেজিস্ট্যান্স প্যাটার্ন
    j = n - 1
    if n >= 25:
        recent_low = L[j - 22:j - 2].min()
        recent_high = H[j - 22:j - 2].max()
        bull = bullish_shape(O, H, L, C, j)
        if bull and bull[1] <= recent_low + tol(j):
            res["sr_type"], res["sr_pattern"] = "Bullish", bull[0]
        else:
            bear = bearish_shape(O, H, L, C, j)
            if bear and bear[1] >= recent_high - tol(j):
                res["sr_type"], res["sr_pattern"] = "Bearish", bear[0]

    if res["hl"] is None and res["sr_type"] is None:
        return None
    return res


# ───────────────────────── সাপ্তাহিক ট্রেন্ড ─────────────────────────
def drop_forming_weekly(df):
    """চলতি সপ্তাহ শুক্রবার ১৫:৩০-এর আগে পর্যন্ত অসম্পূর্ণ; সেটি বাদ দেয়।"""
    if df.empty:
        return df
    last = df.index[-1]
    if last.tzinfo is None:
        last = last.tz_localize(IST)
    monday = last.normalize() - pd.Timedelta(days=last.weekday())
    end = monday + pd.Timedelta(days=4) + MARKET_CLOSE
    return df if end <= datetime.now(IST) else df.iloc[:-1]


def weekly_flags(df):
    """(weekly_uptrend, weekly_higher_low) অথবা None।"""
    df = drop_forming_weekly(df.dropna(subset=["Open", "High", "Low", "Close"]))
    if len(df) < 30:
        return None
    C = df["Close"].to_numpy(float)
    ema20 = pd.Series(C).ewm(span=20, adjust=False).mean().to_numpy()
    ema50 = pd.Series(C).ewm(span=50, adjust=False).mean().to_numpy()
    up = bool(C[-1] > ema50[-1] and ema20[-1] > ema50[-1])
    hl = check_higher_low(df, **WEEKLY_HL_PARAMS) is not None
    return up, hl


# ───────────────────────── ইন্ডিকেটর ও ১৫-পয়েন্ট বিশ্লেষণ ─────────────────────────
OK, WARN, BAD, NA = "✅", "⚠️", "❌", "❓"

SECTOR_INDEX = {  # yfinance সেক্টর → NSE ইনডেক্স (আনুমানিক ম্যাপিং; ইচ্ছেমতো বদলান)
    "Technology": "^CNXIT", "Financial Services": "^NSEBANK", "Healthcare": "^CNXPHARMA",
    "Energy": "^CNXENERGY", "Consumer Defensive": "^CNXFMCG", "Consumer Cyclical": "^CNXAUTO",
    "Basic Materials": "^CNXMETAL", "Industrials": "^CNXINFRA", "Real Estate": "^CNXREALTY",
    "Utilities": "^CNXENERGY", "Communication Services": "^CNXMEDIA",
}
SECTOR_CHOICES = {
    "অটো (কোম্পানির সেক্টর থেকে)": None, "IT": "^CNXIT", "Bank": "^NSEBANK", "Pharma": "^CNXPHARMA",
    "Energy": "^CNXENERGY", "FMCG": "^CNXFMCG", "Auto": "^CNXAUTO", "Metal": "^CNXMETAL",
    "Infra": "^CNXINFRA", "Realty": "^CNXREALTY", "Media": "^CNXMEDIA",
}
WEIGHTS = {"4D": 14, "4W": 14, "5": 12, "6": 12, "7": 10, "8": 14, "10": 14, "14": 5, "15": 5, "1": 6, "3": 8}
POINTS = {OK: 1.0, WARN: 0.5, BAD: 0.0}
ORDER = ["1", "2", "3", "4D", "4W", "5", "6", "7", "8", "10", "13", "14", "15"]


def _ema(x, span):
    return pd.Series(x).ewm(span=span, adjust=False).mean().to_numpy()


def _atr(H, L, C, period=14):
    pc = np.roll(C, 1)
    pc[0] = C[0]
    tr = np.maximum.reduce([H - L, np.abs(H - pc), np.abs(L - pc)])
    return pd.Series(tr).rolling(period, min_periods=5).mean().to_numpy()


def _rsi(C, period=14):
    delta = np.diff(C, prepend=C[0])
    gain = pd.Series(np.where(delta > 0, delta, 0.0)).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    loss = pd.Series(np.where(delta < 0, -delta, 0.0)).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi[(loss == 0) & gain.notna()] = 100.0
    return rsi.to_numpy()


def _fm(x):
    return "—" if x is None else f"{x:,.1f}"


def trend_label(C):
    if len(C) < 30:
        return None
    e20, e50 = _ema(C, 20), _ema(C, 50)
    if C[-1] > e50[-1] and e20[-1] > e50[-1]:
        return "Uptrend"
    if C[-1] < e50[-1] and e20[-1] < e50[-1]:
        return "Downtrend"
    return "Sideways"


def _cluster(levels, tol_pct=0.6):
    groups = []
    for lv in sorted(levels):
        if groups and abs(lv - groups[-1][-1]) / groups[-1][-1] * 100 <= tol_pct:
            groups[-1].append(lv)
        else:
            groups.append([lv])
    return [float(np.mean(g)) for g in groups]


def _levels(df, n, lookback):
    """(swing-low স্তর, swing-high স্তর) — কাছাকাছিগুলো মিলিয়ে।"""
    d = df.tail(lookback)
    if len(d) < 2 * n + 3:
        return [], []
    L = d["Low"].to_numpy(float)
    H = d["High"].to_numpy(float)
    lows = [float(L[i]) for i in _swing_lows(L, n)] + [float(L.min())]
    highs = [float(H[i]) for i in _swing_highs(H, n)] + [float(H.max())]
    return _cluster(lows), _cluster(highs)


def fib_info(df, n, atr_val):
    H = df["High"].to_numpy(float)
    L = df["Low"].to_numpy(float)
    sh = _swing_highs(H, n)
    if not sh:
        return None
    hi = sh[-1]
    before = [i for i in _swing_lows(L, n) if i < hi]
    if not before:
        return None
    A, B = float(L[before[-1]]), float(H[hi])
    if B <= A:
        return None
    pull = float(L[hi:].min())
    levels = {r: B - r * (B - A) for r in (0.382, 0.5, 0.618)}
    tol = max(0.75 * atr_val, 0.003 * pull)
    near = [r for r, v in levels.items() if abs(pull - v) <= tol]
    return dict(A=A, B=B, pull=pull, retr=(B - pull) / (B - A), levels=levels, near=near)


def _ret_by_date(df):
    s = pd.Series(df["Close"].to_numpy(float), index=[x.date() for x in df.index])
    return s.pct_change()


def price_checks(d, w, p, nifty=None):
    """শুধু দাম/ভলিউম-ভিত্তিক পয়েন্টগুলো (৪, ৫, ৬, ৭, ৮, ৯, ১০, ১৪, ১৫)।
    d = বন্ধ-হওয়া দৈনিক ক্যান্ডেল, w = বন্ধ-হওয়া সাপ্তাহিক ক্যান্ডেল (বা None)।"""
    n = len(d)
    O = d["Open"].to_numpy(float)
    H = d["High"].to_numpy(float)
    L = d["Low"].to_numpy(float)
    C = d["Close"].to_numpy(float)
    V = d["Volume"].fillna(0).to_numpy(float)
    atr = _atr(H, L, C)
    a = float(atr[-1]) if np.isfinite(atr[-1]) else C[-1] * 0.01
    e20, e50 = _ema(C, 20), _ema(C, 50)
    rsi = _rsi(C)
    price = float(C[-1])
    checks = []

    def add(i, title, status, detail):
        checks.append(dict(id=i, title=title, status=status, detail=detail))

    # ── অ্যাঙ্কর: Higher Low (না থাকলে সাম্প্রতিক swing low)
    hl = check_higher_low(d, p["n"], p["min_rise"], p["min_swing"], p["max_age"], p["max_dist"])
    ai = anchor = None
    src = ""
    if hl:
        ai, anchor, src = hl["idx"], hl["hl"], "Higher Low"
    else:
        cand = [i for i in _swing_lows(L, p["n"]) if i >= n - 30]
        if cand:
            ai, anchor, src = cand[-1], float(L[cand[-1]]), "সর্বশেষ Swing Low (HL শর্ত পূরণ হয়নি)"
    a_i = float(atr[ai]) if ai is not None and np.isfinite(atr[ai]) else a

    # ── সাপ্তাহিক ডেটা
    wok = w is not None and len(w) >= 30
    w_levels, wl = [], []
    a_w = rsi_w = None
    if wok:
        Ow = w["Open"].to_numpy(float)
        Hw = w["High"].to_numpy(float)
        Lw = w["Low"].to_numpy(float)
        Cw = w["Close"].to_numpy(float)
        atr_w = _atr(Hw, Lw, Cw)
        a_w = float(atr_w[-1]) if np.isfinite(atr_w[-1]) else Cw[-1] * 0.03
        wl, wh = _levels(w, 2, 104)
        w_levels = _cluster(wl + wh)
        rsi_w = _rsi(Cw)[-1]

    # ── ৪: ট্রেন্ড (1D + 1W)
    td = trend_label(C)
    tmap = {"Uptrend": OK, "Sideways": WARN, "Downtrend": BAD}
    add("4D", "দৈনিক ট্রেন্ড (1D)", tmap.get(td, NA),
        f"{td}: EMA20 {e20[-1]:.1f} | EMA50 {e50[-1]:.1f} | দাম {price:.1f}" if td else "ডেটা কম")
    if wok:
        tw = trend_label(Cw)
        add("4W", "সাপ্তাহিক ট্রেন্ড (1W)", tmap.get(tw, NA),
            f"{tw}: EMA20 {_ema(Cw, 20)[-1]:.1f} | EMA50 {_ema(Cw, 50)[-1]:.1f} | সাপ্তাহিক RSI "
            + ("—" if rsi_w is None or not np.isfinite(rsi_w) else f"{rsi_w:.0f}"))
    else:
        add("4W", "সাপ্তাহিক ট্রেন্ড (1W)", NA, "সাপ্তাহিক ডেটা যথেষ্ট নেই")

    # ── ৫: সাপোর্ট-রেজিস্ট্যান্স
    dl, dh = _levels(d, 3, 120)
    d_levels = _cluster(dl + dh)
    sup_d = max([x for x in d_levels if x < price], default=None)
    res_d = min([x for x in d_levels if x > price], default=None)
    sup_w = max([x for x in w_levels if x < price], default=None)
    res_w = min([x for x in w_levels if x > price], default=None)
    lv_text = (f"সাপোর্ট: দৈনিক {_fm(sup_d)}, সাপ্তাহিক {_fm(sup_w)} | "
               f"রেজিস্ট্যান্স: দৈনিক {_fm(res_d)}, সাপ্তাহিক {_fm(res_w)}")
    if anchor is None:
        add("5", "সাপোর্ট-রেজিস্ট্যান্স (1D+1W)", NA, "কোনো স্পষ্ট নিচের পয়েন্ট নেই | " + lv_text)
    else:
        pl, ph = _levels(d.iloc[:ai - 2], 3, 120) if ai > 12 else ([], [])
        prior = _cluster(pl + ph)
        hit_d = any(abs(anchor - x) <= a_i for x in prior)
        hit_w = any(abs(anchor - x) <= a_i for x in w_levels)
        st5 = OK if hit_w else (WARN if hit_d else BAD)
        where = "সাপ্তাহিক জোনে" if hit_w else ("দৈনিক জোনে" if hit_d else "কোনো পুরনো জোনে নয়")
        add("5", "সাপোর্ট-রেজিস্ট্যান্স (1D+1W)", st5, f"{src} ₹{anchor:.1f} {where} টিকেছে | " + lv_text)

    # ── ৬: ফিবোনাচি + EMA + RSI
    fib = fib_info(d, 3, a_i)
    fib_sig = bool(fib and fib["near"])
    near20 = anchor is not None and abs(anchor - e20[ai]) <= a_i
    near50 = anchor is not None and abs(anchor - e50[ai]) <= a_i
    ema_sig = bool(near20 or near50)
    lo, hi2 = (max(0, ai - 3), min(n, ai + 4)) if ai is not None else (max(0, n - 10), n)
    rw = rsi[lo:hi2]
    rsi_min = float(np.nanmin(rw)) if np.isfinite(rw).any() else None
    rsi_sig = rsi_min is not None and rsi_min < 40
    cnt = int(fib_sig) + int(ema_sig) + int(rsi_sig)
    fib_txt = ("Fib: স্পষ্ট swing নেই" if not fib else
               f"Fib পুলব্যাক {fib['retr'] * 100:.0f}%" + (f" (≈{'/'.join(str(r) for r in fib['near'])})" if fib["near"] else ""))
    ema_txt = "EMA: " + ("+".join(x for x, f in (("20", near20), ("50", near50)) if f) + " সাপোর্ট" if ema_sig else "কাছে নয়")
    rsi_txt = "RSI: " + ("—" if rsi_min is None else f"সর্বনিম্ন {rsi_min:.0f}" + (" (<40 ✔)" if rsi_sig else ""))
    add("6", "ফিবোনাচি + EMA + RSI", OK if cnt >= 2 else (WARN if cnt == 1 else BAD),
        f"{cnt}/3 | {fib_txt} | {ema_txt} | {rsi_txt}")

    # ── ৭: ভলিউম
    base = None
    if ai is not None:
        pre = V[max(0, ai - 22):max(1, ai - 2)]
        base = float(pre.mean()) if len(pre) >= 5 else float(V[:max(ai, 1)].mean())
    if ai is None or not base or base <= 0:
        add("7", "ভলিউম অ্যানালাইসিস", NA, "সাপোর্ট পয়েন্ট/ভলিউম ডেটা নেই")
    else:
        near_v = V[max(0, ai - 3):max(ai, 1)]  # সাপোর্টে পৌঁছানোর আগের ৩ ক্যান্ডেল (বিক্রির চাপ)
        after = V[ai + 1:]
        dry = near_v.mean() <= 0.9 * base
        bounce = len(after) > 0 and after.mean() >= base
        add("7", "ভলিউম অ্যানালাইসিস", OK if (dry and bounce) else (WARN if (dry or bounce) else BAD),
            f"সাপোর্টে ভলিউম গড়ের {near_v.mean() / base * 100:.0f}% ({'শুকিয়েছে' if dry else 'শুকায়নি'})"
            + (f" | বাউন্সে {after.mean() / base * 100:.0f}% ({'বাড়ছে' if bounce else 'বাড়েনি'})" if len(after) else ""))

    # ── ৮: এন্ট্রি ক্যান্ডেল (দৈনিক) + সাপ্তাহিক ক্যান্ডেল
    pat = plow = trig = None
    if ai is not None:
        for j in range(ai, min(ai + 4, n)):
            f = bullish_shape(O, H, L, C, j, loose=True)
            if f and abs(f[1] - anchor) <= a_i:
                pat, plow, trig = f[0], f[1], j
                break
    wpat = None
    if wok:
        f = bullish_shape(Ow, Hw, Lw, Cw, len(w) - 1, loose=True)
        if f and any(abs(f[1] - x) <= a_w for x in wl):
            wpat = f[0]
    if ai is None:
        add("8", "এন্ট্রি ক্যান্ডেল সিগন্যাল", NA, "সাপোর্ট পয়েন্ট নেই")
    else:
        add("8", "এন্ট্রি ক্যান্ডেল সিগন্যাল",
            OK if (pat and pat != "➕ Doji") else (WARN if (pat or wpat) else BAD),
            (f"দৈনিক: {pat}" if pat else "দৈনিক: কোনো বুলিশ প্যাটার্ন নেই")
            + (f" | সাপ্তাহিক: {wpat}" if wpat else ""))

    # ── ১৪: স্মার্ট মানি ভলিউম স্পাইক
    idx = trig if trig is not None else ai
    if idx is None or idx < 6:
        add("14", "স্মার্ট মানি ভলিউম স্পাইক", NA, "ডেটা নেই")
    else:
        b20 = V[max(0, idx - 20):idx].mean()
        ratio = V[idx] / b20 if b20 > 0 else 0
        add("14", "স্মার্ট মানি ভলিউম স্পাইক", OK if ratio >= 1.8 else (WARN if ratio >= 1.3 else BAD),
            f"সিগন্যাল-ক্যান্ডেলে ভলিউম ২০-দিনের গড়ের {ratio:.1f}x")

    # ── ১৫: প্যানিক অ্যাবজর্পশন (খবর পড়া যায় না, দাম-ভলিউম থেকে আন্দাজ)
    if ai is None or not base:
        add("15", "প্যানিক অ্যাবজর্পশন (আন্দাজ)", NA, "ডেটা নেই")
    else:
        rngc = H[ai] - L[ai]
        wick = (min(O[ai], C[ai]) - L[ai]) / rngc if rngc > 0 else 0
        wick_sig = wick >= 0.4
        absorb_sig = V[ai] >= 1.2 * base and C[ai] >= (H[ai] + L[ai]) / 2
        panic_txt, panic_ok = "", None
        if nifty is not None and len(nifty) > 10:
            try:
                jn = pd.concat([_ret_by_date(d), _ret_by_date(nifty)], axis=1, keys=["s", "n"]).dropna().tail(10)
                pdays = jn[jn["n"] <= -0.01]
                if len(pdays):
                    panic_ok = bool((pdays["s"] > pdays["n"]).all() and price >= anchor)
                    panic_txt = f" | বাজার-পতনের {len(pdays)} দিনে স্টক {'বাজারের চেয়ে ভালো ছিল' if panic_ok else 'দুর্বল ছিল'}"
            except Exception:  # noqa: BLE001
                pass
        if panic_ok or (wick_sig and absorb_sig):
            s15 = OK
        elif panic_ok is False:
            s15 = BAD
        elif wick_sig or absorb_sig:
            s15 = WARN
        else:
            s15 = BAD
        add("15", "প্যানিক অ্যাবজর্পশন (আন্দাজ)", s15,
            f"নিচের উইক {wick * 100:.0f}%{' ✔' if wick_sig else ''} | ভলিউম-শোষণ {'হ্যাঁ' if absorb_sig else 'না'}{panic_txt}"
            " | (আসল খবর পড়া যায় না)")

    # ── ৯ ও ১০: ট্রেড সেটআপ, R:R
    setup = None
    if anchor is not None:
        entry = price
        sl = min(anchor, plow if plow is not None else anchor) - 0.2 * a_i
        risk = entry - sl
        if risk > 0:
            res_all = sorted(set(x for x in d_levels + w_levels if x > entry + 0.5 * risk))
            t1 = res_all[0] if res_all else entry + 2 * risk
            t2 = next((x for x in res_all if x >= t1 + 0.5 * risk), entry + 3 * risk)
            if t2 <= t1:
                t2 = t1 + risk
            setup = dict(entry=entry, sl=sl, t1=t1, t2=t2, rr1=(t1 - entry) / risk, rr2=(t2 - entry) / risk,
                         risk_pct=risk / entry * 100, t_2r=entry + 2 * risk, src=src, pattern=pat)
    if setup is None:
        add("10", "রিস্ক-টু-রিওয়ার্ড", NA, "বৈধ এন্ট্রি/স্টপ-লস তৈরি হয়নি")
    else:
        rr = setup["rr1"]
        extra = "" if rr >= 2 else f" | ১:২ চাইলে ₹{setup['t_2r']:.1f} পর্যন্ত বাধা-মুক্ত জায়গা লাগবে"
        add("10", "রিস্ক-টু-রিওয়ার্ড", OK if rr >= 2 else (WARN if rr >= 1.5 else BAD),
            f"Entry {setup['entry']:.1f} | SL {setup['sl']:.1f} | T1 {setup['t1']:.1f} (১:{rr:.2f}) | "
            f"T2 {setup['t2']:.1f} (১:{setup['rr2']:.2f}){extra}")

    return dict(checks=checks, setup=setup, anchor=anchor, src=src, pattern=pat, weekly_pattern=wpat,
                score=score_checks(checks), confluence=confluence(checks),
                levels=dict(support=sup_d, resistance=res_d, w_support=sup_w, w_resistance=res_w))


def score_checks(checks):
    num = den = 0.0
    for c in checks:
        w = WEIGHTS.get(c["id"])
        if w is None or c["status"] not in POINTS:
            continue
        num += w * POINTS[c["status"]]
        den += w
    return round(100 * num / den) if den else None


def confluence(checks):
    known = [c for c in checks if c["id"] in WEIGHTS and c["status"] != NA]
    return sum(c["status"] == OK for c in known), len(known)


def decide(checks, setup, score, event_status, global_status, sector_status=None):
    s = {c["id"]: c["status"] for c in checks}
    blockers = []
    if s.get("4D") == BAD:
        blockers.append("দৈনিক ট্রেন্ড নিম্নমুখী")
    if s.get("4W") == BAD:
        blockers.append("সাপ্তাহিক ট্রেন্ড নিম্নমুখী")
    if setup is None:
        blockers.append("স্পষ্ট Higher Low/সাপোর্ট পাওয়া যায়নি")
    elif s.get("10") == BAD:
        blockers.append("R:R ১:১.৫-এর নিচে")
    if blockers:
        return "avoid", "❌ এখন বাদ দিন", blockers
    waits = []
    if s.get("8") != OK:
        waits.append("দৈনিক বুলিশ ক্যান্ডেলের কনফার্মেশন নেই")
    if s.get("10") != OK:
        waits.append("R:R ১:২ নয়")
    if event_status == BAD:
        waits.append("১ সপ্তাহের মধ্যে ইভেন্ট আছে")
    if global_status == BAD:
        waits.append("গ্লোবাল ঝুঁকি বেশি")
    if sector_status == BAD:
        waits.append("সেক্টর বিয়ারিশ")
    if score is not None and score < 65:
        waits.append(f"স্কোর কম ({score})")
    if waits:
        return "wait", "⏳ অপেক্ষা করুন", waits
    return "take", "✅ ৩-৭ দিনের সুইং ট্রেড যুক্তিসঙ্গত", []


# ── শুধু ডিপ-অ্যানালাইসিসে (এক-একটি স্টকের জন্য) ডেটা আনা পয়েন্টগুলো
def check_fundamentals(info):
    info = info or {}
    de, prom = info.get("debtToEquity"), info.get("heldPercentInsiders")
    if de is None and prom is None:
        return NA, "ফান্ডামেন্টাল ডেটা পাওয়া যায়নি (Screener.in-এ নিজে দেখুন)"
    notes, bad, warn = [], False, False
    if de is not None:
        notes.append(f"ঋণ/ইক্যুইটি {de / 100:.2f}")
        bad |= de > 200
        warn |= de > 100
    if prom is not None:
        notes.append(f"ইনসাইডার/প্রমোটার হোল্ডিং ~{prom * 100:.0f}%")
        warn |= prom < 0.25
    if info.get("sector") == "Financial Services":
        notes.append("(ব্যাংক/NBFC-তে ঋণ অনুপাত প্রযোজ্য নয়)")
        bad = False
    return (BAD if bad else WARN if warn else OK), " | ".join(notes) + " | (ইন্ডিকেটিভ, যাচাই করুন)"


def check_events(cal, today):
    items = []
    if isinstance(cal, dict):
        for k, v in cal.items():
            for x in (v if isinstance(v, (list, tuple)) else [v]):
                if isinstance(x, date):
                    items.append((str(k), x.date() if isinstance(x, datetime) else x))
    if not items:
        return NA, "ইভেন্টের তারিখ পাওয়া যায়নি; NSE-র কর্পোরেট ক্যালেন্ডার নিজে দেখুন"
    soon = [(k, x) for k, x in items if 0 <= (x - today).days <= 7]
    if soon:
        return BAD, "আগামী ৭ দিনে: " + ", ".join(f"{k} ({x:%d-%b})" for k, x in soon)
    return OK, "আগামী ৭ দিনে কোনো রেজাল্ট/ডিভিডেন্ড ইভেন্ট পাওয়া যায়নি (ডেটা নিখুঁত নাও হতে পারে)"


def check_sector(info, override, nifty):
    sector = (info or {}).get("sector")
    idx_t = override or SECTOR_INDEX.get(sector)
    if not idx_t:
        return NA, "সেক্টর/ইনডেক্স মেলেনি; ওপর থেকে সেক্টর ইনডেক্স বেছে নিন"
    raw = download_batch([idx_t], "1y", "1d").get(idx_t)
    if raw is None or len(raw) < 50:
        return NA, f"{idx_t} ইনডেক্সের ডেটা পাওয়া যায়নি"
    C = raw["Close"].dropna().to_numpy(float)
    tl = trend_label(C)
    rs_txt = ""
    if nifty is not None and len(nifty) > 25 and len(C) > 25:
        rs = (C[-1] / C[-21] - 1) * 100 - (nifty["Close"].iloc[-1] / nifty["Close"].iloc[-21] - 1) * 100
        rs_txt = f" | ২০ দিনে Nifty-র চেয়ে {rs:+.1f}%"
    status = {"Uptrend": OK, "Sideways": WARN, "Downtrend": BAD}.get(tl, NA)
    return status, f"{sector or 'ম্যানুয়াল'} → {idx_t}: {tl}{rs_txt}"


def check_global(mk):
    flags, have = [], False

    def closes(t):
        df = mk.get(t)
        return None if df is None or len(df) < 6 else df["Close"].dropna().to_numpy(float)

    ivx, vix, spx, nif = closes("^INDIAVIX"), closes("^VIX"), closes("^GSPC"), closes("^NSEI")
    if ivx is not None:
        have = True
        if ivx[-1] > 20:
            flags.append(f"India VIX উঁচু ({ivx[-1]:.1f})")
    if vix is not None:
        have = True
        if vix[-1] > 25:
            flags.append(f"US VIX উঁচু ({vix[-1]:.1f})")
    if spx is not None:
        have = True
        if spx[-1] / spx[-2] - 1 <= -0.02 or spx[-1] / spx[-6] - 1 <= -0.04:
            flags.append("S&P 500-এ বড় পতন")
    if nif is not None:
        have = True
        if nif[-1] / nif[-2] - 1 <= -0.015:
            flags.append("Nifty-তে এক দিনে বড় পতন")
    if not have:
        return NA, "গ্লোবাল সূচকের ডেটা পাওয়া যায়নি"
    if not flags:
        return OK, "India VIX, US VIX, S&P 500, Nifty-তে বড় প্যানিক-সংকেত নেই"
    return (BAD if len(flags) >= 2 else WARN), " | ".join(flags)


def _tick(x):
    return float(np.round(x / 0.05) * 0.05)


def deep_analyze(ticker, params, sector_override=None):
    cfg_d = TIMEFRAMES["1 Day (Daily)"]
    raw_d = download_batch([ticker], "1y", "1d").get(ticker)
    if raw_d is None:
        return dict(error=f"{ticker}: দৈনিক ডেটা পাওয়া যায়নি (টিকার ঠিক আছে কি?)")
    d = drop_forming_candle(prepare_frame(raw_d, cfg_d), cfg_d)
    raw_w = download_batch([ticker], "3y", "1wk").get(ticker)
    w = drop_forming_weekly(raw_w.dropna(subset=["Open", "High", "Low", "Close"])) if raw_w is not None else None
    if len(d) < 60:
        return dict(error=f"{ticker}: বিশ্লেষণের জন্য যথেষ্ট দৈনিক ডেটা নেই")
    mk = download_batch(["^NSEI", "^INDIAVIX", "^GSPC", "^VIX"], "6mo", "1d")
    nifty = None
    if mk.get("^NSEI") is not None:
        nifty = drop_forming_candle(prepare_frame(mk["^NSEI"], cfg_d), cfg_d)

    pc = price_checks(d, w, params, nifty)
    checks = list(pc["checks"])
    today = datetime.now(IST).date()

    info, cal = {}, None
    try:
        tk = yf.Ticker(ticker)
        try:
            info = tk.info or {}
        except Exception:  # noqa: BLE001
            info = {}
        try:
            cal = tk.calendar
        except Exception:  # noqa: BLE001
            cal = None
    except Exception:  # noqa: BLE001
        pass

    s1, t1 = check_fundamentals(info)
    checks.append(dict(id="1", title="ফান্ডামেন্টাল সেফটি", status=s1, detail=t1))
    s2, t2 = check_events(cal, today)
    checks.append(dict(id="2", title="ইভেন্ট রিস্ক (১ সপ্তাহ)", status=s2, detail=t2))
    s3, t3 = check_sector(info, sector_override, nifty)
    checks.append(dict(id="3", title="সেক্টর ট্রেন্ড", status=s3, detail=t3))
    s13, t13 = check_global(mk)
    risk_flag = s2 == BAD or s13 in (BAD, WARN)
    wd = datetime.now(IST).weekday()
    if risk_flag and wd >= 4:
        timing = "শুক্রবার ক্লোজিংয়ে এন্ট্রি নয়; সোমবার বাজার খোলার পর পরিস্থিতি দেখে সিদ্ধান্ত নিন।"
    elif risk_flag:
        timing = "ইভেন্ট/গ্লোবাল ঝুঁকি কেটে যাওয়ার পর এন্ট্রি বিবেচনা করুন।"
    else:
        timing = "বিশেষ ঝুঁকি-সংকেত নেই; স্বাভাবিক এন্ট্রি-প্ল্যান চলতে পারে।"
    checks.append(dict(id="13", title="ইভেন্ট ও গ্লোবাল রিস্ক, এন্ট্রি টাইমিং", status=s13, detail=t13 + " | " + timing))

    checks.sort(key=lambda c: ORDER.index(c["id"]))
    score = score_checks(checks)
    kind, verdict, reasons = decide(checks, pc["setup"], score, s2, s13, s3)
    return dict(ticker=ticker, d=d, checks=checks, setup=pc["setup"], score=score, confluence=confluence(checks),
                verdict_kind=kind, verdict=verdict, reasons=reasons, timing=timing, levels=pc["levels"],
                pattern=pc["pattern"], anchor=pc["anchor"])


# ───────────────────────── স্ক্যান ও ফলাফল ─────────────────────────
def chart_links(ticker):
    sym = ticker.rsplit(".", 1)[0]
    tv = sym.replace("&", "_").replace("-", "_")
    exch = "BSE" if ticker.endswith(".BO") else "NSE"
    return (f"https://in.tradingview.com/chart/?symbol={exch}%3A{quote(tv, safe='')}",
            f"https://groww.in/search?q={quote(sym, safe='')}")


def make_row(ticker, res):
    sym = ticker.rsplit(".", 1)[0]
    tv, groww = chart_links(ticker)
    row = {
        "_t": ticker, "Weekly": "—", "_w_up": None, "_w_hl": None, "Support": "—",
        "Score": np.nan, "Confluence": "", "Entry": np.nan, "SL": np.nan, "T1": np.nan, "T2": np.nan, "R:R": np.nan,
        "Stock": sym, "Name": TICKER_NAMES.get(ticker, ""), "Price": res["price"], "Status": res["status"],
        "Trend": "✅ Uptrend" if res["up"] else "—", "_up": res["up"],
        "Pattern": res["sr_pattern"] or "", "Type": res["sr_type"] or "",
        "Buyer %": res["buyer"], "Seller %": res["seller"],
        "Chart": tv, "Groww": groww,
        "_has_hl": res["hl"] is not None, "Candle at HL": res["hl_pattern"] or "",
    }
    hl = res["hl"]
    if hl:
        t = hl["time"]
        row.update({
            "HL Price": round(hl["hl"], 2), "Prev Low": round(hl["prev"], 2),
            "HL Time": t.strftime("%d-%b-%Y") if hasattr(t, "strftime") else str(t),
            "Candles Ago": hl["age"], "Dist %": round(hl["dist"], 2), "HL Count": hl["count"],
            "Stop": hl["stop"], "Risk %": hl["risk_pct"], "Target 1:2": hl["target"],
            "Support": hl["support"],
        })
    return row


def apply_quick(r, pc):
    r["Score"] = pc["score"] if pc["score"] is not None else np.nan
    ok, tot = pc["confluence"]
    r["Confluence"] = f"{ok}/{tot}"
    st_ = pc["setup"]
    if st_:
        r.update({"Entry": round(st_["entry"], 2), "SL": round(st_["sl"], 2), "T1": round(st_["t1"], 2),
                  "T2": round(st_["t2"], 2), "R:R": round(st_["rr1"], 2)})




# ═════════════════════ স্টক তালিকা: NSE + BSE ═════════════════════
import os  # noqa: E402

TICKER_NAMES = {}
BSE_URL = ("https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w"
           "?Group=&Scripcode=&industry=&segment=Equity&status=Active")
DEFAULT_PARAMS = dict(n=3, max_age=10, max_dist=5.0, min_rise=0.3, min_swing=1.0, min_vol=100000)
SECTOR_NAMES = {
    "^CNXIT": "IT", "^NSEBANK": "Bank", "^CNXPHARMA": "Pharma", "^CNXENERGY": "Energy", "^CNXFMCG": "FMCG",
    "^CNXAUTO": "Auto", "^CNXMETAL": "Metal", "^CNXINFRA": "Infra", "^CNXREALTY": "Realty", "^CNXMEDIA": "Media",
}


def load_nse_universe():
    """(NSE-র সব EQ স্টকের টিকার, ISIN-এর সেট)।"""
    r = requests.get(NSE_EQUITY_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip() for c in df.columns]
    df = df[df["SERIES"].astype(str).str.strip() == "EQ"].copy()
    df["SYMBOL"] = df["SYMBOL"].astype(str).str.strip()
    name_col = next((c for c in df.columns if "NAME" in c.upper()), None)
    isin_col = next((c for c in df.columns if "ISIN" in c.upper()), None)
    for _, row in df.iterrows():
        TICKER_NAMES[row["SYMBOL"] + ".NS"] = str(row[name_col]).strip() if name_col else ""
    isins = set(df[isin_col].astype(str).str.strip()) if isin_col else set()
    return _dedupe([s + ".NS" for s in df["SYMBOL"]]), isins


def load_bse_only(nse_isins):
    """শুধু BSE-তে তালিকাভুক্ত স্টক (NSE-তে যাদের ISIN আছে তাদের বাদ দিয়ে)। টিকার = স্ক্রিপ-কোড + '.BO'"""
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bseindia.com/",
               "Origin": "https://www.bseindia.com", "Accept": "application/json"}
    r = requests.get(BSE_URL, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        data = data.get("Table") or data.get("data") or []
    out = []
    for it in data:
        code = str(it.get("SCRIP_CD") or "").strip()
        isin = str(it.get("ISIN_NUMBER") or "").strip()
        if not code.isdigit():
            continue
        if isin and (isin in nse_isins or not isin.startswith("INE")):
            continue
        t = code + ".BO"
        out.append(t)
        TICKER_NAMES[t] = str(it.get("Scrip_Name") or it.get("SCRIP_NAME") or code).strip()
    return _dedupe(out)


# ═════════════════════ বাজারের অবস্থা: গ্লোবাল + Nifty 50 + সেক্টর ═════════════════════
def market_regime():
    dmap = download_batch(["^NSEI", "^INDIAVIX", "^GSPC", "^VIX"] + list(SECTOR_NAMES), "1y", "1d")
    wmap = download_batch(["^NSEI"], "3y", "1wk")

    def cl(m, t):
        df = m.get(t)
        if df is None:
            return None
        c = df["Close"].dropna().to_numpy(float)
        return c if len(c) >= 5 else None

    nd_c, nw_c, sp_c, iv_c = cl(dmap, "^NSEI"), cl(wmap, "^NSEI"), cl(dmap, "^GSPC"), cl(dmap, "^INDIAVIX")
    nd = trend_label(nd_c) if nd_c is not None else None
    nw = trend_label(nw_c) if nw_c is not None else None
    sd = trend_label(sp_c) if sp_c is not None else None
    pts = {"Uptrend": 1.0, "Sideways": 0.5, "Downtrend": 0.0}
    score = 2 * pts.get(nd, 0.5) + 2 * pts.get(nw, 0.5) + pts.get(sd, 0.5)
    reasons = [f"Nifty 50 দৈনিক: {nd or 'ডেটা নেই'}", f"Nifty 50 সাপ্তাহিক: {nw or 'ডেটা নেই'}",
               f"S&P 500 দৈনিক: {sd or 'ডেটা নেই'}"]
    vix = float(iv_c[-1]) if iv_c is not None else None
    if vix is None:
        score += 0.5
    elif vix < 16:
        score += 1.0
    elif vix < 22:
        score += 0.5
    reasons.append("India VIX: " + ("ডেটা নেই" if vix is None else f"{vix:.1f}"))
    gs, gtext = check_global(dmap)
    score += -1.5 if gs == BAD else (-0.5 if gs == WARN else 0.0)
    reasons.append("গ্লোবাল ঝুঁকি: " + gtext)
    level = "GREEN" if score >= 4.5 else ("YELLOW" if score >= 3 else "RED")

    nret = (nd_c[-1] / nd_c[-21] - 1) * 100 if nd_c is not None and len(nd_c) > 22 else None
    sectors = []
    for t, name in SECTOR_NAMES.items():
        c = cl(dmap, t)
        if c is None or len(c) < 55:
            continue
        r20 = (c[-1] / c[-21] - 1) * 100
        sectors.append(dict(name=name, ticker=t, trend=trend_label(c), ret20=round(r20, 1),
                            rs20=None if nret is None else round(r20 - nret, 1)))
    sectors.sort(key=lambda x: -999 if x["rs20"] is None else x["rs20"], reverse=True)
    return dict(level=level, score=round(score, 1), max=6, reasons=reasons, vix=vix,
                nifty=dict(daily=nd, weekly=nw), global_text=gtext, sectors=sectors,
                time=datetime.now(IST).strftime("%d-%b-%Y %H:%M IST"))


# ═════════════════════ পুরো তালিকা স্ক্যান ═════════════════════
def scan_universe(tickers, cfg, params, include_forming=False, progress=None):
    say = progress or (lambda f, t: None)
    chunks = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
    rows, failed, errors, frames = [], [], [], {}
    scanned = 0
    for ci, chunk in enumerate(chunks):
        data = download_batch(chunk, cfg["period"], cfg["interval"])
        for t in chunk:
            raw = data.get(t)
            if raw is None:
                failed.append(t)
                continue
            try:
                df = prepare_frame(raw, cfg)
                if not include_forming:
                    df = drop_forming_candle(df, cfg)
                if len(df) < 30:
                    failed.append(t)
                    continue
                scanned += 1
                res = analyze_stock(df, params)
                if res:
                    rows.append(make_row(t, res))
                    frames[t] = df
            except Exception as e:  # noqa: BLE001
                errors.append(f"{t}: {type(e).__name__}: {e}")
        say(0.9 * (ci + 1) / len(chunks),
            f"{ci + 1}/{len(chunks)} ব্যাচ শেষ | স্ক্যান: {scanned} | সেটআপ: {len(rows)}")
        time.sleep(0.3)

    by_t = {r["_t"]: r for r in rows}
    sig = list(by_t)
    say(0.92, f"সাপ্তাহিক ট্রেন্ড ও স্কোর যাচাই ({len(sig)} স্টক)...")
    for i in range(0, len(sig), BATCH_SIZE):
        chunk = sig[i:i + BATCH_SIZE]
        wdata = download_batch(chunk, "3y", "1wk")
        ddata = download_batch(chunk, "1y", "1d") if cfg["weekly"] else {}
        for t in chunk:
            r = by_t[t]
            flags = wclosed = None
            if wdata.get(t) is not None:
                try:
                    wclosed = drop_forming_weekly(wdata[t].dropna(subset=["Open", "High", "Low", "Close"]))
                    flags = weekly_flags(wdata[t])
                except Exception:  # noqa: BLE001
                    flags = None
            try:
                if cfg["weekly"]:  # স্কোর সবসময় দৈনিক + সাপ্তাহিক মিলিয়ে
                    dcl = None
                    if ddata.get(t) is not None:
                        dcl = drop_forming_candle(prepare_frame(ddata[t]), TIMEFRAMES["1 Day (Daily)"])
                else:
                    dcl = frames[t]
                if dcl is not None and len(dcl) >= 60:
                    apply_quick(r, price_checks(dcl, wclosed, params, None))
            except Exception as e:  # noqa: BLE001
                errors.append(f"{t} (স্কোর): {type(e).__name__}: {e}")
            if flags is None:
                r["Weekly"] = "ডেটা নেই"
            else:
                r["_w_up"], r["_w_hl"] = flags
                r["Weekly"] = (("W-Uptrend ✅" if flags[0] else "W-Uptrend ✖") + " | "
                               + ("W-HL ✅" if flags[1] else "W-HL ✖"))
    return dict(rows=rows, failed=failed, errors=errors, scanned=scanned, total=len(tickers),
                time=datetime.now(IST).strftime("%d-%b-%Y %H:%M IST"))


# ═════════════════════ ব্যাকটেস্ট: কৌশলটি অতীতে কতটা কাজ করেছে ═════════════════════
def backtest_symbol(df, n=3, horizon=5, min_vol=0):
    """HL + ক্যান্ডেল সংকেতের ঐতিহাসিক সিমুলেশন (এন্ট্রি = সংকেত-দিনের ক্লোজ, টার্গেট = ১:২, মেয়াদ = ৫ সেশন)।"""
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if len(df) < 120:
        return []
    O = df["Open"].to_numpy(float)
    H = df["High"].to_numpy(float)
    L = df["Low"].to_numpy(float)
    C = df["Close"].to_numpy(float)
    V = df["Volume"].fillna(0).to_numpy(float) if "Volume" in df else np.zeros(len(df))
    atr = _atr(H, L, C)
    e20, e50 = _ema(C, 20), _ema(C, 50)
    wk = df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    wc = wk["Close"].to_numpy(float)
    w_up = (wc > _ema(wc, 50)) & (_ema(wc, 20) > _ema(wc, 50))
    pos = wk.index.searchsorted(df.index, side="right") - 1

    trades = []
    sl = _swing_lows(L, n)
    for k in range(1, len(sl)):
        i1, i2 = sl[k - 1], sl[k]
        t = i2 + n
        if t + horizon >= len(df):
            break
        if L[i2] <= L[i1] * 1.003 or (H[i1:i2 + 1].max() - L[i1]) / L[i1] < 0.01:
            continue
        if C[t] < L[i2] or (C[t] - L[i2]) / L[i2] > 0.05:
            continue
        if V[max(0, t - 20):t].mean() < min_vol:
            continue
        a_i = atr[i2] if np.isfinite(atr[i2]) else 0.01 * C[i2]
        pat = None
        for j in range(i2, t + 1):
            f = bullish_shape(O, H, L, C, j, loose=True)
            tol = atr[j] if np.isfinite(atr[j]) else 0.01 * C[j]
            if f and abs(f[1] - L[i2]) <= tol:
                pat = (j, f[0], f[1])
                break
        sl_price = (min(L[i2], pat[2]) if pat else L[i2]) - 0.2 * a_i
        entry = C[t]
        risk = entry - sl_price
        if risk <= 0 or risk / entry > 0.12:
            continue
        target = entry + 2 * risk
        outcome, R = "TIME", None
        for kk in range(t + 1, t + horizon + 1):
            if O[kk] <= sl_price:
                outcome, R = "SL", (O[kk] - entry) / risk
                break
            if L[kk] <= sl_price:  # একই দিনে SL ও টার্গেট ছুঁলে SL ধরা হয় (রক্ষণশীল)
                outcome, R = "SL", (sl_price - entry) / risk
                break
            if H[kk] >= target:
                outcome, R = "TARGET", 2.0
                break
        if R is None:
            R = (C[t + horizon] - entry) / risk
        spike = False
        if pat:
            b20 = V[max(0, pat[0] - 20):pat[0]].mean()
            spike = bool(b20 > 0 and V[pat[0]] / b20 >= 1.5)
        trades.append(dict(date=str(df.index[t].date()), pat=pat is not None, w_up=bool(pos[t] >= 30 and w_up[pos[t]]),
                           d_up=bool(C[t] > e50[t] and e20[t] > e50[t]), spike=spike, outcome=outcome, R=float(R)))
    return trades


def _summ(trs):
    n = len(trs)
    if n == 0:
        return dict(n=0)
    R = np.array([t["R"] for t in trs])
    share = lambda key: round(100 * float(np.mean([t["outcome"] == key for t in trs])), 1)  # noqa: E731
    return dict(n=n, target=share("TARGET"), stop=share("SL"), timeout=share("TIME"),
                win=round(100 * float((R > 0).mean()), 1), avg_r=round(float(R.mean()), 2))


def backtest_summary(trades):
    sets = [
        ("শুধু Higher Low সংকেত", lambda t: True),
        ("HL + ক্যান্ডেল প্যাটার্ন", lambda t: t["pat"]),
        ("HL + ক্যান্ডেল + সাপ্তাহিক Uptrend", lambda t: t["pat"] and t["w_up"]),
        ("… + দৈনিক Uptrend", lambda t: t["pat"] and t["w_up"] and t["d_up"]),
        ("… + ভলিউম স্পাইক", lambda t: t["pat"] and t["w_up"] and t["d_up"] and t["spike"]),
    ]
    return [dict(name=nm, **_summ([t for t in trades if f(t)])) for nm, f in sets]


def run_backtest(nse_tickers, params, k=400, progress=None):
    say = progress or (lambda f, t: None)
    rnd = random.Random(7)
    liquid = [t + ".NS" for t in FALLBACK_TICKERS]
    others = [t for t in nse_tickers if t not in set(liquid)]
    sample = _dedupe(liquid + rnd.sample(others, min(len(others), max(0, k - len(liquid)))))
    _CACHE.clear()
    trades = []
    chunks = [sample[i:i + BATCH_SIZE] for i in range(0, len(sample), BATCH_SIZE)]
    for ci, chunk in enumerate(chunks):
        data = download_batch(chunk, "5y", "1d")
        for t in chunk:
            if data.get(t) is None:
                continue
            try:
                trades += backtest_symbol(prepare_frame(data[t]), n=params["n"], horizon=5, min_vol=params["min_vol"])
            except Exception:  # noqa: BLE001
                continue
        _CACHE.clear()
        say((ci + 1) / len(chunks), f"ব্যাকটেস্ট {ci + 1}/{len(chunks)}")
    return dict(stocks=len(sample), years=5, horizon_sessions=5, n_trades=len(trades), rows=backtest_summary(trades),
                caveats=["বর্তমানে তালিকাভুক্ত স্টকই ধরা হয়েছে (বাদ-পড়া স্টক নেই), তাই ফল কিছুটা বেশি আশাব্যঞ্জক দেখায়।",
                         "ব্রোকারেজ, ট্যাক্স ও স্লিপেজ ধরা হয়নি।",
                         "টার্গেট = ১:২, মেয়াদ = ৫ সেশন; একই দিনে SL ও টার্গেট ছুঁলে SL ধরা হয়েছে।"])


# ═════════════════════ সেরা স্টক বাছাই ═════════════════════
def _num(x):
    return isinstance(x, (int, float, np.floating, np.integer)) and np.isfinite(x)


def select_candidates(rows, min_score=60, min_rr=1.5):
    """HL + ক্যান্ডেল + সাপ্তাহিক Uptrend + পর্যাপ্ত স্কোর ও R:R।"""
    out = []
    for r in rows:
        if not r.get("_has_hl") or not r.get("Candle at HL") or r.get("_w_up") is not True:
            continue
        if not (_num(r.get("Score")) and r["Score"] >= min_score and _num(r.get("R:R")) and r["R:R"] >= min_rr):
            continue
        out.append(r)
    out.sort(key=lambda r: (r["Score"], r["R:R"]), reverse=True)
    return out


def pick_from_report(r, rep):
    d = rep["d"].tail(90)
    chart = dict(x=[str(i.date()) for i in d.index], o=[round(float(v), 2) for v in d["Open"]],
                 h=[round(float(v), 2) for v in d["High"]], l=[round(float(v), 2) for v in d["Low"]],
                 c=[round(float(v), 2) for v in d["Close"]])
    s = rep["setup"]
    setup = None if not s else {k: round(float(s[k]), 2) for k in ("entry", "sl", "t1", "t2", "rr1", "rr2", "risk_pct")}
    return dict(stock=r["Stock"], name=r.get("Name", ""), ticker=r["_t"], price=r["Price"],
                verdict_kind=rep["verdict_kind"], verdict=rep["verdict"], reasons=list(rep["reasons"]),
                score=rep["score"], confluence=list(rep["confluence"]), setup=setup, weekly=r["Weekly"],
                candle=r["Candle at HL"], support=r.get("Support", "—"), hl_price=r.get("HL Price"),
                hl_time=r.get("HL Time"), dist=r.get("Dist %"), hl_count=r.get("HL Count"),
                checks=[dict(id=c["id"], title=c["title"], status=c["status"], detail=c["detail"]) for c in rep["checks"]],
                timing=rep["timing"], levels=rep["levels"], chart=chart,
                links=dict(tv=r["Chart"], groww=r["Groww"]))


SIGNAL_COLS = ["Stock", "Name", "Price", "Weekly", "Candle at HL", "HL Price", "HL Time", "Dist %", "HL Count",
               "Support", "Score", "Confluence", "SL", "T1", "T2", "R:R", "Chart", "Groww"]


def build_picks(params=None, progress=None, include_bse=True, backtest_n=400, max_deep=25):
    params = dict(DEFAULT_PARAMS, **(params or {}))
    say = progress or (lambda f, t: None)
    started = time.time()
    notes = []

    say(0.01, "NSE/BSE স্টক তালিকা আনা হচ্ছে...")
    try:
        nse, isins = load_nse_universe()
    except Exception as e:  # noqa: BLE001
        nse, isins = [t + ".NS" for t in FALLBACK_TICKERS], set()
        notes.append(f"NSE তালিকা ডাউনলোড হয়নি ({type(e).__name__}); ছোট বিল্ট-ইন তালিকা ব্যবহার হয়েছে।")
    bse = []
    if include_bse:
        try:
            bse = load_bse_only(isins)
        except Exception as e:  # noqa: BLE001
            notes.append(f"BSE তালিকা আনা যায়নি ({type(e).__name__}); শুধু NSE স্ক্যান হয়েছে।")
    universe = _dedupe(nse + bse)

    say(0.04, "বাজারের অবস্থা (গ্লোবাল, Nifty 50, সেক্টর)...")
    try:
        regime = market_regime()
    except Exception as e:  # noqa: BLE001
        regime = dict(level="YELLOW", score=None, max=6, sectors=[], reasons=[f"বাজারের ডেটা আনা যায়নি ({type(e).__name__})"],
                      vix=None, nifty={}, global_text="", time=datetime.now(IST).strftime("%d-%b-%Y %H:%M IST"))
        notes.append("বাজারের অবস্থা যাচাই করা যায়নি।")

    scan = scan_universe(universe, TIMEFRAMES["1 Day (Daily)"], params, False,
                         progress=lambda f, t: say(0.06 + 0.54 * f, t))
    cands = select_candidates(scan["rows"])

    picks = []
    for k, r in enumerate(cands[:max_deep]):
        say(0.62 + 0.2 * k / max(1, min(len(cands), max_deep)), f"ডিপ অ্যানালাইসিস: {r['Stock']}")
        try:
            rep = deep_analyze(r["_t"], params, None)
            if not rep.get("error"):
                picks.append(pick_from_report(r, rep))
        except Exception as e:  # noqa: BLE001
            notes.append(f"{r['Stock']}: ডিপ অ্যানালাইসিস ব্যর্থ ({type(e).__name__})")
    if regime["level"] == "RED":
        for p in picks:
            if p["verdict_kind"] == "take":
                p["verdict_kind"], p["verdict"] = "wait", "⏳ অপেক্ষা করুন"
                p["reasons"].append("সার্বিক বাজার ঝুঁকিপূর্ণ (RED)")
    order = {"take": 0, "wait": 1, "avoid": 2}
    picks.sort(key=lambda p: (order[p["verdict_kind"]], -(p["score"] or 0)))

    signals = [{k: r.get(k) for k in SIGNAL_COLS} for r in scan["rows"] if r.get("_has_hl") and r.get("Candle at HL")]
    signals.sort(key=lambda x: -(x["Score"] if _num(x["Score"]) else -1))

    bt = None
    if backtest_n:
        say(0.84, "ব্যাকটেস্ট চলছে (কৌশলটি অতীতে কতটা কাজ করেছে)...")
        try:
            bt = run_backtest(nse, params, backtest_n, progress=lambda f, t: say(0.84 + 0.14 * f, t))
        except Exception as e:  # noqa: BLE001
            notes.append(f"ব্যাকটেস্ট ব্যর্থ ({type(e).__name__}: {e})")
    say(1.0, "সম্পন্ন")
    return dict(generated=datetime.now(IST).strftime("%d-%b-%Y %H:%M IST"), regime=regime, picks=picks,
                signals=signals[:300],
                scan=dict(total=scan["total"], scanned=scan["scanned"], failed=len(scan["failed"]),
                          errors=len(scan["errors"]), setups=len(scan["rows"]), candidates=len(cands),
                          nse=len(nse), bse_only=len(bse)),
                backtest=bt, params=params, notes=notes, runtime_min=round((time.time() - started) / 60, 1))


def _sanitize(o):
    if isinstance(o, dict):
        return {str(k): _sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_sanitize(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        v = float(o)
        return v if np.isfinite(v) else None
    if isinstance(o, (pd.Timestamp, datetime, date)):
        return o.isoformat()
    return o


def save_json(obj, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_sanitize(obj), f, ensure_ascii=False, indent=1)


PICKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "picks.json")
UNI_NSE_BSE = "NSE + BSE সব স্টক (অটো ডাউনলোড)"
LEVEL_UI = {"GREEN": "🟢 অনুকূল", "YELLOW": "🟡 সতর্ক", "RED": "🔴 ঝুঁকিপূর্ণ"}
LINKS = {
    "Chart": st.column_config.LinkColumn("Chart", display_text="📈 খুলুন"),
    "Groww": st.column_config.LinkColumn("Groww", display_text="🚀 খুলুন"),
}


# ───────────────────────── ডেটা লোড ─────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def cached_universe(include_bse):
    notes = []
    try:
        nse, isins = load_nse_universe()
    except Exception as e:  # noqa: BLE001
        return [t + ".NS" for t in FALLBACK_TICKERS], [f"NSE তালিকা ডাউনলোড হয়নি ({type(e).__name__}); ছোট বিল্ট-ইন তালিকা ব্যবহার হচ্ছে।"]
    bse = []
    if include_bse:
        try:
            bse = load_bse_only(isins)
        except Exception as e:  # noqa: BLE001
            notes.append(f"BSE তালিকা আনা যায়নি ({type(e).__name__}); শুধু NSE।")
    return nse + bse, notes


def load_universe(choice, uploaded):
    if choice == UNI_UPLOAD:
        return parse_uploaded_tickers(uploaded) if uploaded else []
    if choice in (UNI_ALL, UNI_NSE_BSE):
        tickers, notes = cached_universe(choice == UNI_NSE_BSE)
        for n_ in notes:
            st.warning(n_)
        return tickers
    return [t + ".NS" for t in FALLBACK_TICKERS]


@st.cache_data(show_spinner=False)
def _read_json(path, mtime):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_picks():
    if not os.path.exists(PICKS_PATH):
        return None
    return _read_json(PICKS_PATH, os.path.getmtime(PICKS_PATH))


def run_scan(tickers, tf, params, include_forming):
    prog = st.progress(0.0, text="স্ক্যান শুরু হচ্ছে...")

    def cb(f, t):
        prog.progress(min(max(float(f), 0.0), 1.0), text=t)

    res = scan_universe(tickers, TIMEFRAMES[tf], params, include_forming, progress=cb)
    prog.empty()
    res["tf"] = tf
    st.session_state["scan"] = res


HL_COLS = ["Stock", "Name", "Price", "Trend", "Weekly", "HL Price", "Prev Low", "HL Time", "Candles Ago", "Dist %",
           "HL Count", "Candle at HL", "Support", "Score", "Confluence", "SL", "T1", "T2", "R:R", "Chart", "Groww"]
SR_COLS = ["Stock", "Name", "Price", "Trend", "Weekly", "Pattern", "Score", "Buyer %", "Seller %", "Chart", "Groww"]


def show_table(df, cols, key):
    if df.empty:
        st.info("⚠️ এই ফিল্টারে এখন কোনো স্টক পাওয়া যায়নি।")
        return
    st.dataframe(
        df[cols], hide_index=True,
        column_config={
            "Chart": st.column_config.LinkColumn("Chart", display_text="📈 খুলুন"),
            "Groww": st.column_config.LinkColumn("Groww", display_text="🚀 খুলুন"),
        },
    )
    st.download_button("⬇️ CSV ডাউনলোড", df[cols].drop(columns=["Chart", "Groww"]).to_csv(index=False).encode("utf-8"),
                       file_name=f"{key}.csv", mime="text/csv", key=f"dl_{key}")


def show_results(price_sel, only_up, weekly_mode):
    s = st.session_state["scan"]
    st.success(f"স্ক্যানিং সম্পন্ন! {s['scanned']}/{s['total']} স্টক | {s['tf']} | {s['time']}")
    df = pd.DataFrame(s["rows"])
    if not df.empty:
        df = df[df["Status"].isin(price_sel)]
        if only_up:
            df = df[df["_up"]]
        if weekly_mode in (W_UP, W_BOTH):
            df = df[df["_w_up"] == True]  # noqa: E712
        if weekly_mode in (W_HL, W_BOTH):
            df = df[df["_w_hl"] == True]  # noqa: E712

    if df.empty:
        hl_pat = hl_all = bull = bear = df
    else:
        hl_all = df[df["_has_hl"]].sort_values(["Score", "HL Count"], ascending=[False, False])
        hl_pat = hl_all[hl_all["Candle at HL"] != ""]
        bull = df[df["Type"] == "Bullish"].sort_values("Buyer %", ascending=False)
        bear = df[df["Type"] == "Bearish"].sort_values("Seller %", ascending=False)

    t1, t2, t3, t4 = st.tabs([
        f"⭐ HL + Candle ({len(hl_pat)})", f"📈 Higher Low ({len(hl_all)})",
        f"🟢 Support Bullish ({len(bull)})", f"🔴 Resistance Bearish ({len(bear)})",
    ])
    with t1:
        st.caption("Higher Low-এর নিচের পয়েন্টে ক্যান্ডেল প্যাটার্নও মিলেছে। Support কলামে দেখুন HL কোথায় টিকেছে। Stop = HL-এর Low।")
        show_table(hl_pat, HL_COLS, "hl_candle")
    with t2:
        st.caption("Higher Low তৈরি হয়েছে (ক্যান্ডেল প্যাটার্ন থাকতেও পারে, না-ও পারে)।")
        show_table(hl_all, HL_COLS, "higher_low")
    with t3:
        show_table(bull, SR_COLS, "support_bullish")
    with t4:
        show_table(bear, SR_COLS, "resistance_bearish")

    if s["failed"]:
        with st.expander(f"⚠️ ডেটা না পাওয়া / কম ডেটার স্টক ({len(s['failed'])})"):
            st.write(", ".join(t.replace('.NS', '') for t in s["failed"]))
    if s["errors"]:
        with st.expander(f"❗ এরর ({len(s['errors'])})"):
            st.write("\n".join(s["errors"][:50]))


def draw_chart(rep):
    d = rep["d"].tail(90)
    try:
        import plotly.graph_objects as go
        fig = go.Figure(go.Candlestick(x=d.index, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"]))
        lines = []
        s = rep["setup"]
        if s:
            lines += [("SL", s["sl"], "red"), ("T1", s["t1"], "green"), ("T2", s["t2"], "green")]
        lv = rep["levels"]
        for k, name in (("support", "S(D)"), ("resistance", "R(D)"), ("w_support", "S(W)"), ("w_resistance", "R(W)")):
            if lv.get(k):
                lines.append((name, lv[k], "gray"))
        for name, y, col in lines:
            fig.add_hline(y=y, line_dash="dot", line_color=col, annotation_text=f"{name} {y:.1f}")
        fig.update_layout(xaxis_rangeslider_visible=False, height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig)
    except Exception:  # noqa: BLE001
        e = rep["d"]["Close"].tail(90)
        st.line_chart(pd.DataFrame({"Close": e, "EMA20": _ema(e.to_numpy(float), 20), "EMA50": _ema(e.to_numpy(float), 50)}, index=e.index))


def render_deep(rep):
    if rep.get("error"):
        st.error(rep["error"])
        return
    box = {"take": st.success, "wait": st.warning, "avoid": st.error}[rep["verdict_kind"]]
    box(f"**{rep['ticker'].replace('.NS', '')} — {rep['verdict']}**"
        + (": " + "; ".join(rep["reasons"]) if rep["reasons"] else ""))
    ok, tot = rep["confluence"]
    s = rep["setup"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("সেটআপ স্কোর", f"{rep['score']}/100" if rep["score"] is not None else "—")
    m2.metric("কনফ্লুয়েন্স", f"{ok}/{tot}")
    m3.metric("R:R (T1)", f"1:{s['rr1']:.2f}" if s else "—")
    m4.metric("ঝুঁকি", f"{s['risk_pct']:.1f}%" if s else "—")
    st.caption("এটি নিয়মভিত্তিক স্কোর, জেতার সম্ভাবনা (probability %) নয়।")
    st.dataframe(pd.DataFrame([{"#": c["id"], "বিষয়": c["title"], "ফল": c["status"], "বিবরণ": c["detail"]}
                               for c in rep["checks"]]), hide_index=True)
    if s:
        st.markdown("**ট্রেড সেটআপ (৩-৭ দিনের হোল্ড)**")
        st.dataframe(pd.DataFrame([{
            "Entry": round(_tick(s["entry"]), 2), "Stop-Loss": round(_tick(s["sl"]), 2),
            "Target 1": round(_tick(s["t1"]), 2), "Target 2": round(_tick(s["t2"]), 2),
            "R:R (T1)": round(s["rr1"], 2), "R:R (T2)": round(s["rr2"], 2),
        }]), hide_index=True)
    st.info("⏰ এন্ট্রি টাইমিং: " + rep["timing"])
    draw_chart(rep)
    st.caption("ফান্ডামেন্টাল, ইভেন্ট ও সেক্টর ডেটা Yahoo থেকে আসে, কখনো অসম্পূর্ণ/ভুল হতে পারে। শুধু শিক্ষামূলক, আর্থিক পরামর্শ নয়।")


# ───────────────────────── UI ─────────────────────────

# ───────────────────────── ⭐ আজকের সেরা স্টক ─────────────────────────
def draw_stored_chart(p):
    ch = p.get("chart")
    if not ch:
        return
    try:
        import plotly.graph_objects as go
        fig = go.Figure(go.Candlestick(x=ch["x"], open=ch["o"], high=ch["h"], low=ch["l"], close=ch["c"]))
        s = p.get("setup") or {}
        for name, key, col in (("SL", "sl", "red"), ("T1", "t1", "green"), ("T2", "t2", "green")):
            if s.get(key):
                fig.add_hline(y=s[key], line_dash="dot", line_color=col, annotation_text=f"{name} {s[key]:.1f}")
        if p.get("hl_price"):
            fig.add_hline(y=p["hl_price"], line_dash="dash", line_color="orange", annotation_text=f"HL {p['hl_price']:.1f}")
        fig.update_layout(xaxis_rangeslider_visible=False, height=380, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig)
    except Exception:  # noqa: BLE001
        st.line_chart(pd.DataFrame({"Close": ch["c"]}, index=ch["x"]))


def picks_table(picks):
    rows = []
    for p in picks:
        s = p.get("setup") or {}
        rows.append({
            "Stock": p["stock"], "Name": p.get("name", ""), "সিদ্ধান্ত": p["verdict"], "Score": p["score"],
            "Confluence": f"{p['confluence'][0]}/{p['confluence'][1]}", "Entry": s.get("entry"), "SL": s.get("sl"),
            "T1": s.get("t1"), "T2": s.get("t2"), "R:R": round(s["rr1"], 2) if s.get("rr1") else None,
            "Weekly": p.get("weekly"), "Candle at HL": p.get("candle"), "Support": p.get("support"),
            "Chart": p["links"]["tv"], "Groww": p["links"]["groww"],
        })
    return pd.DataFrame(rows)


def render_picks(data):
    reg = data["regime"]
    box = {"GREEN": st.success, "YELLOW": st.warning, "RED": st.error}.get(reg["level"], st.info)
    box(f"**সার্বিক বাজার: {LEVEL_UI.get(reg['level'], reg['level'])}** (স্কোর {reg.get('score')}/{reg.get('max')}) "
        f"| স্ক্যানের সময়: {data['generated']}")
    with st.expander("বাজারের বিস্তারিত: গ্লোবাল, Nifty 50, সেক্টর"):
        for r in reg.get("reasons", []):
            st.write("• " + r)
        if reg.get("sectors"):
            st.dataframe(pd.DataFrame(reg["sectors"])[["name", "trend", "ret20", "rs20"]].rename(columns={
                "name": "সেক্টর", "trend": "ট্রেন্ড", "ret20": "২০ দিনে %", "rs20": "Nifty-র চেয়ে %"}), hide_index=True)
    sc = data["scan"]
    st.caption(f"স্ক্যান হয়েছে {sc['scanned']}/{sc['total']} স্টক (NSE {sc['nse']} + শুধু-BSE {sc['bse_only']}) | "
               f"HL + ক্যান্ডেল সেটআপ {len(data['signals'])} | চূড়ান্ত বাছাইয়ের যোগ্য {sc['candidates']}")
    for n_ in data.get("notes", []):
        st.warning(n_)

    picks = data["picks"]
    takes = [p for p in picks if p["verdict_kind"] == "take"]
    st.subheader(f"✅ এখন ট্রেড যুক্তিসঙ্গত ({len(takes)})")
    if takes:
        st.dataframe(picks_table(takes), hide_index=True, column_config=LINKS)
    else:
        st.info("আজ সব শর্ত পূরণ করা কোনো স্টক নেই। অপেক্ষা করাও একটি সিদ্ধান্ত।")
    rest = [p for p in picks if p["verdict_kind"] != "take"]
    if rest:
        with st.expander(f"⏳ অপেক্ষা / ❌ বাদ ({len(rest)})"):
            st.dataframe(picks_table(rest), hide_index=True, column_config=LINKS)
    st.caption("এখানকার Entry = শেষ ক্লোজ। T1/T2 = পরবর্তী রেজিস্ট্যান্স। ৩-৭ দিনের মধ্যে বের হওয়ার পরিকল্পনা।")

    for p in picks[:10]:
        with st.expander(f"📋 {p['stock']} — {p['verdict']} | স্কোর {p['score']}"):
            if p.get("reasons"):
                st.write("কারণ: " + "; ".join(p["reasons"]))
            st.dataframe(pd.DataFrame([{"#": c["id"], "বিষয়": c["title"], "ফল": c["status"], "বিবরণ": c["detail"]}
                                       for c in p["checks"]]), hide_index=True)
            st.info("⏰ এন্ট্রি টাইমিং: " + p.get("timing", ""))
            draw_stored_chart(p)

    if data.get("signals"):
        with st.expander(f"সব HL + ক্যান্ডেল সংকেত ({len(data['signals'])}, শুধু তথ্যের জন্য)"):
            st.dataframe(pd.DataFrame(data["signals"]), hide_index=True, column_config=LINKS)

    bt = data.get("backtest")
    with st.expander("📊 কৌশলটি অতীতে কতটা কাজ করেছে (ব্যাকটেস্ট) — ৯০%-এর বাস্তবতা"):
        if not bt:
            st.info("ব্যাকটেস্টের ফল এই রানে নেই।")
        else:
            st.write(f"{bt['stocks']}টি স্টক, গত {bt['years']} বছর, ট্রেড {bt['n_trades']}টি। "
                     f"প্রতিটি ট্রেড: সংকেতের দিনের ক্লোজে এন্ট্রি, টার্গেট ১:২, সর্বোচ্চ {bt['horizon_sessions']} সেশন।")
            st.dataframe(pd.DataFrame(bt["rows"]).rename(columns={
                "name": "ফিল্টার", "n": "ট্রেড", "target": "টার্গেটে %", "stop": "SL-এ %", "timeout": "সময়-শেষ %",
                "win": "লাভে বন্ধ %", "avg_r": "গড় R"}), hide_index=True)
            for c in bt.get("caveats", []):
                st.caption("• " + c)
        st.warning("কোনো ট্রেডিং কৌশলেই ৯০% জয়ের নিশ্চয়তা দেওয়া যায় না। ফিল্টার বাড়ালে সংখ্যা কমে, জয়ের হার সামান্য বাড়তে পারে, "
                   "কিন্তু ৯০% হয় না। উপরের সংখ্যাগুলোই বাস্তব ঐতিহাসিক চিত্র; ভবিষ্যতে এর চেয়ে খারাপও হতে পারে।")


def render_picks_tab(params):
    data = st.session_state.get("picks_live") or load_picks()
    if data is None:
        st.info("এখনো কোনো সংরক্ষিত স্ক্যান-ফল নেই। README অনুযায়ী GitHub Action চালু করলে রোজ বিকেলে এখানে নিজে থেকে আসবে। "
                "এখনই দেখতে নিচের বাটনে চাপুন (১৫-৩০ মিনিট লাগতে পারে)।")
    else:
        render_picks(data)
    with st.expander("এখনই নতুন করে NSE + BSE সব স্টক স্ক্যান করুন (ধীর)"):
        inc_bse = st.checkbox("BSE-র স্টকও (NSE-তে নেই এমন)", value=True)
        do_bt = st.checkbox("ব্যাকটেস্টও চালান", value=True)
        if st.button("▶️ এখনই স্ক্যান", key="run_now"):
            prog = st.progress(0.0, text="শুরু হচ্ছে...")
            st.session_state["picks_live"] = build_picks(
                params, progress=lambda f, t: prog.progress(min(max(float(f), 0.0), 1.0), text=t),
                include_bse=inc_bse, backtest_n=400 if do_bt else 0)
            prog.empty()
            st.rerun()


# ───────────────────────── 🔍 লাইভ স্ক্যানার ─────────────────────────
def render_live(params):
    c1, c2 = st.columns(2)
    with c1:
        universe = st.selectbox("স্টক তালিকা:", [UNI_NSE_BSE, UNI_ALL, UNI_BUILTIN, UNI_UPLOAD])
    with c2:
        tf = st.selectbox("ক্যান্ডেল টাইমফ্রেম:", list(TIMEFRAMES.keys()))
    uploaded = None
    if universe == UNI_UPLOAD:
        uploaded = st.file_uploader("টিকার ফাইল (প্রতি লাইনে একটি, যেমন RELIANCE)", type=["txt", "csv"])

    price_sel = st.multiselect("🎯 কোন প্রাইস রেঞ্জের স্টক দেখতে চান:", [STATUS_MID, STATUS_HIGH, STATUS_LOW],
                               default=[STATUS_MID, STATUS_HIGH, STATUS_LOW])
    weekly_mode = st.selectbox(
        "📅 সাপ্তাহিক (Weekly) ফিল্টার:", [W_UP, W_HL, W_BOTH, W_OFF],
        help="স্ক্যানের পরেও এটি বদলালে আবার স্ক্যান করতে হয় না।",
    )
    c3, c4 = st.columns(2)
    with c3:
        only_up = st.checkbox("শুধু Uptrend (EMA20 > EMA50, দাম EMA50-এর উপরে)", value=False)
    with c4:
        include_forming = st.checkbox("চলমান (অসম্পূর্ণ) ক্যান্ডেলও গণনা করুন", value=False)

    if st.button("🔍 স্ক্যান শুরু করুন", type="primary"):
        tickers = load_universe(universe, uploaded)
        if not tickers:
            st.error("কোনো টিকার পাওয়া যায়নি।")
        else:
            run_scan(tickers, tf, params, include_forming)

    if "scan" in st.session_state:
        show_results(price_sel, only_up, weekly_mode)

    st.divider()
    st.subheader("🧪 ডিপ অ্যানালাইসিস (১৫-পয়েন্ট চেকলিস্ট, Daily + Weekly)")
    st.caption("একটি স্টক বেছে নিন বা টিকার লিখুন (NSE: TCS, BSE: 500325)। ফান্ডামেন্টাল, ইভেন্ট, সেক্টর, গ্লোবাল রিস্কসহ পুরো রিপোর্ট আসবে।")
    tmap = {}
    if "scan" in st.session_state:
        tmap = {r["Stock"]: r["_t"] for r in st.session_state["scan"]["rows"]}
    c6, c7 = st.columns(2)
    with c6:
        pick = st.selectbox("স্ক্যান-ফলাফল থেকে বাছুন:", ["—"] + list(tmap))
    with c7:
        typed = st.text_input("অথবা টিকার লিখুন (যেমন TCS):")
    sector_label = st.selectbox("সেক্টর ইনডেক্স (ঐচ্ছিক):", list(SECTOR_CHOICES))
    if st.button("🧪 বিশ্লেষণ করুন"):
        sym = typed.strip().upper()
        if sym:
            ticker = sym if sym.endswith((".NS", ".BO")) else sym + (".BO" if sym.isdigit() else ".NS")
        else:
            ticker = tmap.get(pick, "")
        if not ticker:
            st.warning("একটি স্টক বাছুন বা টিকার লিখুন।")
        else:
            with st.spinner("বিশ্লেষণ চলছে..."):
                st.session_state["deep"] = deep_analyze(ticker, params, SECTOR_CHOICES[sector_label])
    if "deep" in st.session_state:
        render_deep(st.session_state["deep"])


# ───────────────────────── UI ─────────────────────────
def main():
    st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")
    st.title("⚡ AI Stock Screener Pro (NSE + BSE)")
    st.caption("Weekly ট্রেন্ডের পক্ষে Daily Higher Low + ক্যান্ডেল প্যাটার্ন। শুধু শিক্ষামূলক, আর্থিক পরামর্শ নয়।")

    with st.sidebar:
        st.header("⚙️ Higher Low সেটিংস")
        n = st.slider("Swing শক্তি (n ক্যান্ডেল দু'পাশে)", 2, 6, 3)
        max_age = st.slider("HL কতগুলো ক্যান্ডেল আগে পর্যন্ত", 3, 30, 10)
        max_dist = st.slider("দাম HL থেকে সর্বোচ্চ কত % উপরে", 1.0, 15.0, 5.0, 0.5)
        min_rise = st.slider("HL পুরনো লো থেকে কমপক্ষে কত % উঁচু", 0.1, 3.0, 0.3, 0.1)
        min_swing = st.slider("দুই লো-এর মাঝে কমপক্ষে কত % উঠা", 0.5, 8.0, 1.0, 0.5)
        min_vol = st.number_input("ন্যূনতম গড় ভলিউম (শেষ ২০ ক্যান্ডেল)", min_value=0, value=100000, step=50000)
    params = dict(n=n, max_age=max_age, max_dist=max_dist, min_rise=min_rise, min_swing=min_swing, min_vol=min_vol)

    tab_picks, tab_live = st.tabs(["⭐ আজকের সেরা স্টক", "🔍 লাইভ স্ক্যানার ও ডিপ অ্যানালাইসিস"])
    with tab_picks:
        render_picks_tab(params)
    with tab_live:
        render_live(params)


# ───────────────────────── রোজকার স্বয়ংক্রিয় স্ক্যান (GitHub Action) ─────────────────────────
def run_job(include_bse=True, backtest_n=400, out="data/picks.json"):
    """NSE + BSE সব স্টক স্ক্যান করে ফল out-এ লেখে।"""
    last = {"p": -1}

    def progress(f, text):
        p = int(f * 100)
        if p != last["p"]:
            last["p"] = p
            print(f"[{p:3d}%] {text}", flush=True)

    data = build_picks(progress=progress, include_bse=include_bse, backtest_n=backtest_n)
    save_json(data, out)
    sc = data["scan"]
    take = sum(p["verdict_kind"] == "take" for p in data["picks"])
    print(f"সম্পন্ন: {sc['scanned']}/{sc['total']} স্টক | HL+ক্যান্ডেল {len(data['signals'])} | "
          f"বাছাই {len(data['picks'])} (ট্রেড-যোগ্য {take}) | বাজার {data['regime']['level']} | {data['runtime_min']} মিনিট")
    for n_ in data["notes"]:
        print("নোট:", n_)



if __name__ == "__main__":
    main()
