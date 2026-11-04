import io

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")
st.title("⚡ AI Stock Screener Pro (All NSE + BSE Pattern Scanner)")
st.caption(
    "NSE ও BSE-র সব স্টকের তালিকা নিজে থেকে লোড হয় (হাতে লেখা তালিকা নেই)।"
    " কালার-ট্যাগিং ও প্যাটার্ন অ্যানালিসিস সুবিধাসহ।"
)

CHUNK = 300  # একবারে কতগুলো স্টক স্ক্যান হবে


# ------------------------------------------------------------------ স্টকের তালিকা
@st.cache_data(ttl=86400, show_spinner=False)
def load_nse():
    r = requests.get(
        "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = [c.strip() for c in df.columns]
    df = df[df["SERIES"].str.strip().isin(["EQ", "BE"])]
    syms = sorted(set(df["SYMBOL"].astype(str).str.strip()))
    return [{"name": s, "ticker": f"{s}.NS", "ex": "NSE"} for s in syms]


@st.cache_data(ttl=86400, show_spinner=False)
def load_bse_api():
    """BSE-র অ্যাক্টিভ ইক্যুইটি তালিকা। না এলে ফাইল আপলোডের পথ আছে।"""
    r = requests.get(
        "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w",
        params={"Group": "", "Scripcode": "", "industry": "", "segment": "Equity", "status": "Active"},
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bseindia.com/",
            "Origin": "https://www.bseindia.com",
        },
        timeout=30,
    )
    r.raise_for_status()
    out = []
    for d in r.json():
        low = {str(k).lower(): v for k, v in d.items()}
        code, sid = low.get("scrip_cd"), low.get("scrip_id")
        if code and sid:
            out.append({"code": str(code).strip(), "id": str(sid).strip()})
    return out


def bse_from_csv(file):
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]
    code = next(c for c in df.columns if "code" in c.lower())
    sid = next(c for c in df.columns if c.lower() in ("security id", "scrip id", "scrip_id"))
    return [
        {"code": str(int(a)), "id": str(b).strip()}
        for a, b in zip(df[code], df[sid])
        if pd.notna(a) and pd.notna(b)
    ]


# ------------------------------------------------------------------ ফিল্টার ও সিলেক্টর
try:
    nse_list = load_nse()
except Exception as e:
    st.error(f"NSE তালিকা আনা যায়নি ({e}). পরে আবার চেষ্টা করুন।")
    st.stop()

with st.expander("🏦 BSE স্টক যোগ করুন (যেসব স্টক NSE-তে নেই)"):
    use_bse = st.checkbox("BSE-র স্টকও স্ক্যান করুন", value=False)
    bse_file = st.file_uploader("BSE তালিকার CSV (অটো না এলে)", type="csv")

universe = list(nse_list)
if use_bse:
    bse_rows = None
    if bse_file is not None:
        try:
            bse_rows = bse_from_csv(bse_file)
        except Exception as e:
            st.warning(f"BSE CSV পড়া যায়নি: {e}")
    if bse_rows is None:
        try:
            bse_rows = load_bse_api()
        except Exception as e:
            st.warning(f"BSE তালিকা অটো আনা যায়নি ({e}). উপরে CSV আপলোড করুন।")
            bse_rows = []
    nse_names = {x["name"] for x in nse_list}
    universe += [
        {"name": r["id"], "ticker": f"{r['code']}.BO", "ex": "BSE"}
        for r in bse_rows
        if r["id"] not in nse_names
    ]

total = len(universe)
parts = [
    f"{i + 1}–{min(i + CHUNK, total)}: {universe[i]['name']} থেকে "
    f"{universe[min(i + CHUNK, total) - 1]['name']} (মোট {total}টি)"
    for i in range(0, total, CHUNK)
]

c_top1, c_top2 = st.columns([2, 2])
with c_top1:
    selected_part = st.selectbox("কোন অংশ স্ক্যান করবেন:", parts)
with c_top2:
    timeframe_option = st.selectbox(
        "ক্যান্ডেল টাইমফ্রেম (Timeframe):",
        ["1 Day (Daily)", "4 Hours (4h)", "1 Hour (1h)", "15 Minutes (15m)"],
    )

selected_price_status = st.multiselect(
    "🎯 যে প্রাইস রেঞ্জের স্টক অ্যাপে দেখতে চান তা টিক দিন:",
    ["🟢 In Range (₹500 - ₹2,000)", "🔴 Above ₹2,000", "🟡 Below ₹500"],
    default=["🟢 In Range (₹500 - ₹2,000)", "🔴 Above ₹2,000", "🟡 Below ₹500"],
)
st.write("")
start_scan = st.button("🔍 স্ক্যান শুরু করুন", use_container_width=True, type="primary")


# ------------------------------------------------------------------ ডেটা (একসাথে অনেক স্টক)
@st.cache_data(ttl=900, show_spinner=False)
def fetch_batch(tickers: tuple, tf_choice: str):
    if tf_choice == "1 Day (Daily)":
        period, interval = "3mo", "1d"
    elif tf_choice == "4 Hours (4h)":
        period, interval = "1mo", "1h"
    elif tf_choice == "1 Hour (1h)":
        period, interval = "1mo", "1h"
    else:
        period, interval = "5d", "15m"
    raw = yf.download(
        list(tickers), period=period, interval=interval,
        group_by="ticker", auto_adjust=True, threads=True, progress=False,
    )
    res = {}
    for t in tickers:
        try:
            d = raw[t] if isinstance(raw.columns, pd.MultiIndex) else raw
            d = d[["Open", "High", "Low", "Close", "Volume"]].dropna()
            if tf_choice == "4 Hours (4h)" and not d.empty:
                d = (
                    d.resample("4h")
                    .agg({"Open": "first", "High": "max", "Low": "min",
                          "Close": "last", "Volume": "sum"})
                    .dropna()
                )
            if not d.empty:
                res[t] = d
        except Exception:
            pass
    return res


# ------------------------------------------------------------------ আগের অ্যাপের বিশ্লেষণ (অপরিবর্তিত)
def analyze_stock(df):
    if len(df) < 21:
        return None
    c1 = df.iloc[-1]
    c2 = df.iloc[-2]
    c3 = df.iloc[-3]
    open1, close1, high1, low1 = c1["Open"], c1["Close"], c1["High"], c1["Low"]
    open2, close2, high2, low2 = c2["Open"], c2["Close"], c2["High"], c2["Low"]
    open3, close3, high3, low3 = c3["Open"], c3["Close"], c3["High"], c3["Low"]

    if close1 < 500:
        price_status = "🟡 Below ₹500"
    elif 500 <= close1 <= 2000:
        price_status = "🟢 In Range (₹500 - ₹2,000)"
    else:
        price_status = "🔴 Above ₹2,000"

    body1 = abs(close1 - open1)
    range1 = high1 - low1
    if range1 == 0:
        return None
    lower_shadow1 = min(open1, close1) - low1
    upper_shadow1 = high1 - max(open1, close1)

    prev_df = df.iloc[-21:-1]
    recent_low = prev_df["Low"].min()
    recent_high = prev_df["High"].max()
    is_at_support = low1 <= recent_low * 1.008
    is_at_resistance = high1 >= recent_high * 0.992

    is_green1 = close1 > open1
    is_red1 = close1 < open1
    is_red2 = close2 < open2
    is_green2 = close2 > open2
    is_red3 = close3 < open3
    is_green3 = close3 > open3

    pattern = "⚪ No Pattern"
    type_tag = "None"

    if is_at_support:
        if (
            is_red3
            and (abs(close2 - open2) <= 0.3 * (high2 - low2))
            and is_green1
            and (close1 > (open3 + close3) / 2)
        ):
            pattern = "🌟 Morning Star"
            type_tag = "Bullish"
        elif is_red2 and is_green1 and (close1 >= open2) and (open1 <= close2):
            pattern = "🔥 Bullish Engulfing"
            type_tag = "Bullish"
        elif (
            is_red2
            and is_green1
            and (open1 < close2)
            and (close1 > (open2 + close2) / 2)
            and (close1 < open2)
        ):
            pattern = "⚡ Piercing Line"
            type_tag = "Bullish"
        elif (
            is_green1
            and (lower_shadow1 >= 2 * body1)
            and (upper_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🔨 Green Bullish Hammer"
            type_tag = "Bullish"
        elif (
            is_green1
            and (upper_shadow1 >= 2 * body1)
            and (lower_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🙃 Inverted Hammer"
            type_tag = "Bullish"
        elif (
            (body1 <= 0.1 * range1)
            and (lower_shadow1 >= 0.6 * range1)
            and (upper_shadow1 <= 0.1 * range1)
        ):
            pattern = "🐉 Dragonfly Doji"
            type_tag = "Bullish"

    if is_at_resistance and type_tag == "None":
        if (
            is_green3
            and (abs(close2 - open2) <= 0.3 * (high2 - low2))
            and is_red1
            and (close1 < (open3 + close3) / 2)
        ):
            pattern = "🌩️ Evening Star"
            type_tag = "Bearish"
        elif is_green2 and is_red1 and (close1 <= open2) and (open1 >= close2):
            pattern = "❄️ Bearish Engulfing"
            type_tag = "Bearish"
        elif (
            is_green2
            and is_red1
            and (open1 > close2)
            and (close1 < (open2 + close2) / 2)
            and (close1 > open2)
        ):
            pattern = "🌧️ Dark Cloud Cover"
            type_tag = "Bearish"
        elif (
            is_red1
            and (upper_shadow1 >= 2 * body1)
            and (lower_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🌠 Shooting Star"
            type_tag = "Bearish"
        elif (
            is_red1
            and (lower_shadow1 >= 2 * body1)
            and (upper_shadow1 <= 0.2 * body1)
            and (body1 > 0)
        ):
            pattern = "🪢 Hanging Man"
            type_tag = "Bearish"
        elif (
            (body1 <= 0.1 * range1)
            and (upper_shadow1 >= 0.6 * range1)
            and (lower_shadow1 <= 0.1 * range1)
        ):
            pattern = "🪦 Gravestone Doji"
            type_tag = "Bearish"

    buyer_power = round(((close1 - low1) / range1) * 100, 1)
    seller_power = round(((high1 - close1) / range1) * 100, 1)

    return {
        "Price": round(close1, 2),
        "Price_Status": price_status,
        "Pattern": pattern,
        "Type": type_tag,
        "Buyer Power %": buyer_power,
        "Seller Power %": seller_power,
    }


def render_cards(items):
    for item in items:
        with st.container():
            c1, c2, c3, c4 = st.columns([2.5, 2, 3, 2])
            stock_name = item["Stock"]
            groww_url = f"https://groww.in/search?q={stock_name}"
            tv_url = f"https://in.tradingview.com/chart/?symbol={item['Exchange']}:{stock_name}"
            with c1:
                st.markdown(f"### {stock_name}")
                st.caption(f"{item['Exchange']} | LTP: ₹{item['Price']} | {item['Price_Status']}")
            with c2:
                st.write(f"**{item['Pattern']}**")
            with c3:
                b_pow = item["Buyer Power (%)"]
                s_pow = item["Seller Power (%)"]
                st.progress(int(b_pow), text=f"🟢 {b_pow}% Buyers | 🔴 {s_pow}% Sellers")
            with c4:
                st.link_button("🚀 Open in Groww", groww_url)
                st.link_button("📈 TradingView", tv_url)
            st.divider()


# ------------------------------------------------------------------ স্ক্যান
if start_scan:
    part_idx = parts.index(selected_part)
    stocks = universe[part_idx * CHUNK : (part_idx + 1) * CHUNK]
    st.write(f"**{selected_part}** স্ক্যান করা হচ্ছে...")

    bullish_results, bearish_results = [], []
    meta = {s["ticker"]: s for s in stocks}
    tickers = list(meta)
    progress = st.progress(0)
    B = 50
    for i in range(0, len(tickers), B):
        batch = tuple(tickers[i : i + B])
        try:
            data = fetch_batch(batch, timeframe_option)
        except Exception:
            data = {}
        for t, df in data.items():
            try:
                res = analyze_stock(df)
                if res and res["Pattern"] != "⚪ No Pattern":
                    if res["Price_Status"] in selected_price_status:
                        card = {
                            "Stock": meta[t]["name"],
                            "Exchange": meta[t]["ex"],
                            "Price": res["Price"],
                            "Price_Status": res["Price_Status"],
                            "Pattern": res["Pattern"],
                            "Buyer Power (%)": res["Buyer Power %"],
                            "Seller Power (%)": res["Seller Power %"],
                        }
                        if res["Type"] == "Bullish":
                            bullish_results.append(card)
                        elif res["Type"] == "Bearish":
                            bearish_results.append(card)
            except Exception:
                pass
        progress.progress(min(1.0, (i + B) / len(tickers)))

    st.success("স্ক্যানিং সম্পন্ন!")
    tab_bullish, tab_bearish = st.tabs([
        f"🟢 Bullish Setups ({len(bullish_results)})",
        f"🔴 Bearish Setups ({len(bearish_results)})",
    ])
    with tab_bullish:
        if bullish_results:
            st.subheader("🟢 সাপোর্টে তৈরি হওয়া বুলিশ সেটআপ:")
            render_cards(bullish_results)
        else:
            st.info("⚠️ নির্বাচিত ফিল্টার অনুযায়ী এই মুহূর্তে কোনো স্টকে বুলিশ রিভার্সাল পাওয়া যায়নি।")
    with tab_bearish:
        if bearish_results:
            st.subheader("🔴 রেজিস্ট্যান্সে তৈরি হওয়া বেয়ারিশ সেটআপ:")
            render_cards(bearish_results)
        else:
            st.info("⚠️ নির্বাচিত ফিল্টার অনুযায়ী এই মুহূর্তে কোনো স্টকে বেয়ারিশ রিভার্সাল পাওয়া যায়নি।")
