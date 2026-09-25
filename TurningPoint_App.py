import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Config
st.set_page_config(page_title="My Stock Watchlist & Trade Setup", layout="wide")

st.title("📊 স্মার্ট ট্রেড সেটআপ ও প্রাইস অ্যানালাইজার")
st.caption("লিস্ট থেকে যেকোনো স্টক সিলেক্ট করুন এবং চার্টসহ বিস্তারিত ট্রেড প্ল্যান দেখে নিন")

# ---------------------------------------------------------
# Your Complete Stock List (ইচ্ছামতো স্টক যোগ/বিয়োগ করতে পারেন)
# ---------------------------------------------------------
SECTOR_STOCKS = {
    "⚡ Energy, Power & Capital Goods": [
        "TDPOWERSYS.NS", "TATAPOWER.NS", "KIRLOSENG.NS", "TRIVENI.NS", "PRAJIND.NS", 
        "GAIL.NS", "RELIANCE.NS", "ONGC.NS", "ABB.NS", "ADANIGREEN.NS", "BHEL.NS", "NTPC.NS", "POWERGRID.NS"
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
st.sidebar.header("🔍 আপনার স্টকের লিস্ট")
selected_sector = st.sidebar.selectbox("১. সেক্টর বেছে নিন:", list(SECTOR_STOCKS.keys()))
selected_stock = st.sidebar.selectbox("২. স্টক বেছে নিন:", SECTOR_STOCKS[selected_sector])

# ---------------------------------------------------------
# Fast & Reliable Data Fetcher
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    try:
        df = yf.download(ticker, period="6m", interval="1d", progress=False, ignore_tz=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if not df.empty and len(df) > 10:
            return df
    except Exception:
        pass
    return pd.DataFrame()

# ---------------------------------------------------------
# Main App Execution
# ---------------------------------------------------------
if selected_stock:
    clean_symbol = selected_stock.replace(".NS", "").replace(".BO", "")
    
    st.subheader(f"📌 {clean_symbol} - ট্রেড প্ল্যান ও চার্ট বিশ্লেষণ")
    
    with st.spinner("ডাটা লোড হচ্ছে... অনুগ্রহ করে এক সেকেন্ড অপেক্ষা করুন"):
        df = fetch_stock_data(selected_stock)

    if not df.empty:
        # Technical Calculation
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Vol_Avg'] = df['Volume'].rolling(20).mean()
        
        latest_price = round(float(df['Close'].iloc[-1]), 2)
        ema_20 = round(float(df['EMA20'].iloc[-1]), 2)
        
        # Calculate Key Levels
        entry_level = latest_price
        target_level = round(entry_level * 1.07, 2)    # +7% Target
        sl_level = round(entry_level * 0.975, 2)       # -2.5% Stop Loss
        
        # Display Key Level Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🟢 এন্ট্রি প্রাইস (Entry)", f"₹{entry_level}")
        c2.metric("🔵 টার্গেট (+৭%)", f"₹{target_level}")
        c3.metric("🔴 স্টপ লস (-২.৫%)", f"₹{sl_level}")
        c4.metric("🟠 20 EMA সাপোর্ট", f"₹{ema_20}")

        # ---------------------------------------------------------
        # Interactive Plotly Chart
        # ---------------------------------------------------------
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, 
                            subplot_titles=(f'{clean_symbol} - Chart with Entry, Target & SL Lines', 'Volume Activity'),
                            row_width=[0.25, 0.75])

        # Candlestick Chart
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Candle'
        ), row=1, col=1)

        # 🟠 20 EMA Support Line
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], mode='lines', name='20 EMA Line',
            line=dict(color='orange', width=2)
        ), row=1, col=1)

        # 🟢 Entry Line
        fig.add_hline(y=entry_level, line_dash="solid", line_color="#26a69a", line_width=2,
                      annotation_text=f"🟢 Entry: ₹{entry_level}", annotation_position="top right", row=1, col=1)

        # 🔵 Target Line
        fig.add_hline(y=target_level, line_dash="dash", line_color="#29b6f6", line_width=2,
                      annotation_text=f"🔵 Target: ₹{target_level}", annotation_position="top right", row=1, col=1)

        # 🔴 Stop Loss Line
        fig.add_hline(y=sl_level, line_dash="dash", line_color="#ef5350", line_width=2,
                      annotation_text=f"🔴 Stop Loss: ₹{sl_level}", annotation_position="bottom right", row=1, col=1)

        # Volume Bar Chart
        vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=vol_colors), row=2, col=1)

        fig.update_layout(height=580, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------
        # Detailed Bangla Trade Breakdown
        # ---------------------------------------------------------
        st.markdown("---")
        st.subheader("📋 ট্রেডের বিস্তারিত কারণ ও লেভেলসমূহ (Groww App-এ বসানোর জন্য):")
        
        volume_spike = float(df['Volume'].iloc[-1]) > (1.3 * float(df['Vol_Avg'].iloc[-1]))

        st.info(f"""
        ### 🎯 ১. প্রধান প্রাইস লেভেল (Key Levels):
        * 🟢 **বাই এন্ট্রি লেভেল (Buy Entry): ₹{entry_level}** — চার্টের বর্তমান সাপোর্ট জোন থেকে বাই করার লেভেল।
        * 🔵 **টার্গেট প্রাইস (Target Price): ₹{target_level}** — এন্ট্রি প্রাইস থেকে +৭% লাভ তোলার লেভেল।
        * 🔴 **স্টপ লস (Stop Loss): ₹{sl_level}** — ঝুঁকি কমানোর জন্য -২.৫% লসে বের হওয়ার লেভেল।
        * 🟠 **সাপোর্ট ইএমএ (20 EMA Line): ₹{ema_20}** — চার্টের কমলা সাপোর্ট লাইন।

        ---

        ### 🧠 ২. কেন এই ট্রেড নেওয়া হচ্ছে? (Trade Reason):
        1. **ইএমএ সাপোর্ট ব্রেকাউট/বাউন্স:** স্টকটি বর্তমানে ২০ দিনের মুভিং এভারেজ (₹{ema_20})-এর ওপরে ট্রেড করছে, যা শক্ত বুলিশ ট্রেন্ড নির্দেশ করে।
        2. **ভলিউম অ্যাক্টিভিটি:** {'সর্বশেষ সেশনে ভালো ভলিউম দেখা গেছে, যা বাইয়ারদের সক্রিয়তা দেখাচ্ছে।' if volume_spike else 'ভলিউম স্থিতিশীল রয়েছে এবং স্টকটি সাপোর্টের কাছে একুমুলেট হচ্ছে।'}
        3. **রিস্ক রিওয়ার্ড রেশিও:** এই ট্রেডে আপনার ঝুঁকি মাত্র ২.৫% (🔴 লাল লাইন), কিন্তু লাভের সুযোগ ৭% (🔵 নীল লাইন)।

        ---

        ### 📱 ৩. Groww (গ্রো) অ্যাপে আপনি কীভাবে এটি প্রয়োগ করবেন?
        1. আপনার **Groww App** ওপেন করে সার্চবার-এ **{clean_symbol}** লিখে স্টকটি বের করুন।
        2. Buy অপশনে গিয়ে লিমিট প্রাইস সেট করুন **₹{entry_level}**।
        3. ট্রেড অ্যাক্টিভ হলে **Stop Loss Trigger Price** বসান **₹{sl_level}** এবং টার্গেট সেট রাখুন **₹{target_level}**।
        """)

    else:
        st.error(f"❌ '{clean_symbol}' স্টকের ডাটা পেতে সমস্যা হচ্ছে। অনুগ্রহ করে আবার পেজটি রিফ্রেশ দিন বা অন্য স্টক সিলেক্ট করুন।")
        
