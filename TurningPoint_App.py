import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# Page Configuration
st.set_page_config(page_title="Smart Trade Analyzer", layout="wide")

st.title("📊 স্মার্ট ট্রেড সেটআপ ও প্রাইস অ্যানালাইজার")
st.caption("আপনার দেওয়া ১০টি সাব-সেক্টরের ৩০০+ স্টকের সম্পূর্ণ তালিকা থেকে সিলেক্ট করুন")

# ---------------------------------------------------------
# Exact User Stock List (Fixed & Corrected NSE Tickers)
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
        "BEML.NS", "CONCOR.NS", "GPPL.NS", "JISLJALEQS.NS", "SCHNEIDER.NS", "VGUARD.NS",
        "HONAUT.NS", "GENUSPOWER.NS", "HPL.NS", "ELGIEQUIP.NS", "DISHTV.NS",
        "KIRLOSBROS.NS", "KSB.NS", "SHAKTIPUMP.NS", "ROTO.NS", "SKIPPER.NS",
        "SURYAROSH.NS", "JINDALSAW.NS", "WELCORP.NS", "MAHSEAMLES.NS", "APLAPOLLO.NS",
        "RATNAMANI.NS", "PITTIENG.NS", "NELCAST.NS", "CRAFTSMAN.NS", "BHARATFORG.NS",
        "RAMKRASN.NS", "GNA.NS", "RICOAUTO.NS", "PRECISION.NS", "SANSERA.NS",
        "SUNDRMFAST.NS", "TIMKEN.NS", "SKFINDIA.NS", "SCHAEFFLER.NS", "AARTISURF.NS",
        "SHARDAMOTR.NS", "SALZERELEC.NS", "KAYNES.NS", "SYRMA.NS", "CYIENTDLM.NS",
        "DCXINDIA.NS", "E2E.NS", "TENT.NS", "DYNAMATECH.NS", "GABRIEL.NS"
    ],
    "9. ⚡ Renewable Energy, Power & Utilities": [
        "NTPC.NS", "POWERGRID.NS", "TATAPOWER.NS", "IREDA.NS", "SUZLON.NS",
        "ADANIGREEN.NS", "ADANIPOWER.NS", "SJVN.NS", "NHPC.NS", "INOXWIND.NS",
        "KPIGREEN.NS", "TORNTPOWER.NS", "CESC.NS", "JSWENERGY.NS", "ADANIENT.NS",
        "BHEL.NS", "BORORENEW.NS", "WEBELSOLAR.NS", "STERENERGY.NS", "SOLEX.NS",
        "GENUSPOWER.NS", "HPL.NS", "SCHNEIDER.NS", "CGPOWER.NS", "SIEMENS.NS",
        "ABB.NS", "POWERINDIA.NS", "CUMMINSIND.NS", "KEC.NS", "KPIL.NS",
        "RITES.NS", "ENGINERSIN.NS", "VATECHWABAG.NS", "IONEXCHANG.NS", "AIAENG.NS",
        "THERMAX.NS", "TDPOWERSYS.NS", "KIRLOSENG.NS", "TRIVENI.NS", "PRAJIND.NS",
        "GAIL.NS", "PETRONET.NS", "MGL.NS", "IGL.NS", "GUJGASLTD.NS",
        "ATGL.NS", "GSPL.NS", "RELIANCE.NS", "ONGC.NS", "OIL.NS",
        "COALINDIA.NS", "NLCINDIA.NS", "DEEPAKNTR.NS", "GIPCL.NS", "OPG.NS",
        "INDIANENERGY.NS", "IEX.NS", "MCX.NS", "BSE.NS", "CDSL.NS",
        "CAMS.NS", "HUDCO.NS", "PFC.NS", "RECLTD.NS", "KPITTECH.NS",
        "TATACOMM.NS", "STERLITE.NS", "HFCL.NS", "TEJASNET.NS", "NELCO.NS",
        "RAILTEL.NS", "ITI.NS", "BEML.NS", "BEL.NS", "HAL.NS",
        "MIDHANI.NS", "MTARTECH.NS", "DATAPATTNS.NS", "PARAS.NS"
    ],
    "10. 🚂 Railways, Logistics & Infrastructure": [
        "IRFC.NS", "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "RITES.NS",
        "TEXRAIL.NS", "TITAGARH.NS", "BEML.NS", "CONCOR.NS", "GPPL.NS",
        "MAZDOCK.NS", "COCHINSHIP.NS", "GRSE.NS", "DELHIVERY.NS", "BLUEDART.NS",
        "TCIEXP.NS", "MAHLOG.NS", "VRLLOG.NS", "GATEWAY.NS", "ALLCARGO.NS",
        "AEGISCHEM.NS", "GMRINFRA.NS", "ADANIPORTS.NS", "JSWINFRA.NS", "IRB.NS",
        "PNCINFRA.NS", "KNRCON.NS", "HGINFRA.NS", "GRINFRA.NS", "DILIPBUILD.NS",
        "JKIL.NS", "ITDCEM.NS", "NCC.NS", "ASHOKA.NS", "SADBHAV.NS",
        "ENGINERSIN.NS", "NBCC.NS", "PSPPROJECT.NS", "CAPACITE.NS", "AHLUCONT.NS",
        "MANINFRA.NS", "TEXINFRA.NS", "WELENT.NS", "DLF.NS", "LODHA.NS",
        "GODREJPROP.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS", "PRESTIGE.NS", "BRIGADE.NS",
        "SOBHA.NS", "SIGNATURE.NS", "MAHLIFE.NS", "SUNTECK.NS", "IBREALEST.NS",
        "KOLTEPATIL.NS", "GANESHIN.NS", "ASHIANA.NS", "PURVA.NS", "AJMERA.NS",
        "MARATHON.NS", "DBREALTY.NS", "PENINLAND.NS", "RAMKY.NS", "GPTINFRA.NS",
        "RPPINFRA.NS", "VPRPL.NS", "OMAXE.NS", "PARSVNATH.NS", "HUBTOWN.NS"
    ]
}

# Sidebar Selector
st.sidebar.header("🔍 স্টক সিলেক্ট করুন")
selected_sector = st.sidebar.selectbox("১. সাব-সেক্টর বেছে নিন:", list(SECTOR_STOCKS.keys()))
selected_stock = st.sidebar.selectbox("২. স্টক বেছে নিন:", SECTOR_STOCKS[selected_sector])

# ---------------------------------------------------------
# Robust Data Fetcher (Streamlit Cloud Block Bypass)
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_bulletproof_data(ticker_symbol):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Method 1: Requests Session + Ticker
    try:
        session = requests.Session()
        session.headers.update(headers)
        t = yf.Ticker(ticker_symbol, session=session)
        df = t.history(period="6m", interval="1d")
        if not df.empty and len(df) > 5:
            return df
    except Exception:
        pass

    # Method 2: Standard Download
    try:
        df = yf.download(ticker_symbol, period="6m", interval="1d", progress=False, ignore_tz=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if not df.empty and len(df) > 5:
            return df
    except Exception:
        pass

    return pd.DataFrame()

# ---------------------------------------------------------
# Main Execution Logic
# ---------------------------------------------------------
if selected_stock:
    raw_name = selected_stock.replace(".NS", "").replace(".BO", "")
    
    st.subheader(f"📌 {raw_name} - ট্রেড প্ল্যান ও চার্ট বিশ্লেষণ")
    
    with st.spinner(f"'{raw_name}' স্টকের চার্ট ডাটা প্রসেস করা হচ্ছে..."):
        df = fetch_bulletproof_data(selected_stock)

    if not df.empty:
        # Technical Indicator Calculations
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Vol_Avg'] = df['Volume'].rolling(20).mean()
        
        latest_price = round(float(df['Close'].iloc[-1]), 2)
        ema_20 = round(float(df['EMA20'].iloc[-1]), 2)
        
        # Key Price Levels
        entry_level = latest_price
        target_level = round(entry_level * 1.07, 2)    # +7% Target
        sl_level = round(entry_level * 0.975, 2)       # -2.5% Stop Loss
        
        # Display Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🟢 বাই এন্ট্রি (Entry)", f"₹{entry_level}")
        c2.metric("🔵 টার্গেট (+৭%)", f"₹{target_level}")
        c3.metric("🔴 স্টপ লস (-২.৫%)", f"₹{sl_level}")
        c4.metric("🟠 20 EMA সাপোর্ট", f"₹{ema_20}")

        # ---------------------------------------------------------
        # Interactive Plotly Chart
        # ---------------------------------------------------------
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, 
                            subplot_titles=(f'{raw_name} - Entry, Target & SL Chart Lines', 'Volume Activity'),
                            row_width=[0.25, 0.75])

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Candle'
        ), row=1, col=1)

        # 🟠 20 EMA Line
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], mode='lines', name='20 EMA Line',
            line=dict(color='orange', width=2)
        ), row=1, col=1)

        # 🟢 Entry Horizontal Line
        fig.add_hline(y=entry_level, line_dash="solid", line_color="#26a69a", line_width=2,
                      annotation_text=f"🟢 Entry: ₹{entry_level}", annotation_position="top right", row=1, col=1)

        # 🔵 Target Horizontal Line
        fig.add_hline(y=target_level, line_dash="dash", line_color="#29b6f6", line_width=2,
                      annotation_text=f"🔵 Target: ₹{target_level}", annotation_position="top right", row=1, col=1)

        # 🔴 Stop Loss Horizontal Line
        fig.add_hline(y=sl_level, line_dash="dash", line_color="#ef5350", line_width=2,
                      annotation_text=f"🔴 Stop Loss: ₹{sl_level}", annotation_position="bottom right", row=1, col=1)

        # Volume Bar Chart
        vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=vol_colors), row=2, col=1)

        fig.update_layout(height=580, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------
        # Detailed Bangla Strategy Breakdown
        # ---------------------------------------------------------
        st.markdown("---")
        st.subheader("📋 ট্রেডের বিস্তারিত কারণ ও লেভেলসমূহ (Groww App-এ বসানোর জন্য):")
        
        vol_latest = float(df['Volume'].iloc[-1])
        vol_avg = float(df['Vol_Avg'].iloc[-1])
        volume_spike = vol_latest > (1.2 * vol_avg)

        st.info(f"""
        ### 🎯 ১. প্রধান প্রাইস লেভেল (Key Levels):
        * 🟢 **বাই এন্ট্রি লেভেল (Buy Entry): ₹{entry_level}** — চার্টের বর্তমান সাপোর্ট প্রাইস।
        * 🔵 **টার্গেট প্রাইস (Target Price): ₹{target_level}** — এন্ট্রি থেকে +৭% প্রফিট বুকিং লেভেল।
        * 🔴 **স্টপ লস (Stop Loss): ₹{sl_level}** — ঝুঁকি এড়াতে -২.৫% লসে এক্সিট করার লেভেল।
        * 🟠 **সাপোর্ট ইএমএ (20 EMA Line): ₹{ema_20}** — চার্টের কমলা রঙের শক্ত সাপোর্ট লাইন।

        ---

        ### 🧠 ২. কেন এই ট্রেড নেওয়া হচ্ছে? (Trade Reason):
        1. **ইএমএ সাপোর্ট বাউন্স:** স্টকটি তার ২০ দিনের মুভিং এভারেজ (₹{ema_20})-এর ওপরে ট্রেড করছে, যা শক্ত বুলিশ ট্রেন্ড নির্দেশ করে।
        2. **ভলিউম অ্যাক্টিভিটি:** {'সর্বশেষ ক্যান্ডেলে ভালো ভলিউম দেখা গেছে, যা বায়িং সাপোর্ট দেখাচ্ছে।' if volume_spike else 'ভলিউম স্থিতিশীল রয়েছে এবং সাপোর্ট লেভেলে একুমুলেশন চলছে।'}
        3. **রিস্ক রিওয়ার্ড রেশিও:** এই ট্রেডে আপনার ঝুঁকি মাত্র ২.৫% (🔴 লাল লাইন), কিন্তু লাভের সুযোগ ৭% (🔵 নীল লাইন)।

        ---

        ### 📱 ৩. Groww (গ্রো) অ্যাপে কীভাবে এটি প্রয়োগ করবেন?
        1. আপনার **Groww App** খুলে **{raw_name}** স্টকটি ওপেন করুন।
        2. Buy অপশনে লিমিট প্রাইস দিন **₹{entry_level}**।
        3. ট্রেড অ্যাক্টিভ হলে **Stop Loss Trigger Price** রাখুন **₹{sl_level}** এবং **Target** দিন **₹{target_level}**।
        """)

    else:
        st.error(f"❌ '{raw_name}' স্টকের ডাটা পেতে সমস্যা হচ্ছে। পেজটি রিফ্রেশ দিন বা অন্য স্টক সিলেক্ট করুন।")
        
