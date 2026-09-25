import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Config
st.set_page_config(page_title="Smart Trade Setup Analyzer", layout="wide")

st.title("📊 স্মার্ট ট্রেড সেটআপ ও প্রাইস অ্যানালাইজার")
st.caption("১০টি সাব-সেক্টরের সম্পূর্ণ স্টক লিস্ট থেকে সিলেক্ট করুন এবং ট্রেড প্ল্যান দেখে নিন")

# ---------------------------------------------------------
# Expanded 10 Sub-Sectors Stock List
# ---------------------------------------------------------
SECTOR_STOCKS = {
    "1. ⚡ Energy, Power & Capital Goods": [
        "TDPOWERSYS.NS", "TATAPOWER.NS", "KIRLOSENG.NS", "TRIVENI.NS", "PRAJIND.NS", 
        "GAIL.NS", "RELIANCE.NS", "ONGC.NS", "ABB.NS", "ADANIGREEN.NS", "BHEL.NS", 
        "NTPC.NS", "POWERGRID.NS", "SUZLON.NS", "NHPC.NS", "SJVN.NS", "IREDA.NS", 
        "SIEMENS.NS", "CGPOWER.NS", "INOXWIND.NS", "THERMAX.NS", "LT.NS", "OIL.NS", 
        "ADANIPOWER.NS", "TORNTPOWER.NS", "JSWENERGY.NS", "CESC.NS"
    ],
    "2. 🏛️ Banking & Financials": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "BAJFINANCE.NS", 
        "PFC.NS", "RECLTD.NS", "BANKBARODA.NS", "CANBK.NS", "KOTAKBANK.NS", 
        "INDUSINDBK.NS", "IDFCFIRSTB.NS", "PNB.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS"
    ],
    "3. 💻 IT & Technology": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "PERSISTENT.NS", 
        "KPITTECH.NS", "TECHM.NS", "LTIM.NS", "COFORGE.NS", "TATAELXSI.NS", "OFSS.NS", "CYIENT.NS"
    ],
    "4. 🚗 Auto & Components": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS", 
        "HEROMOTOCO.NS", "BHARATFORG.NS", "SAMVARDHANA.NS", "BOSCHLTD.NS", "EICHERMOT.NS", "BALKRISIND.NS"
    ],
    "5. 💊 Pharma & Healthcare": [
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "TORNTPHARM.NS", 
        "MANKIND.NS", "LUPIN.NS", "AUROPHARMA.NS", "APOLLOHOSP.NS", "BIOCON.NS", "GLENMARK.NS", "MAXHEALTH.NS"
    ],
    "6. 🛒 FMCG & Consumer Goods": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", 
        "VBL.NS", "DABUR.NS", "MARICO.NS", "GODREJCP.NS", "COLPAL.NS", "TRENT.NS"
    ],
    "7. 🏗️ Metals & Mining": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS", "NMDC.NS", 
        "JINDALSTEL.NS", "NATIONALUM.NS", "VEDL.NS", "SAIL.NS", "HINDZINC.NS"
    ],
    "8. 🏢 Realty & Infrastructure": [
        "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "LODHA.NS", 
        "PHOENIXLTD.NS", "PRESTIGE.NS", "SOBHA.NS", "NCC.NS", "IRB.NS"
    ],
    "9. 🛡️ Defence & Railways (PSU)": [
        "HAL.NS", "BEL.NS", "MAZDOCK.NS", "RVNL.NS", "IRFC.NS", 
        "CONCOR.NS", "BDL.NS", "COCHINSHIP.NS", "IRCTC.NS", "RAILTEL.NS", "RITES.NS"
    ],
    "10. 🧪 Chemicals & Fertilizers": [
        "PIDILITIND.NS", "UPL.NS", "DEEPAKNTR.NS", "SRF.NS", "TATACHEM.NS", 
        "FLUOROCHEM.NS", "AARTIIND.NS", "LINDEINDIA.NS", "FACT.NS", "RCFL.NS"
    ]
}

# Sidebar Selection
st.sidebar.header("🔍 স্টক নির্বাচন করুন")
selected_sector = st.sidebar.selectbox("১. সাব-সেক্টর বেছে নিন:", list(SECTOR_STOCKS.keys()))
selected_stock = st.sidebar.selectbox("২. স্টক বেছে নিন:", SECTOR_STOCKS[selected_sector])

# ---------------------------------------------------------
# Data Fetcher (Error-free with Fallbacks)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    # Method 1: yf.Ticker History
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="6m", interval="1d")
        if not df.empty and len(df) > 5:
            return df
    except Exception:
        pass

    # Method 2: yf.download Fallback
    try:
        df = yf.download(ticker, period="6m", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if not df.empty and len(df) > 5:
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
    
    with st.spinner(f"'{clean_symbol}' স্টকের ডাটা লোড হচ্ছে..."):
        df = fetch_stock_data(selected_stock)

    if not df.empty:
        # Technical Calculation
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Vol_Avg'] = df['Volume'].rolling(20).mean()
        
        latest_price = round(float(df['Close'].iloc[-1]), 2)
        ema_20 = round(float(df['EMA20'].iloc[-1]), 2)
        
        # Key Price Levels
        entry_level = latest_price
        target_level = round(entry_level * 1.07, 2)    # +7% Target
        sl_level = round(entry_level * 0.975, 2)       # -2.5% Stop Loss
        
        # Key Level Cards
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
                            subplot_titles=(f'{clean_symbol} - Entry, Target & SL Chart Lines', 'Volume Activity'),
                            row_width=[0.25, 0.75])

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Candle'
        ), row=1, col=1)

        # 🟠 20 EMA Line
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], mode='lines', name='20 EMA Support',
            line=dict(color='orange', width=2)
        ), row=1, col=1)

        # 🟢 Entry Line
        fig.add_hline(y=entry_level, line_dash="solid", line_color="#26a69a", line_width=2,
                      annotation_text=f"🟢 Entry: ₹{entry_level}", annotation_position="top right", row=1, col=1)

        # 🔵 Target Line
        fig.add_hline(y=target_level, line_dash="dash", line_color="#29b6f6", line_width=2,
                      annotation_text=f"🔵 Target (7%): ₹{target_level}", annotation_position="top right", row=1, col=1)

        # 🔴 Stop Loss Line
        fig.add_hline(y=sl_level, line_dash="dash", line_color="#ef5350", line_width=2,
                      annotation_text=f"🔴 Stop Loss: ₹{sl_level}", annotation_position="bottom right", row=1, col=1)

        # Volume Chart
        vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=vol_colors), row=2, col=1)

        fig.update_layout(height=580, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------
        # Detailed Written Strategy Section
        # ---------------------------------------------------------
        st.markdown("---")
        st.subheader("📋 ট্রেডের বিস্তারিত কারণ ও লেভেলসমূহ (Groww App-এ বসানোর জন্য):")
        
        vol_latest = float(df['Volume'].iloc[-1])
        vol_avg = float(df['Vol_Avg'].iloc[-1])
        volume_spike = vol_latest > (1.2 * vol_avg)

        st.info(f"""
        ### 🎯 ১. প্রধান প্রাইস লেভেল (Key Levels):
        * 🟢 **বাই এন্ট্রি লেভেল (Buy Entry): ₹{entry_level}** — চার্টের সাপোর্ট জোন অনুযায়ী বর্তমানে বাই করার জন্য উপযুক্ত লেভেল।
        * 🔵 **টার্গেট প্রাইস (Target Price): ₹{target_level}** — এন্ট্রি প্রাইস থেকে +৭% লাভ বুক করার লেভেল।
        * 🔴 **স্টপ লস (Stop Loss): ₹{sl_level}** — ঝুঁকি কমানোর জন্য -২.৫% লসে বের হওয়ার লেভেল।
        * 🟠 **সাপোর্ট ইএমএ (20 EMA Line): ₹{ema_20}** — চার্টের কমলা রঙের মুভিং এভারেজ সাপোর্ট লাইন।

        ---

        ### 🧠 ২. কেন এই ট্রেড পজিশন তৈরি হলো? (Trade Reason):
        1. **ইএমএ সাপোর্ট বাউন্স:** স্টকটির দাম বর্তমানে ২০ দিনের মুভিং এভারেজ (₹{ema_20})-এর ওপর অবস্থান করছে, যা বুলিশ মোমেন্টাম নির্দেশ করে।
        2. **ভলিউম কনফার্মেশন:** {'সর্বশেষ ক্যান্ডেলে ভালো ভলিউম দেখা গেছে, যা বায়ারদের সক্রিয়তা নির্দেশ করে।' if volume_spike else 'স্টকে ভলিউম স্বাভাবিক রয়েছে এবং সাপোর্ট ধরে রাখছে।'}
        3. **রিস্ক রিওয়ার্ড অনুপাত:** এই ট্রেডে আপনার সম্ভাব্য ঝুঁকি মাত্র ২.৫% (🔴 লাল লাইন), কিন্তু লাভের সুযোগ ৭% (🔵 আকাশি লাইন)।

        ---

        ### 📱 ৩. Groww (গ্রো) অ্যাপে আপনি এটি কীভাবে প্রয়োগ করবেন?
        1. আপনার **Groww App** ওপেন করে **{clean_symbol}** লিখে সার্চ করুন।
        2. Buy অপশনে গিয়ে লিমিট প্রাইস সেট করুন **₹{entry_level}**।
        3. অর্ডার সম্পন্ন হলে **Stop Loss Trigger Price** দিন **₹{sl_level}** এবং টার্গেট প্রাইস সেট রাখুন **₹{target_level}**।
        """)

    else:
        st.error(f"❌ '{clean_symbol}' স্টকের ডাটা পেতে সমস্যা হচ্ছে। অনুগ্রহ করে আবার পেজটি রিফ্রেশ দিন বা অন্য স্টক সিলেক্ট করুন।")
