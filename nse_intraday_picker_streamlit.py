import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
from plyer import notification
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, time as dt_time
import pytz

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config("📊 NSE Intraday Stock Picker", layout="wide")
st.title("📈 NSE Intraday Stock Picker Dashboard")

# ----------------------------
# Sidebar Filters & Settings
# ----------------------------
st.sidebar.header("⚙️ Filter Settings")

# Default values
interval = "5m"
use_volume = True
use_atr = True
use_rs = True
use_breakout = True
use_ema_rsi = True
vol_spike = 2.0
atr_mult = 2.0
atr_percentile = 50
momentum_lookback = 5
rs_lookback = 5
max_symbols = 100
auto_refresh_sec = 180
notify_desktop = True
notify_telegram = False
BOT_TOKEN = ""
CHAT_ID = ""

# Sidebar inputs
interval = st.sidebar.selectbox("⏱️ Intraday Interval (bars)", ["5m", "15m", "30m", "1h"], index=0)
use_volume = st.sidebar.checkbox("📊 Enable Volume Spike Filter", use_volume)
use_atr = st.sidebar.checkbox("📈 Enable ATR Filter", use_atr)
use_rs = st.sidebar.checkbox("💪 Enable Relative Strength Filter", use_rs)
use_breakout = st.sidebar.checkbox("🚀 Enable Technical Breakout Filter", use_breakout)
use_ema_rsi = st.sidebar.checkbox("📉 EMA(20) + RSI(10) Filter", use_ema_rsi)

vol_spike = st.sidebar.slider("Volume spike multiplier", 1.0, 10.0, vol_spike, 0.1)
atr_mult = st.sidebar.slider("ATR multiplier for stop", 0.5, 5.0, atr_mult, 0.1)
atr_percentile = st.sidebar.slider("ATR percentile threshold", 0, 100, atr_percentile)
momentum_lookback = st.sidebar.slider("Momentum lookback (bars)", 1, 20, momentum_lookback)
rs_lookback = st.sidebar.slider("RS lookback days", 1, 20, rs_lookback)
max_symbols = st.sidebar.slider("Max F&O symbols to scan", 50, 200, max_symbols)
auto_refresh_sec = st.sidebar.slider("Auto refresh (seconds)", 30, 600, auto_refresh_sec, 10)

# Notifications
notify_desktop = st.sidebar.checkbox("💻 Enable Desktop Notification", notify_desktop)
notify_telegram = st.sidebar.checkbox("📨 Enable Telegram Notification", notify_telegram)
BOT_TOKEN = st.sidebar.text_input("Telegram Bot Token", BOT_TOKEN, type="password")
CHAT_ID = st.sidebar.text_input("Telegram Chat ID", CHAT_ID)

# ----------------------------
# Telegram Validation
# ----------------------------
def validate_telegram(bot_token, chat_id):
    if not bot_token or not chat_id:
        return False, "BOT_TOKEN or CHAT_ID is empty"
    test_message = "✅ Telegram test message from NSE Intraday Picker"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={test_message}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return False, f"Failed: {resp.json().get('description', 'Unknown error')}"
        return True, "Telegram setup OK ✅"
    except Exception as e:
        return False, f"Error: {str(e)}"

if BOT_TOKEN and CHAT_ID:
    valid, message = validate_telegram(BOT_TOKEN, CHAT_ID)
    if valid:
        st.sidebar.success(message)
    else:
        st.sidebar.error(message)

# ----------------------------
# Preset Test Combinations
# ----------------------------
st.subheader("🧪 Preset Test Combinations")

preset_combos = {
    "Combo 1 - Aggressive 5m All Filters": {"interval":"5m","use_volume":True,"use_atr":True,"use_rs":True,"use_breakout":True,"use_ema_rsi":True,"vol_spike":2.0,"atr_mult":2.0,"momentum_lookback":5,"rs_lookback":5,"target_type":"ATR"},
    "Combo 2 - 5m Volume+Breakout+EMA-RSI": {"interval":"5m","use_volume":True,"use_atr":False,"use_rs":False,"use_breakout":True,"use_ema_rsi":True,"vol_spike":1.8,"atr_mult":1.5,"momentum_lookback":3,"rs_lookback":5,"target_type":"Fixed %","fixed_percent":2},
    "Combo 3 - 5m EMA-RSI only": {"interval":"5m","use_volume":False,"use_atr":False,"use_rs":False,"use_breakout":False,"use_ema_rsi":True,"target_type":"Fixed Rs","fixed_rs":5},
    "Combo 4 - 15m All Filters": {"interval":"15m","use_volume":True,"use_atr":True,"use_rs":True,"use_breakout":True,"use_ema_rsi":True,"vol_spike":1.5,"atr_mult":2.0,"momentum_lookback":5,"rs_lookback":5,"target_type":"ATR"},
    "Combo 5 - 15m Vol+ATR+RS": {"interval":"15m","use_volume":True,"use_atr":True,"use_rs":True,"use_breakout":False,"use_ema_rsi":False,"vol_spike":2.0,"atr_mult":2.0,"momentum_lookback":5,"rs_lookback":5,"target_type":"Fixed %","fixed_percent":3},
    "Combo 6 - 15m EMA-RSI+Breakout": {"interval":"15m","use_volume":True,"use_atr":True,"use_rs":False,"use_breakout":True,"use_ema_rsi":True,"vol_spike":1.5,"atr_mult":1.5,"momentum_lookback":5,"target_type":"Fixed Rs","fixed_rs":7},
    "Combo 7 - 30m EMA-RSI only": {"interval":"30m","use_volume":False,"use_atr":False,"use_rs":False,"use_breakout":False,"use_ema_rsi":True,"target_type":"ATR"},
    "Combo 8 - 30m EMA-RSI+RS": {"interval":"30m","use_volume":False,"use_atr":False,"use_rs":True,"use_breakout":False,"use_ema_rsi":True,"rs_lookback":5,"target_type":"Fixed %","fixed_percent":2},
    "Combo 9 - 30m ATR+Breakout": {"interval":"30m","use_volume":False,"use_atr":True,"use_rs":False,"use_breakout":True,"use_ema_rsi":False,"atr_mult":2.0,"momentum_lookback":8,"target_type":"Fixed Rs","fixed_rs":10},
    "Combo 10 - 1h EMA-RSI+RS": {"interval":"1h","use_volume":False,"use_atr":False,"use_rs":True,"use_breakout":False,"use_ema_rsi":True,"rs_lookback":10,"target_type":"ATR"},
    "Combo 11 - 1h EMA-RSI only": {"interval":"1h","use_volume":False,"use_atr":False,"use_rs":False,"use_breakout":False,"use_ema_rsi":True,"target_type":"Fixed %","fixed_percent":2},
    "Combo 12 - 5m Aggressive Max Sensitivity": {"interval":"5m","use_volume":True,"use_atr":True,"use_rs":True,"use_breakout":True,"use_ema_rsi":True,"vol_spike":2.5,"atr_mult":2.5,"momentum_lookback":10,"rs_lookback":10,"target_type":"Fixed %","fixed_percent":5},
}

selected_combo = st.selectbox("Select a Preset Test Combo", list(preset_combos.keys()))
combo = preset_combos[selected_combo]

# Apply combo settings
interval = combo.get("interval", interval)
use_volume = combo.get("use_volume", use_volume)
use_atr = combo.get("use_atr", use_atr)
use_rs = combo.get("use_rs", use_rs)
use_breakout = combo.get("use_breakout", use_breakout)
use_ema_rsi = combo.get("use_ema_rsi", use_ema_rsi)
vol_spike = combo.get("vol_spike", vol_spike)
atr_mult = combo.get("atr_mult", atr_mult)
momentum_lookback = combo.get("momentum_lookback", momentum_lookback)
rs_lookback = combo.get("rs_lookback", rs_lookback)
target_type = combo.get("target_type", "ATR")
fixed_percent = combo.get("fixed_percent", 2)
fixed_rs = combo.get("fixed_rs", 5)

# Display target type
st.info(f"🎯 Applied Target: {target_type}")

# ----------------------------
# Helper Functions
# ----------------------------
@st.cache_data(ttl=3600)
def get_fo_symbols(max_symbols=100):
    try:
        from nsepython import fnolist
        fo_list = fnolist()
        return fo_list[:max_symbols]
    except:
        return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

@st.cache_data(ttl=300)
def get_price_data(symbol, period="5d", interval="15m"):
    try:
        df = yf.download(symbol + ".NS", period=period, interval=interval, progress=False)
        df.dropna(inplace=True)
        return df
    except:
        return pd.DataFrame()

def get_fundamentals(symbol):
    try:
        info = yf.Ticker(symbol + ".NS").info
        keys = ["sector", "industry", "marketCap", "trailingPE", "forwardPE",
                "priceToBook", "dividendYield", "returnOnEquity", "profitMargins"]
        return {k: info.get(k, "N/A") for k in keys}
    except:
        return {"error": "N/A"}

# ----------------------------
# Notifications
# ----------------------------
def notify_stock(symbol, last_price, entry=None, stop_loss=None, target=None,
                 desktop_enabled=True, telegram_enabled=True):
    msg = f"📢 {symbol} shortlisted!\n💵 Last: {last_price}"
    if entry: msg += f"\n🟢 Entry: {entry}"
    if stop_loss: msg += f"\n❌ Stop-Loss: {stop_loss}"
    if target: msg += f"\n🏆 Target: {target}"
    if desktop_enabled:
        notification.notify(title=f"📈 NSE Picker: {symbol}", message=msg, timeout=5)
    if telegram_enabled and BOT_TOKEN and CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}"
            requests.get(url, timeout=5)
        except: pass

# ----------------------------
# Stock Scanner
# ----------------------------
def scan_stock(df, symbol):
    if df.empty or len(df) < 20: return False, [], None, None, None
    df["ATR"] = df["High"] - df["Low"]
    df["AvgVol"] = df["Volume"].rolling(20).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(10).mean()
    avg_loss = loss.rolling(10).mean()
    df["RSI10"] = 100 - (100 / (1 + (avg_gain/(avg_loss.replace(0,1)))))
    last_vol = float(df["Volume"].values[-1])
    avg_vol_val = float(df["AvgVol"].values[-1]) if not np.isnan(df["AvgVol"].values[-1]) else 0
    last_atr = float(df["ATR"].values[-1])
    last_close = float(df["Close"].values[-1])

    conds, reasons = [], []

    if use_volume:
        cond = last_vol > avg_vol_val * vol_spike
        conds.append(cond)
        if cond: reasons.append(f"📊 Volume spike: {last_vol:.0f} > {avg_vol_val:.0f}×{vol_spike}")
    if use_atr:
        atr_thresh = df["ATR"].quantile(atr_percentile / 100)
        cond = last_atr > atr_thresh * atr_mult
        conds.append(cond)
        if cond: reasons.append(f"📈 ATR breakout: {last_atr:.2f} > {atr_thresh:.2f}×{atr_mult}")
    if use_breakout:
        high_break = last_close > df["Close"].rolling(momentum_lookback).max().values[-2]
        conds.append(high_break)
        if high_break: reasons.append(f"🚀 Price breakout above {momentum_lookback}-bar high")
    if use_rs:
        nifty = get_price_data("^NSEI", period="5d", interval="1d")
        if not nifty.empty:
            rs = (df["Close"].pct_change(rs_lookback).iloc[-1]) - (nifty["Close"].pct_change(rs_lookback).iloc[-1])
            cond = rs > 0
            conds.append(cond)
            if cond: reasons.append("💪 Positive RS vs NIFTY")

    entry_price, stop_loss, target_price = None, None, None
    if use_ema_rsi:
        ema_cond = last_close > df["EMA20"].values[-1]
        rsi_cond = df["RSI10"].values[-1] > 50
        trend_cond = ema_cond and rsi_cond
        conds.append(trend_cond)
        if trend_cond: reasons.append("🟢 Price > EMA20 & RSI10 > 50 (trend confirmed)")
        if trend_cond:
            entry_price = last_close
            stop_loss = entry_price - 2*last_atr
            if target_type == "ATR": target_price = entry_price + 2*(entry_price-stop_loss)
            elif target_type == "Fixed %": target_price = entry_price*(1 + fixed_percent/100)
            elif target_type == "Fixed Rs": target_price = entry_price + fixed_rs

    return all(conds), reasons, entry_price, stop_loss, target_price

# ----------------------------
# Manual Stock Analyzer
# ----------------------------
st.subheader("📝 Manual Stock Analyzer (Multiple Stocks)")
manual_symbols = st.text_area("Enter stock symbols separated by commas (e.g., RELIANCE,TCS,INFY)")
if manual_symbols:
    manual_list = [s.strip().upper() for s in manual_symbols.split(",") if s.strip()]
    for manual_symbol in manual_list:
        df_manual = get_price_data(manual_symbol, interval=interval)
        passed, reasons, entry, stop_loss, target = scan_stock(df_manual, manual_symbol)
        if not df_manual.empty:
            last_price = float(df_manual["Close"].values[-1])
            st.write(f"📌 **{manual_symbol}**")
            st.write(f"💵 Last: {last_price} | 🟢 Entry: {entry} | ❌ Stop: {stop_loss} | 🏆 Target: {target}")
            st.write("**Filters Passed:**", "✅ Yes" if passed else "❌ No")
            st.write("**Why:**")
            if reasons: [st.markdown(f"- {r}") for r in reasons]
            else: st.write("Did not meet criteria.")
            with st.expander("View Fundamentals"): st.json(get_fundamentals(manual_symbol))
            if passed: notify_stock(manual_symbol, last_price, entry, stop_loss, target,
                                     desktop_enabled=notify_desktop, telegram_enabled=notify_telegram)

# ----------------------------
# Market Status Check
# ----------------------------
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)
market_open = dt_time(9, 15)
market_close = dt_time(15, 30)
if not (market_open <= now.time() <= market_close):
    st.warning("⚠️ Market is currently closed. Displaying latest available data.")

# ----------------------------
# Manual Refresh Button
# ----------------------------
if st.button("🔄 Refresh Data"):
    st.experimental_rerun()

# ----------------------------
# Auto-refresh
# ----------------------------
if auto_refresh_sec > 0:
    st_autorefresh(interval=auto_refresh_sec*1000, key="auto_refresh")

# ----------------------------
# F&O Auto Scan
# ----------------------------
st.subheader("🔍 F&O Intraday Scanner")
fo_symbols = get_fo_symbols(max_symbols)
candidates = []

progress = st.progress(0)
for i, sym in enumerate(fo_symbols):
    df = get_price_data(sym, interval=interval)
    is_candidate, reasons, entry, stop_loss, target = scan_stock(df, sym)
    if is_candidate:
        last_price = float(df["Close"].values[-1])
        candidates.append((sym, reasons, last_price, entry, stop_loss, target))
        notify_stock(sym, last_price, entry, stop_loss, target,
                     desktop_enabled=notify_desktop, telegram_enabled=notify_telegram)
    progress.progress((i+1)/len(fo_symbols))
progress.empty()

if not candidates:
    st.warning("⚠️ No candidates found. Market may be closed or filters too strict.")
else:
    st.success(f"✅ Found {len(candidates)} candidates:")
    for sym, reasons, last_price, entry, stop_loss, target in candidates:
        st.subheader(f"📌 {sym}")
        st.write(f"💵 Last: {last_price} | 🟢 Entry: {entry} | ❌ Stop: {stop_loss} | 🏆 Target: {target}")
        st.write("**Why picked:**")
        for r in reasons:
            st.markdown(f"- {r}")

