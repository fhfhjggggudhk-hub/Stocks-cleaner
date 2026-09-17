import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Stock Screener Pro", layout="wide")

st.title("⚡ AI Stock Screener Pro")
st.caption("শুধুমাত্র কনফার্মড বুলিশ রিভার্সাল প্যাটার্ন যুক্ত স্টকগুলোই নিচে দেখাবে")

# সাব-সেক্টরের বিশাল স্টক লিস্ট (Nifty 500 ও প্রধান সেক্টরাল স্টকসহ)
SUB_SECTORS = {
    "🏦 Banking & NBFC": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "MUTHOOTFIN.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "AUBANK.NS", "CANBK.NS", "UNIONBANK.NS", "BANDHANBNK.NS", "CHOLAFIN.NS", "SHRIRAMFIN.NS", "MNGLMFIN.NS", "BAJAJFINSV.NS"],
    "💻 IT & Software": ["TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS", "HCLTECH.NS", "PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", "MPHASIS.NS", "LTTS.NS", "TATAELXSI.NS", "KPITTECH.NS", "CYIENT.NS", "OFSS.NS", "ZENSARTECH.NS"],
    "⛽ Oil, Gas & Energy": ["ONGC.NS", "RELIANCE.NS", "IOC.NS", "BPCL.NS", "HPCL.NS", "GAIL.NS", "OIL.NS", "ATGL.NS", "PETRONET.NS", "MGL.NS", "IGL.NS", "GUJGASLTD.NS", "COALINDIA.NS", "NTPC.NS", "POWERGRID.NS"],
    "🛡️ Defense & Shipbuilding": ["HAL.NS", "BEL.NS", "MAZDOCK.NS", "COCHINSHIP.NS", "DATAPATTNS.NS", "BDL.NS", "PARAS.NS", "GRSE.NS", "ZENACT.NS", "SOLARINDS.NS"],
    "🚂 Railways & Transport": ["IRCTC.NS", "RVNL.NS", "IRFC.NS", "TITAGARH.NS", "RITES.NS", "CONCOR.NS", "TEXRAIL.NS", "RAILTEL.NS", "BEML.NS"],
    "⚡ Green & Renewable Energy": ["TATAPOWER.NS", "IREDA.NS", "SUZLON.NS", "BORORENEW.NS", "ADANIGREEN.NS", "SJWN.NS", "NHPC.NS", "INOXWIND.NS", "GREENPOWER.NS", "KPIGREEN.NS"],
    "🚗 Auto & EV Components": ["TATAMOTORS.NS", "MARUTI.NS", "M&M.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "SONACOMS.NS", "MOTHERSON.NS", "BOSCHLTD.NS", "EXIDEIND.NS", "OLECTRA.NS", "TUBEINVEST.NS", "BALKRISIND.NS", "BHARATFORG.NS"],
    "🏥 Pharma & Healthcare": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "FORTIS.NS", "MAXHEALTH.NS", "NH.NS", "LALPATHLAB.NS", "MANKIND.NS", "TORNTPHARM.NS", "LUPIN.NS", "ZYDUSLIFE.NS", "AUROPHARMA.NS", "GLENMARK.NS"],
    "🏗️ Cement & Metals": ["LT.NS", "ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS", "ACC.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "JINDALSTEL.NS", "NMDC.NS", "NATIONALUM.NS", "VEDL.NS"],
    "🛒 FMCG & Retail": ["HUNVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DMART.NS", "TRENT.NS", "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "TATACONSUM.NS", "VARUN.NS", "VBL.NS"]
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
    
    c1 = df.iloc[-1]
    c2 = df.iloc[-2]
    c3 = df.iloc[-3]
    
    open1, close1, high1, low1 = c1['Open'], c1['Close'], c1['High'], c1['Low']
    open2, close2, high2, low2 = c2['Open'], c2['Close'], c2['High'], c2['Low']
    open3, close3, high3, low3 = c3['Open'], c3['Close'], c3['High'], c3['Low']
    
    body1 = abs(close1 - open1)
    range1 = high1 - low1
    if range1 == 0:
        return None
        
    lower_shadow1 = min(open1, close1) - low1
    upper_shadow1 = high1 - max(open1, close1)
    
    recent_low = df['Low'].tail(20).min()
    is_at_support = low1 <= (recent_low * 1.03)
    
    is_green1 = close1 > open1
    is_red2 = close2 < open2
    is_red3 = close3 < open3
    
    pattern = "⚪ No Pattern"
    
    if is_at_support:
        if is_red3 and (abs(close2 - open2) <= 0.3 * (high2 - low2)) and is_green1 and (close1 > (open3 + close3) / 2):
            pattern = "🌟 Morning Star (Support)"
        elif is_red2 and is_green1 and (close1 >= open2) and (open1 <= close2):
            pattern = "🔥 Bullish Engulfing (Support)"
        elif is_red2 and is_green1 and (open1 < close2) and (close1 > (open2 + close2) / 2) and (close1 < open2):
            pattern = "⚡ Piercing Line (Support)"
        elif is_green1 and (lower_shadow1 >= 2 * body1) and (upper_shadow1 <= 0.3 * body1) and (body1 > 0):
            pattern = "🔨 Green Bullish Hammer (Support)"
        elif is_green1 and (upper_shadow1 >= 2 * body1) and (lower_shadow1 <= 0.3 * body1) and (body1 > 0):
            pattern = "🙃 Inverted Hammer (Support)"
        elif (body1 <= 0.1 * range1) and (lower_shadow1 >= 0.6 * range1) and (upper_shadow1 <= 0.1 * range1):
            pattern = "🐉 Dragonfly Doji (Support)"
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
    st.write(f"**{selected_category}** সেকশনের সব স্টক স্ক্যান করা হচ্ছে...")
    results = []
    tickers = SUB_SECTORS[selected_category]
    progress = st.progress(0)
    
    for idx, ticker in enumerate(tickers):
        try:
            data = fetch_stock_data(ticker, timeframe_option)
            res = analyze_stock(data)
            # ফিল্টার: শুধুমাত্র যদি ক্যান্ডেল প্যাটার্ন "⚪ No Pattern" না হয়, তবেই স্ক্রিনে দেখাবে!
            if res and res["Pattern"] != "⚪ No Pattern":
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
        st.success(f"স্ক্যানিং সম্পন্ন! মোট {len(results)} টি স্টকে রিভার্সাল প্যাটার্ন পাওয়া গেছে:")
        
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
    else:
        st.warning("⚠️ এই মুহূর্তে এই সাব-সেক্টরের কোনো স্টকে সাপোর্টে রিভার্সাল প্যাটার্ন তৈরি হয়নি।")
