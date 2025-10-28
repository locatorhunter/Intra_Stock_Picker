"""
functions.py - Core utility functions and business logic
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
from plyer import notification
from datetime import datetime, date
import pytz
import talib
import json
import os
import paper

# --- GLOBAL DEFINITIONS ---
IST = pytz.timezone("Asia/Kolkata")
FILTER_DIR = "filter_presets"

# -------------------------
# Notification Functions
# -------------------------

def safe_notify(title, msg):
    """Safe desktop notification (reads from session state)"""
    notify_desktop = st.session_state.get("notify_desktop", True)
    if notify_desktop:
        try:
            notification.notify(title=title, message=msg, timeout=6)
            print(f"[INFO] Desktop notification sent: {title}")
        except Exception as e:
            st.warning(f"Desktop notify error: {e}")


def safe_telegram_send(text):
    """Safe Telegram notification (reads from session state)"""
    notify_telegram = st.session_state.get("notify_telegram", False)
    BOT_TOKEN = st.session_state.get("BOT_TOKEN", "")
    CHAT_ID = st.session_state.get("CHAT_ID", "")

    if not notify_telegram or not BOT_TOKEN or not CHAT_ID:
        print("DEBUG: Telegram disabled or credentials missing.")
        return False, "Telegram disabled or credentials missing"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=5)
        if resp.status_code == 200:
            print("DEBUG: Telegram send SUCCESS (Status 200).")
            return True, "OK"
        else:
            data = resp.json()
            error_msg = data.get("description", f"HTTP {resp.status_code}")
            print(f"DEBUG: Telegram send FAILED (Status {resp.status_code}). Error: {error_msg}")
            return False, error_msg
    except Exception as e:
        print(f"DEBUG: Telegram send EXCEPTION. Error: {str(e)}")
        return False, str(e)


def notify_stock(symbol, last_price, entry=None, stop_loss=None, target=None, score=None, reasons=None):
    """Send detailed notifications for shortlisted stocks — clean, emoji-free criteria"""
    timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')

    # --- Base trade info ---
    msg = (
        f"📢 <b>{symbol}</b> shortlisted!\\n"
        f"💵 <b>Last:</b> ₹{last_price:.2f}\\n"
        f"⏰ <b>Time:</b> {timestamp}"
    )

    # --- Trade levels ---
    if entry:
        msg += f"\\n🟢 <b>Entry:</b> ₹{entry:.2f}"
    if stop_loss:
        msg += f"\\n❌ <b>Stop-Loss:</b> ₹{stop_loss:.2f}"
    if target:
        msg += f"\\n🏆 <b>Target:</b> ₹{target:.2f}"
    if score is not None:
        msg += f"\\n🎯 <b>Score:</b> {score}"

    # --- Passed criteria (no emojis, just clean text) ---
    if reasons and isinstance(reasons, list):
        short_reasons = reasons[:8]
        msg += "\\n\\n<b>Passed Criteria:</b>"
        for r in short_reasons:
            msg += f"\\n• {r}"
        if len(reasons) > 8:
            msg += f"\\n…and {len(reasons) - 8} more."
    elif reasons:
        msg += f"\\n\\n<b>Reason:</b> {reasons}"

    # --- Convert to plain text for desktop ---
    plain_msg = (
        msg.replace("<b>", "")
           .replace("</b>", "")
           .replace("&nbsp;", " ")
           .replace("• ", "- ")
    )

    # --- Desktop notification ---
    safe_notify(f"📈 NSE Picker: {symbol}", plain_msg)

    # --- Telegram notification (HTML formatted) ---
    notify_telegram = st.session_state.get("notify_telegram", False)
    BOT_TOKEN = st.session_state.get("BOT_TOKEN", "")
    CHAT_ID = st.session_state.get("CHAT_ID", "")
    if notify_telegram and BOT_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        try:
            requests.get(
                url,
                params={
                    "chat_id": CHAT_ID,
                    "text": msg,
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            print(f"[OK] Telegram sent for {symbol}")
        except Exception as e:
            print(f"[ERR] Telegram send failed: {e}")


# -------------------------
# Filter Preset Management
# -------------------------

def save_filters(preset_name, filters):
    """Save filter settings to JSON file"""
    if not os.path.exists(FILTER_DIR):
        os.makedirs(FILTER_DIR)
        
    filename = os.path.join(FILTER_DIR, f"{preset_name}.json")
    try:
        with open(filename, 'w') as f:
            json.dump(filters, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving filters to {filename}: {e}") 
        return False


def load_filters(preset_name):
    """Load filter settings from JSON file"""
    filename = os.path.join(FILTER_DIR, f"{preset_name}.json")
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Could not load filter preset '{preset_name}'. Using defaults. ({e})")
            return {}
    return {}


def get_available_presets():
    """Get list of available filter presets"""
    if not os.path.exists(FILTER_DIR):
        return []
    return [f.replace('.json', '') for f in os.listdir(FILTER_DIR) if f.endswith('.json')]


def delete_filter(preset_name):
    """Delete a filter preset"""
    if preset_name == 'Default':
        return False, "Cannot delete 'Default' preset."
        
    filename = os.path.join(FILTER_DIR, f"{preset_name}.json")
    if os.path.exists(filename):
        try:
            os.remove(filename)
            return True, f"Preset '{preset_name}' deleted."
        except Exception as e:
            return False, f"Error deleting file: {e}"
    return False, f"Preset '{preset_name}' not found."


# -------------------------
# Data Fetching Functions
# -------------------------

@st.cache_data(ttl=3600)
def get_fo_symbols(max_symbols_local=80):
    """Get list of F&O symbols to scan"""
    base = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "LT",
        "MARUTI", "AXISBANK", "BHARTIARTL", "ITC", "TATAMOTORS", "SUNPHARMA",
        "KOTAKBANK", "HINDUNILVR", "ASIANPAINT", "WIPRO", "NESTLEIND", "ULTRACEMCO",
        "ADANIPORTS", "POWERGRID", "TATASTEEL", "JSWSTEEL", "M&M", "DRREDDY",
        "CIPLA", "DIVISLAB", "GRASIM", "BAJAJFINSV", "INDIGO", "NTPC", "COALINDIA",
        "BRITANNIA", "EICHERMOT", "HCLTECH", "ONGC", "BEL", "TRENT", "SIEMENS",
        "DLF", "PIDILITIND", "APOLLOHOSP", "HAVELLS", "BAJAJ-AUTO", "TECHM",
        "VEDL", "TITAN", "BOSCHLTD", "GAIL", "UPL", "COLPAL",
        "ICICIGI", "ADANIPOWER", "BAJFINANCE",
        "ABFRL", "ATGL", "CESC", "GRANULES", "IRB", "JSL", "POONAWALLA", "SJVN",
        "AARTIIND", "BSOFT", "HINDCOPPER", "MGL", "PEL", "ACC", "BALKRISIND",
        "CHAMBLFERT", "M&MFIN", "TATACOM", "APOLLOTYRE", "DEEPAKNTR", "ESCORTS",
        "MRF", "RAMCOCEM", "BERGEPAINT", "JKCEMENT", "LTTS", "ABBOTINDIA", "ATUL",
        "BATAINDIA", "CANFINHOME", "COROMANDEL", "CUB", "GNFC", "GUJGASLTD",
        "INDIAMART", "IPCALAB", "LALPATHLAB", "METROPOLIS", "NAVINFLUOR",
        "PVRINOX", "SUNTV", "UBL"
    ]
    return base[:max_symbols_local]


@st.cache_data(ttl=300)
def get_batch_price_data(ticker_list, interval_local):
    """Fetch batch price data for multiple tickers"""
    if not ticker_list:
        return pd.DataFrame()
    try:
        df_all = yf.download(
            tickers=ticker_list,
            period="5d",
            interval=interval_local,
            group_by="ticker",
            auto_adjust=False,
            threads=True,
            progress=False
        )
        return df_all
    except Exception as e:
        st.error(f"Batch download error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_nifty_daily():
    """Fetch NIFTY 50 daily data for relative strength comparison"""
    try:
        df = yf.download("^NSEI", period="10d", interval="1d", progress=False)
        return df
    except Exception:
        return pd.DataFrame()


def extract_symbol_df(df_batch_local: pd.DataFrame, sym: str) -> pd.DataFrame:
    """Extract individual symbol data from batch download"""
    if df_batch_local is None or df_batch_local.empty:
        return pd.DataFrame()

    candidates = {sym, f"{sym}.NS"}
    cols = df_batch_local.columns

    if isinstance(cols, pd.MultiIndex):
        first_level = cols.get_level_values(0).astype(str)
        second_level = cols.get_level_values(1).astype(str)
        first_level_unique = pd.Index(first_level).unique()
        first_level_lc = {s.lower() for s in first_level_unique}

        for cand in candidates:
            cand_lc = cand.lower()  
            if cand_lc in first_level_lc:
                match = next((x for x in first_level_unique if x.lower() == cand_lc), None)
                if match is not None:
                    try:
                        return df_batch_local[match].copy()
                    except KeyError:
                        continue

        second_level_lc = {s.lower() for s in second_level}
        if {"open", "high", "close"}.intersection(second_level_lc):
            try:
                ticker0 = first_level_unique[0]
                return df_batch_local[ticker0].copy()
            except Exception:
                return pd.DataFrame()

        return pd.DataFrame()

    lower_cols = [str(c).lower() for c in cols]

    if {"open", "high", "close"}.intersection(lower_cols):
        return df_batch_local.copy()

    for cand in candidates:
        cand_lc = cand.lower()
        if any(cand_lc in c for c in lower_cols):
            return df_batch_local.copy()

    return pd.DataFrame()


# -------------------------
# Technical Analysis Functions
# -------------------------

def compute_indicators(df, atr_period=7):
    """Compute technical indicators on price data"""
    df = df.rename(columns=str.title).copy()
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c not in df.columns:
            return df
    
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    
    try:
        highs = df["High"].astype(float).values
        lows = df["Low"].astype(float).values
        closes = df["Close"].astype(float).values
        df["ATR"] = talib.ATR(highs, lows, closes, timeperiod=atr_period)
    except Exception:
        df["ATR"] = np.nan
    
    try:
        df["RSI7"] = talib.RSI(df["Close"].astype(float).values, timeperiod=7)
        df["RSI10"] = talib.RSI(df["Close"].astype(float).values, timeperiod=10)
    except Exception:
        df["RSI7"] = np.nan
        df["RSI10"] = np.nan
    
    df["AvgVol20"] = df["Volume"].rolling(20).mean()
    df["VolStd20"] = df["Volume"].rolling(20).std()
    df["Vol_Trend"] = df["Volume"].rolling(5).mean() / df["Volume"].rolling(20).mean()
    
    try:
        macd, signal, hist = talib.MACD(df["Close"].astype(float).values, fastperiod=12, slowperiod=26, signalperiod=9)
        df["MACD"] = macd
        df["MACD_signal"] = signal
        df["MACD_hist"] = hist
    except Exception:
        df["MACD"] = np.nan
        df["MACD_signal"] = np.nan
        df["MACD_hist"] = np.nan
    
    try:
        df["ADX"] = talib.ADX(df["High"].astype(float).values, df["Low"].astype(float).values, df["Close"].astype(float).values, timeperiod=14)
    except Exception:
        df["ADX"] = np.nan
    
    return df


def check_candle_patterns(df):
    """Check for bullish candlestick patterns"""
    patterns = []
    try:
        eng = talib.CDLENGULFING(df["Open"].astype(float), df["High"].astype(float),
                                 df["Low"].astype(float), df["Close"].astype(float))
        morning = talib.CDLMORNINGSTAR(df["Open"].astype(float), df["High"].astype(float),
                                       df["Low"].astype(float), df["Close"].astype(float))
        last_eng = int(eng[-1]) if len(eng) else 0
        last_morning = int(morning[-1]) if len(morning) else 0
        if last_eng > 0:
            patterns.append("🟢 Bullish Engulfing")
        if last_morning > 0:
            patterns.append("🟢 Morning Star")
    except Exception:
        pass
    return patterns


def check_consolidation(df, lookback=10):
    """Detect price consolidation (tight range near recent highs)"""
    recent_high = df["High"].rolling(lookback).max().iloc[-1]
    recent_low = df["Low"].rolling(lookback).min().iloc[-1]
    current_close = df["Close"].iloc[-1]
    
    price_range = (recent_high - recent_low) / recent_low
    position_in_range = (current_close - recent_low) / (recent_high - recent_low)
    
    if price_range < 0.03 and position_in_range > 0.7:
        return True, price_range
    return False, price_range


# -------------------------
# Watchlist Functions
# -------------------------

def remove_from_watchlist(symbol_to_remove):
    """Remove stock from watchlist"""
    if symbol_to_remove in st.session_state.watchlist:
        del st.session_state.watchlist[symbol_to_remove]


def check_watchlist_hits(df_batch):
    """Check if watchlist stocks hit target or stop loss"""
    keys_to_remove = []
    
    for sym, info in st.session_state.watchlist.items(): 
        target = info.get("target")
        sl = info.get("sl")
        
        df_sym = extract_symbol_df(df_batch, sym)
        if df_sym is None or df_sym.empty:
            continue
            
        latest_price = float(df_sym["Close"].iloc[-1])
        message = ""

        if latest_price >= target:
            message = f"🎯 TARGET HIT for {sym}! Current Price: {latest_price:.2f}"
        elif latest_price <= sl:
            message = f"🛑 STOP LOSS HIT for {sym}! Current Price: {latest_price:.2f}"

        if message:
            if st.session_state.get('notify_desktop', True):
                safe_notify("Trade Alert", message)
            if st.session_state.get('notify_telegram', True):
                safe_telegram_send(message)
            keys_to_remove.append(sym)
            info["status"] = "Closed"

    for key in keys_to_remove:
        del st.session_state.watchlist[key]
