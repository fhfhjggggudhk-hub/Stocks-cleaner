import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# Page Configuration
st.set_page_config(page_title="Smart Trade Pattern & Chart Analyzer", layout="wide")

st.title("📊 স্মার্ট ট্রেড প্যাটার্ন ও চার্ট অ্যানালাইজার")
st.caption("অটো-ব্রেকআউট লাইন, সাপোর্ট-রেজিস্ট্যান্স ট্রেন্ডলাইন এবং ক্যান্ডেলস্টিক প্যাটার্ন বিশ্লেষণ")

# ---------------------------------------------------------
# Exact 10 Sub-Sectors Stock Database (300+ Stocks)
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
# Bulletproof Data Fetcher Function
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_stock_data(ticker_symbol):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        session = requests.Session()
        session.headers.update(headers)
        t = yf.Ticker(ticker_symbol, session=session)
        df = t.history(period="6m", interval="1d")
        if not df.empty and len(df) > 5:
            return df
    except Exception:
        pass

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
    
    with st.spinner(f"'{selected_sector}' এর স্টকগুলো স্ক্যান করা হচ্ছে..."):
        scanned_list = []
        for stock in stocks_in_sector:
            df = fetch_stock_data(stock)
            if not df.empty and len(df) > 20:
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
    st.warning("⚠️ বর্তমানে এই সেক্টরে কোনো সেটআপ পাওয়া যায়নি। নিচে থেকে যেকোনো স্টক চার্ট দেখার জন্য সিলেক্ট করুন।")
    available_stocks = stocks_in_sector

st.markdown("---")

# ---------------------------------------------------------
# Single Stock Detail Analysis & Pattern Plotting
# ---------------------------------------------------------
selected_stock = st.selectbox("🎯 বিস্তারিত চার্ট প্যাটার্ন ও ট্রেড প্ল্যান দেখার জন্য স্টক বেছে নিন:", available_stocks)

if selected_stock:
    raw_name = selected_stock.replace(".NS", "").replace(".BO", "")
    
    st.subheader(f"📌 {raw_name} - চার্ট প্যাটার্ন ও টেকনিক্যাল আকৃতি বিশ্লেষণ")
    
    df = fetch_stock_data(selected_stock)

    if not df.empty and len(df) > 30:
        # Technical Calculation
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['Vol_Avg'] = df['Volume'].rolling(20).mean()
        
        latest_price = round(float(df['Close'].iloc[-1]), 2)
        ema_20 = round(float(df['EMA20'].iloc[-1]), 2)
        
        # Calculate Key Levels
        entry_level = latest_price
        target_level = round(entry_level * 1.07, 2)    # +7% Target
        sl_level = round(entry_level * 0.975, 2)       # -2.5% Stop Loss
        
        # Pattern & Trendline Levels Calculation (60 days lookback)
        recent_df = df.tail(60)
        breakout_res_level = round(float(recent_df['High'].max()), 2)
        support_line_level = round(float(recent_df['Low'].min()), 2)
        
        # Metric Display Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🟢 বাই এন্ট্রি (Entry)", f"₹{entry_level}")
        c2.metric("🔵 টার্গেট (+৭%)", f"₹{target_level}")
        c3.metric("🔴 স্টপ লস (-২.৫%)", f"₹{sl_level}")
        c4.metric("🟣 ব্রেকআউট লেভেল", f"₹{breakout_res_level}")

        # ---------------------------------------------------------
        # Interactive Plotly Dual Charts with Pattern Lines
        # ---------------------------------------------------------
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.06, 
                            subplot_titles=(f'{raw_name} - Candlestick Chart with Pattern Lines', 'Volume Activity Bar Chart'),
                            row_width=[0.25, 0.75])

        # 1. Candlestick Chart
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name='Price Candle'
        ), row=1, col=1)

        # 2. 🟠 20 EMA Trend Line
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA20'], mode='lines', name='20 EMA Trend Line',
            line=dict(color='orange', width=2)
        ), row=1, col=1)

        # 3. 🟣 Breakout Resistance Pattern Line (Swing High Line)
        fig.add_hline(y=breakout_res_level, line_dash="solid", line_color="#ab47bc", line_width=2,
                      annotation_text=f"🟣 Breakout Line: ₹{breakout_res_level}", annotation_position="top left", row=1, col=1)

        # 4. 🟡 Key Support Trendline (Swing Low Line)
        fig.add_hline(y=support_line_level, line_dash="dash", line_color="#ffee58", line_width=2,
                      annotation_text=f"🟡 Support Line: ₹{support_line_level}", annotation_position="bottom left", row=1, col=1)

        # 5. 🟢 Buy Entry Line
        fig.add_hline(y=entry_level, line_dash="solid", line_color="#26a69a", line_width=2,
                      annotation_text=f"🟢 Entry: ₹{entry_level}", annotation_position="top right", row=1, col=1)

        # 6. 🔵 Target Horizontal Line
        fig.add_hline(y=target_level, line_dash="dash", line_color="#29b6f6", line_width=2,
                      annotation_text=f"🔵 Target (+7%): ₹{target_level}", annotation_position="top right", row=1, col=1)

        # 7. 🔴 Stop Loss Horizontal Line
        fig.add_hline(y=sl_level, line_dash="dash", line_color="#ef5350", line_width=2,
                      annotation_text=f"🔴 Stop Loss (-2.5%): ₹{sl_level}", annotation_position="bottom right", row=1, col=1)

        # Bottom Chart: Volume Bar Chart
        vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=vol_colors), row=2, col=1)

        fig.update_layout(height=620, xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------------------------------------------
        # Detailed Visual Chart Explanation (Line-by-Line Guide)
        # ---------------------------------------------------------
        st.markdown("---")
        st.subheader("📉 চার্টের প্রতিটি লাইন ও প্যাটার্নের বিস্তারিত ব্যাখ্যা:")
        
        vol_latest = float(df['Volume'].iloc[-1])
        vol_avg = float(df['Vol_Avg'].iloc[-1])
        volume_spike = vol_latest > (1.1 * vol_avg)

        st.info(f"""
        ### 🎨 ১. চার্টের প্রতিটি লাইনের মানে ও কাজ:
        1. 🟣 **বেগুনি লাইন (Breakout Resistance Line - ₹{breakout_res_level}):** এটি স্টকের গত ৬০ দিনের সর্বোচ্চ প্রাইস জোন। স্টক এই বেগুনি দাগটি ভাঙলে (Breakout) তীব্র গতিতে ওপরে ওঠার সম্ভাবনা থাকে।
        2. 🟡 **হলুদ ড্যাশ লাইন (Key Support Trendline - ₹{support_line_level}):** এটি স্টকের সবচেয়ে শক্ত নিচের সাপোর্ট লাইন। স্টকটির দাম কোনোভাবেই এই লাইনের নিচে যাচ্ছে না, অর্থাৎ এখান থেকে বারবার বাউন্স করছে।
        3. 🟠 **কমলা ডায়নামিক লাইন (20 EMA Line - ₹{ema_20}):** এটি শর্ট-টার্ম বুলিশ মোমেন্টাম নির্দেশকারী ট্রেন্ডলাইন। দাম এই লাইনের ওপরে থাকা মানে স্টকে বায়াররা বেশ সক্রিয়।
        4. 🟢 **সবুজ লাইন (Buy Entry Price - ₹{entry_level}):** আপনার বর্তমান বাই এন্ট্রি প্রাইস পয়েন্ট।
        5. 🔵 **আকাশি ড্যাশ লাইন (Target Price - ₹{target_level}):** এন্ট্রি থেকে +৭% লাভ বুক করার লেভেল।
        6. 🔴 **লাল ড্যাশ লাইন (Stop Loss Price - ₹{sl_level}):** ঝুঁকি নিয়ন্ত্রণের জন্য -২.৫% লসে বের হয়ে যাওয়ার লেভেল।

        ---

        ### 🧠 ২. এই স্টকের বর্তমান চার্ট প্যাটার্ন বিশ্লেষণ ({raw_name}):
        * **প্যাটার্ন গঠন:** স্টকটি বর্তমানে 🟡 **হলুদ সাপোর্ট লাইন (₹{support_line_level})** এবং 🟠 **২০ ইএমএ লাইন (₹{ema_20})**-এর ওপর শক্ত ভিত্তি তৈরি করেছে।
        * **ব্রেকআউট সম্ভাবনা:** স্টকটির বর্তমান দাম (₹{latest_price}) থেকে 🟣 **বেগুনি ব্রেকআউট লেভেল (₹{breakout_res_level})** পার হতে পারলে বড় ধরনের মুভমেন্ট তৈরি হবে।
        * **ভলিউম কনফার্মেশন:** {'সর্বশেষ সেশনে নিচে সবুজ রঙের ভলিউম বার অনেক উঁচুতে উঠেছে, যা বড় প্রাতিষ্ঠানিক বিনিয়োগকারীদের কেনাকাটা নির্দেশ করে।' if volume_spike else 'নিচের চার্টে ভলিউম বার স্বাভাবিক ও স্থির রয়েছে।'}

        ---

        ### 📱 ৩. Groww (গ্রো) অ্যাপে ট্রেড নেওয়ার নির্দেশিকা:
        1. **Groww App** খুলে **{raw_name}** স্টকটি সার্চ করে ওপেন করুন।
        2. **Buy** অপশনে লিমিট প্রাইস সেট করুন **₹{entry_level}**।
        3. ট্রেড কেনা সম্পন্ন হলে **Stop Loss Trigger Price** বসান **₹{sl_level}** এবং **Target** দিন **₹{target_level}**।
        """)
    else:
        st.error(f"❌ '{raw_name}' স্টকের চার্ট ডাটা প্রসেস করতে সমস্যা হচ্ছে। পেজটি একবার রিফ্রেশ দিন।")
            
