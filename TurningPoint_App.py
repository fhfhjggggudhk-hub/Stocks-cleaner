import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ==========================================
# ১. পেজ সেটআপ
# ==========================================
st.set_page_config(
    page_title="High-Probability Turning Point Radar",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 High-Probability Turning Point Scanner")
st.markdown(
    "এনএসই (NSE) শেয়ার বাজারের **আসল ডাটা** বিশ্লেষণ করে RSI, Volume Spike, Hammer/Engulfing এবং Market Structure মিলিয়ে টার্নিং পয়েন্ট সনাক্তকরণ।"
)


# ==========================================
# ২. আসল ডাটা ডাউনলোড করার ফাংশন (No Token Required)
# ==========================================
@st.cache_data(ttl=1800)
def fetch_real_stock_data(symbol, period="1y", interval="1d"):
    ticker = f"{symbol.upper()}.NS"
    df = yf.download(ticker, period=period, interval=interval)

    # MultiIndex কলাম ঠিক করা
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return df


# ==========================================
# ৩. টার্নিং পয়েন্ট অ্যালগরিদম
# ==========================================
def detect_turning_points(df):
    data = df.copy()

    # ১. RSI (14)
    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-10)
    data["RSI"] = 100 - (100 / (1 + rs))

    # ২. Volume Spike (২০ দিনের গড়ের ১.৩ গুণ)
    data["Vol_SMA20"] = data["Volume"].rolling(window=20).mean()
    data["Volume_Spike"] = data["Volume"] > (1.3 * data["Vol_SMA20"])

    # ৩. ক্যান্ডেলস্টিক বডি ও উইক
    body = (data["Close"] - data["Open"]).abs()
    lower_wick = np.where(
        data["Close"] > data["Open"],
        data["Open"] - data["Low"],
        data["Close"] - data["Low"],
    )
    upper_wick = np.where(
        data["Close"] > data["Open"],
        data["High"] - data["Close"],
        data["High"] - data["Open"],
    )

    # হ্যামার এবং বুলিশ এঙ্গালফিং
    data["Is_Hammer"] = (lower_wick >= 1.8 * body) & (upper_wick <= body * 0.5)
    data["Is_Engulfing"] = (
        (data["Close"] > data["Open"])
        & (data["Close"].shift(1) < data["Open"].shift(1))
        & (data["Close"] > data["Open"].shift(1))
    )

    # ৪. মার্কেট স্ট্রাকচার ব্রেক (CHoCH)
    data["Prev_Swing_High"] = data["High"].shift(1).rolling(window=5).max()
    data["CHoCH_Break"] = data["Close"] > data["Prev_Swing_High"]

    # ৫. হাই প্রবাবিলিটি টার্নিং পয়েন্ট সিগন্যাল
    data["Turning_Point"] = False
    data.loc[
        ((data["RSI"] <= 45) | data["CHoCH_Break"])
        & (data["Is_Hammer"] | data["Is_Engulfing"])
        & data["Volume_Spike"],
        "Turning_Point",
    ] = True

    return data


# ==========================================
# ৪. নেভিগেশন ও ফিল্টার
# ==========================================
st.sidebar.header("📊 স্টক এবং টাইমফ্রেম নির্বাচন")

stock_list = [
    "CONCOR",
    "RELIANCE",
    "TATASTEEL",
    "INFY",
    "HDFCBANK",
    "SBIN",
    "ITC",
    "AXISBANK",
    "TATAMOTORS",
    "LT",
]
selected_symbol = st.sidebar.selectbox("NSE Stock Choose করুন:", stock_list)

timeframe = st.sidebar.selectbox(
    "টাইমফ্রেম সিলেক্ট করুন:", ["1D (Daily)", "1H (1 Hour)", "15M (15 Min)"]
)

period_map = {"1D (Daily)": "1y", "1H (1 Hour)": "1mo", "15M (15 Min)": "1mo"}
interval_map = {"1D (Daily)": "1d", "1H (1 Hour)": "1h", "15M (15 Min)": "15m"}

# ==========================================
# ৫. ডাটা প্রসেস ও ডিসপ্লে
# ==========================================
try:
    raw_df = fetch_real_stock_data(
        selected_symbol,
        period=period_map[timeframe],
        interval=interval_map[timeframe],
    )

    if not raw_df.empty:
        df = detect_turning_points(raw_df)

        # কার্ড ডিসপ্লে
        latest = df.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Current Price", f"₹{latest['Close']:.2f}")
        c2.metric("RSI (14)", f"{latest['RSI']:.1f}")
        c3.metric("Volume", f"{int(latest['Volume']):,}")

        if latest["Turning_Point"]:
            c4.success("🟢 TURNING POINT DETECTED!")
        else:
            c4.info("⚪ No Turning Point Today")

        # চার্ট তৈরি
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price",
            )
        )

        # টার্নিং পয়েন্ট থাকলে চিহ্নিত করা
        t_points = df[df["Turning_Point"] == True]
        if not t_points.empty:
            fig.add_trace(
                go.Scatter(
                    x=t_points.index,
                    y=t_points["Low"] * 0.988,
                    mode="markers+text",
                    marker=dict(
                        symbol="triangle-up",
                        size=15,
                        color="#00FF66",
                        line=dict(width=1, color="white"),
                    ),
                    text="🟢 BUY",
                    textposition="bottom center",
                    name="Turning Point Signal",
                )
            )

        fig.update_layout(
            title=f"<b>{selected_symbol}</b> - Real-time Turning Point Analysis ({timeframe})",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=620,
        )

        st.plotly_chart(fig, use_container_width=True)

        # টেবিল ডিসপ্লে
        st.subheader("📋 অতীতের টার্নিং পয়েন্ট সিগন্যালের ইতিহাস")
        signals = df[df["Turning_Point"] == True][
            ["Close", "RSI", "Volume", "Is_Hammer", "Is_Engulfing"]
        ]
        if not signals.empty:
            st.dataframe(signals.tail(10), use_container_width=True)
        else:
            st.write(
                "নির্বাচিত সময়ের মধ্যে এই শেয়ারটিতে কোনো টার্নিং পয়েন্ট সংকেত মেলেনি।"
            )

    else:
        st.error("ডাটা পাওয়া যায়নি। স্টক সিম্বল চেক করুন।")

except Exception as e:
        st.error(f"ডাটা লোড করতে সমস্যা হয়েছে: {e}")

