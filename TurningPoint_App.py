import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page Configuration
st.set_page_config(page_title="1-Week Swing Screener - Turning Point", layout="wide")

st.title("🎯 Turning Point - 1-Week Swing Trading Screener")
st.caption("Smart Money Accumulation & High Probability Reversal Setup (3-7 Days Holding)")

# ---------------------------------------------------------
# Sector & Sub-Sector Stock Lists
# ---------------------------------------------------------
SECTOR_STOCKS = {
    "1. Energy, Power & Capital Goods (আপনার দেওয়া তালিকা)": [
        "TDPOWERSYS.NS", "KIRLOSENG.NS", "TRIVENI.NS", "PRAJIND.NS", "GAIL.NS",
        "PETRONET.NS", "MGL.NS", "IGL.NS", "GUJGASLTD.NS", "ATGL.NS", "GSPL.NS",
        "RELIANCE.NS", "ONGC.NS", "OIL.NS", "ABB.NS", "ADANIGREEN.NS", "ADANIPOWER.NS",
        "BHEL.NS", "BORORENEW.NS", "CESC.NS", "CGPOWER.NS", "CUMMINSIND.NS",
        "ENGINERSIN.NS", "GENUSPOWER.NS", "INOXWIND.NS", "IONEXCHANG.NS", "IREDA.NS",
        "JSWENERGY.NS", "KEC.NS", "KPIGREEN.NS", "NHPC.NS", "NTPC.NS", "POWERGRID.NS",
        "SCHNEIDER.NS", "SIEMENS.NS", "SJVN.NS", "SUZLON.NS", "TATAPOWER.NS",
        "THERMAX.NS", "TORNTPOWER.NS"
    ],
    "2. Banking & Finance (ব্যাংকিং ও ফাইন্যান্স)": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS",
        "BAJFINANCE.NS", "BAJAJFINSV.NS", "JIOFIN.NS", "PFC.NS", "RECLTD.NS", "PNB.NS", "BANKBARODA.NS"
    ],
    "3. IT & Technology (আইটি ও টেকনোলজি)": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
        "PERSISTENT.NS", "LTIM.NS", "COFORGE.NS", "KPITTECH.NS", "TATAELXSI.NS"
    ],
    "4. Auto & Components (অটো ও পার্টস)": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
        "EICHERMOT.NS", "BHARATFORG.NS", "MOTHERSON.NS", "TVSMOTOR.NS", "BOSCHLTD.NS"
    ],
    "5. Pharma & Healthcare (ফার্মা ও হেলথকেয়ার)": [
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS",
        "LUPIN.NS", "TORNTPHARM.NS", "MANKIND.NS", "MAXHEALTH.NS", "AUROPHARMA.NS"
    ],
    "6. Metals & Mining (ধাতু ও মাইনিং)": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "JINDALSTEL.NS",
        "NMDC.NS", "NATIONALUM.NS", "SAIL.NS"
    ],
    "7. FMCG & Consumer (কনজিউমার গুডস)": [
        "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS",
        "TRENT.NS", "VBL.NS", "DMART.NS", "GODREJCP.NS", "DABUR.NS"
    ]
}

# ---------------------------------------------------------
# Technical Strategy Calculations (Smart Money Reversal)
# ---------------------------------------------------------
def calculate_indicators(df):
    df = df.copy()
    
    # 20 EMA
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    
    # 20-day Volume Average
    df['Vol_Avg20'] = df['Volume'].rolling(window=20).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Candlestick Anatomy
    df['Body'] = abs(df['Close'] - df['Open'])
    df['Lower_Wick'] = np.where(df['Close'] >= df['Open'], df['Open'] - df['Low'], df['Close'] - df['Low'])
    df['Range'] = df['High'] - df['Low']
    
    # 1-Week Swing Buy Conditions
    cond1 = (df['Low'] <= df['EMA20'] * 1.01) & (df['Close'] >= df['EMA20'])
    cond2 = df['Volume'] >= 1.25 * df['Vol_Avg20']
    cond3 = (df['Lower_Wick'] >= 0.35 * df['Range']) | (df['RSI'] <= 45)
    
    df['BUY_SIGNAL'] = cond1 & cond2 & cond3
    return df

# Highly Reliable Data Fetcher Function
@st.cache_data(ttl=1800)
def load_data(ticker):
    try:
        # Primary: yf.Ticker().history (100% reliable for individual stocks)
        t = yf.Ticker(ticker)
        data = t.history(period="6m", interval="1d")
        if data.empty:
            # Fallback Backup method
            data = yf.download(ticker, period="6m", interval="1d", progress=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
        return data
    except Exception:
        return pd.DataFrame()

# ---------------------------------------------------------
# Sidebar Navigation & Search Controls
# ---------------------------------------------------------
st.sidebar.header("🔍 সাব-সেক্টর ও স্টক নির্বাচন")

selected_sector = st.sidebar.selectbox("১. সাব-সেক্টর বেছে নিন:", list(SECTOR_STOCKS.keys()))
stock_list = SECTOR_STOCKS[selected_sector]

search_mode = st.sidebar.radio("২. দেখার মোড:", ["সেক্টর লিস্ট থেকে", "যেকোনো স্টক সার্চ করুন (5000+)"])

if search_mode == "সেক্টর লিস্ট থেকে":
    selected_stock = st.sidebar.selectbox("স্টক নির্বাচন করুন:", stock_list)
else:
    custom_symbol = st.sidebar.text_input("NSE/BSE কাস্টম স্টক নাম (যেমন: TATAPOWER.NS):", "TATAPOWER.NS")
    selected_stock = custom_symbol.strip().upper()

run_scanner = st.sidebar.button("🚀 এই সেক্টর স্ক্যান করুন")

# ---------------------------------------------------------
# Main Visuals & Interactive Chart
# ---------------------------------------------------------
if selected_stock:
    data = load_data(selected_stock)
    
    if not data.empty and len(data) > 30:
        df = calculate_indicators(data)
        latest = df.iloc[-1]
        
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("বর্তমান দাম (LTP)", f"₹{latest['Close']:.2f}")
        col2.metric("RSI (14)", f"{latest['RSI']:.1f}")
        col3.metric("20 EMA", f"₹{latest['EMA20']:.2f}")
        
        is_buy = latest['BUY_SIGNAL']
        if is_buy:
            col4.error("🔥 SMART MONEY BUY ZONE (১ সপ্তাহ)")
        else:
            col4.info("⏳ Neutral / Waiting for Signal")

        # TradingView Chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.08, 
                            subplot_titles=(f'{selected_stock} - 1-Week Swing Trading Chart', 'Volume Profile'),
                            row_width=[0.25, 0.75])

        # Candlestick Trace
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Price'
        ), row=1, col=1)

        # 20 EMA Line
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], mode='lines', name='20 EMA', line=dict(color='orange', width=1.5)
        ), row=1, col=1)

        # Mark Smart Money Buy Points with Green Triangles
        buy_signals = df[df['BUY_SIGNAL']]
        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['Low'] * 0.985,
            mode='markers+text',
            name='Smart Money Buy Point',
            marker=dict(symbol='triangle-up', size=14, color='green'),
            text=['BUY' for _ in range(len(buy_signals))],
            textposition='bottom center'
        ), row=1, col=1)

        # Target (7%) & Stop-Loss (2.5%) Lines
        if is_buy:
            entry_price = latest['Close']
            target_price = entry_price * 1.07
            sl_price = entry_price * 0.975

            fig.add_hline(y=target_price, line_dash="dash", line_color="cyan", annotation_text=f"Target (7%): ₹{target_price:.2f}", row=1, col=1)
            fig.add_hline(y=sl_price, line_dash="dash", line_color="red", annotation_text=f"Stop Loss (2.5%): ₹{sl_price:.2f}", row=1, col=1)

        # Volume Bar Chart
        colors = ['green' if c >= o else 'red' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(
            x=df.index, y=df['Volume'], name='Volume', marker_color=colors
        ), row=2, col=1)

        fig.update_layout(height=650, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error(f"'{selected_stock}' স্টকের ডাটা পাওয়া যায়নি। সিম্বলটি পরীক্ষা করে আবার চেষ্টা করুন।")

# ---------------------------------------------------------
# Sector-wise Auto Scanner
# ---------------------------------------------------------
if run_scanner:
    st.subheader(f"⚡ {selected_sector} - বায়িং পজিশনে থাকা স্টকসমূহ")
    scan_results = []
    
    progress_bar = st.progress(0)
    total = len(stock_list)
    
    for idx, ticker in enumerate(stock_list):
        s_data = load_data(ticker)
        if not s_data.empty and len(s_data) > 30:
            s_df = calculate_indicators(s_data)
            s_latest = s_df.iloc[-1]
            
            if s_latest['BUY_SIGNAL']:
                entry = s_latest['Close']
                scan_results.append({
                    "Stock": ticker.replace(".NS", "").replace(".BO", ""),
                    "LTP (₹)": round(entry, 2),
                    "RSI": round(s_latest['RSI'], 1),
                    "Target (7%)": round(entry * 1.07, 2),
                    "Stop-Loss (2.5%)": round(entry * 0.975, 2),
                    "Signal": "🟢 Buy Reversal"
                })
        progress_bar.progress((idx + 1) / total)
    
    if scan_results:
        st.dataframe(pd.DataFrame(scan_results), use_container_width=True)
    else:
        st.warning(f"আজকের দিনে '{selected_sector}' এর কোনো স্টকে ১-সপ্তাহের কনফার্মড বাই সিগন্যাল পাওয়া যায়নি।")
