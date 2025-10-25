import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
from plyer import notification
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, time as dt_time, date
import pytz
import talib
import json
import os

st.markdown("<h1 style='text-align: center; margin-bottom: -100px; margin-top: -10px;'> STOCK HUNTER </h1>", 
    unsafe_allow_html=True)

# --- GLOBAL DEFINITIONS ---
IST = pytz.timezone("Asia/Kolkata")

#------------------------
#Notification
#------------------------

def safe_notify(title, msg):
    if notify_desktop:
        try:
            notification.notify(title=title, message=msg, timeout=6)
        except Exception as e:
            st.warning(f"Desktop notify error: {e}")

def safe_telegram_send(text):
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

def notify_stock(symbol, last_price, entry=None, stop_loss=None, target=None):
    timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    msg = f"📢 {symbol} shortlisted!\n💵 Last: {last_price}\n⏰ Time: {timestamp}"
    if entry: msg += f"\n🟢 Entry: {entry:.2f}"
    if stop_loss: msg += f"\n❌ Stop-Loss: {stop_loss:.2f}"
    if target: msg += f"\n🏆 Target: {target:.2f}"
    try:
        safe_notify(f"📈 NSE Picker: {symbol}", msg)
    except Exception:
        pass
    if notify_telegram:
        ok, info = safe_telegram_send(msg)
        if not ok:
            st.warning(f"Telegram notify failed for {symbol}: {info}")

# Use a directory for filters, not a single file
FILTER_DIR = "filter_presets" 

# --- FILTER UTILITY FUNCTIONS ---
def save_filters(preset_name, filters):
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
    if not os.path.exists(FILTER_DIR):
        return []
    return [f.replace('.json', '') for f in os.listdir(FILTER_DIR) if f.endswith('.json')]

def delete_filter(preset_name):
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

# --- INITIALIZE STATE ---
if "watchlist" not in st.session_state:
    st.session_state.watchlist = {}
    
if 'current_preset_name' not in st.session_state:
    st.session_state['current_preset_name'] = 'Default'

saved_filters = load_filters(st.session_state.current_preset_name)

# Initialize filter defaults
default_sl_percent = saved_filters.get('sl_percent', 1.5) 
default_target_percent = saved_filters.get('target_percent', 1.0) 
default_use_volume = saved_filters.get('use_volume', True)
default_use_breakout = saved_filters.get('use_breakout', True)
default_use_ema_rsi = saved_filters.get('use_ema_rsi', True)
default_use_rs = saved_filters.get('use_rs', True)
default_interval = saved_filters.get('interval', "5m")
default_max_symbols = saved_filters.get('max_symbols', 80)
default_vol_zscore_threshold = saved_filters.get('vol_zscore_threshold', 1.2)  # LOWERED
default_breakout_margin_pct = saved_filters.get('breakout_margin_pct', 0.2)  # LOWERED
default_atr_period = saved_filters.get('atr_period', 7)
default_atr_mult = saved_filters.get('atr_mult', 0.9)
default_momentum_lookback = saved_filters.get('momentum_lookback', 3)
default_rs_lookback = saved_filters.get('rs_lookback', 3)
default_signal_score_threshold = saved_filters.get('signal_score_threshold', 5)  # ADJUSTED
default_notify_desktop = saved_filters.get('notify_desktop', True)
default_notify_telegram = saved_filters.get('notify_telegram', False)

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

#==========================================================
#  SIDE BAR
#==========================================================
def display_live_clock():
    now = datetime.now(IST).strftime("%I:%M:%S %p %Z")
    col_clock, col_spacer = st.columns([1, 8])
    with col_clock:
        st.sidebar.markdown(
            f"""
            <h1 style='text-align: center; margin-bottom: -120px; margin-top: -40px;'>
            {now}
            </h1>
            """, 
            unsafe_allow_html=True
    )

display_live_clock()
st.sidebar.markdown("---")

show_technical_predictions = st.sidebar.checkbox("Show Technical Predictions", True)

with st.sidebar.expander("⚙️ Saved Filters", expanded=False):
    st.markdown("#### Load Saved filters:")
    available_presets = get_available_presets()
    display_presets = ['Default'] + available_presets
    preset_container = st.sidebar.container()

    selected_preset_key = st.radio(
        "Select a preset to load:",
        options=display_presets,
        index=display_presets.index(st.session_state.current_preset_name) if st.session_state.current_preset_name in display_presets else 0,
        key='preset_radio_selector',
        help="Click on a preset to load its settings. Click the 🗑️ to delete it.",
    )

    if selected_preset_key != st.session_state.current_preset_name:
        st.session_state.current_preset_name = selected_preset_key
        st.rerun()

    st.markdown("---")
    st.markdown("#### Manage Filters:")
    for preset in available_presets:
        col_name, col_delete = st.columns([4, 1])
        col_name.write(f"{preset}")
        with col_delete:
            if st.button("🗑️", key=f"delete_preset_{preset}", help=f"Delete '{preset}' preset"):
                success, message = delete_filter(preset)
                if success:
                    st.toast(f"Preset '{preset}' deleted successfully!", icon='✅')
                    st.session_state.current_preset_name = 'Default'
                    st.rerun()
                else:
                    st.error(message)

with st.sidebar.expander("Set SL and Target", expanded=False):
    sl_percent = st.number_input(
        "Stop Loss %", 
        min_value=0.1, 
        value=default_sl_percent, 
        step=0.1, 
        key="sl_percent_input" 
    )
    target_percent = st.number_input(
        "Target %", 
        min_value=0.1, 
        value=default_target_percent, 
        step=0.1, 
        key="target_percent_input" 
    )

with st.sidebar.expander("Filters & Parameters", expanded=True):
    use_volume = st.checkbox("📊 Use Volume Spike", default_use_volume)
    use_breakout = st.checkbox("🚀 Use Breakout Filter", default_use_breakout)
    use_ema_rsi = st.checkbox("📉 Use EMA+RSI Filters", default_use_ema_rsi)
    use_rs = st.checkbox("💪 Use Relative Strength vs NIFTY", default_use_rs)

    interval = st.selectbox("Intraday Interval (bars)", ["5m", "15m", "30m", "1h"], index=["5m", "15m", "30m", "1h"].index(default_interval))
    auto_refresh_sec = st.slider("Auto refresh (seconds)", 30, 600, 180, 10)
    max_symbols = st.slider("Max F&O symbols to scan", 30, 150, default_max_symbols)
    vol_zscore_threshold = st.slider("Volume z-score threshold", 0.5, 4.0, default_vol_zscore_threshold, 0.1)
    breakout_margin_pct = st.slider("Breakout margin (%)", 0.0, 3.0, default_breakout_margin_pct, 0.1)
    atr_period = st.slider("ATR period", 5, 21, default_atr_period, 1)
    atr_mult = st.slider("ATR multiplier (SL)", 0.1, 5.0, default_atr_mult, 0.1)
    momentum_lookback = st.slider("Momentum Lookback (bars)", 2, 20, default_momentum_lookback)
    rs_lookback = st.slider("RS lookback days", 2, 15, default_rs_lookback)
    signal_score_threshold = st.slider("Signal score threshold", 2, 10, default_signal_score_threshold)

with st.sidebar.expander("Notification Settings", expanded=False):
    notify_desktop = st.checkbox("💻 Enable Desktop Notification", default_notify_desktop)
    notify_telegram = st.checkbox("📨 Enable Telegram Notification", default_notify_telegram)
    CHAT_ID = st.text_input("Telegram Chat ID", "")    
    BOT_TOKEN = st.text_input("Telegram Bot Token", "", type="password")

    st.markdown("#### Test Notifications")
    test_message = "This is a test notification from the NSE Picker! (If you see this, it works!)"

    if st.button("Test Telegram Alert 📨"):
        if not notify_telegram or not BOT_TOKEN or not CHAT_ID:
            st.error("Please enable Telegram notification and fill in the Bot Token/Chat ID first!")
        else:
            st.info("Sending test message...")
            ok, info = safe_telegram_send(test_message)
            if ok:
                st.success("✅ Telegram Test Success! Check your chat now.")
            else:
                st.error(f"❌ Telegram Test Failed. Response: {info}")

    st.sidebar.markdown("### Save Current Settings")
    custom_name = st.sidebar.text_input("Name for the Filter Preset", value=st.session_state.current_preset_name, max_chars=20)

    if st.sidebar.button(f"💾 Save as '{custom_name}'"):
        if not custom_name or custom_name == 'Default':
            st.sidebar.error("Please enter a valid, non-'Default' name to save your preset.")
        else:
            current_filters = {
                'sl_percent': sl_percent, 
                'target_percent': target_percent,
                'use_volume': use_volume,
                'use_breakout': use_breakout,
                'use_ema_rsi': use_ema_rsi,
                'use_rs': use_rs,
                'interval': interval,
                'max_symbols': max_symbols,
                'vol_zscore_threshold': vol_zscore_threshold,
                'breakout_margin_pct': breakout_margin_pct,
                'atr_period': atr_period,
                'atr_mult': atr_mult,
                'momentum_lookback': momentum_lookback,
                'rs_lookback': rs_lookback,
                'signal_score_threshold': signal_score_threshold,
                'notify_desktop': notify_desktop, 
                'notify_telegram': notify_telegram
            }
            if save_filters(custom_name, current_filters):
                st.session_state.current_preset_name = custom_name
                st.sidebar.success(f"Preset '{custom_name}' saved successfully!")
                st.rerun()

if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = datetime.now(IST).strftime("%I:%M:%S %p")

refresh_count = st_autorefresh(interval=auto_refresh_sec * 1000, limit=None, key="auto_refresh")
current_timestamp = datetime.now(IST).strftime("%I:%M:%S %p")

if 'prev_refresh_count' not in st.session_state:
    st.session_state.prev_refresh_count = 0
    
if refresh_count > st.session_state.prev_refresh_count:
    st.session_state.last_refresh_time = current_timestamp
    st.session_state.prev_refresh_count = refresh_count

st.markdown(
    f"""
    <p style='text-align: center; '>
        ⏰ Refreshed {refresh_count} times. 
        Interval: {auto_refresh_sec} seconds. 
        Last Run: {st.session_state.last_refresh_time}
    </p>
    """, 
    unsafe_allow_html=True
)

if refresh_count > 0:
    timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    msg = f"Scan Refreshed at {timestamp}. Interval: {auto_refresh_sec} sec."
    safe_notify("NSE Picker Status", msg)

if "watchlist" not in st.session_state:
    st.session_state.watchlist = {}
if "notified_today" not in st.session_state:
    st.session_state.notified_today = set()
if "notified_date" not in st.session_state:
    st.session_state.notified_date = date.today().isoformat()

today_iso = date.today().isoformat()
if st.session_state.notified_date != today_iso:
    st.session_state.notified_today = set()
    st.session_state.notified_date = today_iso

# -------------------------
# Symbols list (cached)
# -------------------------
@st.cache_data(ttl=3600)
def get_fo_symbols(max_symbols_local=80):
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
    try:
        df = yf.download("^NSEI", period="10d", interval="1d", progress=False)
        return df
    except Exception:
        return pd.DataFrame()

# -------------------------
# Technical analysis helpers - ENHANCED VERSION
# -------------------------
def compute_indicators(df):
    df = df.rename(columns=str.title).copy()
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c not in df.columns:
            return df
    
    # EMA20
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    
    # ATR
    try:
        highs = df["High"].astype(float).values
        lows = df["Low"].astype(float).values
        closes = df["Close"].astype(float).values
        df["ATR"] = talib.ATR(highs, lows, closes, timeperiod=atr_period)
    except Exception:
        df["ATR"] = np.nan
    
    # RSI (7 and 10)
    try:
        df["RSI7"] = talib.RSI(df["Close"].astype(float).values, timeperiod=7)
        df["RSI10"] = talib.RSI(df["Close"].astype(float).values, timeperiod=10)
    except Exception:
        df["RSI7"] = np.nan
        df["RSI10"] = np.nan
    
    # Volume indicators
    df["AvgVol20"] = df["Volume"].rolling(20).mean()
    df["VolStd20"] = df["Volume"].rolling(20).std()
    df["Vol_Trend"] = df["Volume"].rolling(5).mean() / df["Volume"].rolling(20).mean()
    
    # MACD for early momentum
    try:
        macd, signal, hist = talib.MACD(df["Close"].astype(float).values, fastperiod=12, slowperiod=26, signalperiod=9)
        df["MACD"] = macd
        df["MACD_signal"] = signal
        df["MACD_hist"] = hist
    except Exception:
        df["MACD"] = np.nan
        df["MACD_signal"] = np.nan
        df["MACD_hist"] = np.nan
    
    # ADX for trend strength
    try:
        df["ADX"] = talib.ADX(df["High"].astype(float).values, df["Low"].astype(float).values, df["Close"].astype(float).values, timeperiod=14)
    except Exception:
        df["ADX"] = np.nan
    
    return df

def remove_from_watchlist(symbol_to_remove):
    if symbol_to_remove in st.session_state.watchlist:
        del st.session_state.watchlist[symbol_to_remove]

def check_candle_patterns(df):
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
# ENHANCED SCAN LOGIC WITH EARLY DETECTION
# -------------------------
def scan_stock_improved(sym, df_stock, **kwargs):
    nifty_df = kwargs.get('nifty_df')
    if df_stock is None or df_stock.empty or len(df_stock) < 25:
        return 0, ["⚠️ Not enough data"], None, None, None, {}

    df = compute_indicators(df_stock)
    if df.empty:
        return 0, ["⚠️ Indicator computation failed"], None, None, None, {}

    try:
        last_close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2])
        last_vol = float(df["Volume"].iloc[-1])
        avg_vol = float(df["AvgVol20"].iloc[-1]) if not np.isnan(df["AvgVol20"].iloc[-1]) else 0.0
        vol_std = float(df["VolStd20"].iloc[-1]) if not np.isnan(df["VolStd20"].iloc[-1]) else 0.0
        last_atr = float(df["ATR"].iloc[-1]) if not np.isnan(df["ATR"].iloc[-1]) else 0.0
    except Exception:
        return 0, ["⚠️ Data extraction failed"], None, None, None, {}

    reasons = []
    score = 0

    # 1. EARLY MOMENTUM - MACD crossing (NEW)
    try:
        if len(df) >= 3:
            if (df["MACD"].iloc[-1] > df["MACD_signal"].iloc[-1] and 
                df["MACD"].iloc[-2] <= df["MACD_signal"].iloc[-2]):
                if df["MACD"].iloc[-1] < 0:
                    reasons.append("🔄 Early reversal (MACD cross below zero)")
                    score += 3
                else:
                    reasons.append("📈 MACD momentum confirmed")
                    score += 1
    except:
        pass

    # 2. MODIFIED RSI - Early detection (ENHANCED)
    if use_ema_rsi:
        try:
            rsi7_val = df["RSI7"].iloc[-1]
            rsi7_prev = df["RSI7"].iloc[-2] if len(df) >= 2 else rsi7_val
            
            # Early bullish momentum: RSI crossing 50 upward
            if 50 < rsi7_val < 65 and rsi7_prev <= 50:
                reasons.append("📈 RSI early bullish (50-65)")
                score += 2
            # Recovery from oversold
            elif 35 < rsi7_val < 50 and rsi7_prev <= 35:
                reasons.append("🔄 RSI recovering from oversold")
                score += 1
            # Still check traditional overbought for confirmation
            elif rsi7_val >= 70:
                reasons.append("💥 RSI (7) > 70 (Strong momentum)")
                score += 1
                
            # EMA check
            ema_ok = last_close > df["EMA20"].iloc[-1]
            if ema_ok:
                reasons.append("📈 Price above EMA20")
                score += 1
        except Exception:
            pass

    # 3. VOLUME ACCUMULATION (ENHANCED)
    if use_volume:
        try:
            vol_trend = df["Vol_Trend"].iloc[-1]
            # Volume building up (accumulation phase)
            if 1.2 < vol_trend < 2.0:
                reasons.append("📊 Volume accumulation phase")
                score += 2
            # Traditional spike check
            elif avg_vol > 0 and vol_std > 0:
                z = (last_vol - avg_vol) / vol_std
                if np.isfinite(z) and z >= vol_zscore_threshold:
                    reasons.append(f"📊 Volume spike (z={z:.2f})")
                    score += 1
        except Exception:
            pass

    # 4. CONSOLIDATION CHECK (NEW)
    try:
        is_consolidating, range_pct = check_consolidation(df)
        if is_consolidating:
            reasons.append(f"🔄 Consolidating near highs ({range_pct*100:.1f}% range)")
            score += 2
    except:
        pass

    # 5. EARLY TREND FORMATION - ADX (NEW)
    try:
        adx_val = df["ADX"].iloc[-1]
        adx_prev = df["ADX"].iloc[-2] if len(df) >= 2 else adx_val
        if 20 < adx_val < 30 and adx_val > adx_prev:
            reasons.append("💪 New trend forming (ADX rising)")
            score += 2
    except:
        pass

    # 6. PRE-BREAKOUT & BREAKOUT DETECTION (ENHANCED)
    if use_breakout:
        try:
            rolling_high = df["High"].rolling(momentum_lookback).max()
            if len(rolling_high) >= 2:
                prev_high = float(rolling_high.iloc[-2])
                margin_to_breakout = (prev_high - last_close) / prev_high
                
                # Within 1% of breakout (pre-breakout stage)
                if 0 < margin_to_breakout < 0.01:
                    reasons.append("🎯 Approaching breakout level")
                    score += 3
                # Fresh breakout with reduced margin
                elif last_close > (prev_high * (1 + breakout_margin_pct / 100)) and last_close > prev_close:
                    reasons.append(f"🚀 Fresh breakout ({breakout_margin_pct:.2f}%)")
                    score += 2
        except Exception:
            pass

    # 7. RELATIVE STRENGTH FILTER
    if use_rs and nifty_df is not None and not nifty_df.empty:
        try:
            stock_pct = df["Close"].pct_change(rs_lookback).iloc[-1]
            nifty_pct = nifty_df["Close"].pct_change(rs_lookback).iloc[-1]
            if np.isfinite(stock_pct) and np.isfinite(nifty_pct) and (stock_pct - nifty_pct) > 0:
                reasons.append("💪 Outperforming NIFTY")
                score += 1
        except Exception:
            pass

    # 8. CANDLE PATTERNS
    patterns = check_candle_patterns(df)
    if patterns:
        reasons.extend(patterns)
        score += 1

    # 9. ENTRY / SL / TARGET
    entry_price = last_close
    if last_atr and last_atr > 0:
        stop_loss = entry_price - (atr_mult * last_atr)
        target_price = entry_price + 2 * (entry_price - stop_loss)
    else:
        stop_loss = entry_price * 0.98
        target_price = entry_price * 1.04

    # 10. Filter-free mode
    if not any([use_volume, use_breakout, use_ema_rsi, use_rs]):
        reasons.append("🕵️ Filter-free mode active")
        score = 1

    signal = {
        "score": score,
        "early_momentum": score >= 4
    }

    return score, reasons, entry_price, stop_loss, target_price, signal

# -------------------------
# Scan Universe (batch)
# -------------------------
st.subheader("🐉 Scanning Stocks")

fo_symbols = get_fo_symbols(max_symbols)
tickers = [f"{s}.NS" for s in fo_symbols]

progress = st.progress(0)
status_text = st.empty()

df_batch = get_batch_price_data(tickers, interval)
nifty_df = get_nifty_daily()

candidates = []
shortlisted_stocks = []

def check_watchlist_hits(df_batch):
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
            safe_notify("Trade Alert", message)
            safe_telegram_send(message)
            keys_to_remove.append(sym)
            info["status"] = "Closed"

    for key in keys_to_remove:
        del st.session_state.watchlist[key]

def extract_symbol_df(df_batch_local: pd.DataFrame, sym: str) -> pd.DataFrame:
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

for i, sym in enumerate(fo_symbols):
    status_text.text(f"Scanning {sym} ({i+1}/{len(fo_symbols)})")
    progress.progress((i + 1) / len(fo_symbols))

    df_sym = extract_symbol_df(df_batch, sym)
    
    if df_sym is None or df_sym.empty or len(df_sym) < 25:
        print(f"Skipping {sym}: Data is missing/short (len={len(df_sym) if df_sym is not None else 0})")
        candidates.append({
            "Symbol": sym,
            "Score": 0,
            "Last Close": "N/A",
            "Entry": "N/A",
            "Stop Loss": "N/A",
            "Target": "N/A",
            "Reasons": "⚠️ No data available",
            "Signal": "N/A"
        })
        continue

    score, reasons, entry, stop, target, signal = scan_stock_improved(sym, df_sym, nifty_df=nifty_df)

    last_close = float(df_sym["Close"].iloc[-1])

    candidates.append({
        "Symbol": sym,
        "Score": score,
        "Last Close": last_close,
        "Entry": entry,
        "Stop Loss": stop,
        "Target": target,
        "Reasons": reasons,
    })

    if score >= signal_score_threshold:
        shortlisted_stocks.append(sym)
        
        if sym not in st.session_state.notified_today:
            notify_stock(sym, last_close, entry, stop, target)
            st.session_state.notified_today.add(sym)

progress.empty()
status_text.text("✅ Scan complete!")

if "watchlist" in st.session_state:
    check_watchlist_hits(df_batch)

if not candidates:
    safe_notify("Scan Complete", "🐸 No new stocks met the entry criteria right now.") 
    safe_telegram_send("✅ Scan finished. No new stocks meet the criteria.")

if candidates:
    with st.expander("📈Shortlisted Stocks", expanded=True): 
        df_candidates = pd.DataFrame(candidates).set_index("Symbol").sort_values(by="Score", ascending=False)
        qualified_count = len(df_candidates[df_candidates['Score'] >= signal_score_threshold])
        st.success(f"✅ Scanned {len(df_candidates)} stocks. **{qualified_count}** stocks meet the threshold of {signal_score_threshold}.")
        st.dataframe(df_candidates)
        st.download_button(
            "💾 Download candidates CSV",
            df_candidates.to_csv(index=True),
            file_name=f"candidates_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="candidates_download_2" 
        )
else:
    st.info("⚠️ No candidates found this round.")

# -------------------------
# Technical Predictions
# -------------------------
if show_technical_predictions:
    with st.expander("📈 Technical Predictions for Shortlisted Stocks", expanded=True):
        if not shortlisted_stocks:
            st.info("No shortlisted stocks to show predictions for.")
        else:
            if 'df_candidates' not in locals():
                st.warning("Candidate data not available for detailed predictions.")
                st.stop()

            for stock in shortlisted_stocks:
                try:
                    candidate_row = df_candidates.loc[stock]
                    entry_for_wl = candidate_row['Entry']
                    sl_for_wl = candidate_row['Stop Loss']
                    target_for_wl = candidate_row['Target']
                except KeyError:
                    st.warning(f"Trade levels for {stock} not found in candidates list.")
                    continue
                
                df_for_pred = extract_symbol_df(df_batch, stock)
                if df_for_pred is None or df_for_pred.empty:
                    st.warning(f"No data found for {stock}")
                    continue
                    
                df_for_pred = compute_indicators(df_for_pred)
                analysis = {
                    "Last Close": float(df_for_pred["Close"].iloc[-1]),
                    "EMA20": float(df_for_pred["EMA20"].iloc[-1]) if "EMA20" in df_for_pred else np.nan,
                    "RSI10": float(df_for_pred["RSI10"].dropna().iloc[-1]) if "RSI10" in df_for_pred and not df_for_pred["RSI10"].dropna().empty else np.nan,
                    "ATR": float(df_for_pred["ATR"].iloc[-1]) if "ATR" in df_for_pred and not np.isnan(df_for_pred["ATR"].iloc[-1]) else np.nan
                }
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"### {stock}")
                    st.table(pd.DataFrame(analysis, index=[0]))
                with col2:
                    if stock in st.session_state.watchlist:
                        st.button("Added to Watchlist!", key=f"added_{stock}", disabled=True)
                    else:
                        if st.button("Add to Watchlist", key=f"add_wl_from_pred_{stock}"):
                            st.session_state.watchlist[stock] = {
                                "entry": entry_for_wl,
                                "sl": sl_for_wl,
                                "target": target_for_wl,
                                "status": "Active"
                            }
                            st.success(f"Added {stock} to watchlist!")

# -------------------------
# Manual Analyzer
# -------------------------
with st.expander("📝 Manual Stock Analyzer (Multiple Stocks)", expanded=False): 
    manual_symbols = st.text_area("Enter stock symbols separated by commas (e.g., RELIANCE,TCS,INFY)")
    manual_list = [s.strip().upper() for s in manual_symbols.split(",") if s.strip()] if manual_symbols else []

    for idx, manual_symbol in enumerate(manual_list):
        df_manual = extract_symbol_df(df_batch, manual_symbol)
        if df_manual is None or df_manual.empty:
            @st.cache_data(ttl=300)
            def get_single(sym, interval_local):
                try:
                    dd = yf.download(f"{sym}.NS", period="5d", interval=interval_local, progress=False)
                    return dd
                except Exception:
                    return pd.DataFrame()
            df_manual = get_single(manual_symbol, interval)

        score, reasons, entry, stop_loss, target, signal = scan_stock_improved(manual_symbol, df_manual, nifty_df=nifty_df)

        reasons_str = " | ".join(reasons)

        if df_manual is not None and not df_manual.empty:
            last_price = float(df_manual["Close"].iloc[-1])
            st.write(f"📌 **{manual_symbol}** — Score: {score} **|** **Reasons:** {reasons_str if reasons_str else 'Did not meet criteria.'}")
            st.write(f"💵 Last: {last_price:.2f} | 🟢 Entry: {entry if entry else 'N/A'} | ❌ Stop: {stop_loss if stop_loss else 'N/A'} | 🏆 Target: {target if target else 'N/A'}")
            st.write("**Filters Passed:**", "✅ Yes" if score >= signal_score_threshold else "❌ No")

            with st.expander("View Fundamentals"):
                try:
                    ticker = yf.Ticker(manual_symbol + ".NS")
                    info = ticker.info
                    st.json({
                        "PE Ratio": info.get("trailingPE", "N/A"),
                        "EPS": info.get("trailingEps", "N/A"),
                        "Market Cap": info.get("marketCap", "N/A"),
                        "Sector": info.get("sector", "N/A"),
                        "Industry": info.get("industry", "N/A")
                    })
                except Exception:
                    st.write("Fundamentals not available.")

            if score >= signal_score_threshold:
                notify_stock(manual_symbol, last_price, entry, stop_loss, target)

            if manual_symbol in st.session_state.watchlist:
                st.button("Added to Watchlist!", key=f"added_manual_{manual_symbol}_{idx}", disabled=True)
            else:
                if st.button("Add to Watchlist", key=f"add_manual_{manual_symbol}_{idx}"):
                    if entry is None:
                        current_price = float(df_manual["Close"].iloc[-1])
                        entry_to_save = current_price
                        sl_to_save = current_price * 0.98
                        target_to_save = current_price * 1.04
                    else:
                        entry_to_save = entry
                        sl_to_save = stop_loss
                        target_to_save = target

                    st.session_state.watchlist[manual_symbol] = {
                        "entry": entry_to_save,
                        "sl": sl_to_save,
                        "target": target_to_save,
                        "status": "Active"
                    }
                    st.success(f"Added {manual_symbol} to watchlist with{' default' if entry is None else ''} trade levels!")

# -------------------------
# Watchlist UI
# -------------------------
with st.expander("📑 Watchlist & Alerts - Click to manage trades", expanded=False):
    st.markdown("<div class='watchlist-container'>", unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
    with col1:
        st.markdown("**Symbol**")
    with col2:
        st.markdown("**Entry**")
    with col3:
        st.markdown("**Stop Loss**")
    with col4:
        st.markdown("**Target**")
    with col5:
        st.markdown("**Status**")
    with col6:
        st.markdown("**Action**")

    for sym, info in st.session_state.watchlist.items():
        try:
            df_watch = extract_symbol_df(df_batch, sym)
            if df_watch is None or df_watch.empty:
                df_watch = get_batch_price_data([f"{sym}.NS"], "5m")
                df_watch = extract_symbol_df(df_watch, sym)
        except Exception:
            df_watch = pd.DataFrame()

        curr_price = float(df_watch['Close'].iloc[-1]) if df_watch is not None and not df_watch.empty else None
        
        entry_val = info.get("entry", "N/A")
        sl_val = info.get("sl", "N/A")
        tgt_val = info.get("target", "N/A")
        status = info.get("status", "Active")

        entry = f"{entry_val:.2f}" if isinstance(entry_val, (float, int)) else entry_val
        sl = f"{sl_val:.2f}" if isinstance(sl_val, (float, int)) else sl_val
        tgt = f"{tgt_val:.2f}" if isinstance(tgt_val, (float, int)) else tgt_val

        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
        with col1:
            st.markdown(f"**{sym}**")
        with col2:
            st.markdown(f"{entry}")
        with col3:
            st.markdown(f"{sl}")
        with col4:
            st.markdown(f"{tgt}")
        with col5:
            st.markdown(f"{status}")
        with col6:
            st.button(
                "Remove", 
                key=f"remove_{sym}", 
                on_click=remove_from_watchlist,
                args=(sym,)
            )

    st.markdown("</div>", unsafe_allow_html=True)
    st.info("Page auto-refresh will re-check alerts and prices.")

st.sidebar.markdown("---")    
st.sidebar.markdown("Happy Trading!!! -✏️ Vijay S")