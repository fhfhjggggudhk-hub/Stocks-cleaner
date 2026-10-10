import pandas as pd
import streamlit as st
import yfinance as yf

# পেজ কনফিগারেশন
st.set_page_config(
    page_title="Higher Low & Big Player Screener", page_icon="🚀", layout="wide"
)

st.title("🚀 Pro (All Stock Pattern Scanner)")
st.write(
    "৯৬৩টি ইউনিক স্টকের Higher Low রিটেস্ট, বুলিশ এবং বিয়ারিশ সেটআপ স্ক্যানার।"
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

# ক্যান্ডেল টাইমফ্রেম সিলেকশন[span_4](start_span)[span_4](end_span)
timeframe_option = st.selectbox(
    "ক্যান্ডেল টাইমফ্রেম (Timeframe):",
    ["1 Day (Daily)", "4 Hours (4h)", "1 Hour (1h)", "15 Minutes (15m)"],
)

if "1 Day" in timeframe_option:
    interval_val = "1d"
    period_val = "6mo"
elif "4 Hours" in timeframe_option:
    interval_val = "60m"
    period_val = "60d"
elif "1 Hour" in timeframe_option:
    interval_val = "60m"
    period_val = "30d"
else:
    interval_val = "15m"
    period_val = "5d"

st.write("🎯 যে প্রাইস রেঞ্জের স্টক অ্যাপে দেখতে চান তা টিক দিন:")
col1, col2, col3 = st.columns(3)
with col1:
    filter_in_range = st.checkbox("🟢 In Range (₹500 - ₹2,000)", value=True)
with col2:
    filter_above = st.checkbox("🔴 Above ₹2,000", value=True)
with col3:
    filter_below = st.checkbox("🟡 Below ₹500", value=True)


# স্ক্যান লজিক (বুলিশ এবং বিয়ারিশ আলাদা করা)
def scan_stock(ticker, interval, period):
    try:
        df = yf.download(
            ticker, period=period, interval=interval, progress=False
        )
        if len(df) < 30:
            return None

        current_close = float(df["Close"].iloc[-1].values[0])
        previous_close = float(df["Close"].iloc[-2].values[0])
        current_volume = float(df["Volume"].iloc[-1].values[0])
        avg_volume_20 = float(df["Volume"].rolling(20).mean().iloc[-1].values[0])

        recent_high = float(df["High"].iloc[-20:-3].max().values[0])
        recent_low = float(df["Low"].iloc[-20:-3].min().values[0])
        sma_20 = float(df["Close"].rolling(20).mean().iloc[-1].values[0])

        # প্রাইস রেঞ্জ ফিল্টার চেক
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

        volume_surge_ratio = (
            round(current_volume / avg_volume_20, 2) if avg_volume_20 > 0 else 1.0
        )

        # বুলিশ শর্ত (Higher Low রিটেস্ট বা সাপোর্ট बाउंस)
        is_higher_low = current_close > recent_low
        retest_high = recent_high * 1.025
        retest_low = recent_high * 0.97
        near_retest = retest_low <= current_close <= retest_high
        near_sma = (sma_20 * 0.985) <= current_close <= (sma_20 * 1.015)
        is_green_candle = current_close > previous_close

        if is_higher_low and (near_retest or near_sma) and is_green_candle:
            buyer_pct = (
                min(int(50 + (volume_surge_ratio * 15)), 95)
                if volume_surge_ratio >= 1.3
                else 65
            )
            return {
                "Stock": ticker.replace(".NS", ""),
                "LTP": round(current_close, 2),
                "Price_Tag": price_tag,
                "Type": "Bullish",
                "Pattern": (
                    "Morning Star / HL Retest"
                    if volume_surge_ratio >= 1.3
                    else "Bullish Engulfing"
                ),
                "Buyer_Pct": buyer_pct,
                "Seller_Pct": 100 - buyer_pct,
            }

        # বিয়ারিশ শর্ত (ডাউনট্রেন্ড / উইক স্ট্রাকচার)
        elif current_close < sma_20 and current_close < previous_close:
            seller_pct = min(int(50 + (volume_surge_ratio * 15)), 90)
            return {
                "Stock": ticker.replace(".NS", ""),
                "LTP": round(current_close, 2),
                "Price_Tag": price_tag,
                "Type": "Bearish",
                "Pattern": "Bearish Breakdown / Weakness",
                "Buyer_Pct": 100 - seller_pct,
                "Seller_Pct": seller_pct,
            }

    except Exception:
        pass
    return None


# স্ক্যান শুরু করার বাটন
if st.button("🔍 স্ক্যান শুরু করুন"):
    stocks_to_scan = SECTOR_STOCKS[selected_sector]
    st.write(
        f"🏛️ **{selected_sector}** সেকশনে **{timeframe_option}** টাইমফ্রেমে স্ক্যান করা হচ্ছে..."
    )

    progress_bar = st.progress(0)
    bullish_results = []
    bearish_results = []
    total_stocks = len(stocks_to_scan)

    for i, stock in enumerate(stocks_to_scan):
        res = scan_stock(stock, interval_val, period_val)
        if res:
            if res["Type"] == "Bullish":
                bullish_results.append(res)
            else:
                bearish_results.append(res)
        progress_bar.progress((i + 1) / total_stocks)

    st.success("স্ক্যানিং সম্পন্ন!")

    # ট্যাবস বা সেকশন ডিজাইন (দ্বিতীয় ছবির স্টাইল)[span_5](start_span)[span_5](end_span)
    tab1, tab2 = st.tabs(
        [
            f"🟢 বুলিশ সেটআপ ({len(bullish_results)})",
            f"🔴 বিয়ারিশ সেটআপ ({len(bearish_results)})",
        ]
    )

    with tab1:
        if bullish_results:
            st.markdown("### 🟢 সাপোর্ট তৈরি হওয়া বুলিশ সেটআপ:")
            for item in bullish_results:
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
            st.warning("এই সেকশনে কোনো বুলিশ সেটআপ পাওয়া যায়নি।")

    with tab2:
        if bearish_results:
            st.markdown("### 🔴 বিয়ারিশ বা ডাউনট্রেন্ড সেটআপ:")
            for item in bearish_results:
                clean_symbol = item["Stock"]
                groww_url = f"https://groww.in/stocks/{clean_symbol.lower()}"
                tv_url = f"https://in.tradingview.com/chart/?symbol=NSE:{clean_symbol}"

                st.markdown(f"## **{clean_symbol}**")
                st.write(f"LTP: ₹{item['LTP']} | {item['Price_Tag']}")
                st.markdown(f"⚠️ **{item['Pattern']}**")
                st.write(
                    f"🟢 {item['Buyer_Pct']}% Buyers | 🔴 {item['Seller_Pct']}% Sellers"
                )
                st.progress(item['Buyer_Pct'] / 100)

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.link_button("🚀 Open in Groww", groww_url)
                with col_b2:
                    st.link_button("📈 TradingView", tv_url)
                st.markdown("---")
        else:
            st.warning("এই সেকশনে কোনো বিয়ারিশ সেটআপ পাওয়া যায়নি।")
            
