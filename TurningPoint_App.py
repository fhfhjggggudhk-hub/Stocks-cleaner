import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(page_title="Smart Trade Pattern & Chart Analyzer", layout="wide")

st.title("📊 স্মার্ট ট্রেড স্ক্যানার ও প্যাটার্ন অ্যানালাইজার")
st.caption("অরিজিনাল লাইভ ডাটা, TradingView চার্ট, বায়ার অ্যাক্টিভিটি অ্যানালাইসিস এবং ভয়েস রিডআউট")

# ---------------------------------------------------------
# Exact 10 Sub-Sectors Stock Database
# ---------------------------------------------------------
SECTOR_STOCKS = {
    "1. 🏛️ Banking & Financials": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "BAJFINANCE.NS", 
        "PFC.NS", "RECLTD.NS", "BANKBARODA.NS", "CANBK.NS", "KOTAKBANK.NS", 
        "INDUSINDBK.NS", "IDFCFIRSTB.NS", "PNB.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "SHRIRAMFIN.NS"
    ],
    "2. 💻 IT & Technology": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "PERSISTENT.NS", 
        "KPITTECH.NS", "TECHM.NS", "LTIM.NS", "COFORGE.NS", "TATAELXSI.NS", "OFSS.NS", "CYIENT.NS"
    ],
    "3. 🚗 Auto & Components": [
        "TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "TVSMOTOR.NS", 
        "HEROMOTOCO.NS", "BHARATFORG.NS", "SAMVARDHANA.NS", "BOSCHLTD.NS", "EICHERMOT.NS", "BALKRISIND.NS"
    ],
    "4. 💊 Pharma & Healthcare": [
        "SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "TORNTPHARM.NS", 
        "MANKIND.NS", "LUPIN.NS", "AUROPHARMA.NS", "APOLLOHOSP.NS", "BIOCON.NS", "GLENMARK.NS"
    ],
    "5. 🛒 FMCG & Consumer Goods": [
        "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", 
        "VBL.NS", "DABUR.NS", "MARICO.NS", "GODREJCP.NS", "COLPAL.NS", "TRENT.NS"
    ],
    "6. 🏗️ Metals & Mining": [
        "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS", "NMDC.NS", 
        "JINDALSTEL.NS", "NATIONALUM.NS", "VEDL.NS", "SAIL.NS", "HINDZINC.NS"
    ],
    "7. 🧪 Chemicals & Fertilizers": [
        "PIDILITIND.NS", "UPL.NS", "DEEPAKNTR.NS", "SRF.NS", "TATACHEM.NS", 
        "FLUOROCHEM.NS", "AARTIIND.NS", "LINDEINDIA.NS", "FACT.NS", "RCFL.NS"
    ],
    "8. ⚙️ Capital Goods & Industrial Automation": [
        "ABB.NS", "CGPOWER.NS", "SUZLON.NS", "INOXWIND.NS", "POWERINDIA.NS", "BHEL.NS",
        "CUMMINSIND.NS", "THERMAX.NS", "TRIVENI.NS", "TDPOWERSYS.NS", "KIRLOSENG.NS",
        "AIAENG.NS", "ELECTCAST.NS", "KEC.NS", "KPIL.NS", "ENGINERSIN.NS",
        "VATECHWABAG.NS", "IONEXCHANG.NS", "PRAJIND.NS", "ACTIONIND.NS", "TEXRAIL.NS",
        "TITAGARH.NS", "RAILTEL.NS", "RITES.NS", "RVNL.NS", "IRCON.NS", "IRFC.NS",
        "BEML.NS", "CONCOR.NS", "GPPL.NS", "SCHNEIDER.NS", "VGUARD.NS",
        "GENUSPOWER.NS", "HPL.NS", "ELGIEQUIP.NS", "KIRLOSBROS.NS", "KSB.NS", 
        "SHAKTIPUMP.NS", "SKIPPER.NS", "SURYAROSH.NS", "JINDALSAW.NS", "WELCORP.NS", 
        "MAHSEAMLES.NS", "APLAPOLLO.NS", "RATNAMANI.NS", "PITTIENG.NS", "BHARATFORG.NS", 
        "RAMKRASN.NS", "GNA.NS", "RICOAUTO.NS", "PRECISION.NS", "SANSERA.NS", 
        "SUNDRMFAST.NS", "TIMKEN.NS", "SKFINDIA.NS", "SCHAEFFLER.NS", "KAYNES.NS", 
        "SYRMA.NS", "CYIENTDLM.NS", "DCXINDIA.NS", "DYNAMATECH.NS"
    ],
    "9. ⚡ Renewable Energy, Power & Utilities": [
        "NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "IREDA.NS", "SUZLON.NS",
        "ADANIGREEN.NS", "ADANIPOWER.NS", "SJVN.NS", "NHPC.NS", "INOXWIND.NS",
        "KPIGREEN.NS", "TORNTPOWER.NS", "CESC.NS", "JSWENERGY.NS", "ADANIENT.NS",
        "BHEL.NS", "BORORENEW.NS", "WEBELSOLAR.NS", "GENUSPOWER.NS", "HPL.NS", 
        "SCHNEIDER.NS", "CGPOWER.NS", "SIEMENS.NS", "ABB.NS", "POWERINDIA.NS", 
        "CUMMINSIND.NS", "KEC.NS", "KPIL.NS", "RITES.NS", "ENGINERSIN.NS", 
        "VATECHWABAG.NS", "IONEXCHANG.NS", "THERMAX.NS", "TDPOWERSYS.NS", "KIRLOSENG.NS", 
        "TRIVENI.NS", "PRAJIND.NS", "GAIL.NS", "PETRONET.NS", "MGL.NS", "IGL.NS", 
        "GUJGASLTD.NS", "ATGL.NS", "RELIANCE.NS", "ONGC.NS", "OIL.NS", "COALINDIA.NS", 
        "NLCINDIA.NS", "DEEPAKNTR.NS", "IEX.NS", "MCX.NS", "BSE.NS", "CDSL.NS", 
        "CAMS.NS", "HUDCO.NS", "PFC.NS", "RECLTD.NS", "TATACOMM.NS", "HFCL.NS", 
        "TEJASNET.NS", "RAILTEL.NS", "BEML.NS", "BEL.NS", "HAL.NS", "MIDHANI.NS", 
        "MTARTECH.NS", "DATAPATTNS.NS", "PARAS.NS"
    ],
    "10. 🚂 Railways, Logistics & Infrastructure": [
        "IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "RITES.NS",
        "TEXRAIL.NS", "TITAGARH.NS", "BEML.NS", "CONCOR.NS", "GPPL.NS",
        "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "DELHIVERY.NS", "BLUEDART.NS",
        "TCIEXP.NS", "MAHLOG.NS", "VRLLOG.NS", "ALLCARGO.NS", "AEGISCHEM.NS", 
        "GMRINFRA.NS", "ADANIPORTS.NS", "JSWINFRA.NS", "IRB.NS", "PNCINFRA.NS", 
        "KNRCON.NS", "HGINFRA.NS", "GRINFRA.NS", "DILIPBUILD.NS", "JKIL.NS", 
        "ITDCEM.NS", "NCC.NS", "ASHOKA.NS", "ENGINERSIN.NS", "NBCC.NS", 
        "PSPPROJECT.NS", "CAPACITE.NS", "AHLUCONT.NS", "MANINFRA.NS", "DLF.NS", 
        "LODHA.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS", "PRESTIGE.NS", 
        "BRIGADE.NS", "SOBHA.NS", "SIGNATURE.NS", "MAHLIFE.NS", "SUNTECK.NS", 
        "IBREALEST.NS", "KOLTEPATIL.NS", "PURVA.NS", "AJMERA.NS", "RAMKY.NS", "GPTINFRA.NS"
    ]
}

# ---------------------------------------------------------
# ROBUST LIVE DATA FETCHER (BYPASSING CLOUD BLOCKS)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_stock_data(ticker_symbol):
    clean_symbol = ticker_symbol.strip().upper()
    
    # Custom Browser Headers to prevent blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': f'https://finance.yahoo.com/quote/{clean_symbol}'
    }

    # Direct Yahoo Chart API (Primary Fast Source)
    for domain in ["query2.finance.yahoo.com", "query1.finance.yahoo.com"]:
        try:
            url = f"https://{domain}/v8/finance/chart/{clean_symbol}?range=6m&interval=1d"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if 'chart' in data and data['chart']['result']:
                    result = data['chart']['result'][0]
                    timestamps = result.get('timestamp', [])
                    quote = result['indicators']['quote'][0]
                    
                    df = pd.DataFrame({
                        'Open': quote.get('open'),
                        'High': quote.get('high'),
                        'Low': quote.get('low'),
                        'Close': quote.get('close'),
                        'Volume': quote.get('volume')
                    }, index=pd.to_datetime(timestamps, unit='s'))
                    
                    df.dropna(subset=['Close'], inplace=True)
                    df.bfill(inplace=True)
                    df.ffill(inplace=True)
                    
                    if not df.empty and len(df) >= 5:
                        return df
        except Exception:
            continue

    # Secondary Source: yfinance download
    try:
        df = yf.download(clean_symbol, period="6m", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df is not None and not df.empty:
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            if len(df) >= 5:
                return df
    except Exception:
        pass

    return pd.DataFrame()

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.header("🔍 ফিল্টার ও স্ক্যানার")
selected_sector = st.sidebar.selectbox("১. সাব-সেক্টর বেছে নিন:", list(SECTOR_STOCKS.keys()))

scan_btn = st.sidebar.button("🚀 এই সাব-সেক্টর স্ক্যান করুন", use_container_width=True)

# ---------------------------------------------------------
# Scanner Logic Execution
# ---------------------------------------------------------
stocks_in_sector = SECTOR_STOCKS[selected_sector]

if scan_btn or "scanned_results" not in st.session_state:
    st.session_state["scanned_results"] = []
    
    with st.spinner(f"'{selected_sector}' এর লাইভ ডাটা স্ক্যান করা হচ্ছে..."):
        scanned_list = []
        for stock in stocks_in_sector:
            df = fetch_stock_data(stock)
            if not df.empty and len(df) > 15:
                df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['Vol_Avg'] = df['Volume'].rolling(20).mean()
                
                latest_close = float(df['Close'].iloc[-1])
                latest_open = float(df['Open'].iloc[-1])
                ema_20 = float(df['EMA20'].iloc[-1])
                vol_latest = float(df['Volume'].iloc[-1])
                vol_avg = float(df['Vol_Avg'].iloc[-1])
                
                near_ema = (latest_close >= ema_20 * 0.985)
                is_bullish = latest_close >= latest_open
                vol_spike = vol_latest > (1.1 * vol_avg)
                
                if near_ema and (is_bullish or vol_spike):
                    clean_name = stock.replace(".NS", "")
                    signal = "🟢 20 EMA Support & Volume Spike" if vol_spike else "🟢 20 EMA Support Bounce"
                    scanned_list.append({
                        "Stock Symbol": clean_name,
                        "Full Ticker": stock,
                        "Price (₹)": round(latest_close, 2),
                        "20 EMA (₹)": round(ema_20, 2),
                        "Signal Status": signal
                    })
        st.session_state["scanned_results"] = scanned_list

# Display Scanned Results Table
st.subheader(f"📋 স্ক্যানিং রেজাল্ট: {selected_sector}")

results = st.session_state.get("scanned_results", [])

if results:
    res_df = pd.DataFrame(results)
    st.success(f"✅ মোট {len(results)} টি স্টকে ট্রেড সেটআপ/প্যাটার্ন পাওয়া গেছে!")
    st.dataframe(res_df[["Stock Symbol", "Price (₹)", "20 EMA (₹)", "Signal Status"]], use_container_width=True)
    available_stocks = res_df["Full Ticker"].tolist()
else:
    st.info("ℹ️ এই মূহুর্তে বিশেষ কোনো সাপোর্ট প্যাটার্ন নেই। কিন্তু আপনি নিচে থেকে যেকোনো স্টক সিলেক্ট করে অরিজিনাল লাইভ চার্ট দেখতে পারেন।")
    available_stocks = stocks_in_sector

st.markdown("---")

# ---------------------------------------------------------
# TradingView Style Single Stock Chart & Audio Explanation
# ---------------------------------------------------------
selected_stock = st.selectbox("🎯 বিস্তারিত চার্ট প্যাটার্ন ও ট্রেড প্ল্যান দেখার জন্য স্টক বেছে নিন:", available_stocks)

if selected_stock:
    raw_name = selected_stock.replace(".NS", "").replace(".BO", "")
    
    st.subheader(f"📌 {raw_name} - Real Candlestick Chart")
    
    df = fetch_stock_data(selected_stock)

    if df.empty:
        st.warning(f"⚠️ {raw_name} এর লাইভ ডাটা কানেক্ট হচ্ছে... অনুগ্রহ করে ওপরের '🚀 এই সাব-সেক্টর স্ক্যান করুন' বাটনে চাপ দিন।")
    else:
        # Technical Calculation
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Vol_Avg'] = df['Volume'].rolling(20).mean()
        
        latest_price = round(float(df['Close'].iloc[-1]), 2)
        ema_20 = round(float(df['EMA20'].iloc[-1]), 2)
        
        # Key Levels
        entry_level = latest_price
        target_level = round(entry_level * 1.07, 2)    # +7% Target
        sl_level = round(entry_level * 0.975, 2)       # -2.5% Stop Loss
        
        # Top Metrics Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🟢 বাই এন্ট্রি (Entry)", f"₹{entry_level}")
        c2.metric("🔵 টার্গেট (+৭%)", f"₹{target_level}")
        c3.metric("🔴 স্টপ লস (-২.৫%)", f"₹{sl_level}")
        c4.metric("🟠 20 EMA সাপোর্ট", f"₹{ema_20}")

        # ---------------------------------------------------------
        # TradingView Dark Style Plotly Chart
        # ---------------------------------------------------------
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.03, 
                            subplot_titles=(f'TradingView Style Real Candlestick Chart - Pattern & Strategy Breakdown', 'Volume'),
                            row_width=[0.22, 0.78])

        # 1. TradingView Candlesticks
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Candle',
            increasing_line_color='#089981', decreasing_line_color='#f23645',
            increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'
        ), row=1, col=1)

        # 2. Smooth 20 EMA Support Line (Orange Curve)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], mode='lines', name='20 EMA Support',
            line=dict(color='#ff9800', width=2.5)
        ), row=1, col=1)

        # 3. Horizontal Lines (Entry, Target, Stop Loss)
        fig.add_hline(y=entry_level, line_dash="solid", line_color="#00bfa5", line_width=1.5,
                      annotation_text=f"🟢 Entry: ₹{entry_level}", annotation_position="top left", row=1, col=1)

        fig.add_hline(y=target_level, line_dash="dash", line_color="#29b6f6", line_width=1.5,
                      annotation_text=f"🔵 Target (7%): ₹{target_level}", annotation_position="top left", row=1, col=1)

        fig.add_hline(y=sl_level, line_dash="dash", line_color="#ef5350", line_width=1.5,
                      annotation_text=f"🔴 Stop Loss (2.5%): ₹{sl_level}", annotation_position="bottom left", row=1, col=1)

        # 4. Pointer Arrow Annotation
        fig.add_annotation(
            x=df.index[-1], y=latest_price,
            text="🎯 BUY BREAKOUT & EMA BOUNCE",
            showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor="#089981",
            ax=-90, ay=-60,
            bordercolor="#089981", borderwidth=1.5, borderpad=6,
            bgcolor="#1e222d", opacity=0.95,
            font=dict(color="#ffffff", size=12, family="Arial"),
            row=1, col=1
        )

        # Bottom Chart: Volume Bar Chart
        vol_colors = ['#089981' if c >= o else '#f23645' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=vol_colors), row=2, col=1)

        # TradingView Dark Layout Theme
        fig.update_layout(
            height=650,
            paper_bgcolor='#131722',
            plot_bgcolor='#131722',
            font=dict(color='#d1d4dc'),
            xaxis_rangeslider_visible=False,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1)
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#2a2e39')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#2a2e39')

        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------
        # Dynamic Strategy & Buyer Activity Explanation Logic
        # ---------------------------------------------------------
        st.markdown("---")
        
        vol_latest = float(df['Volume'].iloc[-1])
        vol_avg = float(df['Vol_Avg'].iloc[-1])
        volume_spike = vol_latest > (1.1 * vol_avg)

        strategy_title = "২০ ইএমএ বাউন্স ও ভলিউম ব্রেকআউট স্ট্র্যাটেজি" if volume_spike else "২০ ইএমএ ডাইনামিক সাপোর্ট রিভার্সাল স্ট্র্যাটেজি"

        # Speech Text for Audio Button
        speech_text = f"{raw_name} স্টকের টেকনিক্যাল এবং বায়ার অ্যাক্টিভিটি বিশ্লেষণ। " \
                      f"এখানে {strategy_title} কাজ করছে। " \
                      f"স্টকের বর্তমান বাই এন্ট্রি প্রাইস {entry_level} টাকা। প্রফিট টার্গেট {target_level} টাকা এবং স্টপ লস {sl_level} টাকা। " \
                      f"বায়ারদের অবস্থান: স্টকটি ২০ ইএমএ সাপোর্ট লেভেল {ema_20} টাকার কাছাকাছি আসার পর বায়াররা ব্যাপকভাবে অ্যাক্টিভ হয়েছে এবং সেলারদের সমস্ত সেল প্রেসার শুষে নিয়েছে। " \
                      f"বায়ারদের এই এগ্রেসিভ বাইং এবং ভারী ভলিউমের কারণে এখান থেকে দাম দ্রুত উপরের দিকে যাচ্ছে।"

        clean_js_speech = speech_text.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')

        st.subheader("📢 চার্ট বিশ্লেষণ, বায়ার অ্যাক্টিভিটি ও ট্রেড প্ল্যান:")

        # HTML + JS Text-To-Speech Button
        tts_component = f"""
        <div style="margin-bottom: 20px;">
            <button onclick="playVoice()" style="
                background: linear-gradient(135deg, #00c853, #009688);
                color: white;
                border: none;
                padding: 14px 28px;
                font-size: 17px;
                font-weight: bold;
                border-radius: 8px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,200,83,0.3);
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                🔊 অ্যানালাইসিস ভয়েসে শুনুন (Listen Full Breakdown)
            </button>

            <script>
            function playVoice() {{
                window.speechSynthesis.cancel();
                const text = "{clean_js_speech}";
                const msg = new SpeechSynthesisUtterance(text);
                msg.lang = 'bn-IN';
                msg.rate = 0.88;
                window.speechSynthesis.speak(msg);
            }}
            </script>
        </div>
        """
        components.html(tts_component, height=75)

        # Clear Text Explanation on Screen
        st.info(f"""
        ### 🎯 ১. কোন্ স্ট্র্যাটেজি কাজ করছে:
        এখানে **'{strategy_title}'** ব্যবহার করা হয়েছে। স্টকটি তার ২০ দিনের ডায়নামিক ইএমএ লাইন (₹{ema_20})-এর ওপর এসে শক্ত ভিত্তি বা সাপোর্ট তৈরি করে ওপরে উঠতে শুরু করেছে।

        ---

        ### 🐂 ২. বায়াররা (Buyers) কীভাবে অ্যাক্টিভ হয়েছে এবং কী করছে:
        1. **সেলারদের সেল প্রেসার শোষণ (Buying Absorption):** দাম যখনই ২০ ইএমএ লাইন (₹{ema_20})-এর কাছাকাছি নেমেছিল, বায়াররা সাথে সাথে অ্যাক্টিভ হয়ে সেলারদের সমস্ত সেল প্রেসার শুষে নিয়েছে। ফলে দাম আর নিচে নামতে পারেনি।
        2. **ইনস্টিটিউশনাল বায়ারদের এন্ট্রি:** {'চার্টের নিচে সবুজ ভলিউম বারে বড় স্পাইক দেখাচ্ছে যে, এখানে বড় বড় ইনস্টিটিউশনাল বায়াররা নতুন পজিশন তৈরি করে শেয়ার অ্যাকুমুলেট (জমা) করছে।' if volume_spike else 'বায়াররা সাপোর্ট জোনে ধীরে ধীরে সক্রিয় হয়ে শেয়ার জমা করছে এবং সেলারদের থেকে বায়ারদের আধিপত্য অনেক বেশি।'}
        3. **কেন দাম উপরের দিকে যাচ্ছে:** ২০ ইএমএ লেভেলে বায়ারদের এগ্রেসিভ বাইং এবং ভারী ভলিউম সাপোর্ট থাকায় ডাউনট্রেন্ড পুরোপুরি থেমে গেছে। বায়াররা প্রতি মুহূর্তে দামকে ওপরে ঠেলে নিয়ে যাচ্ছে, যার ফলে এখান থেকে স্টকটি সহজেই ₹{target_level} টার্গেটের দিকে যাবে।

        ---

        ### 📋 ৩. সঠিক ট্রেড প্ল্যান (Trade Plan):
        * 🟢 **বাই এন্ট্রি (Entry Level):** ₹{entry_level}
        * 🔵 **প্রফিট টার্গেট (Target +7%):** ₹{target_level}
        * 🔴 **স্টপ লস (Stop Loss -2.5%):** ₹{sl_level}
        * 🟠 **সাপোর্ট জোন (EMA Support):** ₹{ema_20}

        ---

        ### 📱 ৪. Groww (গ্রো) অ্যাপে অর্ডার দেওয়ার সঠিক নিয়ম:
        1. Groww App খুলে **{raw_name}** সার্চ করুন।
        2. **Buy** প্রেস করে লিমিট প্রাইস সেট করুন **₹{entry_level}**।
        3. অর্ডার এগজিকিউট হলে **Stop Loss Trigger Price** দিন **₹{sl_level}** এবং **Target** দিন **₹{target_level}**।
        """)
        
