import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
import streamlit.components.v1 as components

# TradingView Library Import
try:
    from tvDatafeed import Interval, TvDatafeed

    HAS_TV = True
except Exception:
    HAS_TV = False

# Safe Import for YFinance
try:
    import yfinance as yf

    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# Page Configuration
st.set_page_config(
    page_title="Smart Money Deep-Dive Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎯 স্মার্ট মানি ও ইনস্টিটিউশনাল অ্যাকুমুলেশন অ্যানালাইজার")
st.caption("Powered by TradingView Realtime Chart Engine (NSE India)")


# ---------------------------------------------------------
# TRADINGVIEW DIRECT DATA ENGINE (PRIMARY)
# ---------------------------------------------------------
@st.cache_resource
def get_tv_engine():
    if not HAS_TV:
        return None
    try:
        # Connect to TradingView anonymously
        return TvDatafeed()
    except Exception:
        return None


def fetch_real_stock_data(symbol_str):
    clean_ticker = (
        symbol_str.strip()
        .upper()
        .replace(".NS", "")
        .replace(".BO", "")
        .replace("^", "")
    )
    df = None

    # =========================================================
    # SOURCE 1: DIRECT TRADINGVIEW DATA (PRIMARY PRIORITY)
    # =========================================================
    if HAS_TV:
        try:
            tv = get_tv_engine()
            if tv is not None:
                # Fetch exact daily candles from TradingView NSE
                tv_df = tv.get_hist(
                    symbol=clean_ticker,
                    exchange="NSE",
                    interval=Interval.in_daily,
                    n_bars=150,
                )
                if tv_df is not None and not tv_df.empty:
                    df = tv_df.copy()
                    df.rename(
                        columns={
                            "open": "Open",
                            "high": "High",
                            "low": "Low",
                            "close": "Close",
                            "volume": "Volume",
                        },
                        inplace=True,
                    )
                    df.index = pd.to_datetime(df.index)
        except Exception:
            df = None

    # =========================================================
    # SOURCE 2: BACKUP (ONLY IF TRADINGVIEW TEMPORARILY BLOCKS)
    # =========================================================
    if df is None or df.empty:
        suffixes = [".NS", ".BO"]
        for suffix in suffixes:
            full_symbol = f"{clean_ticker}{suffix}"
            if HAS_YFINANCE:
                try:
                    t_obj = yf.Ticker(full_symbol)
                    temp_df = t_obj.history(period="6m")
                    if (
                        temp_df is not None
                        and not temp_df.empty
                        and len(temp_df) >= 10
                    ):
                        df = temp_df[
                            ["Open", "High", "Low", "Close", "Volume"]
                        ].copy()
                        break
                except Exception:
                    pass

    # Live Google Price Verification
    if df is not None and not df.empty:
        try:
            g_url = f"https://www.google.com/finance/quote/{clean_ticker}:NSE"
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
                )
            }
            g_res = requests.get(g_url, headers=headers, timeout=3)
            if g_res.status_code == 200:
                match = re.search(r'data-last-price="([\d\.]+)"', g_res.text)
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
# SIDEBAR & INPUT SECTION
# ---------------------------------------------------------
st.sidebar.header("🔍 একক স্টক অ্যানালাইসিস")
stock_input = st.sidebar.text_input(
    "স্টকের টিকার লিখুন (যেমন: IFBAGRO, NUVAMA, TATAMOTORS):", "IFBAGRO"
)
analyze_btn = st.sidebar.button(
    "⚡ স্মার্ট মানি স্ক্যান করুন", use_container_width=True
)

if stock_input:
    with st.spinner("TradingView থেকে আসল ক্যান্ডেল ও প্রাইস ডেটা আনা হচ্ছে..."):
        df, clean_ticker = fetch_real_stock_data(stock_input)

    if df is None or df.empty:
        st.error(
            f"❌ **'{stock_input}'** স্টকের ডেটা ট্রেডিংভিউতে পাওয়া যায়নি। স্টকের"
            " সঠিক টিকার নাম চেক করুন।"
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

        # Smart Money Scoring Logic
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
                f"<b>RVOL Spiked ({round(rvol, 2)}x):</b> সেদিনের ভলিউম গত ২০"
                " দিনের গড়ের ১.৮ গুণের বেশি।"
            )
        elif rvol >= 1.2:
            score += 8
            factors_triggered.append(
                f"<b>Moderate RVOL ({round(rvol, 2)}x):</b> বাজারে সন্তোষজনক"
                " ভলিউম রয়েছে।"
            )
        else:
            factors_failed.append(
                f"RVOL দুর্বল ({round(rvol, 2)}x)। ভলিউম পর্যাপ্ত নয়।"
            )

        if lower_wick_ratio >= 0.5:
            score += 15
            factors_triggered.append(
                "<b>Strong Buyer Rejection"
                f" ({round(lower_wick_ratio*100, 1)}%):</b> ক্যান্ডেলের নিচ"
                " থেকে বড় বায়িং রিজেকশন।"
            )
        elif lower_wick_ratio >= 0.3:
            score += 8
            factors_triggered.append(
                "<b>Moderate Lower Wick"
                f" ({round(lower_wick_ratio*100, 1)}%):</b> নিচ থেকে বায়ারদের"
                " সাপোর্ট আছে।"
            )
        else:
            factors_failed.append("Lower Wick ছোট। নিচ থেকে সাপোর্ট কম।")

        if (body_range / total_candle_range <= 0.45) and (rvol >= 1.3):
            score += 15
            factors_triggered.append(
                "<b>VSA Absorption:</b> ছোট বডিতে উচ্চ ভলিউম, সেলিং শুষে নেওয়া"
                " হয়েছে।"
            )

        near_ema20 = abs(c_close - ema20_val) / ema20_val <= 0.02
        near_ema50 = abs(c_close - ema50_val) / ema50_val <= 0.02
        if near_ema20 and near_ema50:
            score += 15
            factors_triggered.append(
                "<b>Dual EMA Support:</b> ২০ ও ৫০ ইএমএ সাপোর্ট জোন।"
            )
        elif near_ema20 or near_ema50:
            score += 10
            factors_triggered.append(
                "<b>Dynamic EMA Support:</b> ইএমএ সাপোর্ট লেভেল থেকে বাউন্স।"
            )
        else:
            factors_failed.append("ইএমএ সাপোর্ট জোন থেকে দূরে।")

        if c_close >= vwap_val:
            score += 10
            factors_triggered.append(
                "<b>VWAP Hold:</b> ইনস্টিটিউশনাল VWAP বেঞ্চমার্কের ওপরে অবস্থান"
                " করছে।"
            )
        else:
            factors_failed.append("VWAP লাইনের নিচে ট্রেড করছে।")

        if mfi_val >= 50:
            score += 10
            factors_triggered.append(
                f"<b>Positive Money Flow (MFI: {round(mfi_val, 1)}):</b> ক্যাশ"
                " ইনফ্লো পজিটিভ।"
            )
        else:
            factors_failed.append(f"MFI দুর্বল ({round(mfi_val, 1)})।")

        if c_close > float(prev["Close"]):
            score += 10
            factors_triggered.append(
                "<b>Market Structure Shift:</b> আগের দিনের ক্লোজিংয়ের ওপর"
                " বুলিশ মোমেন্টাম।"
            )

        final_score = min(score, 100)

        if final_score >= 80:
            verdict_badge = "🔥 ULTRA HIGH CONVICTION SETUP"
            verdict_color = "#00c853"
            verdict_desc = (
                "ইনস্টিটিউশনাল বায়াররা অত্যন্ত সক্রিয়! ৩-৪ দিনের সুইং ট্রেড বাই"
                " সেটআপ।"
            )
        elif final_score >= 70:
            verdict_badge = "🟢 GOOD CONVICTION SETUP"
            verdict_color = "#29b6f6"
            verdict_desc = (
                "স্মার্ট মানি সক্রিয়। কড়া স্টপ লস মেনে পজিশন নেওয়া যেতে পারে।"
            )
        elif final_score >= 50:
            verdict_badge = "🟡 NEUTRAL / WEAK BOUNCE"
            verdict_color = "#ffb300"
            verdict_desc = (
                "আংশিক বায়ার রয়েছে তবে কনফার্মেশন কম। অপেক্ষা করা ভালো।"
            )
        else:
            verdict_badge = "🔴 DANGER - FAKE BOUNCE"
            verdict_color = "#ff3d00"
            verdict_desc = "এটি একটি ফেক বাউন্স! নতুন করে বাই করবেন না।"

        entry_price = round(c_close, 2)
        target_price = round(entry_price * 1.07, 2)
        sl_price = round(entry_price * 0.975, 2)

        st.markdown(
            f"<h2 style='color: {verdict_color};'>{clean_ticker} -"
            f" {verdict_badge}</h2>",
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
                f"TradingView Real Chart ({clean_ticker})",
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
        fig.update_xaxes(showgrid=True, gridcolor="#2a2e39")
        fig.update_yaxes(showgrid=True, gridcolor="#2a2e39")

        st.plotly_chart(fig, use_container_width=True)

        # Audio & Report Section
        st.subheader("📝 বিস্তারিত কারণ ও স্মার্ট মানি প্ল্যান:")

        speech_text = (
            f"{clean_ticker} স্টকের স্মার্ট মানি কনফিডেন্স স্কোর {final_score}"
            f" শতাংশ। বর্তমান বাই এন্ট্রি প্রাইস {entry_price} টাকা। টার্গেট"
            f" {target_price} টাকা এবং স্টপ লস {sl_price} টাকা। {verdict_desc}"
        )
        clean_js_speech = (
            speech_text.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
        )

        tts_html = f"""
        <div style="margin-bottom: 20px;">
            <button onclick="playVoice()" style="background: linear-gradient(135deg, #00c853, #009688); color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer;">
                🔊 ভয়েসে শুনুন (Listen Smart Money Report)
            </button>
            <script>
            function playVoice() {{
                window.speechSynthesis.cancel();
                const text = "{clean_js_speech}";
                const msg = new SpeechSynthesisUtterance(text);
                msg.lang = "bn-IN";
                msg.rate = 0.9;
                window.speechSynthesis.speak(msg);
            }}
            </script>
        </div>
        """
        components.html(tts_html, height=70)

        trig_html = "".join([f"<li>{f}</li>" for f in factors_triggered])
        fail_html = "".join([f"<li>{f}</li>" for f in factors_failed])

        st.markdown(
            f"### ✅ যে ফিল্টারগুলো মিলেছে:\n<ul>{trig_html}</ul>",
            unsafe_allow_html=True,
        )
        if factors_failed:
            st.markdown(
                f"### ⚠️ যে ফিল্টারগুলো দুর্বল:\n<ul>{fail_html}</ul>",
                unsafe_allow_html=True,
        )
