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
import os # Import the os module

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
        print("DEBUG: Telegram disabled or credentials missing.") # <-- NEW DEBUG
        return False, "Telegram disabled or credentials missing"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        # Use a small timeout just in case of network issues
        resp = requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=5)
        
        if resp.status_code == 200:
            print("DEBUG: Telegram send SUCCESS (Status 200).") # <-- NEW DEBUG
            return True, "OK"
        else:
            data = resp.json()
            error_msg = data.get("description", f"HTTP {resp.status_code}")
            # This print is crucial for finding the specific error!
            print(f"DEBUG: Telegram send FAILED (Status {resp.status_code}). Error: {error_msg}") # <-- NEW DEBUG
            return False, error_msg
    except Exception as e:
        print(f"DEBUG: Telegram send EXCEPTION. Error: {str(e)}") # <-- NEW DEBUG
        return False, str(e)

def notify_stock(symbol, last_price, entry=None, stop_loss=None, target=None):
    timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    msg = f"📢 {symbol} shortlisted!\n💵 Last: {last_price}\n⏰ Time: {timestamp}"
    if entry: msg += f"\n🟢 Entry: {entry:.2f}"
    if stop_loss: msg += f"\n❌ Stop-Loss: {stop_loss:.2f}"
    if target: msg += f"\n🏆 Target: {target:.2f}"
    # Desktop
    try:
        safe_notify(f"📈 NSE Picker: {symbol}", msg)
    except Exception:
        pass
    # Telegram (guarded)
    if notify_telegram:
        ok, info = safe_telegram_send(msg)
        if not ok:
            st.warning(f"Telegram notify failed for {symbol}: {info}")

# Use a directory for filters, not a single file
FILTER_DIR = "filter_presets" 

# --- FILTER UTILITY FUNCTIONS (MOVED UP FOR DEFINITION) ---
def save_filters(preset_name, filters):
    """Saves the current filter settings to a JSON file using a custom name."""
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
    """Loads filter settings from a JSON file using a custom name."""
    filename = os.path.join(FILTER_DIR, f"{preset_name}.json")
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Could not load filter preset '{preset_name}'. Using defaults. ({e})")
            return {}
    return {} # Return empty if file does not exist

def get_available_presets():
    """Gets a list of all saved filter preset names."""
    if not os.path.exists(FILTER_DIR):
        return []
    # Find all .json files and remove the extension
    return [f.replace('.json', '') for f in os.listdir(FILTER_DIR) if f.endswith('.json')]

def delete_filter(preset_name):
    """Deletes the specified filter preset file."""
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
# -------------------------------------------------------------------


# --- INITIALIZE STATE (near the top of your script) ---

if "watchlist" not in st.session_state:
    st.session_state.watchlist = {}
    
# Use session state to hold the currently selected preset name
if 'current_preset_name' not in st.session_state:
    st.session_state['current_preset_name'] = 'Default'

# Load filters based on the CURRENTLY SELECTED PRESET NAME
saved_filters = load_filters(st.session_state.current_preset_name)

# Initialize/Get the current filter values from saved data or a default
default_sl_percent = saved_filters.get('sl_percent', 1.5) 
default_target_percent = saved_filters.get('target_percent', 1.0) 

# --- ALL DEFAULTS MUST BE LOADED HERE ---
# Use the default value used in the sidebar for the fallback
default_use_volume = saved_filters.get('use_volume', True)
default_use_breakout = saved_filters.get('use_breakout', True)
default_use_ema_rsi = saved_filters.get('use_ema_rsi', True)
default_use_rs = saved_filters.get('use_rs', True)
default_interval = saved_filters.get('interval', "5m")
default_max_symbols = saved_filters.get('max_symbols', 80)
default_vol_zscore_threshold = saved_filters.get('vol_zscore_threshold', 2.0)
default_breakout_margin_pct = saved_filters.get('breakout_margin_pct', 0.5)
default_atr_period = saved_filters.get('atr_period', 7)
default_atr_mult = saved_filters.get('atr_mult', 0.9)
default_momentum_lookback = saved_filters.get('momentum_lookback', 3)
default_rs_lookback = saved_filters.get('rs_lookback', 3)
default_signal_score_threshold = saved_filters.get('signal_score_threshold', 4)
default_notify_desktop = saved_filters.get('notify_desktop', True)
default_notify_telegram = saved_filters.get('notify_telegram', False)
# --- END NEW DEFAULTS ---

# -------------------------
# Helper / Config
# -------------------------
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
)

#==========================================================
#  SIDE BAR
#==========================================================
# --- UTILITY FUNCTION FOR LIVE CLOCK DISPLAY ---
def display_live_clock():
    """Displays the current time in IST at the top."""
    now = datetime.now(IST).strftime("%I:%M:%S %p %Z") # e.g., 03:30:15 PM IST
    
    # Use columns to align the time nicely
    col_clock, col_spacer = st.columns([1, 8])
    with col_clock:
        # Use HTML/Markdown for a slightly larger, bold clock
        st.sidebar.markdown(
            f"""
            <h1 style='text-align: center; margin-bottom: -120px; margin-top: -40px;
            '>
            {now}
            </h1>
            """, 
            unsafe_allow_html=True
    )
# --- CALL THE CLOCK FUNCTION FIRST IN THE MAIN SCRIPT ---
display_live_clock()

st.sidebar.markdown("---")

#============================

show_technical_predictions = st.sidebar.checkbox("Show Technical Predictions", True) # Not saved/loaded

with st.sidebar.expander("⚙️ Saved Filters", expanded=False):

    # Custom UI for Presets to allow the delete button
    st.markdown("#### Load Saved filters:")

    # Get the list of saved presets
    available_presets = get_available_presets()
    display_presets = ['Default'] + available_presets

    # Create a container for the selector and the delete buttons
    preset_container = st.sidebar.container()

    # 1. Preset Selector (simplified as a hidden widget or controlled by clicks)
    # We will use st.session_state to track the selected preset instead of st.selectbox here, 
    # to allow for the custom layout. The initial selection is already in st.session_state.current_preset_name

    # Display the presets with a radio button/selection and a delete button
    # Using a radio for selection makes it easy to switch, and then a button to delete.
    selected_preset_key = st.radio(
        "Select a preset to load:",
        options=display_presets,
        index=display_presets.index(st.session_state.current_preset_name) if st.session_state.current_preset_name in display_presets else 0,
        key='preset_radio_selector',
        help="Click on a preset to load its settings. Click the 🗑️ to delete it.",
    )

    # Check if the radio selection changed and trigger a rerun
    if selected_preset_key != st.session_state.current_preset_name:
        st.session_state.current_preset_name = selected_preset_key
        st.rerun()

    st.markdown("---")

    # 2. Add the delete button for each available preset (excluding 'Default')
    st.markdown("#### Manage Filters:")
    for preset in available_presets:
        col_name, col_delete = st.columns([4, 1])

        col_name.write(f"{preset}")

        # Add the delete button (🗑️ icon)
        with col_delete:
            # Use a unique key for the button
            if st.button("🗑️", key=f"delete_preset_{preset}", help=f"Delete '{preset}' preset"):
                # Call the delete function
                success, message = delete_filter(preset)
                if success:
                    st.toast(f"Preset '{preset}' deleted successfully!", icon='✅')
                    st.session_state.current_preset_name = 'Default' # Reset to default after deletion
                    st.rerun() # Rerun to refresh the list
                else:
                    st.error(message)

#
#Set SL and Target
#
with st.sidebar.expander("Set SL and Target", expanded=False):
    # Input widgets using the loaded defaults
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

#Filters and Parameters

with st.sidebar.expander("Filters & Parameters", expanded=True):

    # Sidebar Controls using loaded defaults
    use_volume = st.checkbox("📊 Use Volume Spike", default_use_volume)
    use_breakout = st.checkbox("🚀 Use Breakout Filter", default_use_breakout)
    use_ema_rsi = st.checkbox("📉 Use EMA+RSI Filters", default_use_ema_rsi)
    use_rs = st.checkbox("💪 Use Relative Strength vs NIFTY", default_use_rs)

    interval = st.selectbox("Intraday Interval (bars)", ["5m", "15m", "30m", "1h"], index=["5m", "15m", "30m", "1h"].index(default_interval))
    auto_refresh_sec = st.slider("Auto refresh (seconds)", 30, 600, 180, 10) # Not saved/loaded
    max_symbols = st.slider("Max F&O symbols to scan", 30, 150, default_max_symbols)
    vol_zscore_threshold = st.slider("Volume z-score threshold", 1.0, 4.0, default_vol_zscore_threshold, 0.1)
    breakout_margin_pct = st.slider("Breakout margin (%)", 0.0, 3.0, default_breakout_margin_pct, 0.1)  # e.g., 0.5% -> 1.005
    atr_period = st.slider("ATR period", 5, 21, default_atr_period, 1)
    atr_mult = st.slider("ATR multiplier (SL)", 0.1, 5.0, default_atr_mult, 0.1)
    momentum_lookback = st.slider("Momentum Lookback (bars)", 2, 20, default_momentum_lookback)
    rs_lookback = st.slider("RS lookback days", 2, 15, default_rs_lookback)
    signal_score_threshold = st.slider("Signal score threshold", 2, 6, default_signal_score_threshold)

#
#Notification Settings
#
with st.sidebar.expander("Notification Settings", expanded=False):
    notify_desktop = st.checkbox("💻 Enable Desktop Notification", default_notify_desktop)
    notify_telegram = st.checkbox("📨 Enable Telegram Notification", default_notify_telegram)
    CHAT_ID = st.text_input("Telegram Chat ID", "")    
    BOT_TOKEN = st.text_input("Telegram Bot Token", "", type="password")


    # --- ADDED: TELEGRAM TEST BUTTON SECTION ---

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
                # This will now display the exact error from Telegram
                st.error(f"❌ Telegram Test Failed. Response: {info}")

    # --- SAVE BUTTON LOGIC WITH CUSTOM NAME ---
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
                st.session_state.current_preset_name = custom_name # Set new preset as active
                st.sidebar.success(f"Preset '{custom_name}' saved successfully!")
                st.rerun() # Rerun to refresh the selector list



# Initialize last_refresh_time if it doesn't exist
if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = datetime.now(IST).strftime("%I:%M:%S %p")
# Auto refresh
refresh_count = st_autorefresh(interval=auto_refresh_sec * 1000, limit=None, key="auto_refresh")
# Update the time ONLY if the refresh_count changes (i.e., a new run starts)
current_timestamp = datetime.now(IST).strftime("%I:%M:%S %p")

# Use a separate session key to track the previous count to trigger the update
if 'prev_refresh_count' not in st.session_state:
    st.session_state.prev_refresh_count = 0
    
if refresh_count > st.session_state.prev_refresh_count:
    # A new refresh cycle started, update the displayed time
    st.session_state.last_refresh_time = current_timestamp
    st.session_state.prev_refresh_count = refresh_count


# --- DISPLAY THE UPDATED COUNTER ---
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

# --- ADDED: REFRESH NOTIFICATION ---
if refresh_count > 0: # Avoid notifying on the very first load
    timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    msg = f"Scan Refreshed at {timestamp}. Interval: {auto_refresh_sec} sec."
    safe_notify("NSE Picker Status", msg)
    # Don't send telegram for a simple refresh status to avoid spam

# -------------------------
# Session state defaults
# -------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = {}
if "notified_today" not in st.session_state:
    st.session_state.notified_today = set()
if "notified_date" not in st.session_state:
    st.session_state.notified_date = date.today().isoformat()

# Reset notified_today if date changed
today_iso = date.today().isoformat()
if st.session_state.notified_date != today_iso:
    st.session_state.notified_today = set()
    st.session_state.notified_date = today_iso

# -------------------------
# Symbols list (cached)
# -------------------------
@st.cache_data(ttl=3600)
def get_fo_symbols(max_symbols_local=80):
    # Base F&O symbols — truncated to requested max
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

# -------------------------
# Batch download helper (cached)
# -------------------------
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

# We'll also cache daily NIFTY for RS calculation
@st.cache_data(ttl=300)
def get_nifty_daily():
    try:
        df = yf.download("^NSEI", period="10d", interval="1d", progress=False)
        return df
    except Exception:
        return pd.DataFrame()


# -------------------------
# Technical analysis helpers
# -------------------------
def compute_indicators(df):
    # Ensure standard column names (Title case)
    df = df.rename(columns=str.title).copy()
    # minimum columns check
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
    # AvgVol
    df["AvgVol20"] = df["Volume"].rolling(20).mean()
    df["VolStd20"] = df["Volume"].rolling(20).std()
    return df

# Remove from watchlist

def remove_from_watchlist(symbol_to_remove):
    """Callback function to instantly remove a stock from the watchlist."""
    if symbol_to_remove in st.session_state.watchlist:
        del st.session_state.watchlist[symbol_to_remove]

# Candle pattern checks
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

# -------------------------
# Main scan logic (improved)
# -------------------------

def scan_stock_improved(sym, df_stock, **kwargs):
    # --- 1. Early validation ---
    nifty_df = kwargs.get('nifty_df')
    if df_stock is None or df_stock.empty or len(df_stock) < 25:
        return 0, ["⚠️ Not enough data"], None, None, None, {}

    # --- 2. Compute indicators ---
    df = compute_indicators(df_stock)
    if df.empty:
        return 0, ["⚠️ Indicator computation failed"], None, None, None, {}

    # --- 3. Extract latest data safely ---
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

    # --- 4. EMA + RSI Filter ---
    ema_ok = False
    rsi_ok = False
    if use_ema_rsi:
        try:
            ema_ok = last_close > df["EMA20"].iloc[-1]
            if ema_ok:
                reasons.append("📈 Price above EMA20")
                score += 1

            rsi7_val = df["RSI7"].iloc[-1]
            if np.isfinite(rsi7_val):
                if rsi7_val >= 70:
                    reasons.append("💥 RSI (7) > 70 (Overbought)")
                    score += 1
                elif rsi7_val <= 30:
                    reasons.append("💥 RSI (7) < 30 (Oversold)")
                    score += 1
        except Exception:
            reasons.append("⚠️ EMA/RSI calc failed")
    else:
        reasons.append("⚪ EMA+RSI filter skipped (unchecked)")

    # --- 5. Breakout Filter ---
    breakout_ok = False
    if use_breakout:
        try:
            rolling_high = df["High"].rolling(momentum_lookback).max()
            if len(rolling_high) >= 3:
                prev_high = float(rolling_high.iloc[-2])
                margin = 1.0 + (breakout_margin_pct / 100.0)
                if last_close > (prev_high * margin) and last_close > prev_close:
                    breakout_ok = True
                    reasons.append(f"🚀 Breakout > {breakout_margin_pct:.2f}% above lookback high")
                    score += 2
        except Exception:
            reasons.append("⚠️ Breakout calc failed")
    else:
        reasons.append("⚪ Breakout filter skipped (unchecked)")

    # --- 6. Volume Spike Filter ---
    vol_spike_ok = False
    if use_volume:
        if avg_vol > 0 and vol_std > 0:
            try:
                z = (last_vol - avg_vol) / vol_std
                if np.isfinite(z) and z >= vol_zscore_threshold:
                    vol_spike_ok = True
                    reasons.append(f"📊 Volume spike detected (z={z:.2f})")
                    score += 1
            except Exception:
                reasons.append("⚠️ Volume check failed")
    else:
        reasons.append("⚪ Volume filter skipped (unchecked)")

    # --- 7. Relative Strength Filter ---
    rs_ok = False
    if use_rs and nifty_df is not None and not nifty_df.empty:
        try:
            stock_pct = df["Close"].pct_change(rs_lookback).iloc[-1]
            nifty_pct = nifty_df["Close"].pct_change(rs_lookback).iloc[-1]
            if np.isfinite(stock_pct) and np.isfinite(nifty_pct) and (stock_pct - nifty_pct) > 0:
                rs_ok = True
                reasons.append("💪 Outperforming NIFTY")
                score += 1
        except Exception:
            reasons.append("⚠️ RS calc failed")
    else:
        reasons.append("⚪ RS filter skipped (unchecked)")

    # --- 8. Candle Patterns ---
    patterns = check_candle_patterns(df)
    if patterns:
        reasons.extend(patterns)
        score += 1

    # --- 9. Entry / SL / Target ---
    entry_price = last_close
    if last_atr and last_atr > 0:
        stop_loss = entry_price - (atr_mult * last_atr)
        target_price = entry_price + 2 * (entry_price - stop_loss)
    else:
        stop_loss = entry_price * 0.98
        target_price = entry_price * 1.04

    # --- 10. If all filters off, give base score ---
    if not any([use_volume, use_breakout, use_ema_rsi, use_rs]):
        reasons.append("🕵️ Filter-free mode active (all filters off)")
        score = 1

    # --- 11. Return ---
    signal = {
        "score": score,
        "breakout_ok": breakout_ok,
        "vol_spike_ok": vol_spike_ok,
        "ema_ok": ema_ok,
        "rsi_ok": rsi_ok,
        "rs_ok": rs_ok,
        "patterns": patterns
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
# --- ADD THIS NEW FUNCTION ---
def check_watchlist_hits(df_batch):
    keys_to_remove = []
    
    # Looping over items (sym is the key, info is the value/dict)
    for sym, info in st.session_state.watchlist.items(): 
        target = info.get("target")
        sl = info.get("sl")
        
        # 1. Get the latest data for the symbol
        df_sym = extract_symbol_df(df_batch, sym)
        if df_sym is None or df_sym.empty:
            continue
            
        latest_price = float(df_sym["Close"].iloc[-1])
        message = ""

        # 2. Check for Target Hit
        if latest_price >= target:
            message = f"🎯 TARGET HIT for {sym}! Current Price: {latest_price:.2f}"
            
        # 3. Check for Stop Loss Hit
        elif latest_price <= sl:
            message = f"🛑 STOP LOSS HIT for {sym}! Current Price: {latest_price:.2f}"

        # 4. Notify if a level was hit
        if message:
            safe_notify("Trade Alert", message)      # FIXED: Removed is_telegram
            safe_telegram_send(message)              # ADDED: Separate Telegram send
            
            # Mark for removal
            keys_to_remove.append(sym)
            info["status"] = "Closed" # Update status for display if not removed yet

    # 5. Remove outside the loop
    for key in keys_to_remove:
        del st.session_state.watchlist[key]


# --- CALL THE FUNCTION AFTER THE MAIN SCAN ---
# ... (after your main for loop and the progress.empty() call)
# ... (and after the refresh confirmation in part 1)

import pandas as pd

def extract_symbol_df(df_batch_local: pd.DataFrame, sym: str) -> pd.DataFrame:
    """Return a DataFrame for `sym` from a yfinance batch DataFrame.
    Handles:
      - single-ticker DataFrame with columns like ['Open','High','Close',...]
      - multiindex DataFrame where first level is ticker and second is OHLC (group_by='ticker')
    Returns empty DataFrame if symbol not found or input is empty.
    """
    if df_batch_local is None or df_batch_local.empty:
        return pd.DataFrame()

    # normalize symbol candidates (case-insensitive)
    candidates = {sym, f"{sym}.NS"}

    cols = df_batch_local.columns

    # --- MultiIndex case (typical when yfinance group_by='ticker') ---
    if isinstance(cols, pd.MultiIndex):
        # get first level (tickers) and second level (fields like Open/Close)
        first_level = cols.get_level_values(0).astype(str)
        second_level = cols.get_level_values(1).astype(str)

        first_level_unique = pd.Index(first_level).unique()
        first_level_lc = {s.lower() for s in first_level_unique}

        # Try to match ticker (case-insensitive)
        for cand in candidates:
            cand_lc = cand.lower()
            if cand_lc in first_level_lc:
                # find actual string as present in the MultiIndex (preserve original casing)
                match = next((x for x in first_level_unique if x.lower() == cand_lc), None)
                if match is not None:
                    try:
                        return df_batch_local[match].copy()
                    except KeyError:
                        # defensive: try continue if something odd happens
                        continue

        # Fallback: maybe it's a multiindex but only one ticker and you want its columns
        # Detect if second-level contains OHLC names
        second_level_lc = {s.lower() for s in second_level}
        if {"open", "high", "close"}.intersection(second_level_lc):
            # return the first ticker block
            try:
                ticker0 = first_level_unique[0]
                return df_batch_local[ticker0].copy()
            except Exception:
                return pd.DataFrame()

        return pd.DataFrame()

    # --- Single-level columns (no MultiIndex) ---
    # Normalize column names to strings and lowercase
    lower_cols = [str(c).lower() for c in cols]

    # If typical OHLC columns are present, assume this DataFrame is already per-symbol
    if {"open", "high", "close"}.intersection(lower_cols):
        return df_batch_local.copy()

    # maybe column names include the symbol as a prefix/suffix (e.g., "RELIANCE.Open")
    for cand in candidates:
        cand_lc = cand.lower()
        if any(cand_lc in c for c in lower_cols):
            # assume whole DataFrame applies to that symbol
            return df_batch_local.copy()

    return pd.DataFrame()

for i, sym in enumerate(fo_symbols):
    status_text.text(f"Scanning {sym} ({i+1}/{len(fo_symbols)})")
    progress.progress((i + 1) / len(fo_symbols))

    df_sym = extract_symbol_df(df_batch, sym)
    
    # Inside the loop: for i, sym in enumerate(fo_symbols):
    # ... after the line: df_sym = extract_symbol_df(df_batch, sym)

    # --- Check for No Data (Robustly handles None or empty DataFrame) ---
    if df_sym is None or df_sym.empty or len(df_sym) < 25:
        # --- ADD THIS LINE FOR DEBUGGING ---
        print(f"Skipping {sym}: Data is missing/short (len={len(df_sym) if df_sym is not None else 0})")
        # ------------------------------------

        # 🌟 NEW: Append a "No Data" record to the list for debugging 🌟
        candidates.append({
            "Symbol": sym,
            "Score": 0,
            "Last Close": "N/A",
            "Entry": "N/A",
            "Stop Loss": "N/A",
            "Target": "N/A",
            "Reasons": "⚠️ No data available (Market closed or fetch failed)",
            "Signal": "N/A"
        })
        continue # Skip the rest of the logic for this symbol

    # --- Data is good, now run the scanner and append results ---
    # This line is now only run if data is good!
    score, reasons, entry, stop, target, signal = scan_stock_improved(sym, df_sym, nifty_df=nifty_df)

    # Safely read the last close price (This will no longer crash)
    last_close = float(df_sym["Close"].iloc[-1])

    # Append the full score for the scoreboard
    candidates.append({
        "Symbol": sym,
        "Score": score,
        "Last Close": last_close,
        "Entry": entry,
        "Stop Loss": stop,
        "Target": target,
        "Reasons": reasons,
        #"Signal": signal
    })

    # --- Notification Logic (STILL CONDITIONAL) ---
    if score >= signal_score_threshold:
        shortlisted_stocks.append(sym)
        
        # --- NEW LOGIC: Check if already notified for this stock today ---
        if sym not in st.session_state.notified_today:
            notify_stock(sym, last_close, entry, stop, target)
            st.session_state.notified_today.add(sym) # Mark as notified
            
        # The loop continues...

progress.empty()
status_text.text("✅ Scan complete!")
# Now, check the saved stocks
if "watchlist" in st.session_state:
    check_watchlist_hits(df_batch) # Pass the data you fetched earlier

if not candidates:
    # Option A: Simple Confirmation
    # FIX: Remove the 'is_telegram=False' keyword argument
    safe_notify("Scan Complete", "🐸 No new stocks met the entry criteria right now.") 
    
    # Telegram is handled separately, which is correct
    safe_telegram_send("✅ Scan finished. No new stocks meet the criteria.")

# Display results

if candidates:
    with st.expander("📈Shortlisted Stocks", expanded=True): 
        df_candidates = pd.DataFrame(candidates).set_index("Symbol").sort_values(by="Score", ascending=False)
        qualified_count = len(df_candidates[df_candidates['Score'] >= signal_score_threshold])
        st.success(f"✅ Scanned {len(df_candidates)} stocks. **{qualified_count}** stocks meet the threshold of {signal_score_threshold}.")
        df_candidates = pd.DataFrame(candidates).set_index("Symbol").sort_values(by="Score", ascending=False)
        st.dataframe(df_candidates)
        # Download button
        st.download_button(
            "💾 Download candidates CSV",
            df_candidates.to_csv(index=True),
            file_name=f"candidates_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            # 🌟 Add this unique key! 🌟
            key="candidates_download_2" 
        )
else:
    st.info("⚠️ No candidates found this round.")
# # -------------------------
# # Technical Predictions (reuse batch data where possible)
# # -------------------------
# if show_technical_predictions:
#     with st.expander("📈 Technical Predictions for Shortlisted Stocks", expanded=True): 
#         # All the code below MUST be correctly indented (4 spaces/one tab)
        
#         # --- Streamlit Display Section ---
#         if candidates:
#             st.success(f"✅ Found {len(candidates)} candidates (score threshold: {signal_score_threshold})")
            
#             # This line is correct, it defines df_candidates
#             df_candidates = pd.DataFrame(candidates).set_index("Symbol").sort_values(by="Score", ascending=False)
            
#             # The simple st.dataframe is redundant, delete it or skip over it
#             # st.dataframe(df_candidates)
            
#             # Download button (Line 727)
#             st.download_button(
#                 "💾 Download candidates CSV",
#                 df_candidates.to_csv(index=True),
#                 file_name=f"candidates_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv",
#                 mime="text/csv",
#                 # 🌟 Add this unique key! 🌟
#                 key="candidates_download_1" 
#             )
    
#  # 💡 START OF NEW/MOVED CODE BLOCK 💡
    
#     # st.subheader(f"🚀 Scanner Picks ({len(df_candidates)} Stocks Ticking!)") # <--- This line is now replaced by the expander

#     # --- START EXPANDER HERE ---
#     # The title of the expander replaces the subheader
#     with st.expander(f"🚀 Scanner Picks ({len(df_candidates)} Stocks Ticking!) - Click to Expand", expanded=False):
#         # EVERYTHING BELOW THIS LINE MUST BE INDENTED
        
#         # Format the 'Reasons' list into a comma-separated string for display
#         df_candidates['Confluence Tags'] = df_candidates['Reasons'].apply(lambda x: " | ".join(x) if isinstance(x, list) else x)
        
#         # Select and display the relevant columns
#         display_cols = [
#             'Score', 
#             'Confluence Tags',
#             #'Signal', 
#             'Entry', 
#             'Stop Loss', 
#             'Target'
#         ]
        
#         # Display the new table structure
#         st.dataframe(
#             df_candidates[display_cols],
#             column_config={
#                 "Symbol": "Stock",
#                 "Confluence Tags": st.column_config.ListColumn(
#                     "Why it Ticks",
#                     help="A list of technical factors satisfied by the stock.",
#                 ),
#             },
#             use_container_width=True
#         )
#     # --- END EXPANDER HERE ---
    
# # The 'else' block continues correctly
# else:
#     st.info("⚠️ No candidates found this round.")
# # ...
# -------------------------
# Technical Predictions (reuse batch data where possible)
# -------------------------
if show_technical_predictions:
    with st.expander("📈 Technical Predictions for Shortlisted Stocks", expanded=True):
        if not shortlisted_stocks:
            st.info("No shortlisted stocks to show predictions for.")
        else:
            # Check if candidates DataFrame exists
            if 'df_candidates' not in locals():
                st.warning("Candidate data not available for detailed predictions.")
                st.stop() # Use Streamlit's stop function to halt the app rerun

            for stock in shortlisted_stocks:
                # --- NEW CODE: Fetch entry/sl/target from the main candidates DataFrame ---
                try:
                    candidate_row = df_candidates.loc[stock]
                    entry_for_wl = candidate_row['Entry']
                    sl_for_wl = candidate_row['Stop Loss']
                    target_for_wl = candidate_row['Target']
                except KeyError:
                    # Stock was shortlisted but maybe filtered out later, or error in index.
                    st.warning(f"Trade levels for {stock} not found in candidates list.")
                    continue
                # --- END NEW CODE ---
                
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
                        if st.button("Add to Watchlist", key=f"add_wl_from_pred_{stock}"): # Changed key to avoid conflict
                            st.session_state.watchlist[stock] = {
                                "entry": entry_for_wl,      # <-- FIX: Use the fetched variable
                                "sl": sl_for_wl,            # <-- FIX: Use the fetched variable
                                "target": target_for_wl,    # <-- FIX: Use the fetched variable
                                "status": "Active"
                            }
                            st.success(f"Added {stock} to watchlist!")

# The 'Manual Stock Analyzer' section is already correct because 'entry', 'stop_loss', and 'target' 
# are defined immediately before the button logic in that loop.

# -------------------------
# Manual Analyzer (uses batch if possible)
# -------------------------
with st.expander("📝 Manual Stock Analyzer (Multiple Stocks)", expanded=False): 
    manual_symbols = st.text_area("Enter stock symbols separated by commas (e.g., RELIANCE,TCS,INFY)")
    manual_list = [s.strip().upper() for s in manual_symbols.split(",") if s.strip()] if manual_symbols else []

    for idx, manual_symbol in enumerate(manual_list): # <--- THE LOOP START
        # Try find in batch first; otherwise download single symbol (cached)
        df_manual = extract_symbol_df(df_batch, manual_symbol)
        if df_manual is None or df_manual.empty:
            # fallback to single download (cached)
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

        # --- Display Stock Details (Moved inside the loop) ---
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
                # The new logic: Always notify if score threshold is met, regardless of having been notified before.
                notify_stock(manual_symbol, last_price, entry, stop_loss, target)

            # --- Add to Watchlist Button and Logic (FALLBACK FIX IS HERE, inside the loop) ---
            if manual_symbol in st.session_state.watchlist:
                st.button("Added to Watchlist!", key=f"added_manual_{manual_symbol}_{idx}", disabled=True)
            else:
                if st.button("Add to Watchlist", key=f"add_manual_{manual_symbol}_{idx}"):

                    # Check if signal prices are None (meaning score was too low)
                    if entry is None:
                        # Fallback logic to calculate prices when score is too low
                        current_price = float(df_manual["Close"].iloc[-1])
                        entry_to_save = current_price
                        sl_to_save = current_price * 0.98
                        target_to_save = current_price * 1.04
                    else:
                        # Use signal prices if available
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
        # --- END of Manual Analyzer loop ---

# -------------------------
# Watchlist UI
# -------------------------
# st.subheader("📑 Watchlist & Alerts") <-- DELETED

# --- START EXPANDER HERE ---
# The title of the expander replaces the subheader
with st.expander("📑 Watchlist & Alerts - Click to manage trades", expanded=False):

    st.markdown("<div class='watchlist-container'>", unsafe_allow_html=True)

    # ADD THE HEADER ROW HERE 
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
        st.markdown("**Action**") # A header for the remove button

    # Loop to display Watchlist items
    remove_keys = []
    for sym, info in st.session_state.watchlist.items():
        # use batch intraday (1d period) if available;
    # ... The entire loop logic (including the columns and buttons) goes here
        try:
            df_watch = extract_symbol_df(df_batch, sym)
            if df_watch is None or df_watch.empty:
                df_watch = get_batch_price_data([f"{sym}.NS"], "5m")
                df_watch = extract_symbol_df(df_watch, sym)
        except Exception:
            df_watch = pd.DataFrame()

        curr_price = float(df_watch['Close'].iloc[-1]) if df_watch is not None and not df_watch.empty else None
        
        # 
    # Get values, defaulting to 'N/A' if missing
        entry_val = info.get("entry", "N/A")
        sl_val = info.get("sl", "N/A")
        tgt_val = info.get("target", "N/A")
        status = info.get("status", "Active")

        # Format the values for display (Use '.2f' for 2 decimal places)
        # Check if the value is a number (float or int) before formatting
        entry = f"{entry_val:.2f}" if isinstance(entry_val, (float, int)) else entry_val
        sl = f"{sl_val:.2f}" if isinstance(sl_val, (float, int)) else sl_val
        tgt = f"{tgt_val:.2f}" if isinstance(tgt_val, (float, int)) else tgt_val # <-- FIXED: Now a single, complete line

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
            # 
    # --- NEW CALLBACK BUTTON ---
            st.button(
                "Remove", 
                key=f"remove_{sym}", 
                on_click=remove_from_watchlist, # Calls the function immediately
                args=(sym,)                     # Passes the stock symbol to the function
        
       )

    st.markdown("</div>", unsafe_allow_html=True)
    st.info("Page auto-refresh will re-check alerts and prices.")

st.sidebar.markdown("---")    
st.sidebar.markdown("Happy Trading!!! -✏️ Vijay S")
# --- END EXPANDER HERE ---