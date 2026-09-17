import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")

st.title("⚡ AI Stock Screener Pro")
st.caption("কাস্টম সাব-সেক্টর, টাইমফ্রেম ফিল্টার, প্যাটার্ন ও বায়ার/সেলার মোমেন্টাম ট্র্যাকার")

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
    
    latest = df.iloc[-1]
    open_p, close_p = latest['Open'], latest['Close']
    high_p, low_p = latest['High'], latest['Low']
    
    body = abs(close_p - open_p)
    total_range = high_p - low_p
    if total_range == 0:
        return None
        
    lower_shadow = min(open_p, close_p) - low_p
    upper_shadow = high_p - max(open_p, close_p)
    
    recent_low = df['Low'].tail(20).min()
    is_at_support = low_p <= (recent_low * 1.03)
    
    is_hammer = (lower_shadow >= 2 * body) and (upper_shadow <= 0.3 * body) and (body > 0)
    is_spinning_top = (body <= 0.25 * total_range) and (upper_shadow >= body) and (lower_shadow >= body)
    
    pattern = "⚪ No Pattern"
    if is_at_support:
        if is_hammer:
            pattern = "🔨 Bullish Hammer (Support)"
        elif is_spinning_top:
            pattern = "🌀 Spinning Top (Support)"
            
    buyer_power = round(((close_p - low_p) / total_range) * 100, 1)
    seller_power = round(((high_p - close_p) / total_range) * 100, 1)
    
    return {
        "Price": round(close_p, 2),
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
      
