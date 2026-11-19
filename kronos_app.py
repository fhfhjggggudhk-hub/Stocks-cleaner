#!/usr/bin/env python3
"""
ক্রোনোজ: NSE সুইং ট্রেডিং সহায়ক (১-৭ দিনের হোল্ড), এক ফাইলে।
এটা ব্রোকারে কিছু করে না। সিদ্ধান্ত আর ট্রেড আপনার নিজের। আর্থিক পরামর্শ নয়।
চালানো: streamlit run kronos_app.py
"""
import datetime as dt
import email.utils
import json
import math
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="ক্রোনোজ সুইং", page_icon="📈", layout="centered")
UA = {"User-Agent": "Mozilla/5.0"}
PF = "portfolio.json"
SECTOR_INDEX = {
    "Technology": "^CNXIT", "Healthcare": "^CNXPHARMA", "Financial Services": "^NSEBANK",
    "Consumer Defensive": "^CNXFMCG", "Consumer Cyclical": "^CNXAUTO", "Basic Materials": "^CNXMETAL",
    "Energy": "^CNXENERGY", "Utilities": "^CNXENERGY", "Industrials": "^CNXINFRA",
    "Real Estate": "^CNXREALTY", "Communication Services": "^CNXMEDIA"}
NEG = r"fraud|probe|raid|penalty|default|downgrade|resign|lawsuit|sebi|ban\b|plunge|crash|scam|fine[sd]?\b|recall|loss|slump|tumble|cut"


# ───────────────────────── ডেটা ─────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def hist(sym, min_len=80):
    try:
        t = sym if sym.startswith("^") else sym + ".NS"
        df = yf.Ticker(t).history(period="1y", auto_adjust=False)
    except Exception:
        return None
    if df is None or len(df) < min_len:
        return None
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df if len(df) >= min_len else None


def to_date(x):
    if isinstance(x, dt.datetime):
        return x.date()
    return x if isinstance(x, dt.date) else None


@st.cache_data(ttl=3600, show_spinner=False)
def meta(sym):
    out = {"name": sym, "sector": None, "earn": None, "exdiv": None}
    today = dt.date.today()
    try:
        t = yf.Ticker(sym + ".NS")
        inf = t.info or {}
        out["name"] = inf.get("longName") or inf.get("shortName") or sym
        out["sector"] = inf.get("sector")
        if inf.get("exDividendDate"):
            out["exdiv"] = dt.datetime.fromtimestamp(inf["exDividendDate"]).date()
        cal = t.calendar
        if isinstance(cal, dict):
            fut = [to_date(x) for x in (cal.get("Earnings Date") or [])]
            fut = [x for x in fut if x and x >= today]
            out["earn"] = min(fut) if fut else None
            xd = to_date(cal.get("Ex-Dividend Date"))
            if xd:
                out["exdiv"] = xd
    except Exception:
        pass
    return out


@st.cache_data(ttl=1800, show_spinner=False)
def news(name):
    try:
        url = "https://news.google.com/rss/search?q=%s&hl=en-IN&gl=IN&ceid=IN:en" % quote(name + " share")
        root = ET.fromstring(requests.get(url, timeout=8, headers=UA).content)
    except Exception:
        return None
    out, cut = [], dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)
    for it in list(root.iter("item"))[:15]:
        try:
            when = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            continue
        if when >= cut:
            out.append((it.findtext("title") or "", it.findtext("link") or ""))
    return out


# ───────────────────────── ইন্ডিকেটর ─────────────────────────
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(c, n=14):
    d = c.diff()
    g = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))


def atr(df, n=14):
    pc = df.Close.shift()
    tr = pd.concat([df.High - df.Low, (df.High - pc).abs(), (df.Low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def tick(x, up=False):
    f = math.ceil if up else math.floor
    return round(f(x / 0.05 - 1e-9) * 0.05, 2)


# ───────────────────────── এজেন্টের কাজ ─────────────────────────
def find_setups(df, e20, r, sup, a):
    c, last = df.Close, df.iloc[-1]
    s = []
    if c.iloc[-1] > c.iloc[-21:-1].max():
        s.append("২০ দিনের ক্লোজিং হাই ব্রেকআউট")
    if df.Low.iloc[-3:].min() <= sup + 0.5 * a and last.Close > last.Open and c.iloc[-1] > c.iloc[-2]:
        s.append("সাপোর্ট থেকে বাউন্স")
    if c.iloc[-2] < e20.iloc[-2] and c.iloc[-1] > e20.iloc[-1]:
        s.append("২০ দিনের গড় ফিরে দখল")
    if r.iloc[-2] < 35 and c.iloc[-1] > c.iloc[-2]:
        s.append("ওভারসোল্ড থেকে ওঠা")
    return s


def volume_view(df, sup, a):
    avg = df.Volume.iloc[-21:-1].mean()
    near = bool((df.Low.iloc[-5:] <= sup + 0.5 * a).any())
    last5 = df.iloc[-5:]
    down = last5[last5.Close < last5.Open]
    dry = bool(near and len(down) and down.Volume.mean() < 0.8 * avg)
    last = df.iloc[-1]
    ratio = float(last.Volume / avg) if avg else 0.0
    return {"avg": avg, "near": near, "dry": dry, "ratio": ratio,
            "bounce": bool(last.Close > last.Open and ratio > 1.2)}


def sector_view(sector):
    idx = SECTOR_INDEX.get(sector or "", "^NSEI")
    s = hist(idx, 60)
    if s is None:
        idx, s = "^NSEI", hist("^NSEI", 60)
    if s is None:
        return {"idx": idx, "stance": "unknown", "ret": None}
    ret = float(s.Close.iloc[-1] / s.Close.iloc[-22] - 1) * 100
    above = s.Close.iloc[-1] > ema(s.Close, 50).iloc[-1]
    stance = "bullish" if ret > 0 and above else "bearish" if ret < 0 and not above else "neutral"
    return {"idx": idx, "stance": stance, "ret": ret}


def absorption(df, sup, a, avgv, stress):
    last5 = df.iloc[-5:]
    held = bool((last5.Close >= sup * 0.99).all())
    rng = (last5.High - last5.Low).replace(0, np.nan)
    wick = (np.minimum(last5.Open, last5.Close) - last5.Low) / rng
    pos = (last5.Close - last5.Low) / rng
    absorbed = bool(((wick > 0.5) & (pos > 0.5) & (last5.Volume > 1.3 * avgv)).any())
    if not stress:
        return "no_stress", held, absorbed
    if held and absorbed:
        return "absorbing", held, absorbed
    return ("holding" if held else "weak"), held, absorbed


def monte_carlo(df, entry, stop, target, days, n=3000, seed=19):
    r = df.iloc[-250:]
    pc = r.Close.shift().iloc[1:]
    r = r.iloc[1:]
    H, L, C = (r.High / pc).values, (r.Low / pc).values, (r.Close / pc).values
    idx = np.random.default_rng(seed).integers(0, len(C), size=(n, days))
    p, res = np.full(n, float(entry)), np.zeros(n)
    for d in range(days):
        i = idx[:, d]
        alive = res == 0
        stop_hit = alive & (p * L[i] <= stop)
        tgt_hit = alive & ~stop_hit & (p * H[i] >= target)
        res[stop_hit], res[tgt_hit] = 2, 1
        p = p * C[i]
    pt, ps = (res == 1).mean(), (res == 2).mean()
    R = (target - entry) / (entry - stop)
    even = 1 / (1 + R)
    share = pt / (pt + ps) if pt + ps else 0
    return {"pt": pt * 100, "ps": ps * 100, "pn": (res == 0).mean() * 100, "even": even * 100,
            "edge": (share - even) * 100}


def analyze(sym, cfg, nifty):
    df = hist(sym)
    if df is None:
        return {"sym": sym, "err": "ডেটা পাওয়া যায়নি (NSE টিকার ঠিক আছে? যেমন TATASTEEL, M&M)"}
    c = df.Close
    price, a = float(c.iloc[-1]), float(atr(df).iloc[-1])
    e20, e50, r = ema(c, 20), ema(c, 50), rsi(c)
    sup = float(df.Low.iloc[-30:].min())
    res60 = float(df.High.iloc[-60:].max())
    turn = price * float(df.Volume.iloc[-21:-1].mean()) / 1e7
    m = meta(sym)
    today = dt.date.today()
    blocks, warns, goods = [], [], []

    # ইভেন্ট
    de = (m["earn"] - today).days if m["earn"] else None
    dd = (m["exdiv"] - today).days if m["exdiv"] and m["exdiv"] >= today else None
    if de is None:
        warns.append("কোয়ার্টারলি রেজাল্টের তারিখ জানা যায়নি: কোম্পানির সাইটে দেখে নিন")
    elif de <= cfg["hold_days"]:
        blocks.append("রেজাল্ট %d দিনের মধ্যে (%s): হোল্ডের সময়েই পড়ছে" % (de, m["earn"]))
    elif de <= 14:
        warns.append("রেজাল্ট %d দিন পরে (%s)" % (de, m["earn"]))
    else:
        goods.append("২ সপ্তাহের মধ্যে রেজাল্ট নেই")
    if dd is not None and dd <= 14:
        warns.append("লভ্যাংশের এক্স-ডেট %d দিন পরে (%s): সেদিন দাম সেই পরিমাণ কমে" % (dd, m["exdiv"]))

    # সেক্টর
    sec = sector_view(m["sector"])
    if sec["stance"] == "bearish":
        (blocks if c.iloc[-1] < e50.iloc[-1] else warns).append("সেক্টর (%s) বিয়ারিশ" % sec["idx"])
    elif sec["stance"] == "bullish":
        goods.append("সেক্টর (%s) বুলিশ" % sec["idx"])
    elif sec["stance"] == "unknown":
        warns.append("সেক্টরের তথ্য মেলেনি")

    # ভলিউম
    vol = volume_view(df, sup, a)
    if vol["dry"]:
        goods.append("সাপোর্টে সেলিং ভলিউম শুকিয়েছে")
    if vol["bounce"]:
        goods.append("বাউন্সে ভলিউম গড়ের %.1f গুণ" % vol["ratio"])
    if vol["near"] and not vol["dry"] and not vol["bounce"]:
        warns.append("সাপোর্টের কাছে, কিন্তু ভলিউমে পরিষ্কার সংকেত নেই")

    # খবর ও প্যানিক
    items = news(m["name"])
    bad = [(t, l) for t, l in (items or []) if re.search(NEG, t, re.I)]
    mkt_drop = bool(nifty is not None and (nifty.Close.iloc[-1] / nifty.Close.iloc[-4] - 1 < -0.015
                                           or nifty.Close.iloc[-1] / nifty.Close.iloc[-2] - 1 < -0.01))
    pan, held, absorbed = absorption(df, sup, a, float(df.Volume.iloc[-21:-1].mean()), bool(bad) or mkt_drop)
    if items is None:
        warns.append("খবর আনা যায়নি")
    if pan == "weak":
        blocks.append("খারাপ খবর/বাজার পতনের মধ্যে সাপোর্ট ধরে রাখতে পারেনি")
    elif pan == "absorbing":
        goods.append("প্যানিকের মধ্যেও সাপোর্ট ধরে রেখেছে, বড় ক্রেতা বিক্রি শুষে নিচ্ছে")
    elif pan == "holding":
        warns.append("সাপোর্ট ধরে আছে, কিন্তু শোষণের পরিষ্কার ক্যান্ডেল নেই")
    if len(bad) >= 3:
        blocks.append("গত ৭ দিনে ৩টি+ ক্ষতিকর খবর")
    elif bad:
        warns.append("গত ৭ দিনে %d টি সন্দেহজনক খবর" % len(bad))

    # পরিকল্পনা
    entry = tick(price * 1.001, up=True)
    stop = tick(sup - 0.5 * a)
    if entry - stop > 2.5 * a:
        stop = tick(entry - 2.5 * a)
    if stop >= entry - 0.5 * a:
        stop = tick(entry - a)
    risk = round(entry - stop, 2)
    target = tick(entry + cfg["target_r"] * risk, up=True)
    budget = cfg["capital"] * cfg["risk_pct"] / 100
    qty = int(min(budget // risk, cfg["capital"] * cfg["max_pos_pct"] / 100 // entry)) if risk > 0 else 0
    mc = monte_carlo(df, entry, stop, target, cfg["hold_days"])
    if target - entry > 1.3 * math.sqrt(cfg["hold_days"]) * a:
        warns.append("টার্গেট %d দিনের জন্য একটু দূরে (ATR অনুযায়ী)" % cfg["hold_days"])
    if entry < res60 < target:
        warns.append("টার্গেটের আগে ₹%.2f-এ প্রতিরোধ আছে" % res60)
    if mc["edge"] < 0:
        blocks.append("টার্গেট আগে ছোঁয়ার চান্স ব্রেক-ইভেন (%.0f%%) এর নিচে" % mc["even"])
    if qty < 1:
        blocks.append("ঝুঁকির বাজেটে একটা শেয়ারও কেনা যায় না")
    if turn < cfg["min_turnover_cr"]:
        blocks.append("লেনদেন কম (গড় ₹%.1f কোটি/দিন)" % turn)

    setups = find_setups(df, e20, r, sup, a)
    r_now = float(r.iloc[-1])
    trig = bool(setups) and (vol["bounce"] or vol["dry"] or vol["ratio"] >= 1.2) and r_now < 75
    code = "SKIP" if blocks else "ENTER" if trig else "WAIT"
    chart = pd.DataFrame({"দাম": c.iloc[-90:], "EMA20": e20.iloc[-90:], "EMA50": e50.iloc[-90:]})
    return dict(sym=sym, name=m["name"], sector=m["sector"], price=price, atr=a, rsi=r_now, sup=sup, res=res60,
                setups=setups, vol=vol, sec=sec, pan=pan, bad=bad, blocks=blocks, warns=warns, goods=goods,
                entry=entry, stop=stop, target=target, risk=risk, qty=qty, mc=mc, code=code, chart=chart,
                date=df.index[-1].date())


# ───────────────────────── পোর্টফোলিও ─────────────────────────
def pf_load():
    try:
        with open(PF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"positions": [], "closed": []}


def pf_save(d):
    with open(PF, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def pf_add(sym, qty, entry, sl, t1):
    d = pf_load()
    sym = sym.upper().replace(".NS", "")
    if any(p["symbol"] == sym for p in d["positions"]):
        return "%s আগে থেকেই আছে" % sym
    d["positions"].append({"symbol": sym, "qty": float(qty), "entry": float(entry), "sl": float(sl),
                           "t1": float(t1) if t1 else None, "date": dt.date.today().isoformat()})
    pf_save(d)
    return None


def pf_close(sym, px):
    d = pf_load()
    p = next((x for x in d["positions"] if x["symbol"] == sym), None)
    if not p:
        return None
    pnl = (float(px) - p["entry"]) * p["qty"]
    d["positions"].remove(p)
    d["closed"].append({"symbol": sym, "pnl": round(pnl, 2), "exit": float(px), "date": dt.date.today().isoformat()})
    pf_save(d)
    return pnl


def pf_tab(cfg):
    d = pf_load()
    if not d["positions"]:
        st.info("কোনো খোলা পজিশন নেই")
    for p in d["positions"]:
        df = hist(p["symbol"])
        last = float(df.Close.iloc[-1]) if df is not None else None
        held = int(np.busday_count(dt.date.fromisoformat(p["date"]), dt.date.today()))
        st.markdown("**%s** · %g শেয়ার @ ₹%s · %d দিন" % (p["symbol"], p["qty"], p["entry"], held))
        if last:
            pnl = (last - p["entry"]) * p["qty"]
            st.write("এখন ₹%.2f · লাভ/লোকসান ₹%.0f (%+.2f%%) · স্টপ ₹%s" % (last, pnl, (last / p["entry"] - 1) * 100, p["sl"]))
            if last <= p["sl"]:
                st.error("স্টপ ছুঁয়েছে: পরিকল্পনা অনুযায়ী বেরোন")
            if p.get("t1") and last >= p["t1"]:
                st.success("টার্গেট ছুঁয়েছে: অর্ধেক বিক্রি, বাকিটার স্টপ এন্ট্রিতে সরান")
        if held >= cfg["hold_days"]:
            st.warning("%d ট্রেডিং দিন পূর্ণ: সময়ের স্টপ, বেরোনোর কথা" % cfg["hold_days"])
        c1, c2 = st.columns([2, 1])
        px = c1.number_input("বিক্রির দাম", min_value=0.0, value=float(last or p["entry"]), key="px_" + p["symbol"])
        if c2.button("বন্ধ করুন", key="cl_" + p["symbol"]):
            st.success("বন্ধ। লাভ/লোকসান ₹%.2f" % pf_close(p["symbol"], px))
            st.rerun()
        st.divider()
    with st.expander("হাতে পজিশন যোগ করুন"):
        s = st.text_input("সিম্বল", key="a_s")
        q = st.number_input("শেয়ার", min_value=1, value=1, key="a_q")
        e = st.number_input("এন্ট্রি দাম", min_value=0.0, key="a_e")
        sl = st.number_input("স্টপ", min_value=0.0, key="a_sl")
        t = st.number_input("টার্গেট ১", min_value=0.0, key="a_t")
        if st.button("যোগ করুন") and s and e > 0 and 0 < sl < e:
            err = pf_add(s, q, e, sl, t)
            st.error(err) if err else st.rerun()
    if d["closed"]:
        tot = sum(x["pnl"] for x in d["closed"])
        st.caption("বন্ধ ট্রেড %d টি, মোট লাভ/লোকসান ₹%.0f" % (len(d["closed"]), tot))
    st.download_button("পোর্টফোলিও ব্যাকআপ (JSON)", json.dumps(d, ensure_ascii=False), "portfolio.json")
    up = st.file_uploader("ব্যাকআপ ফেরত আনুন", type="json")
    if up is not None and st.button("রিস্টোর"):
        pf_save(json.load(up))
        st.rerun()
    st.caption("Streamlit Cloud রিবুট হলে ফাইল মুছে যায়: নিয়মিত ব্যাকআপ নিন।")


# ───────────────────────── দেখানো ─────────────────────────
LABEL = {"ENTER": "✅ এন্ট্রির মতো", "WAIT": "⏳ অপেক্ষা", "SKIP": "⛔ বাদ"}
STANCE = {"bullish": "বুলিশ", "bearish": "বিয়ারিশ", "neutral": "নিরপেক্ষ", "unknown": "অজানা"}


def show(r, cfg):
    if r.get("err"):
        st.error("%s: %s" % (r["sym"], r["err"]))
        return
    with st.expander("%s  %s  ₹%.2f" % (LABEL[r["code"]], r["sym"], r["price"]), expanded=r["code"] == "ENTER"):
        st.caption("%s · %s · ডেটা %s পর্যন্ত" % (r["name"], r["sector"] or "সেক্টর অজানা", r["date"]))
        if r["setups"]:
            st.write("সেটআপ: " + ", ".join(r["setups"]))
        c1, c2, c3 = st.columns(3)
        c1.metric("এন্ট্রি", "₹%.2f" % r["entry"])
        c2.metric("স্টপ", "₹%.2f" % r["stop"])
        c3.metric("টার্গেট", "₹%.2f" % r["target"])
        st.write("ঝুঁকি ₹%.2f/শেয়ার · সংখ্যা **%d** · সর্বোচ্চ ক্ষতি ≈ ₹%.0f" % (r["risk"], r["qty"], r["risk"] * r["qty"]))
        mc = r["mc"]
        st.write("%d দিনের সিমুলেশন: টার্গেট আগে %.0f%% · স্টপ আগে %.0f%% · কোনোটাই না %.0f%% · ব্রেক-ইভেন %.0f%%"
                 % (cfg["hold_days"], mc["pt"], mc["ps"], mc["pn"], mc["even"]))
        st.write("সাপোর্ট ₹%.2f · প্রতিরোধ ₹%.2f · RSI %.0f · সেক্টর %s" % (r["sup"], r["res"], r["rsi"], STANCE[r["sec"]["stance"]]))
        for x in r["blocks"]:
            st.error(x)
        for x in r["warns"]:
            st.warning(x)
        for x in r["goods"]:
            st.success(x)
        for t, l in r["bad"][:3]:
            st.markdown("- [%s](%s)" % (t, l))
        st.line_chart(r["chart"])
        if r["code"] != "SKIP" and r["qty"] >= 1 and st.button("পোর্টফোলিওতে যোগ (কেনার পর)", key="add_" + r["sym"]):
            err = pf_add(r["sym"], r["qty"], r["entry"], r["stop"], r["target"])
            st.error(err) if err else st.success("যোগ হয়েছে")


def main():
    st.title("📈 ক্রোনোজ সুইং")
    with st.sidebar:
        st.header("সেটিংস")
        cfg = {
            "capital": st.number_input("মূলধন (₹)", 1000, 100000000, 100000, 1000),
            "risk_pct": st.number_input("প্রতি ট্রেডে ঝুঁকি (%)", 0.1, 5.0, 1.0, 0.1),
            "max_pos_pct": st.number_input("এক শেয়ারে সর্বোচ্চ (%)", 5, 100, 30, 5),
            "hold_days": st.slider("সর্বোচ্চ হোল্ড (ট্রেডিং দিন)", 1, 7, 7),
            "target_r": st.number_input("টার্গেট (R গুণ)", 1.0, 5.0, 2.0, 0.5),
            "min_turnover_cr": st.number_input("ন্যূনতম গড় লেনদেন (₹ কোটি/দিন)", 0.0, 100.0, 5.0, 1.0),
        }
    tab1, tab2 = st.tabs(["বিশ্লেষণ", "পোর্টফোলিও"])
    with tab1:
        txt = st.text_area("NSE স্টকের নাম (কমা দিয়ে)", "TCS, INFY, TATASTEEL")
        if st.button("বিশ্লেষণ করুন", type="primary"):
            syms = list(dict.fromkeys(s.strip().upper().replace(".NS", "") for s in re.split(r"[,\s]+", txt) if s.strip()))
            nifty, out, bar = hist("^NSEI", 30), [], st.progress(0.0)
            for i, s in enumerate(syms):
                bar.progress(i / max(len(syms), 1), text="বিশ্লেষণ: " + s)
                try:
                    out.append(analyze(s, cfg, nifty))
                except Exception as e:
                    out.append({"sym": s, "err": "ত্রুটি: %s" % e})
            bar.empty()
            order = {"ENTER": 0, "WAIT": 1, "SKIP": 2}
            out.sort(key=lambda r: (order.get(r.get("code"), 3), -r.get("mc", {}).get("edge", -999)))
            st.session_state["res"] = out
        for r in st.session_state.get("res", []):
            show(r, cfg)
        st.caption("ডেটা Yahoo Finance (বিলম্বিত হতে পারে)। সিমুলেশন ভবিষ্যদ্বাণী নয়। আর্থিক পরামর্শ নয়।")
    with tab2:
        pf_tab(cfg)


main()
