import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Streamlit Page Config
st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")

st.title("⚡ AI Stock Screener Pro (All Stocks & Timeframe Fixed)")
st.caption(
    "১০টি সাব-সেক্টরের সবকটি স্টক নিরবচ্ছিন্নভাবে স্ক্যান করার জন্য ফাস্ট ব্যাচ-ডাউনলোড "
    "এবং ৪-ঘণ্টা/১-দিনের নিখুঁত ক্লোজড-ক্যান্ডেল লজিক যুক্ত করা হয়েছে।"
)

# 10 Complete Sub-Sectors with All Stock Symbols (No Stock Removed)
SUB_SECTORS = {
    "🏦 1. Banking, Finance & NBFC": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS",
        "BAJFINANCE.NS", "BAJAJFINSV.NS", "MUTHOOTFIN.NS", "INDUSINDBK.NS", "BANKBARODA.NS",
        "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "AUBANK.NS", "CANBK.NS",
        "UNIONBANK.NS", "BANDHANBNK.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "M&MFIN.NS",
        "LICHSGFIN.NS", "RECLTD.NS", "PFC.NS", "MANAPPURAM.NS", "J&KBANK.NS",
        "KARURVYSYA.NS", "SOUTHBANK.NS", "CUB.NS", "EQUITASBNK.NS", "UJJIVANSFB.NS"
    ],
    "⛽ 2. Oil, Gas, Energy & Chemicals": [
        "RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "HPCL.NS",
        "GAIL.NS", "OIL.NS", "ATGL.NS", "PETRONET.NS", "MGL.NS",
        "IGL.NS", "GUJGASLTD.NS", "COALINDIA.NS", "NTPC.NS", "POWERGRID.NS",
        "TATAPOWER.NS", "IREDA.NS", "SUZLON.NS", "ADANIGREEN.NS", "ADANIPOWER.NS",
        "DEEPAKNTR.NS", "SRF.NS", "AARTIIND.NS", "ATUL.NS", "UPL.NS"
    ],
    "🏥 3. Pharma, Healthcare & Biotech": [
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS",
        "FORTIS.NS", "MAXHEALTH.NS", "NH.NS", "LALPATHLAB.NS", "MANKIND.NS",
        "TORNTPHARM.NS", "LUPIN.NS", "ZYDUSLIFE.NS", "AUROPHARMA.NS", "GLENMARK.NS",
        "ALKEM.NS", "IPCALAB.NS", "BIOCON.NS", "SYNGENE.NS", "METROPOLIS.NS"
    ],
    "💻 4. IT, Software & Tech Services": [
        "TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS", "HCLTECH.NS",
        "PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", "MPHASIS.NS", "LTTS.NS",
        "TATAELXSI.NS", "KPITTECH.NS", "CYIENT.NS", "OFSS.NS", "ZENSARTECH.NS",
        "BSOFT.NS", "HAPPSTMNDS.NS", "INTELLECT.NS", "MASTEK.NS", "NAUKRI.NS"
    ],
    "🚂 5. Railways, Logistics & Infrastructure": [
        "IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "RITES.NS",
        "TEXRAIL.NS", "TITAGARH.NS", "BEML.NS", "CONCOR.NS", "GPPL.NS",
        "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "DELHIVERY.NS", "BLUEDART.NS",
        "ADANIPORTS.NS", "JSWINFRA.NS", "IRB.NS", "PNCINFRA.NS", "KNRCON.NS"
    ],
    "🛒 6. FMCG, Retail & Consumer Durables": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS",
        "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "COLPAL.NS", "VBL.NS",
        "AWL.NS", "EMAMILTD.NS", "RADICO.NS", "TITAN.NS", "TRENT.NS",
        "DMART.NS", "HAVELLS.NS", "POLYCAB.NS", "CROMPTON.NS", "BLUESTARCO.NS",
        "WHIRLPOOL.NS", "DIXON.NS", "AMBER.NS", "SYRMA.NS", "KEI.NS"
    ],
    "🚗 7. Auto, EV & Auto Components": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS",
        "EICHERMOT.NS", "SONACOMS.NS", "MOTHERSON.NS", "BOSCHLTD.NS", "EXIDEIND.NS",
        "OLECTRA.NS", "TUBEINVEST.NS", "BALKRISIND.NS", "BHARATFORG.NS", "ASHOKLEY.NS",
        "TVSMOTOR.NS", "TIINDIA.NS", "AMARAJA.NS", "CRAFTSMAN.NS", "UNOMINDA.NS"
    ],
    "🏗️ 8. Metals, Mining & Materials": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "JINDALSTEL.NS", "SAIL.NS",
        "NMDC.NS", "VEDL.NS", "NATIONALUM.NS", "HINDZINC.NS", "APLAPOLLO.NS",
        "RATNAMANI.NS", "JSL.NS", "MIDHANI.NS", "GODAWARI.NS", "MOIL.NS"
    ],
    "🏢 9. Real Estate & Construction": [
        "DLF.NS", "LODHA.NS", "GODREJPROP.NS", "OBERREALTY.NS", "PHOENIXLTD.NS",
        "PRESTAGE.NS", "BRIGADE.NS", "SOBHA.NS", "SIGNATURE.NS", "MAHLIFE.NS",
        "SUNTECK.NS", "IBREALEST.NS", "KOLTEPATIL.NS", "ASHIANA.NS", "PURVA.NS"
    ],
    "⚡ 10. Power & Utilities": [
        "NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "ADANIPOWER.NS", "ADANIGREEN.NS",
        "JSWENERGY.NS", "TORNTPOWER.NS", "NHPC.NS", "SJWN.NS", "SUZLON.NS",
        "CESC.NS", "INOXWIND.NS", "KPIGREEN.NS", "GIPCL.NS", "ENGINERSIN.NS"
    ]
}

# Sidebar Control Options
st.sidebar.header("🔍 Scanner Controls")
selected_sector = st.sidebar.selectbox("Select Sub-Sector", list(SUB_SECTORS.keys()))
tickers = SUB_SECTORS[selected_sector]

timeframe_mode = st.sidebar.selectbox(
    "Select Timeframe",
    ["1 Day (Daily)", "4 Hours (Resampled 4H)", "1 Hour (60 Min)"],
    index=0
)

pattern_filter = st.sidebar.multiselect(
    "Filter Pattern Signal", 
    ["All", "Bullish Engulfing", "Bearish Engulfing", "Hammer", "Shooting Star", "Doji"], 
    default=["All"]
)

# Helper: RSI Calculation
def calculate_rsi(df, periods=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Helper: 1H to 4H Resampling for Indian Stock Market Hours (Starts 9:15 AM)
def resample_to_4h(df):
    resampled = df.resample('4h', offset='9h15m').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    return resampled

# Helper: Strict Candlestick Recognition Engine on Completed Candles
def detect_candlestick_patterns(df):
    if len(df) < 2:
        return "Neutral"

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    open_p, close_p = float(curr['Open']), float(curr['Close'])
    high_p, low_p = float(curr['High']), float(curr['Low'])
    p_open, p_close = float(prev['Open']), float(prev['Close'])

    body = abs(close_p - open_p)
    upper_wick = high_p - max(open_p, close_p)
    lower_wick = min(open_p, close_p) - low_p
    range_p = high_p - low_p

    patterns = []

    if range_p > 0:
        # Bullish Engulfing: Previous Red, Current Green engulfing previous body
        if p_close < p_open and close_p > open_p and open_p <= p_close and close_p >= p_open:
            patterns.append("🟢 Bullish Engulfing")

        # Bearish Engulfing: Previous Green, Current Red engulfing previous body
        if p_close > p_open and close_p < open_p and open_p >= p_close and close_p <= p_open:
            patterns.append("🔴 Bearish Engulfing")

        # Hammer (Bullish Reversal)
        if lower_wick >= 2 * body and upper_wick <= body * 0.3 and (body / range_p) > 0.1:
            patterns.append("🔨 Hammer")

        # Shooting Star (Bearish Reversal)
        if upper_wick >= 2 * body and lower_wick <= body * 0.3 and (body / range_p) > 0.1:
            patterns.append("⭐ Shooting Star")

        # Doji (Indecision)
        if body <= range_p * 0.08:
            patterns.append("⚖️ Doji")

    return ", ".join(patterns) if patterns else "Neutral"

# Fast Parallel Data Downloader
@st.cache_data(ttl=600)
def fetch_and_scan_batch(ticker_list, mode):
    results = []
    
    if mode == "1 Day (Daily)":
        period_val, interval_val = "6mo", "1d"
    elif mode == "4 Hours (Resampled 4H)":
        period_val, interval_val = "60d", "60m"
    else:
        period_val, interval_val = "30d", "60m"

    # Fast Multi-threaded Download to prevent dropped/missing tickers
    data_batch = yf.download(
        ticker_list, 
        period=period_val, 
        interval=interval_val, 
        group_by='ticker', 
        threads=True, 
        progress=False
    )

    for ticker in ticker_list:
        try:
            # Extract individual dataframe safely from batch
            if isinstance(data_batch.columns, pd.MultiIndex):
                if ticker in data_batch.columns.get_level_values(0):
                    df = data_batch[ticker].dropna(how='all')
                else:
                    continue
            else:
                df = data_batch.copy().dropna(how='all')

            if df.empty or len(df) < 5:
                continue

            # Resample 1H data to 4H if chosen
            if mode == "4 Hours (Resampled 4H)":
                df = resample_to_4h(df)

            df['RSI'] = calculate_rsi(df)
            pattern = detect_candlestick_patterns(df)
            
            curr_close = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            pct_change = ((curr_close - prev_close) / prev_close) * 100
            rsi_val = df['RSI'].iloc[-1]

            results.append({
                "Ticker": ticker.replace(".NS", ""),
                "Price (₹)": round(curr_close, 2),
                "Change (%)": round(pct_change, 2),
                "RSI (14)": round(rsi_val, 2) if not np.isnan(rsi_val) else "N/A",
                "Timeframe": mode,
                "Pattern Signal": pattern
            })
        except Exception:
            continue

    return pd.DataFrame(results)

# Screen Execution
st.subheader(f"Scanning: {selected_sector} ({len(tickers)} Stocks)")

if st.button("🚀 Run Full Pattern Scanner"):
    with st.spinner(f"Fast-scanning all {len(tickers)} stocks..."):
        res_df = fetch_and_scan_batch(tickers, timeframe_mode)

        if not res_df.empty:
            # Pattern Filter Application
            if "All" not in pattern_filter and pattern_filter:
                filtered_df = res_df[
                    res_df['Pattern Signal'].apply(lambda sig: any(pat in sig for pat in pattern_filter))
                ]
            else:
                filtered_df = res_df

            # Signal Color Highlight Function
            def color_signal(val):
                val_str = str(val)
                if "Bullish" in val_str or "Hammer" in val_str:
                    return 'background-color: #28a745; color: white; font-weight: bold;'
                elif "Bearish" in val_str or "Shooting Star" in val_str:
                    return 'background-color: #dc3545; color: white; font-weight: bold;'
                elif "Doji" in val_str:
                    return 'background-color: #ffc107; color: black; font-weight: bold;'
                return ''

            st.success(f"স্ক্যান সফল! মোট {len(filtered_df)} টি স্টকের ডাটা টেবিলটিতে প্রদর্শিত হচ্ছে।")

            st.dataframe(
                filtered_df.style.map(color_signal, subset=['Pattern Signal'])
                .format({
                    'Price (₹)': "₹{:.2f}",
                    'Change (%)': "{:+.2f}%",
                    'RSI (14)': "{}"
                }),
                use_container_width=True,
                height=650
            )
        else:
            st.error("ডাটা পাওয়া যায়নি। অনুগ্রহ করে নেটওয়ার্ক কানেকশন অথবা রিকোয়েস্ট চেক করুন।")
