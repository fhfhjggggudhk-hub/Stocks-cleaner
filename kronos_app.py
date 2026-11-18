#!/usr/bin/env python3
"""
সংযুক্ত পোর্টফোলিও ট্র্যাকার ও এজেন্ট পাইপলাইন।
এটি দিয়ে আপনি যেমন স্টক পোর্টফোলিও ট্র্যাক ও অ্যালার্ট দেখতে পারবেন,
তেমনি পাইপলাইনের মাধ্যমে নতুন স্টক বিশ্লেষণ করে রিপোর্টও বানাতে পারবেন।

ব্যবহারের উদাহরণ:
    python combined_system.py show                  # পোর্টফোলিও পজিশন দেখুন
    python combined_system.py add TCS 10 3500 3400 3700 # পোর্টফোলিওতে স্টক যোগ করুন
    python combined_system.py close TCS 3650          # ট্রেড বন্ধ করুন
    python combined_system.py analyze TCS             # পাইপলাইন দিয়ে স্টক অ্যানালিসিস করুন
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

# ==========================================
# অংশ ১: পোর্টফোলিও ট্র্যাকার ও অ্যালার্ট ফাংশন
# ==========================================

def load_portfolio():
    return C.load_json("portfolio.json", {"positions": [], "closed": []})

def add_portfolio(sym, qty, entry, sl, t1=None):
    pf = load_portfolio()
    sym = sym.upper().replace(".NS", "")
    if any(p["symbol"] == sym for p in pf["positions"]):
        raise ValueError("%s আগে থেকেই পোর্টফোলিওতে আছে" % sym)
    pf["positions"].append({
        "symbol": sym, 
        "qty": float(qty), 
        "entry": float(entry), 
        "sl": float(sl),
        "t1": float(t1) if t1 else None, 
        "sector": C.sector_of(sym)[0],
        "date": C.ist_now().date().isoformat()
    })
    C.save_json("portfolio.json", pf)
    print("সফলভাবে পোর্টফোলিওতে যোগ হয়েছে।")

def close_portfolio(sym, exit_price):
    pf = load_portfolio()
    sym = sym.upper().replace(".NS", "")
    pos = next((p for p in pf["positions"] if p["symbol"] == sym), None)
    if not pos:
        raise ValueError("%s পোর্টফোলিওতে পাওয়া যায়নি" % sym)
    pnl = (float(exit_price) - pos["entry"]) * pos["qty"]
    pf["positions"].remove(pos)
    pf["closed"].append({
        "symbol": sym, 
        "pnl": round(pnl, 2), 
        "exit": float(exit_price),
        "date": C.ist_now().date().isoformat()
    })
    C.save_json("portfolio.json", pf)
    return pnl

def portfolio_status(cfg):
    pf = load_portfolio()
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
                row["alerts"].append("স্টপ ছুঁয়েছে: পরিকল্পনা অনুযায়ী বেরোন")
            if p.get("t1") and last >= p["t1"]:
                row["alerts"].append("টার্গেট ১ ছুঁয়েছে: অর্ধেক বিক্রি, বাকিটার স্টপ এন্ট্রিতে সরান")
        if held >= cfg["hold_days"]:
            row["alerts"].append("%d ট্রেডিং দিন পূর্ণ: সময়ের স্টপ, বেরোনোর কথা" % cfg["hold_days"])
        rows.append(row)
    return {"positions": rows, "closed": pf["closed"]}


# ==========================================
# অংশ ২: পাইপলাইন ও অ্যানালিসিস লজিক
# ==========================================

LINKS = {
    "scan": {"in": ["আপনার দেওয়া স্টকের নাম", "দৈনিক চার্ট (Yahoo)"], "out": ["news", "event", "strat"]},
    "news": {"in": ["scan (কোন স্টক, কোন সেক্টর)", "Google ও Bing News", "সেক্টর ইনডেক্স"], "out": ["strat", "final"]},
    "event": {"in": ["scan (ভলিউমের হিসাব)", "Yahoo-র ক্যালেন্ডার ও আর্থিক ফল"], "out": ["strat", "final"]},
    "strat": {"in": ["scan (সাপোর্ট, ATR)", "news ও event (ঝুঁকি)", "৪H/১H চার্ট"], "out": ["tm", "final"]},
    "tm": {"in": ["strat (এন্ট্রি, স্টপ, টার্গেট)", "২ বছরের ডেটা"], "out": ["final"]},
    "final": {"in": ["scan, news, event, strat, tm সবার আউটপুট"], "out": ["আপনার চূড়ান্ত সিদ্ধান্ত"]},
}

def build_scenarios(snap, timing, plan, df, cfg):
    if "stop" not in plan:
        return []
    sl, support = plan["stop"], plan.get("support_level")
    avail = bool(timing.get("available"))
    cur = float(timing["last_price"]) if avail else float(snap["price"])
    trig = bool(timing.get("trigger"))
    cands = [("A", "এখনই (১H ট্রিগার হয়েছে)" if trig else "এখনকার দামে (কনফার্মেশন ছাড়া)", float(plan["entry"]),
              "১H বুলিশ ক্যান্ডেল সাপোর্টের কাছে বন্ধ হয়েছে" if trig else "১H কনফার্মেশন ছাড়া এন্ট্রি", "now")]
    if trig and timing.get("confirm_above"):
        lvl, cond = float(timing["confirm_above"]), "ওপরে বন্ধ হলে"
    elif avail and timing.get("recent_high_3"):
        lvl, cond = float(timing["recent_high_3"]), "সর্বোচ্চ সীমার ওপরে উঠলে"
    else:
        lvl, cond = float(df["High"].iloc[-1]), "হাই দাম পার করলে"
    
    b = C.tick_up(lvl * 1.001)
    if b > cur * 1.0005:
        cands.append(("B", "কনফার্মেশনে", b, cond, "up"))
    if support:
        c_entry = C.tick_up(float(support) * 1.004)
        if c_entry < cur * 0.996:
            cands.append(("C", "সাপোর্ট ছুঁলে", c_entry, "দাম সাপোর্ট লেভেলে নামলে", "down"))
            
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
        
        out.append(dict(tg, key=key, name=name, condition=cond, entry=round(entry, 2), stop=sl, risk_per_share=risk,
                        risk_pct=round(risk / entry * 100, 2), reach_pct=reach_pct,
                        p_t1_pct=mc["p_target1_pct"], p_stop_pct=mc["p_stop_pct"], 
                        share_pct=mc["share_target_pct"], breakeven_pct=mc["breakeven_pct"], 
                        edge_pts=mc["edge_pts"], combined_pct=combined, qty=max(qty, 0), ok=ok))
    return out

def pick_best(scens):
    if not scens:
        return None
    pool = [s for s in scens if s["ok"]]
    if not pool:
        return None
    b = max(pool, key=lambda s: (s["edge_pts"] if s["edge_pts"] is not None else -999, s["combined_pct"] or 0))
    return {k: b[k] for k in ("key", "name", "entry", "rr1", "p_t1_pct", "breakeven_pct", "edge_pts", "combined_pct", "ok")}

def analyze_stock(sym, cfg, snap=None, macro=None, df=None):
    df = df if df is not None else C.get_daily(sym, "2y")
    if df is None:
        return None
    snap = snap or C.daily_snapshot(df, cfg)
    if snap is None:
        return None
    info = A2.fetch_info(sym)
    sec_name, _, guessed = A12.resolve_sector(sym, info)
    ctx = A2.analyze(sym, cfg, macro, info=info, df=df)
    fund = A11.analyze(sym, info=info)
    secrep = A12.sector_report(sec_name, sym, df, guessed)
    rad = A10.radar(sym, info.get("longName") or info.get("shortName"), sec_name)
    rad["ai"] = A10.ai_review(rad)
    
    ctx["sector_name"] = sec_name
    ctx["sector"] = {"stance": secrep["stance"], "ret10_pct": (secrep.get("own") or {}).get("ret21")}
    ctx["fundamental"] = {"status": {"safe": "pass", "avoid": "fail", "caution": "fail"}.get(fund["verdict"], "unknown"), "note": fund["summary"]}
    
    timing = A3.analyze(sym, cfg, snap)
    plan = A4.make_plan(sym, snap, timing, cfg)
    tm = A5.run(sym, plan, cfg, df)
    risk = A6.evaluate(sym, plan, ctx, cfg)
    scens = build_scenarios(snap, timing, plan, df, cfg)
    verdict = A7.decide(snap, ctx, timing, plan, tm, risk, cfg, scens, {"radar": rad, "fund": fund, "secrep": secrep})
    
    return {"symbol": sym, "company": rad["company"], "snap": snap, "ctx": ctx, "timing": timing, "plan": plan,
            "tm": tm, "risk": risk, "verdict": verdict, "scenarios": scens, "best": pick_best(scens)}


# ==========================================
# অংশ ৩: প্রধান মেনু ও নিয়ন্ত্রণ (Main Function)
# ==========================================

def main(argv=None):
    a = sys.argv[1:]
    cfg = C.load_config()
    try:
        if not a:
            print("ব্যবহারবিধি:")
            print("  python combined_system.py show")
            print("  python combined_system.py add <symbol> <qty> <entry> <sl> [t1]")
            print("  python combined_system.py close <symbol> <exit_price>")
            print("  python combined_system.py analyze <symbol>")
            return 0

        cmd = a[0]
        if cmd == "show":
            st = portfolio_status(cfg)
            if not st["positions"]:
                print("কোনো খোলা পজিশন নেই।")
            for r in st["positions"]:
                print("%-10s %s শেয়ার @ ₹%s | এখন %s | %s | %d দিন | SL ₹%s" % (
                    r["symbol"], r["qty"], r["entry"], r["last"], 
                    ("%+.2f%%" % r["pnl_pct"]) if r["last"] else "?", r["days_held"], r["sl"]))
                for al in r["alerts"]:
                    print("   ! " + al)
                    
        elif cmd == "add" and len(a) >= 5:
            add_portfolio(*a[1:6])
            
        elif cmd == "close" and len(a) == 3:
            pnl = close_portfolio(a[1], a[2])
            print("ট্রেড বন্ধ। লাভ/লোকসান ₹%.2f" % pnl)
            
        elif cmd == "analyze" and len(a) >= 2:
            sym = a[1].upper()
            print("%s বিশ্লেষণ করা হচ্ছে..." % sym)
            macro = A2.macro_context()
            res = analyze_stock(sym, cfg, macro=macro)
            if res:
                print("বিশ্লেষণ সম্পন্ন! ভার্ডিক্ট কোড: %s" % res["verdict"]["code"])
                print("বিস্তারিত রিপোর্ট তৈরি হয়েছে।")
            else:
                print("বিশ্লেষণ করা সম্ভব হয়নি, পর্যাপ্ত ডেটা নেই।")
        else:
            print("ভুল কমান্ড বা আর্গুমেন্ট দেওয়া হয়েছে।")
            
    except (ValueError, TypeError) as e:
        print("ত্রুটি:", e)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
