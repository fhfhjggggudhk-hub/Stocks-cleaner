import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(page_title="Pro Chart & Smart Money Visualizer", layout="wide")

st.title("📊 Smart Money & Price Action Chart Analyzer")
st.caption("হায়ার হাই (HH), হায়ার লো (HL), ইনস্টিটিউশনাল/বড় ট্রেডারদের অ্যাকশন এবং ট্রেড প্ল্যান বিশ্লেষণ")

# ---------------------------------------------------------
# Stock Database
# ---------------------------------------------------------
SECTOR_STOCKS = {
    "⚡ Energy, Power & Capital Goods": [
        "TDPOWERSYS.NS", "TATAPOWER.NS", "KIRLOSENG.NS", "TRIVENI.NS", "PRAJIND.NS", "GAIL.NS",
        "RELIANCE.NS", "ONGC.NS", "ABB.NS", "ADANIGREEN.NS", "BHEL.NS", "NTPC.NS", "POWERGRID.NS"
    ],
    "🏛️ Banking & Finance": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "BAJFINANCE.NS", "PFC.NS", "RECLTD.NS"
    ],
    "💻 IT & Technology": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "PERSISTENT.NS", "KPITTECH.NS"
    ],
    "🚗 Auto & Components": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS"
    ]
}

# Sidebar Selection
st.sidebar.header("🔍 স্টক নির্বাচন করুন")
selected_sector = st.sidebar.selectbox("১. সেক্টর:", list(SECTOR_STOCKS.keys()))
selected_stock = st.sidebar.selectbox("২. স্টক:", SECTOR_STOCKS[selected_sector])

# ---------------------------------------------------------
# Data Fetcher
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def load_data(ticker):
    try:
        df = yf.download(ticker, period="6m", interval="1d", progress=False, ignore_tz=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if not df.empty and len(df) > 20:
            return df
    except Exception:
        pass
    return pd.DataFrame()

# ---------------------------------------------------------
# Technical Analysis Logic (Price Action & Smart Money)
# ---------------------------------------------------------
def analyze_market_structure(df):
    df = df.copy()
    
    # 20 EMA & Moving Averages
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['Vol_Avg20'] = df['Volume'].rolling(window=20).mean()
    
    # Smart Money Volume Activity (Vol > 1.5x average)
    df['Smart_Money_Vol'] = df['Volume'] > (1.5 * df['Vol_Avg20'])
    
    # Identify Peaks & Valleys for Higher High (HH) and Higher Low (HL)
    df['Local_High'] = df['High'].rolling(window=5, center=True).max() == df['High']
    df['Local_Low'] = df['Low'].rolling(window=5, center=True).min() == df['Low']
    
    return df

# ---------------------------------------------------------
# Main Visualization
# ---------------------------------------------------------
if selected_stock:
    raw_name = selected_stock.replace(".NS", "").replace(".BO", "")
    tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{raw_name}"
    
    st.subheader(f"📈 {raw_name} - স্মার্ট মানি ট্র্যাকার ও প্রাইস অ্যাকশন চার্ট")
    st.markdown(f"[📲 ডাইরেক্ট TradingView-তে এই চার্টটি খুলুন (Open Chart ↗)]({tv_url})")

    df = load_data(selected_stock)
    
    if not df.empty and len(df) > 30:
        df = analyze_market_structure(df)
        
        latest = df.iloc[-1]
        entry_price = float(latest['Close'])
        target_price = round(entry_price * 1.07, 2)    # 7% Profit Target
        sl_price = round(entry_price * 0.975, 2)       # 2.5% Stop Loss
        ema_val = round(float(latest['EMA20']), 2)
        
        # Key Summary Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("বর্তমান দাম (LTP)", f"₹{entry_price:.2f}")
        m2.metric("20 EMA সাপোর্ট", f"₹{ema_val:.2f}")
        m3.metric("টার্গেট (+৭%)", f"₹{target_price}")
        m4.metric("স্টপ লস (-২.৫%)", f"₹{sl_price}")

        # ---------------------------------------------------------
        # Plotly Chart Generation
        # ---------------------------------------------------------
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.06, 
                            subplot_titles=(f'{raw_name} - Price Action & Smart Money Footprint', 'Volume & Institutional Spike'),
                            row_width=[0.25, 0.75])

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Price Candle'
        ), row=1, col=1)

        # 🟠 Orange Line: 20 EMA
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], mode='lines', name='20 EMA Support Line',
            line=dict(color='orange', width=2)
        ), row=1, col=1)

        # 🟢 Entry Level
        fig.add_hline(y=entry_price, line_dash="solid", line_color="#26a69a", line_width=2,
                      annotation_text=f"🟢 BUY ENTRY: ₹{entry_price:.2f}", annotation_position="top right", row=1, col=1)

        # 🔵 Target Level
        fig.add_hline(y=target_price, line_dash="dash", line_color="#29b6f6", line_width=2,
                      annotation_text=f"🔵 TARGET (7%): ₹{target_price:.2f}", annotation_position="top right", row=1, col=1)

        # 🔴 Stop Loss Level
        fig.add_hline(y=sl_price, line_dash="dash", line_color="#ef5350", line_width=2,
                      annotation_text=f"🔴 STOP LOSS (2.5%): ₹{sl_price:.2f}", annotation_position="bottom right", row=1, col=1)

        # Annotate Higher Highs (HH) & Higher Lows (HL)
        hh_points = df[df['Local_High']].tail(3)
        hl_points = df[df['Local_Low']].tail(3)

        for date, row in hh_points.iterrows():
            fig.add_annotation(x=date, y=row['High']*1.01, text="<b>HH</b>", showarrow=False,
                               font=dict(color="#29b6f6", size=11), row=1, col=1)

        for date, row in hl_points.iterrows():
            fig.add_annotation(x=date, y=row['Low']*0.99, text="<b>HL</b>", showarrow=False,
                               font=dict(color="#26a69a", size=11), row=1, col=1)

        # Smart Money Volume Markers on Chart
        smart_money_df = df[df['Smart_Money_Vol'] & (df['Close'] > df['Open'])].tail(3)
        for date, row in smart_money_df.iterrows():
            fig.add_annotation(x=date, y=row['Low']*0.985, text="🐳 BIG TRADER", showarrow=True,
                               arrowhead=2, arrowcolor="#00e676", arrowsize=1,
                               font=dict(color="#ffffff", size=9), bgcolor="#004d40", row=1, col=1)

        # Volume Chart
        colors = ['#00e676' if sm else ('#26a69a' if c >= o else '#ef5350') 
                  for sm, c, o in zip(df['Smart_Money_Vol'], df['Close'], df['Open'])]
        fig.add_trace(go.Bar(
            x=df.index, y=df['Volume'], name='Volume', marker_color=colors
        ), row=2, col=1)

        fig.update_layout(height=680, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------
        # Comprehensive Bengali Analysis Section
        # ---------------------------------------------------------
        st.subheader("📚 চার্টের টেকনিক্যাল সিগন্যাল ও বড় ট্রেডারদের পজিশন বিশ্লেষণ")
        
        info_box = st.container(border=True)
        with info_box:
            st.markdown(f"""
            ### 🎨 ১. চার্টের গুরুত্বপূর্ণ লাইনসমূহ (Visual Level Breakdown):
            * 🟢 **সবুজ সলিড লাইন (Buy Entry Line): ₹{entry_price:.2f}** — এই দামে বর্তমান বায়িং কনফার্মেশন তৈরি হয়েছে।
            * 🔵 **আকাশি ড্যাশড লাইন (Target Line): ₹{target_price:.2f}** — এন্ট্রি প্রাইস থেকে +৭% লাভের পয়েন্ট।
            * 🔴 **লাল ড্যাশড লাইন (Stop Loss Line): ₹{sl_price:.2f}** — ঝুঁকি কমানোর জন্য -২.৫% স্টপ লস লেভেল।
            * 🟠 **কমলা লাইন (20 EMA Support Line): ₹{ema_val:.2f}** — এটি ২০ দিনের এক্সপোনেনশিয়াল মুভিং এভারেজ, যা শক্ত সাপোর্ট হিসেবে কাজ করে।

            ---

            ### 📈 ২. চার্টের ট্রেন্ড ও মার্কেট স্ট্রাকচার (HH & HL Analysis):
            * **Higher High (HH):** চার্টে চিহ্নিত **HH** পয়েন্টগুলি নির্দেশ করছে স্টকটির সর্বোচ্চ দামের চূড়াগুলো দিন দিন ওপরের দিকে উঠছে।
            * **Higher Low (HL):** চার্টে চিহ্নিত **HL** পয়েন্টগুলি নির্দেশ করছে যখনই স্টক সামান্য নিচে নেমেছে, আগের লো-এর চেয়ে ওপরে সাপোর্ট নিয়েছে।
            * **ট্রেন্ড নির্দেশক:** চার্টে ক্রমাগত **Higher High (HH)** এবং **Higher Low (HL)** তৈরি হওয়া একটি অত্যন্ত শক্ত **Uptrend (বুলিশ মার্কেট)** এর লক্ষণ।

            ---

            ### 🐳 ৩. বড় বড় ট্রেডাররা (Smart Money / Institutional Buyers) কী করছে?
            * **ইনস্টিটিউশনাল অ্যাকুমুলেশন (Big Trader Entry):** চার্টের যেখানে **`🐳 BIG TRADER`** লেখা সবুজ তীরচিহ্ন রয়েছে, সেখানে সাধারণ দিনের তুলনায় দ্বিগুণ বা তার চেয়ে বেশি ভলিউমে বড় বড় মিউচুয়াল ফান্ড বা প্রাতিষ্ঠানিক বিনিয়োগকারীরা শেয়ার কিনেছে।
            * **ইএমএ রিজেকশন (EMA Rejection):** বড় ট্রেডাররা স্টকটির দাম 🟠 **কমলা (20 EMA)** লাইনের কাছে আসলেই প্রচুর শেয়ার কেনা শুরু করে, যার ফলে ক্যান্ডেলটি নিচে না নেমে আবার ওপরের দিকে লাফিয়ে ওঠে (Bounce Back)।

            ---

            ### 📱 ৪. TradingView App-এ আপনি কীভাবে একই ট্রেড প্ল্যান সেট করবেন?
            1. ওপরে দেওয়া **`Open Chart ↗`** লিঙ্কে ক্লিক করে TradingView-এ **{raw_name}** চার্ট খুলুন।
            2. **`fx Indicators`** থেকে **EMA** যোগ করে তার দিন সংখ্যা **`20`** করে দিন (কমলা লাইন পেয়ে যাবেন)।
            3. বামপাশের Drawing Tools থেকে **`Long Position`** টুলটি নিয়ে এই ক্যান্ডেলের ওপর বসান এবং প্রাইজ দিন:
               * **Entry Price:** ₹{entry_price:.2f}
               * **Target Price:** ₹{target_price:.2f}
               * **Stop Loss:** ₹{sl_price:.2f}
            """)

    else:
        st.warning(f"'{raw_name}' স্টকের ডাটা লোড হতে কয়েক সেকেন্ড সময় লাগছে। পেজটি রিফ্রেশ দিন।")
        
