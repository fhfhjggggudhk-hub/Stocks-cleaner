import io

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Support + Candle Scanner", layout="wide")

IST = "Asia/Kolkata"
PATTERNS = ["Green Hammer", "Red Hammer", "Dragonfly Doji", "Doji", "Bullish Engulfing"]


# ---------------------------------------------------------------- indicators
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def atr(df, n=14):
    pc = df.Close.shift()
    tr = pd.concat(
        [df.High - df.Low, (df.High - pc).abs(), (df.Low - pc).abs()], axis=1
    ).max(axis=1)
    return tr.rolling(n).mean()


# ---------------------------------------------------------------- candle patterns
def candle_pattern(df):
    """Pattern on the LAST candle, only after a short downtrend. Returns name or None."""
    if len(df) < 12:
        return None
    o, h, l, c = (df[x].values for x in ("Open", "High", "Low", "Close"))
    O, H, L, C = o[-1], h[-1], l[-1], c[-1]
    rng = H - L
    if rng <= 0:
        return None
    if not c[-2] < c[-7]:  # needs a prior downtrend
        return None
    body = abs(C - O)
    upper = H - max(O, C)
    lower = min(O, C) - L

    if body <= 0.1 * rng:
        if upper <= 0.1 * rng and lower >= 0.6 * rng:
            return "Dragonfly Doji"
        return "Doji"
    # hammer: long lower shadow (>=2x body), tiny upper shadow, body in top 40% of range
    if lower >= 2 * body and upper <= 0.5 * body and min(O, C) >= L + 0.6 * rng:
        return "Green Hammer" if C > O else "Red Hammer"
    # bullish engulfing: red candle fully covered by a bigger green body
    pO, pC = o[-2], c[-2]
    if pC < pO and C > O and O <= pC and C >= pO and body >= 1.1 * abs(pC - pO):
        return "Bullish Engulfing"
    return None


# ---------------------------------------------------------------- supports
def pivots(df, k=3, look=150):
    n = len(df)
    lows, highs = df.Low.values, df.High.values
    pl, ph = [], []
    for i in range(max(k, n - look), n - k - 1):  # confirmed pivots, last candle excluded
        if lows[i] == lows[i - k : i + k + 1].min():
            pl.append((i, lows[i]))
        if highs[i] == highs[i - k : i + k + 1].max():
            ph.append((i, highs[i]))
    return pl, ph


def find_supports(df, tol):
    n = len(df)
    L, C = df.Low.iat[-1], df.Close.iat[-1]
    o, h, l, c = (df[x].values for x in ("Open", "High", "Low", "Close"))
    out = []

    def near(lv):  # candle low tested the level and the close held it
        return abs(L - lv) <= lv * tol and C >= lv * (1 - tol)

    pl, ph = pivots(df)

    # 1) Swing low
    for _, lv in reversed(pl):
        if near(lv):
            out.append(f"Swing Low ₹{lv:.2f}")
            break

    # 2) EMA
    for p in (20, 50, 100, 200):
        if n >= p:
            lv = ema(df.Close, p).iat[-1]
            if near(lv):
                out.append(f"EMA{p} ₹{lv:.2f}")

    # 3) Breakout retest (old resistance -> new support)
    for ip, hv in reversed(ph):
        after = np.where(c[ip + 1 :] > hv)[0]
        if len(after) == 0:
            continue
        j = ip + 1 + after[0]
        if j <= n - 3 and c[j : n - 1].min() >= hv * (1 - tol) and near(hv):
            out.append(f"Breakout Retest ₹{hv:.2f}")
            break

    # 4) Fibonacci retracement of the biggest recent up-swing
    look = min(n, 120)
    sl, sh = l[-look:], h[-look:]
    il = int(sl.argmin())
    ih = il + int(sh[il:].argmax())
    if il < ih <= look - 2 and sh[ih] / sl[il] - 1 >= 0.15:
        for r in (0.382, 0.5, 0.618):
            lv = sh[ih] - (sh[ih] - sl[il]) * r
            if near(lv):
                out.append(f"Fib {r * 100:.1f}% ₹{lv:.2f}")

    # 5) Demand zone: base candle before a strong green impulse, zone still unbroken
    a = atr(df).values
    for j in range(n - 4, max(15, n - 120), -1):
        if np.isnan(a[j - 1]):
            continue
        if c[j] > o[j] and (c[j] - o[j]) >= 1.5 * a[j - 1] and c[j] > h[j - 1]:
            zlo, zhi = l[j - 1], max(o[j - 1], c[j - 1])
            if c[j + 1 : n - 1].min() < zlo * (1 - tol / 2):
                continue  # zone already broken
            if zlo * (1 - tol) <= L <= zhi * (1 + tol) and C >= zlo * (1 - tol):
                out.append(f"Demand Zone ₹{zlo:.2f}–{zhi:.2f}")
                break
    return out


# ---------------------------------------------------------------- data
@st.cache_data(ttl=86400, show_spinner=False)
def nse_symbols():
    r = requests.get(
        "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [x.strip() for x in df.columns]
    df = df[df["SERIES"].str.strip().isin(["EQ", "BE"])]
    return df["SYMBOL"].str.strip().tolist()


def read_nse_csv(file):
    df = pd.read_csv(file)
    df.columns = [x.strip() for x in df.columns]
    col = "SYMBOL" if "SYMBOL" in df.columns else df.columns[0]
    return df[col].astype(str).str.strip().tolist()


def read_bse_csv(file, nse_set):
    df = pd.read_csv(file)
    df.columns = [x.strip() for x in df.columns]
    code = next(c for c in df.columns if "code" in c.lower())
    sid = next(
        (c for c in df.columns if "id" in c.lower().split() or c.lower().endswith(" id")),
        None,
    )
    if sid:  # skip BSE stocks already covered through NSE
        df = df[~df[sid].astype(str).str.strip().isin(nse_set)]
    return [str(int(x)) for x in df[code].dropna()]


@st.cache_data(ttl=3600, show_spinner=False)
def fetch(tickers: tuple):
    raw = yf.download(
        list(tickers), period="5y", interval="1d", group_by="ticker",
        auto_adjust=True, threads=True, progress=False,
    )
    res = {}
    for t in tickers:
        try:
            d = raw[t] if isinstance(raw.columns, pd.MultiIndex) else raw
            d = d[["Open", "High", "Low", "Close"]].dropna()
            idx = pd.DatetimeIndex(d.index)
            if idx.tz is not None:
                idx = idx.tz_localize(None)
            d.index = idx.normalize()
            if len(d) > 60:
                res[t] = d
        except Exception:
            pass
    return res


def to_weekly(d):
    return d.resample("W-FRI").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    ).dropna()


# ---------------------------------------------------------------- UI
st.title("Support + Bullish Candle Scanner")

with st.sidebar:
    tfs = st.multiselect("Timeframe", ["Daily", "Weekly"], default=["Daily", "Weekly"])
    pats = st.multiselect("Patterns", PATTERNS, default=PATTERNS)
    tol_pct = st.slider("Support tolerance %", 0.5, 5.0, 2.0, 0.5)
    complete_only = st.checkbox("Ignore running (incomplete) candle", value=True)
    max_n = st.number_input("Max stocks to scan (0 = all)", 0, 10000, 300, 100)
    bse_file = st.file_uploader("BSE list CSV (optional)", type="csv")
    nse_file = st.file_uploader("NSE list CSV (only if auto-fetch fails)", type="csv")
    run = st.button("Scan", type="primary")

if run:
    # ---- stock list
    try:
        nse = nse_symbols() if nse_file is None else read_nse_csv(nse_file)
    except Exception as e:
        st.error(f"NSE list could not be fetched ({e}). Upload the NSE CSV in the sidebar.")
        st.stop()
    bse = []
    if bse_file is not None:
        try:
            bse = read_bse_csv(bse_file, set(nse))
        except Exception as e:
            st.warning(f"BSE CSV could not be read: {e}")
    universe = [(f"{s}.NS", "NSE", s) for s in nse] + [(f"{s}.BO", "BSE", s) for s in bse]
    if max_n:
        universe = universe[: int(max_n)]
    st.write(f"Scanning {len(universe)} stocks...")

    now = pd.Timestamp.now(tz=IST)
    today = now.tz_localize(None).normalize()
    mkt_open = now.weekday() < 5 and (now.hour * 60 + now.minute) < 15 * 60 + 45
    tol = tol_pct / 100

    def is_running(ts):
        return ts > today or (ts == today and mkt_open)

    rows, bar = [], st.progress(0.0)
    meta = {t: (ex, sym) for t, ex, sym in universe}
    tickers = [t for t, _, _ in universe]
    CH = 100
    for i in range(0, len(tickers), CH):
        data = fetch(tuple(tickers[i : i + CH]))
        for t, d in data.items():
            ex, sym = meta[t]
            for tf in tfs:
                x = d if tf == "Daily" else to_weekly(d)
                if complete_only and len(x) and is_running(x.index[-1]):
                    x = x.iloc[:-1]
                if len(x) < 30:
                    continue
                pat = candle_pattern(x)
                if pat is None or pat not in pats:
                    continue
                sup = find_supports(x, tol)
                if not sup:
                    continue
                link = f"https://www.tradingview.com/chart/?symbol={ex}:{sym}"
                rows.append({
                    "Stock": sym, "Exchange": ex, "Timeframe": tf, "Pattern": pat,
                    "Support": " + ".join(sup), "Close": round(float(x.Close.iat[-1]), 2),
                    "Candle date": x.index[-1].date(), "Chart": link,
                })
        bar.progress(min(1.0, (i + CH) / len(tickers)))
    st.session_state["result"] = pd.DataFrame(rows)

res = st.session_state.get("result")
if res is not None:
    if res.empty:
        st.info("No stock matched.")
    else:
        st.success(f"{len(res)} matches")
        st.dataframe(
            res, use_container_width=True, hide_index=True,
            column_config={"Chart": st.column_config.LinkColumn("Chart", display_text="Open")},
        )
        st.download_button("Download CSV", res.to_csv(index=False), "scan_result.csv", "text/csv")
