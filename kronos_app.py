import datetime as dt
import json
import os
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# ==========================================
# অংশ ১: কমন ফাংশন ও ডাটা হ্যান্ডলিং (Common)
# ==========================================

st.set_page_config(page_title="Kronos Stock & Portfolio System", layout="wide")

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ist_now():
    return dt.datetime.now()

def load_config():
    return {
        "capital": 100000,
        "risk_per_trade_pct": 1.0,
        "max_position_pct": 20.0,
        "hold_days": 7,
        "min_rr": 1.5,
        "min_turnover_cr": 1.0,
        "min_price": 50.0,
        "top_n": 5
    }

def get_daily(symbol, period="2y"):
    try:
        ticker = symbol if ".NS" in symbol else symbol + ".NS"
        df = yf.download(ticker, period=period, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

def daily_snapshot(df, cfg):
    if df is None or len(df) < 50:
        return None
    close = float(df["Close"].iloc[-1])
    high = float(df["High"].iloc[-1])
    low = float(df["Low"].iloc[-1])
    vol = float(df["Volume"].iloc[-1])
    turnover = (close * vol) / 1e7
    
    return {
        "price": close,
        "high": high,
        "low": low,
        "volume": vol,
        "turnover_cr": round(turnover, 2),
        "close_date": str(df.index[-1].date()),
        "atr": float(df["High"].iloc[-20:].max() - df["Low"].iloc[-20:].min()) / 20,
        "setups": ["breakout"]
    }

def sector_of(symbol):
    return ["IT & Tech", symbol]

def tick_up(val):
    return round(val + 0.05, 2)


# ==========================================
# অংশ ২: Streamlit ইউজার ইন্টারফেস ও মেনু
# ==========================================

st.title("📊 Kronos পোর্টফোলিও ও স্টক অ্যানালিসিস সিস্টেম")

cfg = load_config()

menu = st.sidebar.selectbox("মেনু নির্বাচন করুন", [
    "📌 পোর্টফোলিও স্ট্যাটাস (Show)", 
    "➕ নতুন স্টক যোগ করুন (Add)", 
    "❌ ট্রেড বন্ধ করুন (Close)", 
    "🔍 স্টক অ্যানালিসিস পাইপলাইন"
])

# ১. পোর্টফোলিও স্ট্যাটাস
if menu == "📌 পোর্টফোলিও স্ট্যাটাস (Show)":
    st.subheader("আপনার খোলা পজিশন ও অ্যালার্ট")
    pf = load_json("portfolio.json", {"positions": [], "closed": []})
    
    if not pf["positions"]:
        st.info("কোনো খোলা পজিশন নেই।")
    else:
        today = ist_now().date()
        for p in pf["positions"]:
            df = get_daily(p["symbol"], "3mo")
            last = float(df["Close"].iloc[-1]) if df is not None and len(df) else None
            held = int(np.busday_count(dt.date.fromisoformat(p["date"]), today))
            
            pnl_str, pnl_pct_str = "?", "?"
            if last is not None:
                pnl = round((last - p["entry"]) * p["qty"], 2)
                pnl_pct = round((last / p["entry"] - 1) * 100, 2)
                pnl_str = f"₹{pnl}"
                pnl_pct_str = f"{pnl_pct:+.2f}%"
            
            with st.expander(f"📌 {p['symbol']} | {p['qty']} শেয়ার | PNL: {pnl_pct_str}"):
                st.write(f"**এন্ট্রি প্রাইস:** ₹{p['entry']} | **বর্তমান দাম:** ₹{last} | **হোল্ড দিন:** {held} দিন | **স্টপ-লস:** ₹{p['sl']}")
                if last and last <= p['sl']:
                    st.error("⚠️ স্টপ ছুঁয়েছে: পরিকল্পনা অনুযায়ী বেরোন!")
                if p.get('t1') and last and last >= p['t1']:
                    st.warning("⚠️ টার্গেট ১ ছুঁয়েছে: অর্ধেক বিক্রি করুন!")
                if held >= cfg["hold_days"]:
                    st.warning(f"⚠️ {cfg['hold_days']} ট্রেডিং দিন পূর্ণ হয়েছে!")

# ২. স্টক যোগ করা
elif menu == "➕ নতুন স্টক যোগ করুন (Add)":
    st.subheader("পোর্টফোলিওতে নতুন স্টক যোগ করুন")
    with st.form("add_form"):
        sym = st.text_input("স্টকের সিম্বল (যেমন: TCS, RELIANCE)").upper().replace(".NS", "").strip()
        qty = st.number_input("শেয়ার সংখ্যা", min_value=1, value=10)
        entry = st.number_input("এন্ট্রি প্রাইস (₹)", min_value=0.0, value=100.0)
        sl = st.number_input("স্টপ-লস (₹)", min_value=0.0, value=90.0)
        t1 = st.number_input("টার্গেট ১ (ঐচ্ছিক)", min_value=0.0, value=120.0)
        submitted = st.form_submit_button("যোগ করুন")
        
        if submitted and sym:
            pf = load_json("portfolio.json", {"positions": [], "closed": []})
            if any(p["symbol"] == sym for p in pf["positions"]):
                st.error(f"{sym} আগে থেকেই পোর্টফোলিওতে আছে!")
            else:
                pf["positions"].append({
                    "symbol": sym, "qty": float(qty), "entry": float(entry), 
                    "sl": float(sl), "t1": float(t1) if t1 else None, 
                    "sector": sector_of(sym)[0], "date": ist_now().date().isoformat()
                })
                save_json("portfolio.json", pf)
                st.success(f"{sym} সফলভাবে যোগ করা হয়েছে!")

# ৩. ট্রেড বন্ধ করা
elif menu == "❌ ট্রেড বন্ধ করুন (Close)":
    st.subheader("ট্রেড ক্লোজ বা বন্ধ করুন")
    pf = load_json("portfolio.json", {"positions": [], "closed": []})
    symbols = [p["symbol"] for p in pf["positions"]]
    
    if not symbols:
        st.info("বন্ধ করার মতো কোনো পজিশন নেই।")
    else:
        with st.form("close_form"):
            sym = st.selectbox("স্টক সিলেক্ট করুন", symbols)
            exit_price = st.number_input("বিক্রির দাম (Exit Price)", min_value=0.0, value=100.0)
            submitted = st.form_submit_button("ট্রেড বন্ধ করুন")
            
            if submitted:
                pos = next((p for p in pf["positions"] if p["symbol"] == sym), None)
                if pos:
                    pnl = (float(exit_price) - pos["entry"]) * pos["qty"]
                    pf["positions"].remove(pos)
                    pf["closed"].append({
                        "symbol": sym, "pnl": round(pnl, 2), "exit": float(exit_price),
                        "date": ist_now().date().isoformat()
                    })
                    save_json("portfolio.json", pf)
                    st.success(f"ট্রেড সফলভাবে বন্ধ হয়েছে! লাভ/লোকসান: ₹{pnl:.2f}")

# ৪. স্টক অ্যানালিসিস পাইপলাইন
elif menu == "🔍 স্টক অ্যানালিসিস পাইপলাইন":
    st.subheader("স্টক ডিপ অ্যানালিসিস ও টেকনিক্যাল ওভারভিউ")
    sym_input = st.text_input("স্টকের নাম লিখুন (যেমন: TCS, INFY)", "TCS").upper().strip()
    
    if st.button("বিশ্লেষণ শুরু করুন"):
        with st.spinner("ডাটা ফেচ করা হচ্ছে এবং বিশ্লেষণ চলছে..."):
            df = get_daily(sym_input, "2y")
            if df is None:
                st.error("এই স্টকের জন্য পর্যাপ্ত ডাটা পাওয়া যায়নি। সঠিক টিকার নাম দিন।")
            else:
                snap = daily_snapshot(df, cfg)
                st.success("বিশ্লেষণ সফলভাবে সম্পন্ন হয়েছে!")
                st.metric(label="বর্তমান বাজার দর", value=f"₹{snap['price']}")
                st.write(f"**ডেইলি হাই:** ₹{snap['high']} | **ডেইলি লো:** ₹{snap['low']}")
                st.write(f"**টার্নওভার:** ₹{snap['turnover_cr']} কোটি")
                st.write(f"**ATR (Volatility):** {round(snap['atr'], 2)}")
                
                # ছোট চার্ট দেখানো
                st.line_chart(df["Close"].iloc[-90:])
