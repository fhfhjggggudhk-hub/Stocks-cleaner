#!/usr/bin/env python3
"""
সুইং ট্রেডিং এজেন্ট: অ্যাপ (Streamlit)।
হোমে ৮টা এজেন্টের কার্ড। কার্ডে ট্যাপ করলে ওই এজেন্টের ভেতরের কাজ দেখা যায়।
এজেন্টরা আগেরজনের আউটপুট নিয়ে পরেরজনকে পাঠায়, শেষে ৭ নম্বর চূড়ান্ত সিদ্ধান্ত দেয়।

চালানো:  streamlit run app.py
এটা বিনিয়োগ পরামর্শ নয়। সম্ভাবনা অতীতের অনুমান, নিশ্চয়তা নয়।
"""
import streamlit as st

import common as C
import pipeline as P
import a1_scanner as A1
import a7_verdict as A7
import a8_portfolio as A8

st.set_page_config(page_title="সুইং ট্রেডিং এজেন্ট", page_icon="📈", layout="centered")

AGENTS = [
    ("a1", "🔍", "স্ক্যানার", "চার্ট স্ক্যান করে সেটআপ খোঁজে"),
    ("a2", "📰", "নিউজ ও ইভেন্ট", "খবর, রেজাল্ট, সেক্টর, গ্লোবাল ঝুঁকি"),
    ("a3", "⏱️", "এন্ট্রি টাইমার", "৪H/১H চার্টে ঢোকার মুহূর্ত"),
    ("a4", "🎯", "এক্সিট প্ল্যানার", "স্টপ লস ও টার্গেট"),
    ("a5", "⏳", "টাইম মেশিন", "ইতিহাস ও ১০,০০০ সিমুলেশন"),
    ("a6", "🛡️", "রিস্ক ম্যানেজার", "সীমা ভাঙলে আটকায়, শেয়ার হিসাব"),
    ("a7", "⚖️", "ফাইনাল ভার্ডিক্ট", "১১ পয়েন্টের মিল ও সিদ্ধান্ত"),
    ("a8", "💼", "পোর্টফোলিও", "খোলা ট্রেড, লাভ-লোকসান, অ্যালার্ট"),
]
NAME = {k: "%s %s" % (e, n) for k, e, n, _ in AGENTS}
ACTION_ICON = {"ENTER": "🟢", "MONDAY": "🟡", "WAIT": "🟠", "SKIP": "🔴"}

ss = st.session_state
ss.setdefault("page", "home")
if "report" not in ss:
    ss.report = C.load_json("report.json")


def go(page):
    ss.page = page
    st.rerun()


def metrics(pairs):
    cols = st.columns(len(pairs))
    for c, (k, v) in zip(cols, pairs):
        c.metric(k, v)


def links_box(key):
    L = P.LINKS[key]
    names = lambda xs: ", ".join(NAME.get(x, x) for x in xs)
    st.info("**ইনপুট নেয়:** %s\n\n**আউটপুট পাঠায়:** %s" % ("; ".join(L["in"]), names(L["out"])))


def pick_stock(rep):
    syms = [r["symbol"] for r in rep["results"]]
    if not syms:
        st.warning("গভীর বিশ্লেষণের মতো কোনো স্টক নেই। হোমে গিয়ে আবার চালান।")
        return None
    s = st.selectbox("স্টক বাছুন", syms)
    return next(r for r in rep["results"] if r["symbol"] == s)


# ---------------------------------------------------------------- হোম

def home():
    st.title("📈 সুইং ট্রেডিং এজেন্ট")
    st.caption("NSE | ৩-৭ দিনের হোল্ড | এটা বিনিয়োগ পরামর্শ নয়")
    with st.expander("▶ সব এজেন্ট চালান", expanded=ss.report is None):
        txt = st.text_input("নিজের স্টক (কমা দিয়ে, ফাঁকা = ডিফল্ট তালিকা)", "")
        if st.button("এজেন্টদের কাজে লাগান", type="primary", use_container_width=True):
            cfg = C.load_config()
            syms = A1.read_universe(txt or None)
            bar = st.progress(0.0, text="শুরু হচ্ছে...")
            box = st.empty()
            ss.report = P.run_all(
                cfg, syms, log=lambda m: box.caption(m),
                progress=lambda i, n, s: bar.progress(i / max(n, 1), text="বিশ্লেষণ: %s" % s))
            st.rerun()
    rep = ss.report
    if rep:
        st.caption("শেষ আপডেট: %s" % rep["created_at"][:16].replace("T", " "))
        st.subheader("চূড়ান্ত সিদ্ধান্ত")
        if not rep["results"]:
            st.write("আজ গভীর বিশ্লেষণের মতো সেটআপ মেলেনি।")
        for r in rep["results"]:
            v = r["verdict"]
            with st.expander("%s %s: %s (%d/%d)" % (ACTION_ICON[v["code"]], r["symbol"], v["action"], v["passed"], v["applicable"])):
                st.code(A7.format_report(r), language=None)
    st.subheader("এজেন্টরা")
    st.caption("কার্ডে ট্যাপ করে ভেতরে দেখুন")
    for i in range(0, len(AGENTS), 2):
        cols = st.columns(2)
        for col, (k, e, n, d) in zip(cols, AGENTS[i:i + 2]):
            with col:
                if st.button("%s %s" % (e, n), key="b_" + k, use_container_width=True):
                    go(k)
                st.caption(d + _status(k, rep))


def _status(k, rep):
    if not rep:
        return ""
    if k == "a1":
        return " | %d হিট" % rep["scan_stats"]["hits"]
    if k == "a8":
        return ""
    return " | %d স্টক" % len(rep["results"])


# ---------------------------------------------------------------- এজেন্ট পেজ

def a1_page(rep):
    s = rep["scan_stats"]
    metrics([("স্ক্যান", s["universe"]), ("ডেটা এসেছে", s["fetched"]), ("সেটআপ", s["hits"])])
    rows = [{"স্টক": h["symbol"], "দাম": h["price"], "স্কোর": h["score"], "ট্রেন্ড": A1.TREND_BN[h["trend"]],
             "RSI": h["rsi"], "সাপোর্ট": h["support"], "সাপোর্ট থেকে %": h["dist_support_pct"],
             "সেটআপ": ", ".join(A1.LABEL[x] for x in h["setups"])} for h in rep["hits"]]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("এটা নিয়মে মিলে যাওয়া চার্টের তালিকা, কেনার পরামর্শ নয়।")


def a2_page(r):
    c = r["ctx"]
    st.write("**ফান্ডামেন্টাল:** %s। %s" % (c["fundamental"]["status"], c["fundamental"]["note"]))
    st.write("**ইভেন্ট:** %s" % (c["events"]["note"] or "-"))
    st.write("**সেক্টর (%s):** %s" % (c["sector_name"], c["sector"]["stance"]))
    m = c["macro"]
    st.write("**গ্লোবাল ঝুঁকি:** %s" % ("; ".join(m["reasons"]) if m.get("risk_flag") else "বড় কোনো পতাকা নেই"))
    st.write("**হেডলাইন** (খবর লিড, তথ্য নয়; পড়ে যাচাই করুন):")
    for t in c["news"]["titles"][:6]:
        st.write(("⚠️ " if t in c["news"]["negative"] else "• ") + t)


def a3_page(r):
    t = r["timing"]
    if not t.get("available"):
        st.warning(t["note"])
        return
    metrics([("৪H RSI", t["rsi_4h"]), ("শেষ দাম", t["last_price"]), ("ট্রিগার", "হ্যাঁ" if t["trigger"] else "না")])
    st.write("৪H সাপোর্ট: %s | রেজিস্ট্যান্স: %s" % (t["supports_4h"], t["resistances_4h"]))
    st.write("ফিবোনাচি কাছে: %s" % ([n["level"] for n in t["near_fib"]] or "নেই"))
    for f in t["patterns_1h"]:
        st.write("১H প্যাটার্ন: %s (%s) %s" % ("+".join(f["patterns"]), f["bar_start"], "সাপোর্টে ✓" if f["at_support"] else "সাপোর্টের কাছে নয়"))
    if not t["patterns_1h"]:
        st.write("১H-এ বুলিশ প্যাটার্ন নেই")


def a4_page(r):
    p = r["plan"]
    if not p["valid"]:
        st.error("; ".join(p["flags"]))
        return
    metrics([("এন্ট্রি", p["entry"]), ("স্টপ", p["stop"]), ("T1", p["target1"]), ("T2", p["target2"])])
    metrics([("R:R (T1)", p["rr1"]), ("R:R (T2)", p["rr2"]), ("ঝুঁকি/শেয়ার", p["risk_per_share"])])
    st.caption("এন্ট্রি: %s | স্টপ: %s | T1: %s" % (p["entry_basis"], p["stop_basis"], p["target1_basis"]))
    for f in p["flags"]:
        st.warning(f)
    st.write(p["management"])
    st.caption(p["note"])


def a5_page(r):
    tm = r["tm"]
    if not tm.get("available"):
        st.warning(tm.get("note", ""))
        return
    h, m = tm["history"], tm["mc"]
    st.write("**ইতিহাস (২ বছর):**")
    if h.get("trades"):
        metrics([("এন্ট্রি", h["trades"]), ("হিট-রেট %", h["hit_rate_pct"]), ("গড় নিট R", h["avg_R"])])
        if h["note"]:
            st.warning(h["note"])
    else:
        st.write(h.get("note", ""))
    if m.get("available"):
        st.write("**সিমুলেশন (%s বার, seed %d):**" % ("{:,}".format(m["runs"]), m["seed"]))
        metrics([("T1 আগে %", m["p_target1_pct"]), ("স্টপ আগে %", m["p_stop_pct"]), ("কোনোটাই না %", m["p_neither_pct"])])
        st.write("ব্রেক-ইভেন %.1f%% → এজ %+.1f পয়েন্ট: **%s**" % (m["breakeven_pct"], m["edge_pts"] or 0, tm["edge_label"]))
        st.write("৭ দিন পরে দাম: মধ্যম ₹%s, ৯০%% সিমুলেশন ₹%s থেকে ₹%s" % (m["price_median"], m["price_p5"], m["price_p95"]))
    st.caption("অতীত ডেটার ভিত্তিতে অনুমান, ভবিষ্যদ্বাণী নয়। গ্যাপে লোকসান পরিকল্পিতের চেয়ে বেশি হতে পারে।")


def a6_page(r):
    k = r["risk"]
    (st.success if k["verdict"] == "PASS" else st.error)("রিস্ক চেক: " + k["verdict"])
    if k["qty"]:
        metrics([("শেয়ার", k["qty"]), ("পজিশন ₹", k["position_value"]), ("সর্বোচ্চ লোকসান ₹", k["max_loss_inr"])])
    for x in k["reasons"]:
        st.error(x)
    for x in k["warnings"]:
        st.warning(x)


def a7_page(r):
    v = r["verdict"]
    st.subheader("%s %s" % (ACTION_ICON[v["code"]], v["action"]))
    st.write("সংকেতের মিল: **%d/%d**" % (v["passed"], v["applicable"]))
    for p in v["confluence"]:
        st.write("%s %s" % ({True: "✅", False: "❌", "?": "❓", None: "➖"}[p["status"]], p["label"]))
        if p["detail"]:
            st.caption(p["detail"])
    for x in v["reasons"]:
        st.write("→ " + x)
    with st.expander("পুরো রিপোর্ট"):
        st.code(A7.format_report(r), language=None)


def a8_page():
    cfg = C.load_config()
    with st.form("add"):
        st.write("**নতুন ট্রেড লিখে রাখুন** (ব্রোকারে নিজে কেনার পর)")
        c = st.columns(5)
        sym = c[0].text_input("স্টক")
        qty = c[1].number_input("শেয়ার", min_value=1, value=1)
        ent = c[2].number_input("এন্ট্রি", min_value=0.0)
        sl = c[3].number_input("স্টপ", min_value=0.0)
        t1 = c[4].number_input("টার্গেট ১", min_value=0.0)
        if st.form_submit_button("যোগ করুন") and sym:
            try:
                A8.add(sym, qty, ent, sl, t1 or None)
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    stt = A8.status(cfg)
    if not stt["positions"]:
        st.write("কোনো খোলা পজিশন নেই")
    for p in stt["positions"]:
        st.write("**%s** %s শেয়ার @ ₹%s | এখন %s | %s | %d দিন" % (
            p["symbol"], p["qty"], p["entry"], p["last"], ("%+.2f%%" % p["pnl_pct"]) if p.get("pnl_pct") is not None else "?", p["days_held"]))
        for a in p["alerts"]:
            st.warning(a)
        ex = st.number_input("বিক্রির দাম", min_value=0.0, key="x_" + p["symbol"])
        if st.button("%s বন্ধ করুন" % p["symbol"], key="c_" + p["symbol"]) and ex:
            A8.close(p["symbol"], ex)
            st.rerun()
    if stt["closed"]:
        st.write("বন্ধ ট্রেড:")
        st.dataframe(stt["closed"], use_container_width=True, hide_index=True)


def agent_page(k):
    if st.button("← হোম"):
        go("home")
    st.title(NAME[k])
    links_box(k)
    rep = ss.report
    if k == "a8":
        return a8_page()
    if not rep:
        st.warning("আগে হোমে গিয়ে এজেন্টদের চালান।")
        return
    if k == "a1":
        return a1_page(rep)
    r = pick_stock(rep)
    if r:
        {"a2": a2_page, "a3": a3_page, "a4": a4_page, "a5": a5_page, "a6": a6_page, "a7": a7_page}[k](r)
        with st.expander("কাঁচা ডেটা (JSON)"):
            st.json({"a2": r["ctx"], "a3": r["timing"], "a4": r["plan"], "a5": r["tm"], "a6": r["risk"], "a7": r["verdict"]}[k])


(home if ss.page == "home" else lambda: agent_page(ss.page))()
