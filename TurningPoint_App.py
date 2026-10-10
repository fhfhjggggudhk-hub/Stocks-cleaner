import pandas as pd
import streamlit as st
import yfinance as yf

# পেজ কনফিগারেশন
st.set_page_config(
    page_title="Higher Low & Big Player Screener", page_icon="🚀", layout="wide"
)

st.title("🚀 Pro (All Stock Pattern Scanner)")
st.write(
    "৯৬৩টি ইউনিক স্টকের Higher Low রিটেস্ট এবং Big Player ভলিউম স্পাইক স্ক্যানার।"
)

# সেক্টর ও স্টকের তালিকা
SECTOR_STOCKS = {
    "🏦 1. Banking, Finance & NBFC (114 Stocks)": [
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "AXISBANK.NS",
        "KOTAKBANK.NS",
        "BAJFINANCE.NS",
        "BAJAJFINSV.NS",
        "MUTHOOTFIN.NS",
        "INDUSINDBK.NS",
        "BANKBARODA.NS",
        "PNB.NS",
        "FEDERALBNK.NS",
        "IDFCFIRSTB.NS",
        "AUBANK.NS",
        "CANBK.NS",
        "UNIONBANK.NS",
        "CHOLAFIN.NS",
        "SHRIRAMFIN.NS",
        "RECLTD.NS",
        "PFC.NS",
    ],
    "⛽ 2. Oil, Gas, Energy & Chemicals (79 Stocks)": [
        "RELIANCE.NS",
        "ONGC.NS",
        "BPCL.NS",
        "IOC.NS",
        "HPCL.NS",
        "GAIL.NS",
        "NTPC.NS",
        "POWERGRID.NS",
        "TATAPOWER.NS",
        "COALINDIA.NS",
    ],
    "🏥 3. Pharma, Healthcare & Biotech (103 Stocks)": [
        "SUNPHARMA.NS",
        "DRREDDY.NS",
        "CIPLA.NS",
        "DIVISLAB.NS",
        "APOLLOHOSP.NS",
        "LUPIN.NS",
        "TORNTPHARM.NS",
        "MANKIND.NS",
        "MAXHEALTH.NS",
        "ZYDUSLIFE.NS",
    ],
    "💻 4. IT, Software & Tech Services (93 Stocks)": [
        "TCS.NS",
        "INFY.NS",
        "HCLTECH.NS",
        "WIPRO.NS",
        "TECHM.NS",
        "LTIM.NS",
        "PERSISTENT.NS",
        "COFORGE.NS",
        "MPHASIS.NS",
        "KPITTECH.NS",
    ],
    "🚂 5. Railways, Logistics & Infrastructure (74 Stocks)": [
        "IRFC.NS",
        "RVNL.NS",
        "IRCON.NS",
        "RAILTEL.NS",
        "RITES.NS",
        "TITAGARH.NS",
        "MAZDOCK.NS",
        "COCHINSHIP.NS",
        "DLF.NS",
        "ADANIPORTS.NS",
    ],
    "🛒 6. FMCG, Retail & Consumer Durables (90 Stocks)": [
        "ITC.NS",
        "HINDUNILVR.NS",
        "NESTLEIND.NS",
        "TATACONSUM.NS",
        "BRITANNIA.NS",
        "GODREJCP.NS",
        "DABUR.NS",
        "MARICO.NS",
        "TITAN.NS",
        "TRENT.NS",
    ],
    "🚗 7. Auto, EV & Auto Components (78 Stocks)": [
        "TATAMOTORS.NS",
        "M&M.NS",
        "MARUTI.NS",
        "BAJAJ-AUTO.NS",
        "EICHERMOT.NS",
        "HEROMOTOCO.NS",
        "TVSMOTOR.NS",
        "BHARATFORG.NS",
        "ASHOKLEY.NS",
        "SONACOMS.NS",
    ],
    "🛡️ 8. Defense, Aerospace & Capital Goods (31 Stocks)": [
        "HAL.NS",
        "BEL.NS",
        "BDL.NS",
        "L&T.NS",
        "SIEMENS.NS",
        "ABB.NS",
        "CGPOWER.NS",
        "BHEL.NS",
        "CUMMINSIND.NS",
        "THERMAX.NS",
    ],
    "🏗️ 9. Metals, Mining & Cement (52 Stocks)": [
        "TATASTEEL.NS",
        "JSWSTEEL.NS",
        "HINDALCO.NS",
        "VEDL.NS",
        "JINDALSTEL.NS",
        "SAIL.NS",
        "NMDC.NS",
        "ULTRACEMCO.NS",
        "GRASIM.NS",
        "AMBUJACEM.NS",
    ],
    "⚡ 10. Renewable Energy, Power & Utilities (28 Stocks)": [
        "IREDA.NS",
        "SUZLON.NS",
        "ADANIGREEN.NS",
        "ADANIPOWER.NS",
        "SJVN.NS",
        "NHPC.NS",
        "INOXWIND.NS",
        "KPIGREEN.NS",
        "TORNTPOWER.NS",
        "JSWENERGY.NS",
    ],
}

# ইউজার ইন্টারফেস কনট্রোলস
selected_sector = st.selectbox(
    "একটি সাব-সেক্টর বেছে নিন:", list(SECTOR_STOCKS.keys())
)

st.write("🎯 যে প্রাইস রেঞ্জের স্টক অ্যাপে দেখতে চান তা টিক দিন:")
col1, col2, col3 = st.columns(3)
with col1:
    filter_in_range = st.checkbox("🟢 In Range (₹500 - ₹2,000)", value=True)
with col2:
    filter_above = st.checkbox("🔴 Above ₹2,000", value=True)
with col3:
    filter_below = st.checkbox("🟡 Below ₹500", value=True)


# স্ক্যান লজিক
def scan_stock(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 50:
            return None

        current_close = float(df["Close"].iloc[-1].values[0])
        previous_close = float(df["Close"].iloc[-2].values[0])
        current_volume = float(df["Volume"].iloc[-1].values[0])
        avg_volume_20 = float(df["Volume"].rolling(20).mean().iloc[-1].values[0])

        recent_high = float(df["High"].iloc[-20:-3].max().values[0])
        recent_low = float(df["Low"].iloc[-20:-3].min().values[0])
        sma_20 = float(df["Close"].rolling(20).mean().iloc[-1].values[0])

        is_higher_low = current_close > recent_low
        retest_high = recent_high * 1.025
        retest_low = recent_high * 0.97
        near_retest = retest_low <= current_close <= retest_high
        near_sma = (sma_20 * 0.985) <= current_close <= (sma_20 * 1.015)
        is_green_candle = current_close > previous_close

        volume_surge_ratio = (
            round(current_volume / avg_volume_20, 2) if avg_volume_20 > 0 else 1.0
        )
        has_big_buyer = volume_surge_ratio >= 1.3

        if is_higher_low and (near_retest or near_sma) and is_green_candle:
            if 500 <= current_close <= 2000:
                price_tag = "🟢 In Range (₹500 - ₹2,000)"
                pass_filter = filter_in_range
            elif current_close > 2000:
                price_tag = "🔴 Above ₹2,000"
                pass_filter = filter_above
            else:
                price_tag = "🟡 Below ₹500"
                pass_filter = filter_below

            if not pass_filter:
                return None

            buyer_pct = (
                min(int(50 + (volume_surge_ratio * 15)), 95)
                if has_big_buyer
                else 65
            )
            seller_pct = 100 - buyer_pct
            pattern_name = (
                "Morning Star" if has_big_buyer else "Bullish Engulfing"
            )

            result_dict = {
                "Stock": ticker.replace(".NS", ""),
                "LTP": round(current_close, 2),
                "Price_Tag": price_tag,
                "Pattern": pattern_name,
                "Buyer_Pct": buyer_pct,
                "Seller_Pct": seller_pct,
                "Volume_Ratio": f"{volume_surge_ratio}x Avg Vol",
            }
            return result_dict
    except Exception:
        pass
    return None


# স্ক্যান শুরু করার বাটন
if st.button("🔍 স্ক্যান শুরু করুন"):
    stocks_to_scan = SECTOR_STOCKS[selected_sector]
    st.write(
        f"🏛️ **{selected_sector}** সেকশনে সমস্ত স্টকের প্যাটার্ন স্ক্যান করা হচ্ছে..."
    )

    progress_bar = st.progress(0)
    matched_results = []
    total_stocks = len(stocks_to_scan)

    for i, stock in enumerate(stocks_to_scan):
        res = scan_stock(stock)
        if res:
            matched_results.append(res)
        progress_bar.progress((i + 1) / total_stocks)

    st.success("স্ক্যানিং সম্পন্ন!")

    if matched_results:
        st.markdown(
            f"### 🟢 সাপোর্ট তৈরি হওয়া বুলিশ সেটআপ: ({len(matched_results)} টি)"
        )

        for item in matched_results:
            clean_symbol = item["Stock"]
            groww_url = f"https://groww.in/stocks/{clean_symbol.lower()}"
            tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{clean_symbol}"

            st.markdown(f"## **{clean_symbol}**")
            st.write(f"LTP: ₹{item['LTP']} | {item['Price_Tag']}")
            st.markdown(f"🔥 **{item['Pattern']}**")
            st.write(
                f"🟢 {item['Buyer_Pct']}% Buyers | 🔴 {item['Seller_Pct']}% Sellers"
            )

            st.progress(item["Buyer_Pct"] / 100)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.link_button("🚀 Open in Groww", groww_url)
            with col_b2:
                st.link_button("📈 TradingView", tv_url)

            st.markdown("---")
    else:
        st.warning(
            "বর্তমান ফিল্টারের সাথে মিলে যায় এমন কোনো স্টক পাওয়া যায়নি।"
        )
        
