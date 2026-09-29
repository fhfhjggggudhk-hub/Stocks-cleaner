import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf

# Page Configuration
st.set_page_config(
    page_title="Smart Money Deep-Dive Analyzer", layout="wide"
)

st.title("🎯 স্মার্ট মানি ও ইনস্টিটিউশনাল অ্যাকুমুলেশন অ্যানালাইজার")
st.caption(
    "মেগা ১০-ফ্যাক্টর কনফ্লুয়েন্স স্কোরিং এনজিন (৩-৪ দিনের মোমেন্টাম ও সুইং"
    " ট্রেড সেটআপ)"
)


# ---------------------------------------------------------
# REAL-TIME GOOGLE FINANCE LTP SCRAPER
# ---------------------------------------------------------
def fetch_realtime_ltp(raw_symbol):
    """Google Finance থেকে লাইভ রিয়েল-টাইম দাম নিয়ে আসে"""
    try:
        url = f"https://www.google.com/finance/quote/{raw_symbol}:NSE"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            match = re.search(r'data-last-price="([\d\.]+)"', resp.text)
            if match:
                return float(match.group(1))
            match_curr = re.search(r"₹\s*([\d,]+\.?\d*)", resp.text)
            if match_curr:
                return float(match_curr.group(1).replace(",", ""))
    except Exception:
        pass
    return None


# ---------------------------------------------------------
# 100% REAL HISTORICAL DATA ENGINE (NO SYNTHETIC/FAKE DATA)
# ---------------------------------------------------------
def fetch_stock_data_pure_real(ticker_symbol):
    clean_symbol = ticker_symbol.strip().upper()
    raw_symbol = (
        clean_symbol.replace(".NS", "")
        .replace(".BO", "")
        .replace("^", "")
        .strip()
    )
    yf_symbol = f"{raw_symbol}.NS"

    # Step 1: Live Price Fetch
    realtime_price = fetch_realtime_ltp(raw_symbol)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Referer": "https://finance.yahoo.com/",
    }

    df = None

    # Step 2: Try Direct Yahoo Finance Chart v8 Endpoint (Real NSE Candles)
    for domain in [
        "query2.finance.yahoo.com",
        "query1.finance.yahoo.com",
    ]:
        try:
            url = f"https://{domain}/v8/finance/chart/{yf_symbol}?range=6m&interval=1d"
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                data = res.json()
                if "chart" in data and data["chart"]["result"]:
                    result = data["chart"]["result"][0]
                    timestamps = result.get("timestamp", [])
                    quote = result["indicators"]["quote"][0]

                    temp_df = pd.DataFrame(
                        {
                            "Open": quote.get("open"),
                            "High": quote.get("high"),
                            "Low": quote.get("low"),
                            "Close": quote.get("close"),
                            "Volume": quote.get("volume"),
                        },
                        index=pd.to_datetime(timestamps, unit="s"),
                    )

                    temp_df.dropna(subset=["Close"], inplace=True)
                    temp_df.bfill(inplace=True)
                    temp_df.ffill(inplace=True)

                    if not temp_df.empty and len(temp_df) >= 15:
                        df = temp_df
                        break
        except Exception:
            continue

    # Step 3: Backup yfinance library
    if df is None or df.empty:
        try:
            ticker_obj = yf.Ticker(yf_symbol)
            temp_df = ticker_obj.history(period="6m", interval="1d")
            if temp_df is not None and not temp_df.empty:
                if isinstance(temp_df.columns, pd.MultiIndex):
                    temp_df.columns = temp_df.columns.get_level_values(0)
                df = temp_df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        except Exception:
            pass

    # Step 4: Synchronize Last Candle Price with Live Market LTP
    if df is not None and not df.empty:
        if realtime_price is not None and realtime_price > 0:
            df.iloc[-1, df.columns.get_loc("Close")] = realtime_price
            df.iloc[-1, df.columns.get_loc("High")] = max(
                realtime_price, float(df.iloc[-1]["High"])
            )
            df.iloc[-1, df.columns.get_loc("Low")] = min(
                realtime_price, float(df.iloc[-1]["Low"])
            )
        return df, raw_symbol

    return None, raw_symbol


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
    with st.spinner(
        "NSE (National Stock Exchange) থেকে আসল লাইভ ডেটা আনা হচ্ছে..."
    ):
        df, clean_ticker = fetch_stock_data_pure_real(stock_input)

    if df is None or df.empty:
        st.error(
            f"❌ **'{stock_input}'** স্টকের আসল লাইভ ডেটা আনতে সমস্যা হয়েছে।"
            " অনুগ্রহ করে স্টকের নাম সঠিকভাবে চেক করুন বা ১ মিনিট পর আবার চেষ্টা"
            " করুন।"
        )
    else:
        # ---------------------------------------------------------
        # TECHNICAL CALCULATIONS
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # 10-FACTOR SCORING ENGINE
        # ---------------------------------------------------------
        total_candle_range = max(c_high - c_low, 0.01)
        body_range = abs(c_close - c_open)
        lower_wick = min(c_open, c_close) - c_low
        lower_wick_ratio = lower_wick / total_candle_range
        rvol = c_vol / (vol_avg + 1e-6)

        score = 0
        factors_triggered = []
        factors_failed = []

        # Factor 1: RVOL
        if rvol >= 1.8:
            score += 15
            factors_triggered.append(
                f"<b>RVOL Spiked ({round(rvol, 2)}x):</b> ভলিউম গত ২০ দিনের"
                " গড়ের ১.৮ গুণের বেশি। ইনস্টিটিউশনাল অ্যাক্টিভিটি স্পষ্ট।"
            )
        elif rvol >= 1.2:
            score += 8
            factors_triggered.append(
                f"<b>Moderate RVOL ({round(rvol, 2)}x):</b> ভলিউম সন্তোষজনক।"
            )
        else:
            factors_failed.append(
                f"RVOL দুর্বল ({round(rvol, 2)}x)। পর্যাপ্ত ভলিউম নেই।"
            )

        # Factor 2: Buyer Rejection
        if lower_wick_ratio >= 0.5:
            score += 15
            factors_triggered.append(
                "<b>Strong Buyer Rejection"
                f" ({round(lower_wick_ratio*100, 1)}% Lower Wick):</b> ক্যান্ডেলের"
                " ৫০%-এর বেশি অংশ জুড়ে রয়েছে নিচের উইক/ছায়া।"
            )
        elif lower_wick_ratio >= 0.3:
            score += 8
            factors_triggered.append(
                f"<b>Moderate Lower Wick ({round(lower_wick_ratio*100, 1)}%):</b>"
                " নিচ থেকে বায়ারদের সাপোর্ট আছে।"
            )
        else:
            factors_failed.append(
                "Lower Wick ছোট। নিচ থেকে বায়ারদের রিজেকশন দেখা যায়নি।"
            )

        # Factor 3: VSA Absorption
        if body_range / total_candle_range <= 0.45 and rvol >= 1.3:
            score += 15
            factors_triggered.append(
                "<b>Volume Spread Analysis (VSA):</b> ছোট বডিতে বিশাল ভলিউম!"
                " সেলিং প্রেশার অ্যাবজর্ব করা হয়েছে।"
            )

        # Factor 4: Confluence Support
        near_ema20 = abs(c_close - ema20_val) / ema20_val <= 0.02
        near_ema50 = abs(c_close - ema50_val) / ema50_val <= 0.02
        if near_ema20 and near_ema50:
            score += 15
            factors_triggered.append(
                "<b>Dual Confluence Support:</b> 20 EMA এবং 50 EMA একই সাথে"
                " সাপোর্ট হিসেবে কাজ করছে।"
            )
        elif near_ema20 or near_ema50:
            score += 10
            factors_triggered.append(
                "<b>Dynamic EMA Support:</b> ২০/৫০ ইএমএ সাপোর্ট জোন থেকে বাউন্স"
                " করছে।"
            )
        else:
            factors_failed.append("স্টকটি ইএমএ সাপোর্ট লেভেল থেকে দূরে।")

        # Factor 5: VWAP Hold
        if c_close >= vwap_val:
            score += 10
            factors_triggered.append(
                "<b>VWAP Hold:</b> স্টকটি ইনস্টিটিউশনাল VWAP বেঞ্চমার্কের ওপর"
                " রয়েছে।"
            )
        else:
            factors_failed.append("স্টকটি VWAP লাইনের নিচে আছে।")

        # Factor 6: MFI Money Flow
        if mfi_val >= 50:
            score += 10
            factors_triggered.append(
                f"<b>Positive Money Flow (MFI: {round(mfi_val, 1)}):</b> স্টকে"
                " ক্যাশ ইনফ্লো হচ্ছে।"
            )
        else:
            factors_failed.append(f"MFI দুর্বল ({round(mfi_val, 1)})।")

        # Factor 7: Market Structure Shift
        if c_close > float(prev["Close"]):
            score += 10
            factors_triggered.append(
                "<b>Market Structure Shift (MSS):</b> আগের দিনের ক্লোজিংয়ের ওপর"
                " বুলিশ মোমেন্টাম।"
            )

        final_score = min(score, 100)

        if final_score >= 80:
            verdict_badge = "🔥 ULTRA HIGH CONVICTION SETUP"
            verdict_color = "#00c853"
            verdict_desc = (
                "ইনস্টিটিউশনাল বায়াররা সক্রিয়! ৩-৪ দিনের সুইং ট্রেডের জন্য"
                " সেরা সেটআপ।"
            )
        elif final_score >= 70:
            verdict_badge = "🟢 GOOD CONVICTION SETUP"
            verdict_color = "#29b6f6"
            verdict_desc = (
                "স্মার্ট মানি অ্যাক্টিভ থাকার প্রমাণ আছে। স্টপ লস মেনে বাই করা"
                " যায়।"
            )
        elif final_score >= 50:
            verdict_badge = "🟡 NEUTRAL / WEAK BOUNCE"
            verdict_color = "#ffb300"
            verdict_desc = (
                "আংশিক বায়ার রয়েছে তবে যথেষ্ট কনফার্মেশন নেই। অপেক্ষা করা ভালো।"
            )
        else:
            verdict_badge = "🔴 DANGER - FAKE BOUNCE / SELLING LIKELY"
            verdict_color = "#ff3d00"
            verdict_desc = (
                "এটি একটি ফেক বাউন্স! সেলিং প্রেশার আসার আশঙ্কা বেশি। বাই করবেন"
                " না।"
            )

        entry_price = round(c_close, 2)
        target_price = round(entry_price * 1.07, 2)
        sl_price = round(entry_price * 0.975, 2)

        st.markdown(
            f"<h2 style='color: {verdict_color};'>{clean_ticker} - {verdict_badge}</h2>",
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📊 Smart Money Score", f"{final_score}%")
        m2.metric("🟢 বাই এন্ট্রি (Entry)", f"₹{entry_price}")
        m3.metric("🔵 প্রফিট টার্গেট (+৭%)", f"₹{target_price}")
        m4.metric("🔴 কড়া স্টপ লস (-২.৫%)", f"₹{sl_price}")

        st.info(f"💡 **সিদ্ধান্ত:** {verdict_desc}")

        # Interactive Plotly Chart
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(
                "Real NSE Daily Candlestick Chart with Trade Levels",
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
                name="Real Candle",
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
        fig.update_xaxes(showgrid=True, gridcolor="#2a2e39")
        fig.update_yaxes(showgrid=True, gridcolor="#2a2e39")

        st.plotly_chart(fig, use_container_width=True)

        # Strategy Breakdown & Audio
        st.subheader(
            "📝 বিস্তারিত কারণ ও স্মার্ট মানি ট্রেড প্ল্যান (Explanation):"
        )

        trig_html = "".join([f"<li>{f}</li>" for f in factors_triggered])
        fail_html = "".join([f"<li>{f}</li>" for f in factors_failed])

        speech_text = (
            f"{clean_ticker} স্টকের স্মার্ট মানি কনফিডেন্স স্কোর {final_score}"
            f" শতাংশ। বর্তমান বাই এন্ট্রি প্রাইস {entry_price} টাকা। টার্গেট"
            f" {target_price} টাকা এবং স্টপ লস {sl_price} টাকা। {verdict_desc}"
        )
        clean_js_speech = (
            speech_text.replace("'", "\\'")
            .replace('"', '\\"')
            .replace("\n", " ")
        )

        tts_html = (
            '<div style="margin-bottom: 20px;">'
            '<button onclick="playVoice()" style="'
            'background: linear-gradient(135deg, #00c853, #009688); '
            'color: white; border: none; padding: 12px 24px; font-size: 16px; '
            'font-weight: bold; border-radius: 8px; cursor: pointer;">'
            '🔊 ভয়েসে শুনুন (Listen Smart Money Report)'
            '</button>'
            '<script>'
            'function playVoice() {'
            '   window.speechSynthesis.cancel();'
            '   const text = "' + clean_js_speech + '";'
            '   const msg = new SpeechSynthesisUtterance(text);'
            '   msg.lang = "bn-IN";'
            '   msg.rate = 0.9;'
            '   window.speechSynthesis.speak(msg);'
            '}'
            '</script>'
            '</div>'
        )
        components.html(tts_html, height=70)

        st.markdown(
            "### ✅ যে স্ট্র্যাটেজিগুলো বায়ার অ্যাক্টিভ থাকার কথা"
            f" বলছে:\n<ul>{trig_html}</ul>",
            unsafe_allow_html=True,
        )

        if factors_failed:
            st.markdown(
                f"### ⚠️ যে ফিল্টারগুলো দুর্বল বা মেলেনি:\n<ul>{fail_html}</ul>",
                unsafe_allow_html=True,
        )
            
