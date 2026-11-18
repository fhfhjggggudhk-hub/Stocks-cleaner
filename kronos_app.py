import datetime as dt
import numpy as np
import streamlit as st

import common as C
import a1_scanner as A1
import a2_news_events as A2
import a3_entry_timer as A3
import a4_exit_planner as A4
import a5_time_machine as A5
import a6_risk_manager as A6
import a7_verdict as A7
import a10_news_radar as A10
import a11_fundamentals as A11
import a12_sector as A12

st.set_page_config(page_title="Kronos Stock System", layout="wide")

st.title("📊 Kronos পোর্টফোলিও ও স্টক অ্যানালিসিস সিস্টেম")

# কনফিগারেশন লোড
cfg = C.load_config()

# সাইডবার মেনু
menu = st.sidebar.selectbox("মেনু নির্বাচন করুন", ["পোর্টফোলিও স্ট্যাটাস", "নতুন স্টক যোগ করুন", "ট্রেড বন্ধ করুন", "স্টক অ্যানালিসিস পাইপলাইন"])

# ==========================================
# ১. পোর্টফোলিও স্ট্যাটাস (Show)
# ==========================================
if menu == "পোর্টফোলিও স্ট্যাটাস":
    st.subheader("📌 আপনার খোলা পজিশনসমূহ")
    pf = C.load_json("portfolio.json", {"positions": [], "closed": []})
    
    if not pf["positions"]:
        st.info("কোনো খোলা পজিশন নেই।")
    else:
        today = C.ist_now().date()
        for p in pf["positions"]:
            df = C.get_daily(p["symbol"], "3mo")
            last = float(df["Close"].iloc[-1]) if df is not None and len(df) else None
            held = int(np.busday_count(dt.date.fromisoformat(p["date"]), today))
            
            pnl_pct_str = "?"
            if last is not None:
                pnl = round((last - p["entry"]) * p["qty"], 2)
                pnl_pct = round((last / p["entry"] - 1) * 100, 2)
                pnl_pct_str = f"{pnl_pct:+.2f}%"
            
            with st.expander(f"📌 {p['symbol']} - {p['qty']} শেয়ার (PNL: {pnl_pct_str})"):
                st.write(f"**এন্ট্রি প্রাইস:** ₹{p['entry']} | **বর্তমান দাম:** ₹{last} | **হোল্ড দিন:** {held} দিন | **স্টপ-লস:** ₹{p['sl']}")
                if last and last <= p['sl']:
                    st.error("⚠️ স্টপ ছুঁয়েছে: পরিকল্পনা অনুযায়ী বেরোন!")
                if p.get('t1') and last and last >= p['t1']:
                    st.warning("⚠️ টার্গেট ১ ছুঁয়েছে: অর্ধেক বিক্রি করুন!")
                if held >= cfg["hold_days"]:
                    st.warning(f"⚠️ {cfg['hold_days']} ট্রেডিং দিন পূর্ণ হয়েছে!")

# ==========================================
# ২. পোর্টফোলিওতে স্টক যোগ করা (Add)
# ==========================================
elif menu == "নতুন স্টক যোগ করুন":
    st.subheader("➕ পোর্টফোলিওতে নতুন স্টক যোগ করুন")
    with st.form("add_form"):
        sym = st.text_input("স্টকের সিম্বল (যেমন: TCS)").upper().replace(".NS", "")
        qty = st.number_input("শেয়ার সংখ্যা", min_value=1, value=10)
        entry = st.number_input("এন্ট্রি প্রাইস (₹)", min_value=0.0, value=100.0)
        sl = st.number_input("স্টপ-লস (₹)", min_value=0.0, value=90.0)
        t1 = st.number_input("টার্গেট ১ (ঐচ্ছিক)", min_value=0.0, value=120.0)
        submitted = st.form_submit_button("যোগ করুন")
        
        if submitted:
            pf = C.load_json("portfolio.json", {"positions": [], "closed": []})
            if any(p["symbol"] == sym for p in pf["positions"]):
                st.error(f"{sym} আগে থেকেই পোর্টফোলিওতে আছে!")
            else:
                pf["positions"].append({
                    "symbol": sym, "qty": float(qty), "entry": float(entry), 
                    "sl": float(sl), "t1": float(t1) if t1 else None, 
                    "sector": C.sector_of(sym)[0], "date": C.ist_now().date().isoformat()
                })
                C.save_json("portfolio.json", pf)
                st.success(f"{sym} সফলভাবে যোগ করা হয়েছে!")

# ==========================================
# ৩. ট্রেড বন্ধ করা (Close)
# ==========================================
elif menu == "ট্রেড বন্ধ করুন":
    st.subheader("❌ ট্রেড বন্ধ বা ক্লোজ করুন")
    pf = C.load_json("portfolio.json", {"positions": [], "closed": []})
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
                        "date": C.ist_now().date().isoformat()
                    })
                    C.save_json("portfolio.json", pf)
                    st.success(f"ট্রেড বন্ধ হয়েছে! লাভ/লোকসান: ₹{pnl:.2f}")

# ==========================================
# ৪. স্টক অ্যানালিসিস পাইপলাইন (Analyze)
# ==========================================
elif menu == "স্টক অ্যানালিসিস পাইপলাইন":
    st.subheader("🔍 স্টক ডিপ অ্যানালিসিস ও এজেন্ট পাইপলাইন")
    sym_input = st.text_input("স্টকের নাম লিখুন (যেমন: RELIANCE, TCS)", "TCS").upper().strip()
    
    if st.button("বিশ্লেষণ শুরু করুন"):
        with st.spinner("এজেন্টরা কাজ করছে, দয়া করে অপেক্ষা করুন..."):
            try:
                macro = A2.macro_context()
                df = C.get_daily(sym_input, "2y")
                if df is None:
                    st.error("ডেটা পাওয়া যায়নি। সঠিক টিকার নাম দিন।")
                else:
                    snap = C.daily_snapshot(df, cfg)
                    info = A2.fetch_info(sym_input)
                    sec_name, _, guessed = A12.resolve_sector(sym_input, info)
                    ctx = A2.analyze(sym_input, cfg, macro, info=info, df=df)
                    fund = A11.analyze(sym_input, info=info)
                    secrep = A12.sector_report(sec_name, sym_input, df, guessed)
                    rad = A10.radar(sym_input, info.get("longName") or info.get("shortName"), sec_name)
                    
                    timing = A3.analyze(sym_input, cfg, snap)
                    plan = A4.make_plan(sym_input, snap, timing, cfg)
                    tm = A5.run(sym_input, plan, cfg, df)
                    risk = A6.evaluate(sym_input, plan, ctx, cfg)
                    
                    st.success("বিশ্লেষণ সম্পন্ন হয়েছে!")
                    st.metric(label="কোম্পানির নাম", value=rad.get("company", sym_input))
                    st.write(f"**বর্তমান দাম:** ₹{snap['price']} | **সেক্টর:** {sec_name}")
                    st.write(f"**ফান্ডামেন্টাল স্ট্যাটাস:** {fund['verdict']}")
                    st.json(risk)
            except Exception as e:
                st.error(f"ত্রুটি দেখা দিয়েছে: {e}")
