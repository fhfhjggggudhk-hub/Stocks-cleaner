"""
⚡ AI Stock Screener Pro — NSE All-Stock Scanner
  * Higher Low (HL) + HL-এর নিচের পয়েন্টে ক্যান্ডেল প্যাটার্ন (⭐ সবচেয়ে মজবুত সেটআপ)
  * সাপ্তাহিক (Weekly) ট্রেন্ড ফিল্টার + দৈনিক (Daily) HL/এন্ট্রি
  * 🧪 ডিপ অ্যানালাইসিস: ১৫-পয়েন্ট চেকলিস্ট, এন্ট্রি/SL/টার্গেট, R:R, স্কোর ও সিদ্ধান্ত
  * সাপোর্টে বুলিশ / রেজিস্ট্যান্সে বেয়ারিশ ক্যান্ডেল প্যাটার্ন
  * একবারে সব NSE স্টক, ব্যাচে ডাউনলোড (দ্রুত), শুধু বন্ধ হয়ে যাওয়া ক্যান্ডেল বিশ্লেষণ

Run:  streamlit run app.py
এটি শুধু শিক্ষামূলক টুল, আর্থিক পরামর্শ নয়।
"""
import io
import re
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


@st.cache_data(ttl=86400, show_spinner=False)
def load_nse_universe():
    r = requests.get(NSE_EQUITY_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip() for c in df.columns]
    df = df[df["SERIES"].astype(str).str.strip() == "EQ"]
    return _dedupe([s.strip() + ".NS" for s in df["SYMBOL"].astype(str)])


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


def load_universe(choice, uploaded):
    if choice == UNI_UPLOAD:
        return parse_uploaded_tickers(uploaded) if uploaded else []
    if choice == UNI_ALL:
        try:
            return load_nse_universe()
        except Exception as e:  # noqa: BLE001
            st.warning(f"NSE তালিকা ডাউনলোড হয়নি ({type(e).__name__}); বিল্ট-ইন তালিকা ব্যবহার হচ্ছে।")
    return [t + ".NS" for t in FALLBACK_TICKERS]


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


@st.cache_data(ttl=600, show_spinner=False, max_entries=50)
def _cached_download(tickers, period, interval):
    out = _download(tickers, period, interval)
    if not out:
        raise ValueError("empty")  # খালি ফলাফল ক্যাশ হবে না
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
    wok = w is not None and len(w) >=
