import time
import pandas as pd
import yfinance as yf

# ১. মূল সেক্টর অনুযায়ী জনপ্রিয় ও লিকুইড স্টকের তালিকা
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
        "PERSISTENT.NS",,
        "COFORGE.NS",
        "MPHASIS.NS",
    ],
    "Automobile": [
        "TATAMOTORS.NS",
        "M&M.NS",
        "MARUTI.NS",
        "BAJAJ-AUTO.NS",
        "EICHERMOT.NS",
        "HEROMOTOCO.NS",,
        "TVSMOTOR.NS",
        "BHARATFORG.NS",
    ],
    "Pharma & Healthcare": [
        "SUNPHARMA.NS",
        "DRREDDY.NS",
        "CIPLA.NS",
        "DIVISLAB.NS",
        "APOLLOHOSP.NS",,
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
    "Capital Goods & Infrastructure": [
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
        # গত ৬ মাসের ডেইলি ক্যান্ডেল ডাউনলোড
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if len(df) < 50:
            return None

        # সাম্প্রতিক ক্লোজ এবং হাই বের করা
        current_close = float(df["Close"].iloc[-1].values[0])
        previous_close = float(df["Close"].iloc[-2].values[0])

        # বিগত ২০ দিনের সর্বোচ্চ রেজিস্ট্যান্স (Recent High)
        recent_high = float(df["High"].iloc[-20:-3].max().values[0])

        # ২০ দিনের Moving Average (Dynamic Support)
        sma_20 = float(df["Close"].rolling(window=20).mean().iloc[-1].values[0])

        # কন্ডিশন ১: সাম্প্রতিক হাই-এর ২% থেকে ৩%-এর মধ্যে রিটেস্ট অথবা ২০ SMA-তে সাপোর্ট
        retest_zone_high = recent_high * 1.02
        retest_zone_low = recent_high * 0.97

        is_retesting_breakout = (
            retest_zone_low <= current_close <= retest_zone_high
        )
        is_retesting_sma = (sma_20 * 0.985) <= current_close <= (sma_20 * 1.015)

        # কন্ডিশন ২: আজকের ক্যান্ডেলটি কিছুটা বুলিশ (পূর্বের দিনের চেয়ে উপরে ক্লোজ)
        is_bouncing = current_close > previous_close

        if (is_retesting_breakout or is_retesting_sma) and is_bouncing:
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Current Price": round(current_close, 2),
                "Retest Level": round(recent_high, 2),
                "20 SMA": round(sma_20, 2),
            }
    except Exception:
        pass

    return None


# ৩. মেইন স্ক্যানার এক্সিকিউশন
print("=" * 60)
print("     SECTOR-WISE RETEST STOCK SCREENER (NSE)     ")
print("=" * 60)

matched_results = []

for sector, stocks in SECTOR_STOCKS.items():
    print(f"\nScanning Sector: {sector}...")

    for stock in stocks:
        res = scan_retest(stock)
        if res:
            res["Sector"] = sector
            matched_results.append(res)
            print(f"  [+] Match Found: {res['Ticker']} (₹{res['Current Price']})")

print("\n" + "=" * 60)
print("                   FINAL RESULT LIST                   ")
print("=" * 60)

if matched_results:
    final_df = pd.DataFrame(matched_results)
    # কলামগুলো সুন্দরভাবে সাজানো
    final_df = final_df[
        ["Sector", "Ticker", "Current Price", "Retest Level", "20 SMA"]
    ]
    print(final_df.to_string(index=False))
else:
    print(
        "বর্তমানে কোনো সেক্টরের স্টকে উপযুক্ত রিটেস্ট প্যাটার্ন পাওয়া যায়নি।"
              )
