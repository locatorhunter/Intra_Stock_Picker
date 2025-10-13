import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
from plyer import notification
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, time as dt_time
import pytz
import talib

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config("📊 NSE Intraday Stock Picker", layout="wide")
st.title("📈 NSE Intraday Stock Picker Dashboard")

# ----------------------------
# Sidebar Filters & Settings
# ----------------------------

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
show_technical_predictions = st.sidebar.checkbox("Show Technical Predictions", value=True)

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

notify_desktop = st.sidebar.checkbox("💻 Enable Desktop Notification", notify_desktop)
notify_telegram = st.sidebar.checkbox("📨 Enable Telegram Notification", notify_telegram)
BOT_TOKEN = st.sidebar.text_input("Telegram Bot Token", BOT_TOKEN, type="password")
CHAT_ID = st.sidebar.text_input("Telegram Chat ID", CHAT_ID)

# -------------- Dummy placeholder variables to prevent errors ----------------
def fetch_intraday_data(stock, interval):
    # Dummy yfinance intraday data fetch for technical section
    try:
        df = yf.download(stock + ".NS", period="5d", interval=interval, progress=False)
        df.rename(columns=str.lower, inplace=True)  # talib expects lowercase column names
        return df
    except:
        return pd.DataFrame()

shortlisted_stocks = []  # This will be assigned from scan results below

# ---------------- Technical analysis function --------------
def analyze_technical_indicators(df):
    result = {}

# Ensure column is lowercase and 1D numpy array
    close_col = "close" if "close" in df.columns else "Close"
    close_series = df[close_col].dropna()
    close_clean = close_series.values.astype(float).flatten()  # ENSURE 1D
    
    if len(close_clean) < 7:
        result["RSI Signal"] = "⚪ Not enough data"
        return result

    rsi_vals = talib.RSI(close_clean, timeperiod=7)
    rsi_series = pd.Series(np.nan, index=close_series.index)
    rsi_series.iloc[-len(rsi_vals):] = rsi_vals
    df['RSI'] = rsi_series

    latest_rsi = rsi_series.dropna().iloc[-1]

    if latest_rsi > 80:
        result["RSI Signal"] = "🔴 Overbought (Sell Bias)"
    elif latest_rsi < 20:
        result["RSI Signal"] = "🟢 Oversold (Buy Bias)"
    else:
        result["RSI Signal"] = "⚪ Neutral (Wait)"

    recent_highs = df['high'].tail(20)
    recent_lows = df['low'].tail(20)
    support = float(recent_lows.min())  # ensures scalar
    resistance = float(recent_highs.max())
    last_close = float(df['close'].iloc[-1])

    if abs(last_close - support) / support < 0.01:
        result["S/R Zone"] = "🟢 Near Support"
    elif abs(last_close - resistance) / resistance < 0.01:
        result["S/R Zone"] = "🔴 Near Resistance"
    else:
        result["S/R Zone"] = "⚪ Mid Range"

    print(type(df['high']))
    # Defensive: Handle if 'high' is a Series or accidental DataFrame
    if 'high' in df.columns:
        highs_temp = df['high'].tail(10)
        if isinstance(highs_temp, pd.Series):
            highs = highs_temp.tolist()
        elif isinstance(highs_temp, pd.DataFrame):
            highs = highs_temp.iloc[:, 0].tolist()  # Take the first column
        else:
            highs = list(highs_temp)
    else:
        highs = []

    if 'low' in df.columns:
        lows_temp = df['low'].tail(10)
        if isinstance(lows_temp, pd.Series):
            lows = lows_temp.tolist()
        elif isinstance(lows_temp, pd.DataFrame):
            lows = lows_temp.iloc[:, 0].tolist()
        else:
            lows = list(lows_temp)
    else:
        lows = []


    double_top = highs[-3] < highs[-2] > highs[-1]
    double_bottom = lows[-3] > lows[-2] < lows[-1]

    if double_top:
        result["Pattern"] = "🔴 Double Top (Bearish)"
    elif double_bottom:
        result["Pattern"] = "🟢 Double Bottom (Bullish)"
    else:
        result["Pattern"] = "⚪ None"

    closes = df['close'].tail(15).to_numpy()
    x = np.arange(len(closes))
    slope = np.polyfit(x, closes, 1)[0]
    if slope > 0:
        result["Trend"] = "🟢 Uptrend"
    else:
        result["Trend"] = "🔴 Downtrend"

    signals = list(result.values())
    bullish = sum("🟢" in s for s in signals)
    bearish = sum("🔴" in s for s in signals)

    if bullish > bearish:
        result["Verdict"] = "✅ Strong Buy Setup"
    elif bearish > bullish:
        result["Verdict"] = "❌ Sell Setup"
    else:
        result["Verdict"] = "⚪ Neutral / Wait"

    return result
# ---------------------------
# Market Timing Warning
# ---------------------------
IST = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(IST)
market_open_time = dt_time(9, 15)
market_close_time = dt_time(15, 30)
if not (market_open_time <= now_ist.time() <= market_close_time):
    st.warning("📴 Market is currently closed — displaying latest historical data.")
    
# --- Run Technical Predictions Section ---
if show_technical_predictions:
    st.subheader("📈 Technical Predictions for Shortlisted Stocks")
    if len(shortlisted_stocks) == 0:
        st.info("No shortlisted stocks to show predictions for.")
    else:
        for stock in shortlisted_stocks:
            df = fetch_intraday_data(stock, interval)
            if df is not None and not df.empty:
                analysis = analyze_technical_indicators(df)
                st.markdown(f"### {stock}")
                st.table(pd.DataFrame(analysis, index=[0]))
            else:
                st.warning(f"No data found for {stock}")

# ---------------- Telegram Validation ----------------
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

# ------------------------
# Helper functions for scanning and notifications
def get_fundamentals(symbol):
    try:
        info = yf.Ticker(symbol + ".NS").info
        keys = ["sector", "industry", "marketCap", "trailingPE", "forwardPE",
                "priceToBook", "dividendYield", "returnOnEquity", "profitMargins"]
        return {k: info.get(k, "N/A") for k in keys}
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=3600)
def get_fo_symbols():
    return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"][:max_symbols]

@st.cache_data(ttl=300)
def get_price_data(symbol, period="5d", interval="15m"):
    try:
        df = yf.download(symbol + ".NS", period=period, interval=interval, progress=False)
        if df.empty:
            return pd.DataFrame()
        df.dropna(inplace=True)
        return df
    except:
        return pd.DataFrame()

def notify_stock(symbol, last_price, entry=None, stop_loss=None, target=None,
                 desktop_enabled=True, telegram_enabled=True):
    msg = f"📢 {symbol} shortlisted!\n💵 Last: {last_price}"
    if entry: msg += f"\n🟢 Entry: {entry}"
    if stop_loss: msg += f"\n❌ Stop-Loss: {stop_loss}"
    if target: msg += f"\n🏆 Target: {target}"

    if desktop_enabled:
        try:
            notification.notify(title=f"📈 NSE Picker: {symbol}", message=msg, timeout=5)
           # st.write(f"Desktop notification sent: {symbol}")
        except Exception as e:
            st.warning(f"Desktop notification error: {e}")

    if telegram_enabled and BOT_TOKEN and CHAT_ID:
        valid, _ = validate_telegram(BOT_TOKEN, CHAT_ID)
        if valid:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            try:
                requests.get(url, params={"chat_id": CHAT_ID, "text": msg}, timeout=5)
               # st.write(f"Telegram notification sent: {symbol}")
            except Exception as e:
                st.warning(f"Telegram notification error: {e}")

def scan_stock(df, symbol):
    if df.empty or len(df) < 20:
        return False, [], None, None, None

    df["ATR"] = df["High"] - df["Low"]
    df["AvgVol"] = df["Volume"].rolling(20).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(10).mean()
    avg_loss = loss.rolling(10).mean()
    df["RSI10"] = 100 - (100 / (1 + avg_gain/avg_loss))

    try:
        last_vol = float(df["Volume"].values[-1])
        avg_vol_val = float(df["AvgVol"].values[-1]) if not np.isnan(df["AvgVol"].values[-1]) else 0
        last_atr = float(df["ATR"].values[-1])
        last_close = float(df["Close"].values[-1])
    except:
        return False, [], None, None, None

    conds, reasons = [], []

    if use_volume:
        cond = last_vol > avg_vol_val * vol_spike
        conds.append(cond)
        if cond:
            reasons.append("📊 Volume spike")

    if use_atr:
        atr_thresh = df["ATR"].quantile(atr_percentile / 100)
        cond = last_atr > atr_thresh * atr_mult
        conds.append(cond)
        if cond:
            reasons.append("📈 ATR breakout")

    if use_breakout:
        high_break = last_close > df["Close"].rolling(momentum_lookback).max().values[-2]
        conds.append(high_break)
        if high_break:
            reasons.append(f"🚀 Price breakout above {momentum_lookback}-bar high")

    if use_rs:
        nifty = get_price_data("^NSEI", period="5d", interval="1d")
        if not nifty.empty:
            rs = (df["Close"].pct_change(rs_lookback).iloc[-1]) - (nifty["Close"].pct_change(rs_lookback).iloc[-1])
            cond = rs > 0
            conds.append(cond)
            if cond:
                reasons.append("💪 Positive RS vs NIFTY")

    entry_price, stop_loss, target_price = None, None, None
    if use_ema_rsi:
        ema_cond = last_close > df["EMA20"].values[-1]
        rsi_cond = df["RSI10"].values[-1] > 50
        trend_cond = ema_cond and rsi_cond
        conds.append(trend_cond)
        if trend_cond:
            reasons.append("🟢 EMA20 and RSI10 confirmation")
            entry_price = last_close
            stop_loss = entry_price - 2*last_atr
            target_price = entry_price + 2*(entry_price-stop_loss)

    return all(conds), reasons, entry_price, stop_loss, target_price

# ---------------------------
# Scanner and Results Display
# ---------------------------

candidates = []
shortlisted_stocks = []

fo_symbols = get_fo_symbols()
progress = st.progress(0)

for i, sym in enumerate(fo_symbols):
    df = get_price_data(sym, interval=interval)
    passed, reasons, entry, stop, target = scan_stock(df, sym)
    if passed:
        last_close = df["Close"].values[-1]
        candidates.append({
            "Symbol": sym,
            "Last Close": last_close,
            "Entry": entry,
            "Stop Loss": stop,
            "Target": target,
            "Reasons": ", ".join(reasons)
        })
        shortlisted_stocks.append(sym)
        notify_stock(sym, last_close, entry, stop, target, desktop_enabled=notify_desktop, telegram_enabled=notify_telegram)
    progress.progress((i+1)/len(fo_symbols))
progress.empty()

if candidates:
    st.success(f"✅ Found {len(candidates)} candidates")
    st.dataframe(pd.DataFrame(candidates))
else:
    st.info("⚠️ No candidates found.")

# ---------------------------
# Technical Predictions Section
# ---------------------------

if show_technical_predictions:
    st.subheader("📈 Technical Predictions for Shortlisted Stocks")
    if not shortlisted_stocks:
        st.info("No shortlisted stocks to show predictions for.")
    else:
        for stock in shortlisted_stocks:
            df = fetch_intraday_data(stock, interval)
            if df is not None and not df.empty:
                analysis = analyze_technical_indicators(df)
                st.markdown(f"### {stock}")
                st.table(pd.DataFrame(analysis, index=[0]))
            else:
                st.warning(f"No data found for {stock}")

# ----------------------------
# Manual Refresh Button
# ----------------------------
if st.button("🔄 Refresh Data"):
    try:
        st.experimental_rerun()
    except AttributeError:
        st.rerun()

# ----------------------------
# Manual Stock Analyzer
# ----------------------------
st.subheader("📝 Manual Stock Analyzer (Multiple Stocks)")

manual_symbols = st.text_area(
    "Enter stock symbols separated by commas (e.g., RELIANCE,TCS,INFY)"
)

if manual_symbols:
    manual_list = [s.strip().upper() for s in manual_symbols.split(",") if s.strip()]
    for manual_symbol in manual_list:
        df_manual = get_price_data(manual_symbol, interval=interval)
        passed, reasons, entry, stop_loss, target = scan_stock(df_manual, manual_symbol)
        if not df_manual.empty:
            last_price = float(df_manual["Close"].values[-1])
            st.write(f"📌 **{manual_symbol}**")
            st.write(
                f"💵 Last: {last_price} | 🟢 Entry: {entry} | ❌ Stop: {stop_loss} | 🏆 Target: {target}"
            )
            st.write("**Filters Passed:**", "✅ Yes" if passed else "❌ No")
            st.write("**Why:**")
            if reasons:
                for r in reasons:
                    st.markdown(f"- {r}")
            else:
                st.write("Did not meet criteria.")
            with st.expander("View Fundamentals"):
                st.json(get_fundamentals(manual_symbol))
            if passed:
                notify_stock(
                    manual_symbol,
                    last_price,
                    entry,
                    stop_loss,
                    target,
                    desktop_enabled=notify_desktop,
                    telegram_enabled=notify_telegram,
                )