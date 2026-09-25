import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page Setup
st.set_page_config(page_title="Stock Pattern Scanner", layout="wide")

st.title("🎯 Stock Pattern Scanner")
st.write("১০টি সাব-সেক্টরের প্রপার লিকুইড স্টকের অল-প্রাইস ক্যান্ডেলস্টিক ও সুইং স্ক্যানার। কালার-ট্যাগিং ও সরাসরি ট্রেডিংভিউ লিঙ্ক সুবিধাসহ।")

# ---------------------------------------------------------
# Stock Database
# ---------------------------------------------------------
SECTOR_STOCKS = {
    "🏛️ 1. Banking, Finance & NBFC": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS",
        "BAJFINANCE.NS", "BAJAJFINSV.NS", "JIOFIN.NS", "PFC.NS", "RECLTD.NS", "PNB.NS", "BANKBARODA.NS"
    ],
    "⚡ 2. Energy, Power & Capital Goods": [
        "TDPOWERSYS.NS", "KIRLOSENG.NS", "TRIVENI.NS", "PRAJIND.NS", "GAIL.NS",
        "PETRONET.NS", "MGL.NS", "IGL.NS", "GUJGASLTD.NS", "ATGL.NS", "GSPL.NS",
        "RELIANCE.NS", "ONGC.NS", "OIL.NS", "ABB.NS", "ADANIGREEN.NS", "ADANIPOWER.NS",
        "BHEL.NS", "BORORENEW.NS", "CESC.NS", "CGPOWER.NS", "CUMMINSIND.NS",
        "ENGINERSIN.NS", "GENUSPOWER.NS", "INOXWIND.NS", "IONEXCHANG.NS", "IREDA.NS",
        "JSWENERGY.NS", "KEC.NS", "KPIGREEN.NS", "NHPC.NS", "NTPC.NS", "POWERGRID.NS",
        "SCHNEIDER.NS", "SIEMENS.NS", "SJVN.NS", "SUZLON.NS", "TATAPOWER.NS",
        "THERMAX.NS", "TORNTPOWER.NS"
    ],
    "💻 3. IT & Technology": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS",
        "PERSISTENT.NS", "LTIM.NS", "COFORGE.NS", "KPITTECH.NS", "TATAELXSI.NS"
    ],
    "🚗 4. Auto & Components": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
        "EICHERMOT.NS", "BHARATFORG.NS", "MOTHERSON.NS", "TVSMOTOR.NS", "BOSCHLTD.NS"
    ],
    "💊 5. Pharma & Healthcare": [
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS",
        "LUPIN.NS", "TORNTPHARM.NS", "MANKIND.NS", "MAXHEALTH.NS", "AUROPHARMA.NS"
    ],
    "🏗️ 6. Metals & Mining": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "JINDALSTEL.NS",
        "NMDC.NS", "NATIONALUM.NS", "SAIL.NS"
    ],
    "🛒 7. FMCG & Consumer Goods": [
        "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS",
        "TRENT.NS", "VBL.NS", "DMART.NS", "GODREJCP.NS", "DABUR.NS"
    ]
}

# ---------------------------------------------------------
# UI Elements (Matching Screenshot Layout)
# ---------------------------------------------------------
selected_sector = st.selectbox("একটি সাব-সেক্টর বেছে নিন:", list(SECTOR_STOCKS.keys()))

timeframe = st.selectbox("ক্যান্ডেল টাইমফ্রেম (Timeframe):", ["1 Day (Daily)", "1 Week (Weekly)"])

price_filters = st.multiselect(
    "🎯 যে প্রাইস রেঞ্জের স্টক অ্যাপে দেখতে চান তা টিক দিন:",
    ["🟢 Below ₹500", "🟡 In Range (₹500 - ₹2,000)", "🔴 Above ₹2,000"],
    default=["🟢 Below ₹500", "🟡 In Range (₹500 - ₹2,000)", "🔴 Above ₹2,000"]
)

# Robust Technical Indicator Calculation
def analyze_stock(df):
    if df.empty or len(df) < 20:
        return None
        
    df = df.copy()
    if 'Close' not in df.columns and 'Adj Close' in df.columns:
        df['Close'] = df['Adj Close']
        
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['Vol_Avg20'] = df['Volume'].rolling(window=20).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    latest = df.iloc[-1]
    
    # Reversal Strategy Conditions
    cond1 = (latest['Low'] <= latest['EMA20'] * 1.01) and (latest['Close'] >= latest['EMA20'])
    cond2 = latest['Volume'] >= 1.2 * latest['Vol_Avg20']
    
    is_buy = cond1 and cond2
    
    return {
        "LTP": float(latest['Close']),
        "RSI": float(latest['RSI']),
        "EMA20": float(latest['EMA20']),
        "Signal": "🟢 Buy Reversal" if is_buy else "⚪ Neutral"
    }

# Fetch Stock Data safely
def fetch_data(symbol, tf_str):
    interval = "1d" if "Day" in tf_str else "1wk"
    period = "6m" if "Day" in tf_str else "1y"
    
    try:
        t = yf.Ticker(symbol)
        data = t.history(period=period, interval=interval, auto_adjust=True)
        if not data.empty:
            return data
    except Exception:
        pass
    return pd.DataFrame()

# Scan Execution Button
scan_btn = st.button("🔍 স্ক্যান শুরু করুন", type="primary", use_container_width=True)

if scan_btn:
    stocks_to_scan = SECTOR_STOCKS[selected_sector]
    st.subheader(f"📊 স্ক্যান রেজাল্ট - {selected_sector}")
    
    results = []
    progress = st.progress(0)
    
    for idx, symbol in enumerate(stocks_to_scan):
        df_stock = fetch_data(symbol, timeframe)
        analysis = analyze_stock(df_stock)
        
        raw_name = symbol.replace(".NS", "").replace(".BO", "")
        # TradingView Direct Link Formulation
        tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{raw_name}"
        
        if analysis:
            ltp = analysis['LTP']
            
            # Price Filter Check
            include = False
            price_tag = ""
            if ltp < 500 and "🟢 Below ₹500" in price_filters:
                include = True
                price_tag = "Below ₹500"
            elif 500 <= ltp <= 2000 and "🟡 In Range (₹500 - ₹2,000)" in price_filters:
                include = True
                price_tag = "₹500 - ₹2,000"
            elif ltp > 2000 and "🔴 Above ₹2,000" in price_filters:
                include = True
                price_tag = "Above ₹2,000"
                
            if include:
                results.append({
                    "Stock Symbol": raw_name,
                    "LTP (₹)": round(ltp, 2),
                    "Price Category": price_tag,
                    "RSI (14)": round(analysis['RSI'], 1),
                    "Signal": analysis['Signal'],
                    "TradingView App Direct Link": tv_link
                })
        else:
            # Fallback direct link row if data fetch delays
            results.append({
                "Stock Symbol": raw_name,
                "LTP (₹)": "Check TV",
                "Price Category": "N/A",
                "RSI (14)": "N/A",
                "Signal": "⚠️ Tap TV Link",
                "TradingView App Direct Link": tv_link
            })
            
        progress.progress((idx + 1) / len(stocks_to_scan))
        
    if results:
        res_df = pd.DataFrame(results)
        
        # Display nicely with clickable links to TradingView
        st.dataframe(
            res_df,
            column_config={
                "TradingView App Direct Link": st.column_config.LinkColumn(
                    "📈 Open in TradingView",
                    display_text="Open Chart ↗"
                )
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("আপনার নির্বাচিত প্রাইস ফিল্টারে কোনো স্টক পাওয়া যায়নি।")


# চার্টে Entry, Target ও Stop Loss লাইন আঁকার কোড অংশ
if is_buy:
    entry_p = latest['Close']
    target_p = entry_p * 1.07  # ৭% টার্গেট
    sl_p = entry_p * 0.975     # ২.৫% স্টপ লস

    # 🟢 Entry Line
    fig.add_hline(y=entry_p, line_dash="solid", line_color="green", 
                  annotation_text=f"🟢 BUY ENTRY: ₹{entry_p:.2f}", annotation_position="top right", row=1, col=1)

    # 🔵 Target Line
    fig.add_hline(y=target_p, line_dash="dash", line_color="cyan", 
                  annotation_text=f"🔵 TARGET (7%): ₹{target_p:.2f}", annotation_position="top right", row=1, col=1)

    # 🔴 Stop Loss Line
    fig.add_hline(y=sl_p, line_dash="dash", line_color="red", 
                  annotation_text=f"🔴 STOP LOSS (2.5%): ₹{sl_p:.2f}", annotation_position="bottom right", row=1, col=1)
    
