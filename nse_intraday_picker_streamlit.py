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
default_sl_percent = saved_filters.get('sl_percent', 5.0) 
default_target_percent = saved_filters.get('target_percent', 10.0) 

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
st.set_page_config(page_title="📊 NSE Intraday Stock Picker (Improved)", layout="wide")
st.title("📈 NSE Intraday Stock Picker — Cleaner Signals")

# --- FILTER WIDGETS SECTION (MOVED TO SIDEBAR) ---
st.sidebar.markdown("### ⚙️ Filter Presets & Trade Levels")

# Custom UI for Presets to allow the delete button
st.sidebar.markdown("#### Load Saved Preset:")

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
selected_preset_key = st.sidebar.radio(
    "Select a preset to load:",
    options=display_presets,
    index=display_presets.index(st.session_state.current_preset_name) if st.session_state.current_preset_name in display_presets else 0,
    key='preset_radio_selector',
    help="Click on a preset to load its settings. Click the ❌ to delete it.",
)

# Check if the radio selection changed and trigger a rerun
if selected_preset_key != st.session_state.current_preset_name:
    st.session_state.current_preset_name = selected_preset_key
    st.rerun()

st.sidebar.markdown("---")

# 2. Add the delete button for each available preset (excluding 'Default')
st.sidebar.markdown("#### Manage Presets:")
for preset in available_presets:
    col_name, col_delete = st.sidebar.columns([4, 1])
    
    col_name.write(f"**{preset}**")
    
    # Add the delete button (❌ icon)
    with col_delete:
        # Use a unique key for the button
        if st.button("❌", key=f"delete_preset_{preset}", help=f"Delete '{preset}' preset"):
            # Call the delete function
            success, message = delete_filter(preset)
            if success:
                st.toast(f"Preset '{preset}' deleted successfully!", icon='✅')
                st.session_state.current_preset_name = 'Default' # Reset to default after deletion
                st.rerun() # Rerun to refresh the list
            else:
                st.sidebar.error(message)

st.sidebar.markdown("---")


# Input widgets using the loaded defaults
sl_percent = st.sidebar.number_input(
    "Stop Loss %", 
    min_value=0.1, 
    value=default_sl_percent, 
    step=0.1, 
    key="sl_percent_input" 
)

target_percent = st.sidebar.number_input(
    "Target %", 
    min_value=0.1, 
    value=default_target_percent, 
    step=0.1, 
    key="target_percent_input" 
)

st.sidebar.markdown("### Filters & Parameters")

# Sidebar Controls using loaded defaults
use_volume = st.sidebar.checkbox("📊 Use Volume Spike", default_use_volume)
use_breakout = st.sidebar.checkbox("🚀 Use Breakout Filter", default_use_breakout)
use_ema_rsi = st.sidebar.checkbox("📉 Use EMA+RSI Filters", default_use_ema_rsi)
use_rs = st.sidebar.checkbox("💪 Use Relative Strength vs NIFTY", default_use_rs)

interval = st.sidebar.selectbox("Intraday Interval (bars)", ["5m", "15m", "30m", "1h"], index=["5m", "15m", "30m", "1h"].index(default_interval))
auto_refresh_sec = st.sidebar.slider("Auto refresh (seconds)", 30, 600, 180, 10) # Not saved/loaded
max_symbols = st.sidebar.slider("Max F&O symbols to scan", 30, 150, default_max_symbols)
vol_zscore_threshold = st.sidebar.slider("Volume z-score threshold", 1.0, 4.0, default_vol_zscore_threshold, 0.1)
breakout_margin_pct = st.sidebar.slider("Breakout margin (%)", 0.0, 3.0, default_breakout_margin_pct, 0.1)  # e.g., 0.5% -> 1.005
atr_period = st.sidebar.slider("ATR period", 5, 21, default_atr_period, 1)
atr_mult = st.sidebar.slider("ATR multiplier (SL)", 0.1, 5.0, default_atr_mult, 0.1)
momentum_lookback = st.sidebar.slider("Momentum Lookback (bars)", 2, 20, default_momentum_lookback)
rs_lookback = st.sidebar.slider("RS lookback days", 2, 15, default_rs_lookback)
signal_score_threshold = st.sidebar.slider("Signal score threshold", 2, 6, default_signal_score_threshold)

st.sidebar.markdown("---")

show_technical_predictions = st.sidebar.checkbox("🔮 Show Technical Predictions", True) # Not saved/loaded
notify_desktop = st.sidebar.checkbox("💻 Enable Desktop Notification", default_notify_desktop)
notify_telegram = st.sidebar.checkbox("📨 Enable Telegram Notification", default_notify_telegram)
BOT_TOKEN = st.sidebar.text_input("Telegram Bot Token", "", type="password")
CHAT_ID = st.sidebar.text_input("Telegram Chat ID", "")


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



# Auto refresh
refresh_count = st_autorefresh(interval=auto_refresh_sec * 1000, limit=None, key="auto_refresh")
st.markdown(f"⏰ Refreshed {refresh_count} times. Interval: {auto_refresh_sec} seconds.")

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
        "ICICIGI", "ADANIPOWER", "BAJFINANCE"
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
# Utility functions
# -------------------------
IST = pytz.timezone("Asia/Kolkata")

def safe_notify(title, msg):
    if notify_desktop:
        try:
            notification.notify(title=title, message=msg, timeout=6)
        except Exception as e:
            st.warning(f"Desktop notify error: {e}")

def safe_telegram_send(text):
    if not notify_telegram or not BOT_TOKEN or not CHAT_ID:
        return False, "Telegram disabled or credentials missing"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=5)
        if resp.status_code == 200:
            return True, "OK"
        else:
            data = resp.json()
            return False, data.get("description", f"HTTP {resp.status_code}")
    except Exception as e:
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
def scan_stock_improved(df, sym, nifty_df=None):
    """
    Returns: score (int), reasons (list), entry, stop, target, signal_dict
    """
    if df is None or df.empty or len(df) < 25:
        return 0, [], None, None, None, {}

    df = compute_indicators(df)
    reasons = []
    score = 0

    try:
        last_close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2])
        last_vol = float(df["Volume"].iloc[-1])
        avg_vol = float(df["AvgVol20"].iloc[-1]) if not np.isnan(df["AvgVol20"].iloc[-1]) else 0.0
        vol_std = float(df["VolStd20"].iloc[-1]) if not np.isnan(df["VolStd20"].iloc[-1]) else 0.0
        last_atr = float(df["ATR"].iloc[-1]) if not np.isnan(df["ATR"].iloc[-1]) else 0.0
    except Exception:
        return 0, [], None, None, None, {}

    # --- Breakout detection with margin ---
    breakout_ok = False
    try:
        rolling_high = df["High"].rolling(momentum_lookback).max() # Use 'High' column for a true price barrier
        # ensure there are enough values
        if len(rolling_high) >= 3:
            prev_high = float(rolling_high.iloc[-2])
            prev_prev_high = float(rolling_high.iloc[-3]) if len(rolling_high) >= 3 else prev_high
            margin = 1.0 + (breakout_margin_pct / 100.0)
            brk1 = last_close > (prev_high * margin)
            brk2 = prev_close > (prev_prev_high * margin)
            breakout_ok = (brk1 and brk2 and (last_close > prev_close))
            if breakout_ok:
                reasons.append(f"🚀 Breakout confirmed (> {breakout_margin_pct:.2f}% above lookback high)")
                score += 2  # breakout is worth 2 points
    except Exception:
        breakout_ok = False

    # --- Volume z-score spike ---
    vol_spike_ok = False
    if use_volume and avg_vol > 0 and vol_std > 0:
        try:
            z = (last_vol - avg_vol) / vol_std
            if np.isfinite(z) and z >= vol_zscore_threshold:
                vol_spike_ok = True
                reasons.append(f"📊 Volume z-score {z:.2f} >= {vol_zscore_threshold}")
                score += 1
        except Exception:
            vol_spike_ok = False

    # --- EMA check ---
    ema_ok = False
    try:
        ema_ok = last_close > df["EMA20"].iloc[-1]
        if ema_ok:
            reasons.append("📈 Price above EMA20")
            score += 1
    except Exception:
        ema_ok = False

    # --- RSI cross confirmation ---
    rsi_ok = False
    try:
        rsi_series = df["RSI10"].dropna().values
        if len(rsi_series) >= 2:
            rsi_cross = (rsi_series[-2] < 50) and (rsi_series[-1] > 55)
            rsi_simple = rsi_series[-1] > 55
            if rsi_cross:
                reasons.append("💪 RSI crossed 50→55 (momentum shift)")
                rsi_ok = True
                score += 1
            elif rsi_simple and not rsi_ok:
                # reward simple RSI>55 too, but lower priority than cross
                reasons.append("💪 RSI > 55")
                rsi_ok = True
                score += 1
    except Exception:
        rsi_ok = False

    # --- Candle patterns
    patterns = check_candle_patterns(df)
    if patterns:
        reasons.extend(patterns)
        # give patterns a small boost (0.5 rounded by adding 1 only when score beneficial)
        score += 1

    # --- Relative Strength vs NIFTY
    rs_ok = False
    if use_rs and nifty_df is not None and not nifty_df.empty:
        try:
            # percent change over rs_lookback days (using close)
            stock_pct = df["Close"].pct_change(rs_lookback).iloc[-1]
            nifty_pct = nifty_df["Close"].pct_change(rs_lookback).iloc[-1]
            if np.isfinite(stock_pct) and np.isfinite(nifty_pct) and (stock_pct - nifty_pct) > 0:
                rs_ok = True
                reasons.append("📊 Outperforming NIFTY")
                score += 1
        except Exception:
            rs_ok = False

    # --- Compose final decision
    # We allow disablement of individual filters. However, scoring handles final selection.
    # The signal strength threshold is configured by user (signal_score_threshold)
    entry_price = None
    stop_loss = None
    target_price = None

    if score >= signal_score_threshold:
        entry_price = last_close
        if last_atr and last_atr > 0:
            stop_loss = entry_price - (atr_mult * last_atr)
            target_price = entry_price + 2 * (entry_price - stop_loss)
        # if ATR not available, use simple percent stops
        else:
            stop_loss = entry_price * 0.98
            target_price = entry_price * 1.04

    # Collect signal metadata
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
st.subheader("🚀 Scanning F&O Stocks (Improved Signals)")

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

# df_batch can be structured as either single ticker DataFrame (if one) or multiindex columns when group_by used.
def extract_symbol_df(df_batch_local, sym):
    # sym e.g., "RELIANCE"
    if df_batch_local is None or df_batch_local.empty:
        return pd.DataFrame()
    # When group_by='ticker' and multiple tickers, df_batch has top-level columns = tickers
    if isinstance(df_batch_local.columns, pd.MultiIndex):
        if sym in df_batch_local.columns.levels[0]:
            try:
                df_sym = df_batch_local[sym].copy()
                return df_sym
            except Exception:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    else:
        # Single-structure DataFrame (maybe only one ticker was downloaded)
        # Try to detect if the DataFrame corresponds to the symbol (match in columns or index)
        # Best-effort: if first column name contains typical OHLC
        if any(c.lower() in [col.lower() for col in df_batch_local.columns] for c in ["Open", "High", "Close"]):
            return df_batch_local.copy()
        return pd.DataFrame()

for i, sym in enumerate(fo_symbols):
    status_text.text(f"Scanning {sym} ({i+1}/{len(fo_symbols)})")
    progress.progress((i + 1) / len(fo_symbols))

    df_sym = extract_symbol_df(df_batch, sym)
    
    # 1. Check for missing data (This handles the case where yfinance fails or data is too short)
    if df_sym is None or df_sym.empty or len(df_sym) < momentum_lookback:
        # Using 'sym' instead of the undefined 'symbol'
        print(f"Skipping {sym}: Data is missing or too short.") 
        continue

    # Note: Using 'sym' and 'df_sym' for printing the last bar info
    print(f"Scanning the last bar for {sym}. Date is: {df_sym.index[-1].date()}")
    
    # Run improved scan
    score, reasons, entry, stop, target, signal = scan_stock_improved(df_sym, sym, nifty_df=nifty_df)
    if score >= signal_score_threshold:
        last_close = float(df_sym["Close"].iloc[-1])
        candidates.append({
            "Symbol": sym,
            "Score": score,
            "Last Close": last_close,
            "Entry": entry,
            "Stop Loss": stop,
            "Target": target,
            "Reasons": "; ".join(reasons),
            "Signal": signal
        })
        shortlisted_stocks.append(sym)

        # Notify only once per day
        if sym not in st.session_state.notified_today:
            notify_stock(sym, last_close, entry, stop, target)
            st.session_state.notified_today.add(sym)

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
    st.success(f"✅ Found {len(candidates)} candidates (score threshold: {signal_score_threshold})")
    df_candidates = pd.DataFrame(candidates).set_index("Symbol").sort_values(by="Score", ascending=False)
    st.dataframe(df_candidates)
    # Download button
    st.download_button(
        "💾 Download candidates CSV",
        df_candidates.to_csv(index=True),
        file_name=f"candidates_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
else:
    st.info("⚠️ No candidates found this round.")

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
st.subheader("📝 Manual Stock Analyzer (Multiple Stocks)")
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

    score, reasons, entry, stop_loss, target, signal = scan_stock_improved(df_manual, manual_symbol, nifty_df=nifty_df)
    
    # --- Display Stock Details (Moved inside the loop) ---
    if df_manual is not None and not df_manual.empty:
        last_price = float(df_manual["Close"].iloc[-1])
        st.write(f"📌 **{manual_symbol}** — Score: {score}")
        st.write(f"💵 Last: {last_price:.2f} | 🟢 Entry: {entry if entry else 'N/A'} | ❌ Stop: {stop_loss if stop_loss else 'N/A'} | 🏆 Target: {target if target else 'N/A'}")
        st.write("**Filters Passed:**", "✅ Yes" if score >= signal_score_threshold else "❌ No")
        st.write("**Why:**")
        if reasons:
            for r in reasons:
                st.markdown(f"- {r}")
        else:
            st.write("Did not meet criteria.")
            
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
            if manual_symbol not in st.session_state.notified_today:
                notify_stock(manual_symbol, last_price, entry, stop_loss, target)
                st.session_state.notified_today.add(manual_symbol)
        
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
st.subheader("📑 Watchlist & Alerts")
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
    # use batch intraday (1d period) if available; fallback quick fetch
    try:
        df_watch = extract_symbol_df(df_batch, sym)
        if df_watch is None or df_watch.empty:
            df_watch = get_batch_price_data([f"{sym}.NS"], "5m")
            df_watch = extract_symbol_df(df_watch, sym)
    except Exception:
        df_watch = pd.DataFrame()

    curr_price = float(df_watch['Close'].iloc[-1]) if df_watch is not None and not df_watch.empty else None
    
    # Get values, defaulting to 'N/A' if missing
    entry_val = info.get("entry", "N/A")
    sl_val = info.get("sl", "N/A")
    tgt_val = info.get("target", "N/A")
    status = info.get("status", "Active")
    
    # Format the values for display (Use '.2f' for 2 decimal places)
    # Check if the value is a number (float or int) before formatting
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
        # --- NEW CALLBACK BUTTON ---
        st.button(
            "Remove", 
            key=f"remove_{sym}", 
            on_click=remove_from_watchlist, # Calls the function immediately
            args=(sym,)                     # Passes the stock symbol to the function
        )

st.markdown("</div>", unsafe_allow_html=True)
st.info("Page auto-refresh will re-check alerts and prices.")
