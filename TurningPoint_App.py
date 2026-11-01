"""Swing scanner: Higher-Low reversal inside an uptrend (Daily + Weekly), NSE/BSE."""
import io, os, datetime as dt
import numpy as np
import pandas as pd
import requests
import yfinance as yf

NSE_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
NIFTY = "^NSEI"
GLOBAL = {"S&P500": "^GSPC", "Nasdaq": "^IXIC", "Nikkei": "^N225", "HangSeng": "^HSI", "DAX": "^GDAXI"}
INDIA = {"Nifty50": "^NSEI", "Bank": "^NSEBANK", "IT": "^CNXIT", "Pharma": "^CNXPHARMA",
         "Auto": "^CNXAUTO", "FMCG": "^CNXFMCG", "Metal": "^CNXMETAL",
         "Energy": "^CNXENERGY", "Realty": "^CNXREALTY"}

PARAMS = {
    "D": dict(fast=50, slow=200, short=10, n=3, min_age=3, max_age=12, min_bars=210,
              depth=(0.03, 0.20), bounce=(0.01, 0.10), rs_len=63),
    "W": dict(fast=10, slow=30, short=4, n=2, min_age=2, max_age=6, min_bars=45,
              depth=(0.05, 0.30), bounce=(0.02, 0.15), rs_len=13),
}
MIN_PRICE, MIN_TURNOVER = 20, 5e7   # Rs 20, avg daily value Rs 5 crore


# ---------- indicators ----------
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def pivot_lows(low, n):
    a, out = low.values, []
    for i in range(n, len(a) - n):
        if a[i] == a[i - n:i + n + 1].min():
            if out and i - out[-1] <= n:
                continue
            out.append(i)
    return out


def to_weekly(d):
    return d.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min",
                                    "Close": "last", "Volume": "sum"}).dropna()


# ---------- core strategy ----------
def find_setup(df, tf, rs_ref=None):
    """Uptrend -> pullback -> Higher Low pivot -> bounce confirmed."""
    p = PARAMS[tf]
    if len(df) < p["min_bars"]:
        return None
    c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
    ef, es = ema(c, p["fast"]), ema(c, p["slow"])
    last = c.iloc[-1]
    # 1) uptrend
    if not (last > es.iloc[-1] and ef.iloc[-1] > es.iloc[-1] and es.iloc[-1] > es.iloc[-11]):
        return None
    # 2) last two swing lows, second one higher
    lows = pivot_lows(l, p["n"])
    if len(lows) < 2:
        return None
    i1, i2 = lows[-2], lows[-1]
    age = len(df) - 1 - i2
    if not p["min_age"] <= age <= p["max_age"]:
        return None
    low1, low2 = l.iloc[i1], l.iloc[i2]
    if low2 <= low1 * 1.005:
        return None
    # 3) real pullback between the two lows
    swing_hi = h.iloc[i1:i2 + 1].max()
    depth = (swing_hi - low2) / swing_hi
    if not p["depth"][0] <= depth <= p["depth"][1]:
        return None
    # 4) reversal confirmed, not already extended
    bounce = (last - low2) / low2
    if not p["bounce"][0] <= bounce <= p["bounce"][1]:
        return None
    if last <= ema(c, p["short"]).iloc[-1]:
        return None
    r = rsi(c)
    if not (40 <= r.iloc[-1] <= 68 and r.iloc[-1] > r.iloc[-4]):
        return None
    # 5) risk sanity
    sl = low2 * 0.99
    risk = last - sl
    if risk <= 0 or risk / last > 0.10:
        return None
    base_vol = v.iloc[-23:-3].mean()
    vol_ratio = v.iloc[-3:].mean() / base_vol if base_vol > 0 else 1.0
    score = 40
    score += 15 if vol_ratio > 1.1 else 0
    score += 10 if r.iloc[-1] > 50 else 0
    if rs_ref is not None and len(c) > p["rs_len"]:
        score += 15 if (last / c.iloc[-1 - p["rs_len"]] - 1) > rs_ref else 0
    score += 10 if 0.05 <= depth <= 0.12 else 0
    score += 10 if low2 > low1 * 1.02 else 0
    return dict(tf=tf, close=last, low2=low2, low2_date=df.index[i2].date(), depth=depth,
                bounce=bounce, rsi=r.iloc[-1], vol_ratio=vol_ratio, sl=sl,
                t1=last + 1.5 * risk, t2=last + 2.5 * risk, score=score)


# ---------- data ----------
def clean(d):
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    return d.dropna(how="all")


def get_universe():
    try:
        r = requests.get(NSE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
    except Exception:
        df = pd.read_csv("nse_symbols.csv")  # fallback: EQUITY_L.csv manually
    df.columns = [c.strip() for c in df.columns]
    if "SERIES" in df:
        df = df[df["SERIES"].str.strip() == "EQ"]
    syms = [s.strip() + ".NS" for s in df["SYMBOL"]]
    if os.path.exists("bse_symbols.csv"):  # optional BSE-only scrips
        syms += [str(s).strip() + ".BO" for s in pd.read_csv("bse_symbols.csv")["SYMBOL"]]
    return syms


def market_regime():
    rows = []
    for grp, m in (("Global", GLOBAL), ("India", INDIA)):
        for name, t in m.items():
            try:
                d = clean(yf.download(t, period="1y", progress=False, auto_adjust=True))
                c = d["Close"]
                rows.append((grp, name, c.iloc[-1] > ema(c, 50).iloc[-1],
                             c.iloc[-1] / c.iloc[-22] - 1))
            except Exception:
                pass
    pct = np.mean([r[2] for r in rows]) * 100 if rows else 0
    verdict = "FAVOURABLE" if pct >= 60 else "MIXED" if pct >= 40 else "WEAK - naya buy risky"
    return rows, pct, verdict


# ---------- run ----------
def main():
    rows, pct, verdict = market_regime()
    nd = clean(yf.download(NIFTY, period="2y", progress=False, auto_adjust=True))["Close"]
    nw = nd.resample("W-FRI").last().dropna()
    rs = {"D": nd.iloc[-1] / nd.iloc[-1 - PARAMS["D"]["rs_len"]] - 1,
          "W": nw.iloc[-1] / nw.iloc[-1 - PARAMS["W"]["rs_len"]] - 1}

    syms, found = get_universe(), {}
    print(f"Universe: {len(syms)} stocks")
    for k in range(0, len(syms), 150):
        chunk = syms[k:k + 150]
        try:
            data = yf.download(chunk, period="2y", interval="1d", group_by="ticker",
                               auto_adjust=True, threads=True, progress=False)
        except Exception as e:
            print("chunk failed", e)
            continue
        for s in chunk:
            try:
                d = data[s].dropna(how="all")
                if len(d) < 60 or d["Close"].iloc[-1] < MIN_PRICE:
                    continue
                if (d["Close"] * d["Volume"]).tail(20).mean() < MIN_TURNOVER:
                    continue
                for tf, df in (("D", d), ("W", to_weekly(d))):
                    res = find_setup(df, tf, rs[tf])
                    if res:
                        found.setdefault(s, {})[tf] = res
            except Exception:
                continue

    out = []
    for s, r in found.items():
        best = max(r.values(), key=lambda x: x["score"])
        both = len(r) == 2
        out.append(dict(Stock=s.replace(".NS", "").replace(".BO", ""),
                        Exch="NSE" if s.endswith(".NS") else "BSE",
                        Timeframe="D+W" if both else best["tf"],
                        Score=min(100, best["score"] + (20 if both else 0)),
                        Close=round(best["close"], 2), HigherLow=round(best["low2"], 2),
                        LowDate=best["low2_date"], StopLoss=round(best["sl"], 2),
                        Target1=round(best["t1"], 2), Target2=round(best["t2"], 2),
                        RSI=round(best["rsi"], 1), VolRatio=round(best["vol_ratio"], 2)))
    res = pd.DataFrame(out).sort_values("Score", ascending=False) if out else pd.DataFrame()
    os.makedirs("results", exist_ok=True)
    res.to_csv("results/latest.csv", index=False)

    md = [f"# Swing Scan - {dt.date.today()}", "",
          f"**Market regime: {verdict}** ({pct:.0f}% indices above 50-DMA)", "",
          "| Group | Index | >50DMA | 1M % |", "|---|---|---|---|"]
    md += [f"| {g} | {n} | {'Yes' if a else 'No'} | {m*100:+.1f} |" for g, n, a, m in rows]
    md += ["", f"## Candidates ({len(res)})", "",
           "Exit rule: buy ke 7 din ke andar sell. SL ya Target pehle hit ho to wahi exit.", ""]
    if len(res):
        cols = list(res.columns)
        md += ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        md += ["| " + " | ".join(str(x) for x in row) + " |" for row in res.head(40).values]
    open("results/latest.md", "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
