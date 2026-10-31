"""
⚡ AI Stock Screener Pro — NSE All-Stock Scanner
  * Higher Low (HL) + HL-এ ক্যান্ডেল প্যাটার্ন (⭐ সবচেয়ে মজবুত সেটআপ)
  * সাপোর্টে বুলিশ / রেজিস্ট্যান্সে বেয়ারিশ ক্যান্ডেল প্যাটার্ন
  * একবারে সব NSE স্টক, ব্যাচে ডাউনলোড (দ্রুত), শুধু বন্ধ হয়ে যাওয়া ক্যান্ডেল বিশ্লেষণ

Run:  streamlit run app.py
এটি শুধু শিক্ষামূলক টুল, আর্থিক পরামর্শ নয়।
"""
import io
import re
import time
from datetime import datetime
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
    "1 Day (Daily)": dict(period="6mo", interval="1d", resample=None, delta=pd.Timedelta(days=1)),
    "4 Hours (4h)": dict(period="3mo", interval="1h", resample="4h", delta=pd.Timedelta(hours=4)),
    "1 Hour (1h)": dict(period="3mo", interval="1h", resample=None, delta=pd.Timedelta(hours=1)),
    "15 Minutes (15m)": dict(period="1mo", interval="15m", resample=None, delta=pd.Timedelta(minutes=15)),
}

STATUS_MID = "🟢 In Range (₹500 - ₹2,000)"
STATUS_HIGH = "🔴 Above ₹2,000"
STATUS_LOW = "🟡 Below ₹500"

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


def prepare_frame(df, cfg):
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    if cfg["resample"] and not df.empty:
        # NSE ৯:১৫ থেকে শুরু, তাই ৪-ঘণ্টার ক্যান্ডেল ৯:১৫ ও ১৩:১৫ থেকে
        df = (
            df.resample(cfg["resample"], offset="9h15min")
            .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
            .dropna(subset=["Open"])
        )
    return df


def drop_forming_candle(df, cfg):
    """বাজার চলাকালীন তৈরি হওয়া অসম্পূর্ণ শেষ ক্যান্ডেল বাদ দেয়।"""
    if df.empty:
        return df
    last = df.index[-1]
    if last.tzinfo is None:
        last = last.tz_localize(IST)
    end = min(last + cfg["delta"], last.normalize() + MARKET_CLOSE)
    return df if end <= datetime.now(IST) else df.iloc[:-1]


# ───────────────────────── Higher Low ─────────────────────────
def _swing_lows(L, n):
    idx = []
    for i in range(n, len(L) - n):
        if L[i] < L[i - n:i].min() and L[i] <= L[i + 1:i + n + 1].min():
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
def bullish_shape(O, H, L, C, j):
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
    if g1 and b1 > 0 and lower1 >= 2 * b1 and upper1 <= 0.2 * b1:
        return "🔨 Green Hammer", l1
    if g1 and b1 > 0 and upper1 >= 2 * b1 and lower1 <= 0.2 * b1:
        return "🙃 Inverted Hammer", l1
    if b1 <= 0.1 * rng1 and lower1 >= 0.6 * rng1 and upper1 <= 0.1 * rng1:
        return "🐉 Dragonfly Doji", l1
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
    O, H, L, C = (df[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
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
            found = bullish_shape(O, H, L, C, j)
            if found and abs(found[1] - hl["hl"]) <= tol(j, 1.0):
                res["hl_pattern"] = found[0]
                break
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


# ───────────────────────── স্ক্যান ও ফলাফল ─────────────────────────
def chart_links(ticker):
    sym = ticker.replace(".NS", "")
    tv = sym.replace("&", "_").replace("-", "_")
    return (f"https://in.tradingview.com/chart/?symbol=NSE%3A{quote(tv, safe='')}",
            f"https://groww.in/search?q={quote(sym, safe='')}")


def make_row(ticker, res):
    sym = ticker.replace(".NS", "")
    tv, groww = chart_links(ticker)
    row = {
        "Stock": sym, "Price": res["price"], "Status": res["status"],
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
            "HL Time": t.strftime("%d-%b %H:%M") if hasattr(t, "strftime") else str(t),
            "Candles Ago": hl["age"], "Dist %": round(hl["dist"], 2), "HL Count": hl["count"],
            "Stop": hl["stop"], "Risk %": hl["risk_pct"], "Target 1:2": hl["target"],
        })
    return row


def run_scan(tickers, tf, params, include_forming):
    cfg = TIMEFRAMES[tf]
    chunks = [tickers[i:i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
    rows, failed, errors = [], [], []
    scanned = 0
    prog = st.progress(0.0, text="স্ক্যান শুরু হচ্ছে...")
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
            except Exception as e:  # noqa: BLE001
                errors.append(f"{t}: {type(e).__name__}: {e}")
        prog.progress((ci + 1) / len(chunks),
                      text=f"{ci + 1}/{len(chunks)} ব্যাচ শেষ | স্ক্যান: {scanned} | সেটআপ পাওয়া গেছে: {len(rows)}")
        time.sleep(0.3)
    prog.empty()
    st.session_state["scan"] = dict(
        rows=rows, failed=failed, errors=errors, scanned=scanned, total=len(tickers),
        tf=tf, time=datetime.now(IST).strftime("%d-%b-%Y %H:%M IST"),
    )


HL_COLS = ["Stock", "Price", "Trend", "HL Price", "Prev Low", "HL Time", "Candles Ago", "Dist %",
           "HL Count", "Candle at HL", "Stop", "Risk %", "Target 1:2", "Chart", "Groww"]
SR_COLS = ["Stock", "Price", "Trend", "Pattern", "Buyer %", "Seller %", "Chart", "Groww"]


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


def show_results(price_sel, only_up):
    s = st.session_state["scan"]
    st.success(f"স্ক্যানিং সম্পন্ন! {s['scanned']}/{s['total']} স্টক | {s['tf']} | {s['time']}")
    df = pd.DataFrame(s["rows"])
    if not df.empty:
        df = df[df["Status"].isin(price_sel)]
        if only_up:
            df = df[df["_up"]]

    if df.empty:
        hl_pat = hl_all = bull = bear = df
    else:
        hl_all = df[df["_has_hl"]].sort_values(["HL Count", "Dist %"], ascending=[False, True])
        hl_pat = hl_all[hl_all["Candle at HL"] != ""]
        bull = df[df["Type"] == "Bullish"].sort_values("Buyer %", ascending=False)
        bear = df[df["Type"] == "Bearish"].sort_values("Seller %", ascending=False)

    t1, t2, t3, t4 = st.tabs([
        f"⭐ HL + Candle ({len(hl_pat)})", f"📈 Higher Low ({len(hl_all)})",
        f"🟢 Support Bullish ({len(bull)})", f"🔴 Resistance Bearish ({len(bear)})",
    ])
    with t1:
        st.caption("Higher Low তৈরি হওয়ার জায়গায় বুলিশ ক্যান্ডেল প্যাটার্নও মিলেছে। Stop = HL-এর Low।")
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


# ───────────────────────── UI ─────────────────────────
def main():
    st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")
    st.title("⚡ AI Stock Screener Pro (সব NSE স্টক স্ক্যানার)")
    st.caption("Higher Low + ক্যান্ডেলস্টিক প্যাটার্ন। একবারে সব স্টক স্ক্যান হয়। শুধু শিক্ষামূলক, আর্থিক পরামর্শ নয়।")

    with st.sidebar:
        st.header("⚙️ Higher Low সেটিংস")
        n = st.slider("Swing শক্তি (n ক্যান্ডেল দু'পাশে)", 2, 6, 3)
        max_age = st.slider("HL কতগুলো ক্যান্ডেল আগে পর্যন্ত", 3, 30, 10)
        max_dist = st.slider("দাম HL থেকে সর্বোচ্চ কত % উপরে", 1.0, 15.0, 5.0, 0.5)
        min_rise = st.slider("HL পুরনো লো থেকে কমপক্ষে কত % উঁচু", 0.1, 3.0, 0.3, 0.1)
        min_swing = st.slider("দুই লো-এর মাঝে কমপক্ষে কত % উঠা", 0.5, 8.0, 1.0, 0.5)

    c1, c2 = st.columns(2)
    with c1:
        universe = st.selectbox("স্টক তালিকা:", [UNI_ALL, UNI_BUILTIN, UNI_UPLOAD])
    with c2:
        tf = st.selectbox("ক্যান্ডেল টাইমফ্রেম:", list(TIMEFRAMES.keys()))
    uploaded = None
    if universe == UNI_UPLOAD:
        uploaded = st.file_uploader("টিকার ফাইল (প্রতি লাইনে একটি, যেমন RELIANCE)", type=["txt", "csv"])

    price_sel = st.multiselect("🎯 কোন প্রাইস রেঞ্জের স্টক দেখতে চান:", [STATUS_MID, STATUS_HIGH, STATUS_LOW],
                               default=[STATUS_MID, STATUS_HIGH, STATUS_LOW])
    c3, c4, c5 = st.columns(3)
    with c3:
        only_up = st.checkbox("শুধু Uptrend (EMA20 > EMA50, দাম EMA50-এর উপরে)", value=False)
    with c4:
        include_forming = st.checkbox("চলমান (অসম্পূর্ণ) ক্যান্ডেলও গণনা করুন", value=False)
    with c5:
        min_vol = st.number_input("ন্যূনতম গড় ভলিউম (শেষ ২০ ক্যান্ডেল)", min_value=0, value=100000, step=50000)

    if st.button("🔍 স্ক্যান শুরু করুন", type="primary"):
        tickers = load_universe(universe, uploaded)
        if not tickers:
            st.error("কোনো টিকার পাওয়া যায়নি।")
        else:
            params = dict(n=n, max_age=max_age, max_dist=max_dist, min_rise=min_rise,
                          min_swing=min_swing, min_vol=min_vol)
            run_scan(tickers, tf, params, include_forming)

    if "scan" in st.session_state:
        show_results(price_sel, only_up)


if __name__ == "__main__":
    main()
