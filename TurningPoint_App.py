import pandas as pd
import streamlit as st
import yfinance as yf

# পেজ কনফিগারেশন
st.set_page_config(
    page_title="Retest Stock Screener", page_icon="📈", layout="wide"
)

st.title("📈 Sector-Wise Retest Stock Screener (NSE)")
st.write(
    "নিচের বাটনে ক্লিক করে এনএসই-এর বিভিন্ন সেক্টরের স্টক স্ক্যান করুন।"
)

# ১. মূল সেক্টর অনুযায়ী জনপ্রিয় স্টকের তালিকা
SECTOR_STOCKS = {
    "Financial & Banking": [
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "KOTAKBANK.NS",
        "AXISBANK.NS",
        "BAJFINANCE.NS",
        "BAJAJFINSV.NS",
        "PFC.NS",
        "RECLTD.NS",
        "BANKBARODA.NS",
    ],
    "IT (Information Technology)": [
        "TCS.NS",
        "INFY.NS",
        "HCLTECH.NS",
        "WIPRO.NS",
        "TECHM.NS",
        "LTIM.NS",
        "PERSISTENT.NS",
        "COFORGE.NS",
        "MPHASIS.NS",
    ],
    "Automobile": [
        "TATAMOTORS.NS",
        "M&M.NS",
        "MARUTI.NS",
        "BAJAJ-AUTO.NS",
        "EICHERMOT.NS",
        "HEROMOTOCO.NS",
        "TVSMOTOR.NS",
        "BHARATFORG.NS",
    ],
    "Pharma & Healthcare": [
        "SUNPHARMA.NS",
        "DRREDDY.NS",
        "CIPLA.NS",
        "DIVISLAB.NS",
        "APOLLOHOSP.NS",
        "LUPIN.NS",
        "TORNTPHARM.NS",
        "MANKIND.NS",
    ],
    "FMCG": [
        "ITC.NS",
        "HINDUNILVR.NS",
        "NESTLEIND.NS",
        "TATACONSUM.NS",
        "BRITANNIA.NS",
        "GODREJCP.NS",
        "DABUR.NS",
        "MARICO.NS",
    ],
    "Energy, Oil & Gas": [
        "RELIANCE.NS",
        "NTPC.NS",
        "ONGC.NS",
        "POWERGRID.NS",
        "BPCL.NS",
        "IOC.NS",
        "GAIL.NS",
        "TATAPOWER.NS",
        "ADANIGREEN.NS",
    ],
    "Metals & Mining": [
        "TATASTEEL.NS",
        "JSWSTEEL.NS",
        "HINDALCO.NS",
        "COALINDIA.NS",
        "VEDL.NS",
        "JINDALSTEL.NS",
        "NMDC.NS",
    ],
    "Capital Goods & Infra": [
        "LT.NS",
        "HAL.NS",
        "BEL.NS",
        "SIEMENS.NS",
        "ABB.NS",
        "DLF.NS",
        "GMRINFRA.NS",
    ],
    "Chemicals": [
        "PIIND.NS",
        "SRF.NS",
        "UPL.NS",
        "AARTIIND.NS",
        "ATUL.NS",
        "DEEPAKNTR.NS",
    ],
    "Telecom & Media": [
        "BHARTIARTL.NS",
        "IDEA.NS",
        "TATACOMM.NS",
        "SUNTV.NS",
        "PVRINOX.NS",
    ],
}


# ২. রিটেস্ট ফিল্টার লজিক
def scan_retest(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if len(df) < 50:
            return None

        current_close = float(df["Close"].iloc[-1].values[0])
        previous_close = float(df["Close"].iloc[-2].values[0])
        recent_high = float(df["High"].iloc[-20:-3].max().values[0])
        sma_20 = float(df["Close"].rolling(window=20).mean().iloc[-1].values[0])

        retest_zone_high = recent_high * 1.02
        retest_zone_low = recent_high * 0.97

        is_retesting_breakout = (
            retest_zone_low <= current_close <= retest_zone_high
        )
        is_retesting_sma = (sma_20 * 0.985) <= current_close <= (sma_20 * 1.015)
        is_bouncing = current_close > previous_close

        if (is_retesting_breakout or is_retesting_sma) and is_bouncing:
            return {
                "Stock": ticker.replace(".NS", ""),
                "Current Price (₹)": round(current_close, 2),
                "Retest Level (₹)": round(recent_high, 2),
                "20 SMA (₹)": round(sma_20, 2),
            }
    except Exception:
        pass
    return None


# ৩. স্ক্যানার বাটন
if st.button("🚀 Scan Stocks Now"):
    matched_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_sectors = len(SECTOR_STOCKS)

    for idx, (sector, stocks) in enumerate(SECTOR_STOCKS.items()):
        status_text.text(f"Scanning Sector: {sector}...")
        for stock in stocks:
            res = scan_retest(stock)
            if res:
                res["Sector"] = sector
                matched_results.append(res)

        progress_bar.progress((idx + 1) / total_sectors)

    status_text.text("Scanning Completed!")

    # রেজাল্ট প্রদর্শন
    if matched_results:
        final_df = pd.DataFrame(matched_results)
        final_df = final_df[
            [
                "Sector",
                "Stock",
                "Current Price (₹)",
                "Retest Level (₹)",
                "20 SMA (₹)",
            ]
        ]
        st.success("ফিল্টারে আসা সম্ভাব্য স্টকগুলোর তালিকা:")
        st.dataframe(final_df, use_container_width=True)
    else:
        st.warning(
            "বর্তমানে কোনো সেক্টরের স্টকে উপযুক্ত রিটেস্ট প্যাটার্ন পাওয়া যায়নি।"
        )
        
