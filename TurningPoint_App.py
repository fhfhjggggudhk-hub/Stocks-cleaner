import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

st.set_page_config(
    page_title="Smart Money Deep-Dive Analyzer", layout="wide"
)

st.title("🎯 স্মার্ট মানি ও ইনস্টিটিউশনাল অ্যাকুমুলেশন অ্যানালাইজার")
st.caption(
    "মেগা ১০-ফ্যাক্টর কনফ্লুয়েন্স স্কোরিং এনজিন (৩-৪ দিনের মোমেন্টাম ও সুইং"
    " ট্রেড সেটআপ)"
)


# ---------------------------------------------------------
# DIRECT BULLETPROOF NSE DATA FETCH ENGINE
# ---------------------------------------------------------
def get_real_nse_data(symbol_str):
    clean_ticker = (
        symbol_str.strip()
        .upper()
        .replace(".NS", "")
        .replace(".BO", "")
        .replace("^", "")
    )
    yf_symbol = f"{clean_ticker}.NS"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    df = None

    # Source 1: Direct Yahoo API Query
    try:
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{yf_symbol}?range=6m&interval=1d"
        req = requests.get(url, headers=headers, timeout=5)
        if req.status_code == 200:
            res = req.json()
            if res.get("chart", {}).get("result"):
                chart_data = res["chart"]["result"][0]
                timestamps = chart_data.get("timestamp", [])
                quotes = chart_data["indicators"]["quote"][0]

                temp_df = pd.DataFrame(
                    {
                        "Open": quotes.get("open"),
                        "High": quotes.get("high"),
                        "Low": quotes.get("low"),
                        "Close": quotes.get("close"),
                        "Volume": quotes.get("volume"),
                    },
                    index=pd.to_datetime(timestamps, unit="s"),
                )
                temp_df.dropna(subset=["Close"], inplace=True)
                if len(temp_df) >= 10:
                    df = temp_df
    except Exception:
        pass

    # Source 2: YFinance Fallback
    if df is None or df.empty:
        try:
            temp_df = yf.download(
                yf_symbol, period="6m", interval="1d", progress=False
            )
            if temp_df is not None and not temp_df.empty:
                if isinstance(temp_df.columns, pd.MultiIndex):
                    temp_df.columns = temp_df.columns.get_level_values(0)
                df = temp_df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        except Exception:
            pass

    # Live Price Sync
    if df is not None and not df.empty:
        try:
            g_url = f"https://www.google.com/finance/quote/{clean_ticker}:NSE"
            g_req = requests.get(g_url, headers=headers, timeout=4)
            if g_req.status_code == 200:
                match = re.search(r'data-last-price="([\d\.]+)"', g_req.text)
                if match:
                    lp = float(match.group(1))
                    df.iloc[-1, df.columns.get_loc("Close")] = lp
                    df.iloc[-1, df.columns.get_loc("High")] = max(
                        lp, float(df.iloc[-1]["High"])
                    )
                    df.iloc[-1, df.columns.get_loc("Low")] = min(
                        lp, float(df.iloc[-1]["Low"])
                    )
        except Exception:
            pass
        return df, clean_ticker

    return None, clean_ticker


# ---------------------------------------------------------
# INPUT SECTION
# ---------------------------------------------------------
st.sidebar.header("🔍 একক স্টক অ্যানালাইসিস")
stock_input = st.sidebar.text_input(
    "স্টকের টিকার লিখুন (যেমন: IFBAGRO, NUVAMA, TATAMOTORS):", "IFBAGRO"
)
analyze_btn = st.sidebar.button(
    "⚡ স্মার্ট মানি স্ক্যান করুন", use_container_width=True
)

if stock_input:
    with st.spinner("NSE থেকে আসল ক্যান্ডেল ডেটা লোড করা হচ্ছে..."):
        df, clean_ticker = get_real_nse_data(stock_input)

    if df is None or df.empty:
        st.error(
            f"❌ '{stock_input}' এর ডেটা সার্ভার থেকে পাওয়া যাচ্ছে না। নাম ঠিক"
            " আছে কিনা বা অন্য কোনো স্টক চেক করুন।"
        )
    else:
        # Technical Indicator Calculations
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["Vol_Avg20"] = df["Volume"].rolling(20).mean()

        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        df["VWAP"] = (typical_price * df["Volume"]).cumsum() / df[
            "Volume"
        ].cumsum()

        raw_money_flow = typical_price * df["Volume"]
        pos_flow = np.where(
            typical_price > typical_price.shift(1), raw_money_flow, 0
        )
        neg_flow = np.where(
            typical_price < typical_price.shift(1), raw_money_flow, 0
        )
        pos_mf = pd.Series(pos_flow).rolling(14).sum()
        neg_mf = pd.Series(neg_flow).rolling(14).sum()
        mfi_ratio = pos_mf / (neg_mf + 1e-6)
        df["MFI"] = 100 - (100 / (1 + mfi_ratio)).values

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        c_open = float(latest["Open"])
        c_high = float(latest["High"])
        c_low = float(latest["Low"])
        c_close = float(latest["Close"])
        c_vol = float(latest["Volume"])
        vol_avg = (
            float(latest["Vol_Avg20"])
            if not np.isnan(latest["Vol_Avg20"])
            else c_vol
        )
        ema20_val = float(latest["EMA20"])
        ema50_val = float(latest["EMA50"])
        vwap_val = float(latest["VWAP"])
        mfi_val = float(latest["MFI"]) if not np.isnan(latest["MFI"]) else 55.0

        # Scoring Logic
        total_candle_range = max(c_high - c_low, 0.01)
        body_range = abs(c_close - c_open)
        lower_wick = min(c_open, c_close) - c_low
        lower_wick_ratio = lower_wick / total_candle_range
        rvol = c_vol / (vol_avg + 1e-6)

        score = 0
        factors_triggered = []
        factors_failed = []

        if rvol >= 1.8:
            score += 15
            factors_triggered.append(
                f"<b>RVOL Spiked ({round(rvol, 2)}x):</b> ভলিউম স্পাইক করেছে।"
            )
        elif rvol >= 1.2:
            score += 8
            factors_triggered.append(
                f"<b>Moderate RVOL ({round(rvol, 2)}x):</b> ভলিউম ভালো।"
            )
        else:
            factors_failed.append("RVOL দুর্বল।")

        if lower_wick_ratio >= 0.5:
            score += 15
            factors_triggered.append(
                "<b>Strong Buyer Rejection:</b> নিচ থেকে স্ট্রং বায়িং প্রেশার।"
            )
        elif lower_wick_ratio >= 0.3:
            score += 8
            factors_triggered.append(
                "<b>Moderate Lower Wick:</b> বায়ারদের সাপোর্ট আছে।"
            )
        else:
            factors_failed.append("Lower Wick ছোট।")

        if body_range / total_candle_range <= 0.45 and rvol >= 1.3:
            score += 15
            factors_triggered.append(
                "<b>VSA Absorption:</b> সেলিং অ্যাবজর্বড করা হয়েছে।"
            )

        near_ema20 = abs(c_close - ema20_val) / ema20_val <= 0.02
        near_ema50 = abs(c_close - ema50_val) / ema50_val <= 0.02
        if near_ema20 or near_ema50:
            score += 15
            factors_triggered.append(
                "<b>EMA Support:</b> ২০/৫০ ইএমএ সাপোর্ট জোন।"
            )
        else:
            factors_failed.append("ইএমএ সাপোর্ট থেকে দূরে।")

        if c_close >= vwap_val:
            score += 10
            factors_triggered.append("<b>VWAP Hold:</b> VWAP-এর ওপরে আছে।")
        else:
            factors_failed.append("VWAP-এর নিচে আছে।")

        if mfi_val >= 50:
            score += 10
            factors_triggered.append(f"<b>Positive Money Flow (MFI):</b> {round(mfi_val, 1)}")
        else:
            factors_failed.append(f"MFI দুর্বল: {round(mfi_val, 1)}")

        if c_close > float(prev["Close"]):
            score += 10
            factors_triggered.append(
                "<b>Market Structure Shift:</b> আগের দিনের ওপরে ক্লোজিং।"
            )

        final_score = min(score, 100)

        if final_score >= 80:
            verdict_badge = "🔥 ULTRA HIGH CONVICTION SETUP"
            verdict_color = "#00c853"
            verdict_desc = "ইনস্টিটিউশনাল বায়াররা সক্রিয়! সুইং ট্রেড বাই সেটআপ।"
        elif final_score >= 70:
            verdict_badge = "🟢 GOOD CONVICTION SETUP"
            verdict_color = "#29b6f6"
            verdict_desc = "স্মার্ট মানি অ্যাক্টিভ। স্টপ লস মেনে বাই করতে পারেন।"
        elif final_score >= 50:
            verdict_badge = "🟡 NEUTRAL / WEAK BOUNCE"
            verdict_color = "#ffb300"
            verdict_desc = "কনফার্মেশন কম, অপেক্ষা করা ভালো।"
        else:
            verdict_badge = "🔴 DANGER - FAKE BOUNCE"
            verdict_color = "#ff3d00"
            verdict_desc = "ফেক বাউন্স! এভোয়েড করুন।"

        entry_price = round(c_close, 2)
        target_price = round(entry_price * 1.07, 2)
        sl_price = round(entry_price * 0.975, 2)

        st.markdown(
            f"<h2 style='color: {verdict_color};'>{clean_ticker} - {verdict_badge}</h2>",
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📊 Smart Money Score", f"{final_score}%")
        m2.metric("🟢 বাই এন্ট্রি", f"₹{entry_price}")
        m3.metric("🔵 প্রফিট টার্গেট (+৭%)", f"₹{target_price}")
        m4.metric("🔴 স্টপ লস (-২.৫%)", f"₹{sl_price}")

        st.info(f"💡 **সিদ্ধান্ত:** {verdict_desc}")

        # Interactive Chart
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(
                "Real NSE Daily Candlestick Chart",
                "Volume Breakdown",
            ),
            row_width=[0.22, 0.78],
        )

        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Candle",
                increasing_line_color="#089981",
                decreasing_line_color="#f23645",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["EMA20"],
                mode="lines",
                name="20 EMA",
                line=dict(color="#ff9800", width=2),
            ),
            row=1,
            col=1,
        )

        fig.add_hline(
            y=entry_price,
            line_color="#00bfa5",
            annotation_text=f"🟢 Entry: ₹{entry_price}",
            row=1,
            col=1,
        )
        fig.add_hline(
            y=target_price,
            line_dash="dash",
            line_color="#29b6f6",
            annotation_text=f"🔵 Target: ₹{target_price}",
            row=1,
            col=1,
        )
        fig.add_hline(
            y=sl_price,
            line_dash="dash",
            line_color="#ef5350",
            annotation_text=f"🔴 Stop Loss: ₹{sl_price}",
            row=1,
            col=1,
        )

        vol_colors = [
            "#089981" if c >= o else "#f23645"
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color=vol_colors,
            ),
            row=2,
            col=1,
        )

        fig.update_layout(
            height=550,
            paper_bgcolor="#131722",
            plot_bgcolor="#131722",
            font=dict(color="#d1d4dc"),
            xaxis_rangeslider_visible=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📝 ট্রেড প্ল্যান বিশ্লেষণ:")
        trig_html = "".join([f"<li>{f}</li>" for f in factors_triggered])
        st.markdown(f"<ul>{trig_html}</ul>", unsafe_allow_html=True)
        
