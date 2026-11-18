#!/usr/bin/env python3
"""
সব এজেন্ট এক ফাইলে: পাইপলাইন (এজেন্ট ১-৭, ১০-১২) + পোর্টফোলিও ট্র্যাকার (এজেন্ট ৮)।

প্রতিটা এজেন্ট আগের এজেন্টের আউটপুট ইনপুট হিসেবে নেয়।

  ১ স্ক্যানার ─┬─> ২ নিউজ/ইভেন্ট ──────────────┐
               ├─> ৩ এন্ট্রি টাইমার ─> ৪ এক্সিট ─┼─> ৬ রিস্ক ─┐
               └──────────────────────> ৫ টাইম মেশিন <┘         ├─> ৭ ভার্ডিক্ট
                                       (৪-এর প্ল্যান)  ২,৩,৪,৫,৬ ─┘

ব্যবহার:
    python trading_agents.py analyze TCS INFY M&M      # আপনার দেওয়া স্টকগুলোর পূর্ণ বিশ্লেষণ
    python trading_agents.py scan TCS INFY RELIANCE    # স্ক্যান করে সেরা N টার বিশ্লেষণ

    python trading_agents.py show                      # পোর্টফোলিও দেখুন
    python trading_agents.py add TCS 10 3500 3400 3700 # সিম্বল, শেয়ার, এন্ট্রি, স্টপ, টার্গেট১
    python trading_agents.py close TCS 3650            # বিক্রির দাম

পোর্টফোলিও ব্রোকারে কিছু করে না: ট্রেড আপনি নিজের ব্রোকারে করে এখানে হাতে লিখে রাখবেন।
"""
import datetime as dt
import sys

import numpy as np

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

# ════════════════════════════════════════════════════════════════
# অংশ ১: পাইপলাইন
# ════════════════════════════════════════════════════════════════

# কে কার কাছ থেকে ডেটা নেয় (অ্যাপে দেখানোর জন্য)
LINKS = {
    "scan": {"in": ["আপনার দেওয়া স্টকের নাম", "দৈনিক চার্ট (Yahoo)"], "out": ["news", "event", "strat"]},
    "news": {"in": ["scan (কোন স্টক, কোন সেক্টর)", "Google ও Bing News", "সেক্টর ইনডেক্স"], "out": ["strat", "final"]},
    "event": {"in": ["scan (ভলিউমের হিসাব)", "Yahoo-র ক্যালেন্ডার ও আর্থিক ফল"], "out": ["strat", "final"]},
    "strat": {"in": ["scan (সাপোর্ট, ATR)", "news ও event (ঝুঁকি)", "৪H/১H চার্ট"], "out": ["tm", "final"]},
    "tm": {"in": ["strat (এন্ট্রি, স্টপ, টার্গেট)", "২ বছরের ডেটা"], "out": ["final"]},
    "final": {"in": ["scan, news, event, strat, tm সবার আউটপুট"], "out": ["আপনার চূড়ান্ত সিদ্ধান্ত ও পড়ে শোনানো"]},
}


def build_scenarios(snap, timing, plan, df, cfg):
    """২-৩টা এন্ট্রি জায়গা (এখন / কনফার্মেশনে / সাপোর্ট ছুঁলে), প্রতিটার জন্য আলাদা স্টপ-টার্গেট ও চান্স।"""
    if "stop" not in plan:
        return []
    sl, support = plan["stop"], plan.get("support_level")
    avail = bool(timing.get("available"))
    cur = float(timing["last_price"]) if avail else float(snap["price"])
    trig = bool(timing.get("trigger"))
    cands = [("A", "এখনই (১H ট্রিগার হয়েছে)" if trig else "এখনকার দামে (কনফার্মেশন ছাড়া)", float(plan["entry"]),
              "১H বুলিশ ক্যান্ডেল সাপোর্টের কাছে বন্ধ হয়েছে: ট্রিগার বারের ক্লোজে ঢোকা" if trig
              else "১H কনফার্মেশন ছাড়াই এখনকার দামে ঢোকা: ঝুঁকি বেশি", "now")]
    if trig and timing.get("confirm_above"):
        lvl, cond = float(timing["confirm_above"]), "পরের ১H বার ট্রিগার বারের হাই (₹%s)-এর ওপরে বন্ধ হলে" % timing["confirm_above"]
    elif avail and timing.get("recent_high_3"):
        lvl, cond = float(timing["recent_high_3"]), "১H বার গত ৩টা বারের সর্বোচ্চ (₹%s)-এর ওপরে বন্ধ হলে" % timing["recent_high_3"]
    else:
        lvl, cond = float(df["High"].iloc[-1]), "দাম গতকালের হাই (₹%s)-এর ওপরে উঠলে" % round(float(df["High"].iloc[-1]), 2)
    b = C.tick_up(lvl * 1.001)
    if b > cur * 1.0005:
        cands.append(("B", "কনফার্মেশনে (ওপরে ভাঙলে)", b, cond, "up"))
    if support:
        c_entry = C.tick_up(float(support) * 1.004)
        if c_entry < cur * 0.996 and (cur - c_entry) <= 1.3 * cfg["hold_days"] ** 0.5 * snap["atr"]:   # হোল্ড-সময়ে নামার মতো দূরত্বের মধ্যে
            cands.append(("C", "সাপোর্ট ছুঁলে (নিচে নামলে)", c_entry,
                          "দাম ₹%s-এ নামলে (সাপোর্ট ₹%s-এর ঠিক ওপরে); ১H-এ ঘুরে দাঁড়ানো দেখে ঢোকাই নিরাপদ" % (c_entry, support), "down"))
    budget = cfg["capital"] * cfg["risk_per_trade_pct"] / 100.0
    out = []
    for key, name, entry, cond, mode in cands:
        risk = round(entry - sl, 2)
        if risk <= 0:
            continue
        tg = A4.targets_for(entry, risk, snap, timing, cfg["hold_days"])
        mc = A5.monte_carlo(df, entry, sl, tg["target1"], cfg)
        if not mc.get("available"):
            continue
        reach = 1.0 if mode == "now" else A5.reach_probability(df, cur, entry, cfg, up=(mode == "up"))
        reach_pct = None if reach is None else round(100 * reach, 1)
        combined = None if reach_pct is None else round(reach_pct * mc["p_target1_pct"] / 100.0, 1)
        qty = int(min(budget // risk, cfg["capital"] * cfg["max_position_pct"] / 100.0 // entry))
        ok = tg["rr1"] >= cfg["min_rr"] and (mc["edge_pts"] is None or mc["edge_pts"] >= 0)
        why = []
        if tg["rr1"] < cfg["min_rr"]:
            why.append("R:R %.2f, ন্যূনতম %g-এর কম" % (tg["rr1"], cfg["min_rr"]))
        if mc["edge_pts"] is not None and mc["edge_pts"] < 0:
            why.append("টার্গেট আগে ছোঁয়ার চান্স ব্রেক-ইভেনের নিচে")
        out.append(dict(tg, key=key, name=name, condition=cond, entry=round(entry, 2), stop=sl, risk_per_share=risk,
                        risk_pct=round(risk / entry * 100, 2), reach_pct=reach_pct,
                        p_t1_pct=mc["p_target1_pct"], p_stop_pct=mc["p_stop_pct"], p_neither_pct=mc["p_neither_pct"],
                        share_pct=mc["share_target_pct"], breakeven_pct=mc["breakeven_pct"], edge_pts=mc["edge_pts"],
                        combined_pct=combined, qty=max(qty, 0), position_pct=round(max(qty, 0) * entry / cfg["capital"] * 100, 1), ok=ok, why=why))
    return out


def pick_best(scens):
    if not scens:
        return None
    pool = [s for s in scens if s["ok"]]       # নিয়মে মেলে এমন এন্ট্রি না থাকলে "সেরা" বলা হবে না
    if not pool:
        return None
    b = max(pool, key=lambda s: (s["edge_pts"] if s["edge_pts"] is not None else -999, s["combined_pct"] or 0))
    return {k: b[k] for k in ("key", "name", "entry", "rr1", "p_t1_pct", "breakeven_pct", "edge_pts", "combined_pct", "ok")}


def analyze_stock(sym, cfg, snap=None, macro=None, df=None):
    """একটা স্টকের জন্য সব এজেন্ট ক্রমে চালায়; প্রতিটা আগের জনের ডেটা নেয়। ডেটা না পেলে None।"""
    df = df if df is not None else C.get_daily(sym, "2y")
    if df is None:
        return None
    snap = snap or C.daily_snapshot(df, cfg)
    if snap is None:
        return None
    info = A2.fetch_info(sym)                                   # একবারই আনা: নাম, ফান্ডামেন্টাল, সেক্টর
    sec_name, _, guessed = A12.resolve_sector(sym, info)
    ctx = A2.analyze(sym, cfg, macro, info=info, df=df)         # ইভেন্ট, ভলিউম, বাজার প্রেক্ষাপট
    fund = A11.analyze(sym, info=info)                          # ফান্ডামেন্টাল সেফটি
    secrep = A12.sector_report(sec_name, sym, df, guessed)      # সেক্টরের অবস্থা
    rad = A10.radar(sym, info.get("longName") or info.get("shortName"), sec_name)   # প্যানিক/ক্ষতিকর খবর
    rad["ai"] = A10.ai_review(rad)                              # ANTHROPIC_API_KEY থাকলে Claude-এর সারাংশ
    ctx["sector_name"] = sec_name
    ctx["sector"] = {"stance": secrep["stance"], "ret10_pct": (secrep.get("own") or {}).get("ret21")}
    ctx["fundamental"] = {"status": {"safe": "pass", "avoid": "fail", "caution": "fail"}.get(fund["verdict"], "unknown"), "note": fund["summary"]}
    extra = {"radar": rad, "fund": fund, "secrep": secrep}
    timing = A3.analyze(sym, cfg, snap)
    plan = A4.make_plan(sym, snap, timing, cfg)
    tm = A5.run(sym, plan, cfg, df)
    risk = A6.evaluate(sym, plan, ctx, cfg)
    scens = build_scenarios(snap, timing, plan, df, cfg)
    verdict = A7.decide(snap, ctx, timing, plan, tm, risk, cfg, scens, extra)
    if snap["turnover_cr"] < cfg["min_turnover_cr"] or snap["price"] < cfg["min_price"]:
        risk["warnings"].append("কম লেনদেন/কম দাম (গড় ₹%s কোটি/দিন, দাম ₹%s): কেনা-বেচার দামে ফারাক বড় হতে পারে, স্টপ লাগলে দাম পরিকল্পিতের চেয়ে খারাপ হতে পারে"
                                % (snap["turnover_cr"], snap["price"]))
    d = df.iloc[-90:]
    chart = {"dates": [x.date().isoformat() for x in d.index],
             "close": [round(float(x), 2) for x in d["Close"]],
             "ema20": [round(float(x), 2) for x in C.ema(df["Close"], 20).iloc[-90:]],
             "ema50": [round(float(x), 2) for x in C.ema(df["Close"], 50).iloc[-90:]]}
    return {"symbol": sym, "company": rad["company"], "snap": snap, "ctx": ctx, "timing": timing, "plan": plan,
            "tm": tm, "risk": risk, "verdict": verdict, "chart": chart, "scenarios": scens, "best": pick_best(scens),
            "radar": rad, "fund": fund, "secrep": secrep, "volume": ctx.get("volume")}


def health(results, macro, scan_stats):
    """আসল ডেটা সত্যিই এসেছে কি না: কোন তথ্য মিলেছে আর কোনটা যাচাই করা যায়নি।"""
    return {
        "stocks": len(results),
        "last_data_date": max((r["snap"]["close_date"] for r in results), default=None),
        "scan_fetched": scan_stats["fetched"], "scan_failed": scan_stats["failed"],
        "hourly_ok": sum(1 for r in results if r["timing"].get("available")),
        "events_known": sum(1 for r in results if r["ctx"]["events"].get("event_risk") is not None),
        "fund_known": sum(1 for r in results if r["fund"]["verdict"] != "unknown"),
        "sector_known": sum(1 for r in results if r["secrep"]["available"]),
        "news_ok": sum(1 for r in results if r["radar"]["queries_ok"] > 0),
        "macro_ok": bool(macro.get("available")),
    }


PRIORITY = {"ENTER": 0, "MONDAY": 1, "WAIT": 2, "SKIP": 3}


def sort_key(r):
    b = r.get("best") or {}
    e = b.get("edge_pts")
    return (PRIORITY[r["verdict"]["code"]], -(e if e is not None else -999), -r["verdict"]["ratio"])


def run_all(cfg, symbols, log=None, progress=None):
    """১ নম্বর দিয়ে স্ক্যান, তারপর সেরা N টার জন্য ২-৭। পুরো ফল output/report.json-এ সেভ।"""
    log = log or (lambda m: None)
    A2.clear_cache()
    A10.clear_cache()
    A12.clear_cache()
    log("১) স্ক্যানার: %d টি স্টক..." % len(symbols))
    hits, stats = A1.scan(symbols, cfg, log=log)
    top = hits[:cfg["top_n"]]
    log("২) ম্যাক্রো/গ্লোবাল প্রেক্ষাপট...")
    macro = A2.macro_context()
    results = []
    for i, h in enumerate(top, 1):
        if progress:
            progress(i - 1, len(top), h["symbol"])
        log("   বিশ্লেষণ: %s (%d/%d)" % (h["symbol"], i, len(top)))
        try:
            r = analyze_stock(h["symbol"], cfg, snap=h, macro=macro)
        except Exception as e:  # একটা স্টকের সমস্যায় বাকিগুলো থামবে না
            log("   %s: ত্রুটি (%s), বাদ" % (h["symbol"], e))
            continue
        if r:
            results.append(r)
    results.sort(key=sort_key)
    if progress:
        progress(len(top), len(top), "")
    report = {"mode": "scan", "created_at": C.ist_now().isoformat(), "config": cfg, "scan_stats": stats,
              "hits": hits, "macro": macro, "results": results, "failed": [],
              "health": health(results, macro, stats)}
    C.save_json("report.json", report)
    return report


def analyze_list(cfg, symbols, log=None, progress=None):
    """আপনার দেওয়া প্রতিটা NSE স্টকের জন্য ২-৭ নম্বর এজেন্ট চালায়: কোনো ছাঁকনি বা সীমা নেই।
    ডেটা না পেলে চুপচাপ বাদ না দিয়ে "failed" তালিকায় কারণসহ রাখে।"""
    log = log or (lambda m: None)
    A2.clear_cache()
    A10.clear_cache()
    A12.clear_cache()
    log("ম্যাক্রো/গ্লোবাল প্রেক্ষাপট...")
    macro = A2.macro_context()
    results, snaps, failed = [], [], []
    n = len(symbols)
    for i, sym in enumerate(symbols, 1):
        if progress:
            progress(i - 1, n, sym)
        log("বিশ্লেষণ: %s (%d/%d)" % (sym, i, n))
        try:
            df = C.get_daily(sym, "2y")
            if df is None:
                failed.append({"symbol": sym, "reason": "ডেটা পাওয়া যায়নি (NSE টিকার ঠিক আছে? যেমন TATASTEEL, M&M)"})
                continue
            snap = C.daily_snapshot(df, cfg)
            if snap is None:
                failed.append({"symbol": sym, "reason": "ডেটা কম (৮০ দিনের কম: নতুন তালিকাভুক্ত?)"})
                continue
            snap["symbol"] = sym
            snap["sector"] = C.sector_of(sym)[0]
            snap["score"] = A1.prelim_score(snap)
            r = analyze_stock(sym, cfg, snap=snap, macro=macro, df=df)
        except Exception as e:
            failed.append({"symbol": sym, "reason": "ত্রুটি: %s" % e})
            continue
        if r is None:
            failed.append({"symbol": sym, "reason": "বিশ্লেষণ করা যায়নি"})
            continue
        snaps.append(snap)
        results.append(r)
    results.sort(key=sort_key)
    if progress:
        progress(n, n, "")
    stats = {"universe": n, "fetched": len(snaps), "failed": len(failed), "short": 0, "illiquid": 0,
             "nosetup": sum(1 for s in snaps if not s["setups"]), "hits": sum(1 for s in snaps if s["setups"])}
    report = {"mode": "my_list", "created_at": C.ist_now().isoformat(), "config": cfg, "scan_stats": stats,
              "hits": snaps, "macro": macro, "results": results, "failed": failed,
              "health": health(results, macro, stats)}
    C.save_json("report.json", report)
    return report


# ════════════════════════════════════════════════════════════════
# অংশ ২: পোর্টফোলিও ট্র্যাকার ও অ্যালার্ট (এজেন্ট ৮)
# ════════════════════════════════════════════════════════════════

def pf_load():
    return C.load_json("portfolio.json", {"positions": [], "closed": []})


def pf_add(sym, qty, entry, sl, t1=None):
    pf = pf_load()
    sym = sym.upper().replace(".NS", "")
    if any(p["symbol"] == sym for p in pf["positions"]):
        raise ValueError("%s আগে থেকেই আছে" % sym)
    pf["positions"].append({"symbol": sym, "qty": float(qty), "entry": float(entry), "sl": float(sl),
                            "t1": float(t1) if t1 else None, "sector": C.sector_of(sym)[0],
                            "date": C.ist_now().date().isoformat()})
    C.save_json("portfolio.json", pf)


def pf_close(sym, exit_price):
    pf = pf_load()
    sym = sym.upper().replace(".NS", "")
    pos = next((p for p in pf["positions"] if p["symbol"] == sym), None)
    if not pos:
        raise ValueError("%s পাওয়া যায়নি" % sym)
    pnl = (float(exit_price) - pos["entry"]) * pos["qty"]
    pf["positions"].remove(pos)
    pf["closed"].append({"symbol": sym, "pnl": round(pnl, 2), "exit": float(exit_price),
                         "date": C.ist_now().date().isoformat()})
    C.save_json("portfolio.json", pf)
    return pnl


def pf_status(cfg):
    pf = pf_load()
    rows = []
    today = C.ist_now().date()
    for p in pf["positions"]:
        df = C.get_daily(p["symbol"], "3mo")
        last = float(df["Close"].iloc[-1]) if df is not None and len(df) else None
        held = int(np.busday_count(dt.date.fromisoformat(p["date"]), today))
        row = dict(p, last=last, days_held=held, alerts=[])
        if last is not None:
            row["pnl"] = round((last - p["entry"]) * p["qty"], 2)
            row["pnl_pct"] = round((last / p["entry"] - 1) * 100, 2)
            if last <= p["sl"]:
                row["alerts"].append("স্টপ ছুঁয়েছে: পরিকল্পনা অনুযায়ী বেরোন")
            if p.get("t1") and last >= p["t1"]:
                row["alerts"].append("টার্গেট ১ ছুঁয়েছে: অর্ধেক বিক্রি, বাকিটার স্টপ এন্ট্রিতে সরান")
        if held >= cfg["hold_days"]:
            row["alerts"].append("%d ট্রেডিং দিন পূর্ণ: সময়ের স্টপ, বেরোনোর কথা" % cfg["hold_days"])
        rows.append(row)
    return {"positions": rows, "closed": pf["closed"]}


def print_portfolio(cfg):
    st = pf_status(cfg)
    if not st["positions"]:
        print("কোনো খোলা পজিশন নেই")
    for r in st["positions"]:
        print("%-10s %s শেয়ার @ ₹%s | এখন %s | %s | %d দিন | SL ₹%s" % (
            r["symbol"], r["qty"], r["entry"], r["last"],
            ("%+.2f%%" % r["pnl_pct"]) if r.get("pnl_pct") is not None else "?",
            r["days_held"], r["sl"]))
        for al in r["alerts"]:
            print("   ! " + al)


# ════════════════════════════════════════════════════════════════
# কমান্ড লাইন
# ════════════════════════════════════════════════════════════════

def print_results(report):
    for r in report["results"]:
        b = r.get("best") or {}
        print("%-12s %-7s এন্ট্রি: %s" % (r["symbol"], r["verdict"]["code"], b.get("entry", "-")))
    for f in report.get("failed", []):
        print("%-12s বাদ: %s" % (f["symbol"], f["reason"]))
    print("সম্পূর্ণ ফল: output/report.json")


def main():
    a = sys.argv[1:]
    cfg = C.load_config()
    cmd = a[0] if a else "show"
    try:
        if cmd == "add" and len(a) >= 5:
            pf_add(*a[1:6])
            print("যোগ হয়েছে")
        elif cmd == "close" and len(a) == 3:
            print("বন্ধ। লাভ/লোকসান ₹%.2f" % pf_close(a[1], a[2]))
        elif cmd == "analyze" and len(a) >= 2:
            syms = [s.upper().replace(".NS", "") for s in a[1:]]
            print_results(analyze_list(cfg, syms, log=print))
        elif cmd == "scan" and len(a) >= 2:
            syms = [s.upper().replace(".NS", "") for s in a[1:]]
            print_results(run_all(cfg, syms, log=print))
        elif cmd == "show":
            print_portfolio(cfg)
        else:
            print(__doc__)
            return 1
    except (ValueError, TypeError) as e:
        print("ত্রুটি:", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
