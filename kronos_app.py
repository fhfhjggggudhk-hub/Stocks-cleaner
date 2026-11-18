import datetime as dt
import json
import os
import pandas as pd
import yfinance as yf
import streamlit as st

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
    turnover = (close * vol) / 1e7 # কোটি টাকায়
    
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

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()
