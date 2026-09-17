import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")

st.title("⚡ AI Stock Screener Pro")
st.caption("কাস্টম সাব-সেক্টর, টাইমফ্রেম ফিল্টার, ৭টি রিভার্সাল প্যাটার্ন ও বায়ার/সেলার মোমেন্টাম ট্র্যাকার")

SUB_SECTORS = {
    "🏥 Hospitals & Diagnostics": ["APOLLOHOSP.NS", "FORTIS.NS", "MAXHEALTH.NS", "NH.NS", "ASTERDM.NS", "LALPATHLAB.NS"],
    "⛽ Oil & Gas": ["ONGC.NS", "RELIANCE.NS", "IOC.NS", "BPCL.NS", "HPCL.NS", "GAIL.NS", "OIL.NS", "ATGL.NS"],
    "🛡️ Defense & Aerospace": ["HAL.NS", "BEL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "DATAPATTNS.NS", "BDL.NS"],
    "🚂 Railways & Transport": ["IRCTC.NS", "RVNL.NS", "IRFC.NS", "TITAGARH.NS", "RITES.NS", "CONCOR.NS"],
    "⚡ Green & Renewable Energy": ["TATAPOWER.NS", "IREDA.NS", "SUZLON.NS", "BORORENEW.NS", "ADANIGREEN.NS", "SJWN.NS"],
    "🏨 Hotels & Tourism": ["INDHOTEL.NS", "EIHOTEL.NS", "LEMONTREE.NS", "CHALET.NS", "EASEMYTRIP.NS"],
    "🧪 Specialty Chemicals": ["PIDILITIND.NS", "AARTIIND.NS", "SRF.NS", "DEEPAKNTR.NS", "TATACHEM.NS", "ATUL.NS"],
    "🍬 Sugar & Ethanol": ["RENUKA.NS", "BALRAMCHIN.NS", "TRIVENI.NS", "EIDPARRY.NS", "BAJAJIND.NS"],
    "🚗 EV & Auto Components": ["SONACOMS.NS", "MOTHERSON.NS", "BOSCHLTD.NS", "AMARAJABAT.NS", "EXIDEIND.NS", "OLECTRA.NS"],
    "💻 IT & Software": ["TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS", "HCLTECH.NS", "PERSISTENT.NS", "COFORGE.NS"],
    "🏦 Banking & NBFC": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "MUTHOOTFIN.NS"],
    "🏗️ Construction & Cement": ["LT.NS", "ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS", "ACC.NS", "NCC.NS"],
    "📱 Telecom & Digital": ["BHARTIARTL.NS", "IDEA.NS", "TATACOMM.NS", "INDUSTOWER.NS"],
    "📜 Paper & Packaging": ["JKPAPER.NS", "CENTURYTEX.NS", "WESTCOAST.NS"],
    "🛒 FMCG & Retail": ["HUNVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DMART.NS", "TRENT.NS"]
}

col_sec, col_tf = st.columns(2)
with col_sec:
    selected_category = st.selectbox("একটি সাব-সেক্টর বেছে নিন:", list(SUB_SECTORS.keys()))
with col_tf:
    timeframe_option = st.selectbox("ক্যান্ডেল টাইমফ্রেম (Timeframe):", ["1 Day (Daily)", "4 Hours (4h)", "1 Hour (1h)", "15 Minutes (15m)"])

def fetch_stock_data(ticker, tf_choice):
    stock = yf.Ticker(ticker)
    if tf_choice == "1 Day (Daily)":
        return stock.history(period="3mo", interval="1d")
    elif tf_choice == "4 Hours (4h)":
        df = stock.history(period="1mo", interval="1h")
        if not df.empty:
            df = df.resample('4h').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
        return df
    elif tf_choice == "1 Hour (1h)":
        return stock.history(period="1mo", interval="1h")
    elif tf_choice == "15 Minutes (15m)":
        return stock.history(period="5d", interval="15m")
    return pd.DataFrame()

def analyze_stock(df):
    if len(df) < 20:
        return None
    
    # শেষ ৩টি ক্যান্ডেলের ডাটা (Multi-candle Pattern ধরার জন্য)
    c1 = df.iloc[-1]  # বর্তমান ক্যান্ডেল
    c2 = df.iloc[-2]  # আগের দিনের ক্যান্ডেল
    c3 = df.iloc[-3]  # ২ দিন আগের ক্যান্ডেল
    
    open1, close1, high1, low1 = c1['Open'], c1['Close'], c1['High'], c1['Low']
    open2, close2, high2, low2 = c2['Open'], c2['Close'], c2['High'], c2['Low']
    open3, close3, high3, low3 = c3['Open'], c3['Close'], c3['High'], c3['Low']
    
    body1 = abs(close1 - open1)
    range1 = high1 - low1
    if range1 == 0:
        return None
        
    lower_shadow1 = min(open1, close1) - low1
    upper_shadow1 = high1 - max(open1, close1)
    
    # সাপোর্টে থাকার শর্ত (গত ২০ ক্যান্ডেলের লো-এর ৩%-এর মধ্যে থাকা)
    recent_low = df['Low'].tail(20).min()
    is_at_support = low1 <= (recent_low * 1.03)
    
    is_green1 = close1 > open1
    is_red2 = close2 < open2
    is_red3 = close3 < open3
    
    pattern = "⚪ No Pattern"
    
    if is_at_support:
        # ১. Morning Star (৩ ক্যান্ডেলের প্যাটার্ন)
        if is_red3 and (abs(close2 - open2) <= 0.3 * (high2 - low2)) and is_green1 and (close1 > (open3 + close3) / 2):
            pattern = "🌟 Morning Star (Support)"
            
        # ২. Bullish Engulfing (২ ক্যান্ডেলের প্যাটার্ন)
        elif is_red2 and is_green1 and (close1 >= open2) and (open1 <= close2):
            pattern = "🔥 Bullish Engulfing (Support)"
            
        # ৩. Piercing Line (২ ক্যান্ডেলের প্যাটার্ন)
        elif is_red2 and is_green1 and (open1 < close2) and (close1 > (open2 + close2) / 2) and (close1 < open2):
            pattern = "⚡ Piercing Line (Support)"
            
        # ৪. Green Bullish Hammer
        elif is_green1 and (lower_shadow1 >= 2 * body1) and (upper_shadow1 <= 0.3 * body1) and (body1 > 0):
            pattern = "🔨 Green Bullish Hammer (Support)"
            
        # ৫. Inverted Hammer
        elif is_green1 and (upper_shadow1 >= 2 * body1) and (lower_shadow1 <= 0.3 * body1) and (body1 > 0):
            pattern = "🙃 Inverted Hammer (Support)"
            
        # ৬. Dragonfly Doji
        elif (body1 <= 0.1 * range1) and (lower_shadow1 >= 0.6 * range1) and (upper_shadow1 <= 0.1 * range1):
            pattern = "🐉 Dragonfly Doji (Support)"
            
        # ৭. Spinning Top
        elif (body1 <= 0.25 * range1) and (upper_shadow1 >= body1) and (lower_shadow1 >= body1):
            pattern = "🌀 Spinning Top (Support)"
            
    buyer_power = round(((close1 - low1) / range1) * 100, 1)
    seller_power = round(((high1 - close1) / range1) * 100, 1)
    
    return {
        "Price": round(close1, 2),
        "Pattern": pattern,
        "Buyer Power %": buyer_power,
        "Seller Power %": seller_power
    }

if st.button("🔍 স্ক্যান শুরু করুন"):
    st.write(f"**{selected_category}** সেকশনে **[{timeframe_option}]** টাইমফ্রেমে স্ক্যান করা হচ্ছে...")
    results = []
    tickers = SUB_SECTORS[selected_category]
    progress = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        try:
            data = fetch_stock_data(ticker, timeframe_option)
            res = analyze_stock(data)
            if res:
                clean_name = ticker.replace(".NS", "")
                results.append({
                    "Stock": clean_name,
                    "Price": res["Price"],
                    "Pattern": res["Pattern"],
                    "Buyer Power (%)": res["Buyer Power %"],
                    "Seller Power (%)": res["Seller Power %"]
                })
        except Exception:
            pass
        progress.progress((idx + 1) / len(tickers))
        
    if results:
        st.success(f"স্ক্যানিং সম্পন্ন! ({timeframe_option} রেজাল্ট):")
        
        for item in results:
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 2, 3, 2])
                stock_name = item["Stock"]
                groww_url = f"https://groww.in/search?q={stock_name}"
                tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{stock_name}"
                
                with c1:
                    st.markdown(f"### **{stock_name}**")
                    st.caption(f"₹{item['Price']}")
                with c2:
                    st.write(f"**{item['Pattern']}**")
                with c3:
                    b_pow = item["Buyer Power (%)"]
                    s_pow = item["Seller Power (%)"]
                    st.progress(int(b_pow), text=f"🟢 {b_pow}% | 🔴 {s_pow}%")
                with c4:
                    st.link_button("🚀 Open in Groww", groww_url)
                    st.link_button("📈 TradingView", tv_url)
                st.divider()
    
