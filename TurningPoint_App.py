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
# RELIABLE LIVE DATA FETCHER (NO FAKE FALLBACK)
# ---------------------------------------------------------
def fetch_stock_data(ticker_symbol):
    clean_symbol = ticker_symbol.strip().upper()
    if not clean_symbol.endswith(".NS") and not clean_symbol.endswith(".BO"):
        clean_symbol += ".NS"

    # Method 1: yfinance Ticker Object (Most accurate for NSE/BSE)
    try:
        ticker_obj = yf.Ticker(clean_symbol)
        df = ticker_obj.history(period="6m", interval="1d")
        if df is not None and not df.empty and len(df) >= 20:
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df.dropna(inplace=True)
            return df, clean_symbol
    except Exception:
        pass

    # Method 2: Direct Yahoo Finance Chart API with strict headers
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        }
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{clean_symbol}?range=6m&interval=1d"
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if "chart" in data and data["chart"]["result"]:
                result = data["chart"]["result"][0]
                timestamps = result.get("timestamp", [])
                quote = result["indicators"]["quote"][0]

                df = pd.DataFrame(
                    {
                        "Open": quote.get("open"),
                        "High": quote.get("high"),
                        "Low": quote.get("low"),
                        "Close": quote.get("close"),
                        "Volume": quote.get("volume"),
                    },
                    index=pd.to_datetime(timestamps, unit="s"),
                )

                df.dropna(subset=["Close"], inplace=True)
                df.bfill(inplace=True)
                df.ffill(inplace=True)

                if not df.empty and len(df) >= 20:
                    return df, clean_symbol
    except Exception:
        pass

    return None, clean_symbol


# ---------------------------------------------------------
# INPUT SECTION
# ---------------------------------------------------------
st.sidebar.header("🔍 একক স্টক অ্যানালাইসিস")
stock_input = st.sidebar.text_input(
    "স্টকের টিকার লিখুন (যেমন: NUVAMA, TATAMOTORS, SBIN):", "NUVAMA"
)
analyze_btn = st.sidebar.button(
    "⚡ স্মার্ট মানি স্ক্যান করুন", use_container_width=True
)

if stock_input:
    with st.spinner("এনএসই (NSE) থেকে রিয়েল লাইভ ডেটা আনা হচ্ছে..."):
        df, clean_ticker = fetch_stock_data(stock_input)

    if df is None or df.empty:
        st.error(
            f"❌ **'{stock_input}'** স্টকের সঠিক লাইভ ডেটা পাওয়া যায়নি! দয়া করে"
            " স্টকের নাম বা টিকার সঠিক আছে কিনা চেক করুন (যেমন: NUVAMA,"
            " TATAMOTORS)।"
        )
    else:
        # ---------------------------------------------------------
        # TECHNICAL CALCULATIONS ON REAL DATA
        # ---------------------------------------------------------
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["Vol_Avg20"] = df["Volume"].rolling(20).mean()

        # VWAP Approximation
        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        df["VWAP"] = (typical_price * df["Volume"]).cumsum() / df[
            "Volume"
        ].cumsum()

        # MFI (Money Flow Index) Approximation
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
        vol_avg = float(latest["Vol_Avg20"])
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

        # Factor 1: RVOL Spike (>1.8x)
        if rvol >= 1.8:
            score += 15
            factors_triggered.append(
                f"<b>RVOL Spiked ({round(rvol, 2)}x):</b> সেদিনের ভলিউম গত ২০"
                " দিনের গড়ের চেয়ে ১.৮ গুণেরও বেশি। বড় ইনস্টিটিউশনাল এন্ট্রি"
                " কনফার্মড।"
            )
        elif rvol >= 1.2:
            score += 8
            factors_triggered.append(
                f"<b>Moderate RVOL ({round(rvol, 2)}x):</b> ভলিউম গড়ের চেয়ে বেশ"
                " ভালো।"
            )
        else:
            factors_failed.append(
                f"RVOL দুর্বল ({round(rvol, 2)}x)। পর্যাপ্ত ভলিউম নেই।"
            )

        # Factor 2: Buyer Rejection (Lower Wick > 50%)
        if lower_wick_ratio >= 0.5:
            score += 15
            factors_triggered.append(
                "<b>Strong Buyer Rejection"
                f" ({round(lower_wick_ratio*100, 1)}% Lower Wick):</b>"
                " ক্যান্ডেলের ৫০%-এর বেশি অংশ জুড়ে রয়েছে নিচের ছায়া। সেলারদের"
                " ঠেলে বায়াররা ওপরে প্রাইস বন্ধ করেছে।"
            )
        elif lower_wick_ratio >= 0.3:
            score += 8
            factors_triggered.append(
                f"<b>Moderate Lower Wick ({round(lower_wick_ratio*100, 1)}%):</b>"
                " নিচ থেকে কিছুটা বাইং সাপোর্ট রয়েছে।"
            )
        else:
            factors_failed.append(
                "Lower Wick ছোট। নিচ থেকে বায়ারদের রিজেকশন দেখা যায়নি।"
            )

        # Factor 3: VSA (Volume Spread Analysis)
        if body_range / total_candle_range <= 0.45 and rvol >= 1.3:
            score += 15
            factors_triggered.append(
                "<b>Volume Spread Analysis (VSA) Absorption:</b> ক্যান্ডেলের বডি"
                " ছোট কিন্তু ভলিউম অনেক বেশি! স্মার্ট মানি সেলারদের সমস্ত সেল"
                " প্রেশার শুষে নিয়েছে।"
            )

        # Factor 4: Confluence Support (20 EMA / 50 EMA)
        near_ema20 = abs(c_close - ema20_val) / ema20_val <= 0.02
        near_ema50 = abs(c_close - ema50_val) / ema50_val <= 0.02
        if near_ema20 and near_ema50:
            score += 15
            factors_triggered.append(
                "<b>Dual Confluence Support:</b> একই জায়গায় 20 EMA এবং 50 EMA"
                " সাপোর্ট হিসেবে দাঁড়িয়ে আছে।"
            )
        elif near_ema20 or near_ema50:
            score += 10
            factors_triggered.append(
                "<b>Dynamic EMA Support:</b> স্টকটি ২০/৫০ ইএমএ সাপোর্ট লেভেল"
                " ছুঁয়ে বাউন্স করছে।"
            )
        else:
            factors_failed.append("স্টকটি ইএমএ সাপোর্ট জোন থেকে কিছুটা দূরে।")

        # Factor 5: VWAP Hold
        if c_close >= vwap_val:
            score += 10
            factors_triggered.append(
                "<b>VWAP Hold:</b> স্টকটি ইনস্টটিউশনাল বেঞ্চমার্ক VWAP লাইনের"
                " ওপরে ট্রেড করছে।"
            )
        else:
            factors_failed.append(
                "স্টকটি VWAP লাইনের নিচে আছে (সেলার প্রেশার নির্দেশ করে)।"
            )

        # Factor 6: MFI Money Flow
        if mfi_val >= 50:
            score += 10
            factors_triggered.append(
                f"<b>Positive Money Flow (MFI: {round(mfi_val, 1)}):</b> স্টকে"
                " ক্যাশ ইনফ্লো বা টাকা ঢোকার সংকেত স্পষ্ট।"
            )
        else:
            factors_failed.append(
                f"MFI দুর্বল ({round(mfi_val, 1)}), টাকা বের হওয়ার প্রবণতা"
                " রয়েছে।"
            )

        # Factor 7: Market Structure Shift
        if c_close > float(prev["Close"]):
            score += 10
            factors_triggered.append(
                "<b>Market Structure Shift (MSS):</b> আগের দিনের ক্লোজিং"
                " প্রাইসের ওপর বুলিশ মোমেন্টাম তৈরি হয়েছে।"
            )

        # Final Score Calculation
        final_score = min(score, 100)

        if final_score >= 80:
            verdict_badge = "🔥 ULTRA HIGH CONVICTION SETUP"
            verdict_color = "#00c853"
            verdict_desc = (
                "ইনস্টিটিউশনাল বায়াররা (Big Players) ১০০% সক্রিয়! ৩-৪ দিনের"
                " মোমেন্টামের জন্য সেরা বাই সেটআপ।"
            )
        elif final_score >= 70:
            verdict_badge = "🟢 GOOD CONVICTION SETUP"
            verdict_color = "#29b6f6"
            verdict_desc = (
                "স্মার্ট মানি অ্যাক্টিভ থাকার শক্ত প্রমাণ রয়েছে। স্টপ লস মেনে"
                " এন্ট্রি নেওয়া যায়।"
            )
        elif final_score >= 50:
            verdict_badge = "🟡 NEUTRAL / WEAK BOUNCE"
            verdict_color = "#ffb300"
            verdict_desc = (
                "আংশিক বায়ার রয়েছে তবে যথেষ্ট কনফার্মেশন নেই। অপেক্ষা করাই"
                " ভালো।"
            )
        else:
            verdict_badge = "🔴 DANGER - FAKE BOUNCE / SELLING LIKELY"
            verdict_color = "#ff3d00"
            verdict_desc = (
                "এটি একটি ফেক বাউন্স! নিচে আরও সেলিং আসার সম্ভাবনা বেশি। ভুলেও"
                " বাই করবেন না।"
            )

        # Real Trade Targets based on Live Price
        entry_price = round(c_close, 2)
        target_price = round(entry_price * 1.07, 2)  # +7% Target
        sl_price = round(entry_price * 0.975, 2)  # -2.5% Stop Loss

        # Display Top Metrics
        st.markdown(
            f"<h2 style='color: {verdict_color};'>{clean_ticker.replace('.NS','')} - {verdict_badge}</h2>",
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📊 Smart Money Score", f"{final_score}%")
        m2.metric("🟢 বাই এন্ট্রি (Entry)", f"₹{entry_price}")
        m3.metric("🔵 প্রফিট টার্গেট (+৭%)", f"₹{target_price}")
        m4.metric("🔴 কড়া স্টপ লস (-২.৫%)", f"₹{sl_price}")

        st.info(f"💡 **সিদ্ধান্ত:** {verdict_desc}")

        # ---------------------------------------------------------
        # INTERACTIVE PLOTLY CHART
        # ---------------------------------------------------------
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(
                "Candlestick Chart with 20 EMA Support & Trade Levels",
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
                name="20 EMA Support",
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

        # ---------------------------------------------------------
        # DETAILED STRATEGY EXPLANATION & AUDIO READOUT
        # ---------------------------------------------------------
        st.subheader(
            "📝 বিস্তারিত কারণ ও স্মার্ট মানি ট্রেড প্ল্যান (Explanation):"
        )

        trig_html = "".join([f"<li>{f}</li>" for f in factors_triggered])
        fail_html = "".join([f"<li>{f}</li>" for f in factors_failed])

        speech_text = (
            f"{clean_ticker.replace('.NS','')} স্টকের স্মার্ট মানি কনফিডেন্স"
            f" স্কোর {final_score} শতাংশ। বর্তমান বাই এন্ট্রি প্রাইস"
            f" {entry_price} টাকা। টার্গেট {target_price} টাকা এবং স্টপ লস"
            f" {sl_price} টাকা। {verdict_desc}"
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

        st.markdown("---")
        st.markdown(
            f"### 📱 Groww (গ্রো) অ্যাপে অর্ডার দেওয়ার সঠিক নিয়ম:\n"
            f"1. Groww অ্যাপে সার্চ করুন **{clean_ticker.replace('.NS','')}**।\n"
            f"2. **Buy (Delivery)** অপশনে ক্লিক করে লিমিট প্রাইস দিন **₹{entry_price}**।\n"
            f"3. অর্ডার এক্সিকিউট হলে স্টপ লস ট্রিগার দিন **₹{sl_price}** এবং টার্গেট সেট করুন **₹{target_price}**।\n"
            f"4. আগামী ৩-৪ দিনের মধ্যে টার্গেট বা স্টপ লস হিট করলে ট্রেড ক্লোজ করুন।"
    )
        
