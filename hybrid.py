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

# App-wide CSS / Styles (Enhanced)
# ---------------------------
APP_STYLE = """
<style>
/* ===== Base App Styling ===== */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0b1120 0%, #101b3a 100%);
    color: #e6eef8;
    font-family: 'Inter', sans-serif;
}

/* Sidebar background and text */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #1e293b 100%);
    color: #f3f4f6;
    border-right: 1px solid rgba(255,255,255,0.05);
    box-shadow: 4px 0 16px rgba(0,0,0,0.4);
}
[data-testid="stSidebar"] * {
    color: #dbeafe !important;
}
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: #93c5fd !important;
}

/* ===== Header Banner ===== */
.header-banner {
    background: linear-gradient(90deg, rgba(99,102,241,0.95), rgba(168,85,247,0.9));
    padding: 18px 28px;
    border-radius: 12px;
    color: white;
    box-shadow: 0 6px 20px rgba(0,0,0,0.45);
    margin-bottom: 18px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.15);
}
.header-banner h1 {
    font-size: 28px;
    margin: 0;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.header-banner p {
    font-size: 15px;
    opacity: 0.9;
    margin-top: 4px;
}

/* ===== Cards ===== */
.card {
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.35);
}

/* ===== Watchlist Table ===== */
.watchlist-container { font-size: 14px; margin-top: 8px; }
table {
    border-collapse: collapse;
    width: 100%;
}
thead tr {
    background-color: rgba(255,255,255,0.08);
    font-weight: 600;
}
tbody tr:hover {
    background-color: rgba(255,255,255,0.07);
    transition: background 0.2s ease-in-out;
}
td, th {
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding: 8px 12px;
}

/* ===== Badges & Tags ===== */
.badge {
    display:inline-block;
    padding:6px 10px;
    border-radius:14px;
    color:white;
    font-weight:600;
    margin-right:8px;
    margin-bottom:8px;
}
.badge-green { background: #10b981; }
.badge-red { background: #ef4444; }
.badge-yellow { background: #f59e0b; }
.badge-blue { background: #3b82f6; }

/* ===== Buttons ===== */
div.stButton > button {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
}
div.stButton > button:hover {
    background: linear-gradient(90deg, #818cf8, #a78bfa);
    transform: translateY(-1px);
}

/* ===== Section Titles ===== */
.section-title {
    font-size: 20px;
    font-weight: 700;
    margin-top: 16px;
    margin-bottom: 8px;
    color: #a5b4fc;
    border-left: 4px solid #6366f1;
    padding-left: 10px;
}

/* ===== Scrollbar ===== */
::-webkit-scrollbar {
    width: 8px;
}
::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 6px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255,255,255,0.25);
}
</style>
"""

# Inject styles into Streamlit
st.markdown(APP_STYLE, unsafe_allow_html=True)

# --- GLOBAL DEFINITIONS ---
IST = pytz.timezone("Asia/Kolkata")
# Initialize notification variables globally
notify_desktop = True
notify_telegram = True
BOT_TOKEN = ""
CHAT_ID = ""
# ADD THIS NEW SECTION HERE - Initialize session state FIRST:
if 'notify_desktop' not in st.session_state:
    st.session_state.notify_desktop = True
if 'notify_telegram' not in st.session_state:
    st.session_state.notify_telegram = True
if 'BOT_TOKEN' not in st.session_state:
    st.session_state.BOT_TOKEN = ""
if 'CHAT_ID' not in st.session_state:
    st.session_state.CHAT_ID = ""

# Now set global variables from session state
notify_desktop = st.session_state.notify_desktop
notify_telegram = st.session_state.notify_telegram
BOT_TOKEN = st.session_state.BOT_TOKEN
CHAT_ID = st.session_state.CHAT_ID    
#------------------------
#Notification
#------------------------

def safe_notify(title, msg):
    notify_desktop = st.session_state.get("notify_desktop", True)
    if notify_desktop:
        try:
            notification.notify(title=title, message=msg, timeout=6)
        except Exception as e:
            st.warning(f"Desktop notify error: {e}")


def safe_telegram_send(text):
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


#------------------------
# NOTIFICATION SECTION (FIXED)
#------------------------

import time

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
        f"📢 <b>{symbol}</b> shortlisted!\n"
        f"💵 <b>Last:</b> ₹{last_price:.2f}\n"
        f"⏰ <b>Time:</b> {timestamp}"
    )

    # --- Trade levels ---
    if entry:
        msg += f"\n🟢 <b>Entry:</b> ₹{entry:.2f}"
    if stop_loss:
        msg += f"\n❌ <b>Stop-Loss:</b> ₹{stop_loss:.2f}"
    if target:
        msg += f"\n🏆 <b>Target:</b> ₹{target:.2f}"
    if score is not None:
        msg += f"\n🎯 <b>Score:</b> {score}"

    # --- Passed criteria (no emojis, just clean text) ---
    if reasons and isinstance(reasons, list):
        short_reasons = reasons[:8]
        msg += "\n\n<b>Passed Criteria:</b>"
        for r in short_reasons:
            msg += f"\n• {r}"
        if len(reasons) > 8:
            msg += f"\n…and {len(reasons) - 8} more."
    elif reasons:
        msg += f"\n\n<b>Reason:</b> {reasons}"

    # --- Convert to plain text for desktop ---
    plain_msg = (
        msg.replace("<b>", "")
           .replace("</b>", "")
           .replace("&nbsp;", " ")
           .replace("• ", "- ")
    )

    print(f"[DEBUG notify_stock] Desktop={st.session_state.get('notify_desktop')}, "
          f"Telegram={st.session_state.get('notify_telegram')}, "
          f"Token={bool(st.session_state.get('BOT_TOKEN'))}, "
          f"ChatID={bool(st.session_state.get('CHAT_ID'))}")

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

# --- FILTER PRESET MANAGEMENT ---
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

if 'scan_mode' not in st.session_state:
    st.session_state['scan_mode'] = 'Early Detection 🐇'

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
default_vol_zscore_threshold = saved_filters.get('vol_zscore_threshold', 1.2)
default_breakout_margin_pct = saved_filters.get('breakout_margin_pct', 0.2)
default_atr_period = saved_filters.get('atr_period', 7)
default_atr_mult = saved_filters.get('atr_mult', 0.9)
default_momentum_lookback = saved_filters.get('momentum_lookback', 3)
default_rs_lookback = saved_filters.get('rs_lookback', 3)
default_signal_score_threshold = saved_filters.get('signal_score_threshold', 10)
default_notify_desktop = saved_filters.get('notify_desktop', True)
default_notify_telegram = saved_filters.get('notify_telegram', True)

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

# === SCAN MODE SELECTOR ===
with st.sidebar.expander("### 🎯 Scan Strategy", expanded=True):
# st.sidebar.markdown("### 🎯 Scan Strategy")
    scan_mode = st.radio(
        "Choose scanning mode:",
        ["Early Detection 🐇", "Original 🦖"],
        index=0 if st.session_state['scan_mode'] == 'Early Detection 🐇' else 1,
        help="**Early Detection 🐇**: Catches stocks BEFORE major moves (pre-breakout, consolidation)\n\n**Original 🦖**: Waits for confirmation signals (breakouts, high RSI)"
    )

    if scan_mode != st.session_state['scan_mode']:
        st.session_state['scan_mode'] = scan_mode

# # Show mode info
# if scan_mode == "Early Detection 🐇":
#     st.sidebar.info("🎯 **Early Detection 🐇 Mode**\n\nCatches stocks in accumulation/consolidation phase before major moves.")
# else:
#     st.sidebar.info("✅ **Confirmation Mode**\n\nWaits for strong confirmation signals before alerting.")

with st.sidebar.expander("⚙️ Saved Filters", expanded=True):
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

with st.sidebar.expander("🗑️ Manage Filters:", expanded=False):
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

with st.sidebar.expander("Filter Parameters", expanded=False):
    use_volume = st.checkbox("📊 Use Volume Spike", default_use_volume)
    use_breakout = st.checkbox("🚀 Use Breakout Filter", default_use_breakout)
    use_ema_rsi = st.checkbox("📉 Use EMA+RSI Filters", default_use_ema_rsi)
    use_rs = st.checkbox("💪 Use Relative Strength vs NIFTY", default_use_rs)

    interval = st.selectbox("Intraday Interval (bars)", ["5m", "15m", "30m", "1h"], index=["5m", "15m", "30m", "1h"].index(default_interval))
    auto_refresh_sec = st.slider("Auto refresh (seconds)", 30, 600, 180, 10)
    max_symbols = st.slider("Max F&O symbols to scan", 30, 150, default_max_symbols)
    vol_zscore_threshold = st.slider("Volume z-score threshold", 0.5, 4.0, default_vol_zscore_threshold, 0.1)
    breakout_margin_pct = st.slider("Breakout margin (%)", 0.0, 3.0, default_breakout_margin_pct, 0.1)
    atr_period = st.slider("ATR period", 3, 15, default_atr_period, 1)
    atr_mult = st.slider("ATR multiplier (SL)", 0.1, 5.0, default_atr_mult, 0.1)
    momentum_lookback = st.slider("Momentum Lookback (bars)", 2, 20, default_momentum_lookback)
    rs_lookback = st.slider("RS lookback days", 2, 15, default_rs_lookback)
    signal_score_threshold = st.slider("Signal score threshold", 2, 10, default_signal_score_threshold)

with st.sidebar.expander("Notification Settings", expanded=False):
    # Use session state to persist notification settings
    if 'notify_desktop' not in st.session_state:
        st.session_state.notify_desktop = True
    if 'notify_telegram' not in st.session_state:
        st.session_state.notify_telegram = True
    if 'BOT_TOKEN' not in st.session_state:
        st.session_state.BOT_TOKEN = ""
    if 'CHAT_ID' not in st.session_state:
        st.session_state.CHAT_ID = ""
    
    # Update from checkbox/inputs
    st.session_state.notify_desktop = st.checkbox(
        "💻 Enable Desktop Notification", 
        value=st.session_state.notify_desktop
    )
    st.session_state.notify_telegram = st.checkbox(
        "📨 Enable Telegram Notification", 
        value=st.session_state.notify_telegram
    )
    st.session_state.CHAT_ID = st.text_input(
        "Telegram Chat ID", 
        value=st.session_state.CHAT_ID
    )
    st.session_state.BOT_TOKEN = st.text_input(
        "Telegram Bot Token", 
        value=st.session_state.BOT_TOKEN, 
        type="password"
    ) 

    # Update globals after user changes
    notify_desktop = st.session_state.notify_desktop
    notify_telegram = st.session_state.notify_telegram
    BOT_TOKEN = st.session_state.BOT_TOKEN
    CHAT_ID = st.session_state.CHAT_ID

    st.markdown("#### Test Notifications")
    test_message = "This is a test notification from the NSE Picker! (If you see this, it works!)"

    if st.button("Test Telegram Alert 📨"):
        if not st.session_state.notify_telegram or not st.session_state.BOT_TOKEN or not st.session_state.CHAT_ID:
            st.error("Please enable Telegram notification and fill in the Bot Token/Chat ID first!")
        else:
            # Update globals before test
            notify_telegram = st.session_state.notify_telegram
            BOT_TOKEN = st.session_state.BOT_TOKEN
            CHAT_ID = st.session_state.CHAT_ID

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
show_technical_predictions = st.sidebar.checkbox("Show Technical Predictions", True)

if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = datetime.now(IST).strftime("%I:%M:%S %p")

refresh_count = st_autorefresh(interval=auto_refresh_sec * 1000, limit=None, key="auto_refresh")
current_timestamp = datetime.now(IST).strftime("%I:%M:%S %p")

if 'prev_refresh_count' not in st.session_state:
    st.session_state.prev_refresh_count = 0
    
if refresh_count > st.session_state.prev_refresh_count:
    st.session_state.last_refresh_time = current_timestamp
    st.session_state.prev_refresh_count = refresh_count
#Reduce the space between header and top
st.markdown("""
<style>
div.block-container {
    padding-top: 0rem;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Render the header
st.markdown(f"""
<div class="header-banner" style="
    margin-top:0px;
    padding:4px 12px;
    border-radius:10px;
">
    <h1 style='font-size:22px; margin-bottom:4px;'>Stock Hunter Dashboard</h1>
    <p style='text-align:center; font-size:13px; margin-top:0px; line-height:1.3;'>
        ⏰ Refreshed <b>{refresh_count}</b> times |
        🔁 Interval: <b>{auto_refresh_sec}</b> sec |
        🕒 Last Run: <b>{st.session_state.last_refresh_time}</b> |
        ⚙️ Mode: <b>{scan_mode}</b>
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------
if refresh_count > 0:
    timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    msg = f"Scan Refreshed at {timestamp}. Mode: {scan_mode}. Interval: {auto_refresh_sec} sec."
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
# Technical analysis helpers
# -------------------------
def compute_indicators(df):
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
# ORIGINAL SCAN LOGIC 🦖
# -------------------------
def scan_stock_original(sym, df_stock, **kwargs):
    """Original 🦖 scanning logic - waits for confirmation"""
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

    # Traditional RSI + EMA
    if use_ema_rsi:
        try:
            rsi7_val = df["RSI7"].iloc[-1]
            if rsi7_val >= 70:
                reasons.append("💥 RSI (7) > 70")
                score += 2
            ema_ok = last_close > df["EMA20"].iloc[-1]
            if ema_ok:
                reasons.append("📈 Price above EMA20")
                score += 1
        except Exception:
            pass

    # Traditional volume spike
    if use_volume:
        try:
            if avg_vol > 0 and vol_std > 0:
                z = (last_vol - avg_vol) / vol_std
                if np.isfinite(z) and z >= vol_zscore_threshold:
                    reasons.append(f"📊 Volume spike (z={z:.2f})")
                    score += 2
        except Exception:
            pass

    # Traditional breakout
    if use_breakout:
        try:
            rolling_high = df["High"].rolling(momentum_lookback).max()
            if len(rolling_high) >= 2:
                prev_high = float(rolling_high.iloc[-2])
                if last_close > (prev_high * (1 + breakout_margin_pct / 100)) and last_close > prev_close:
                    reasons.append(f"🚀 Breakout ({breakout_margin_pct:.2f}%)")
                    score += 2
        except Exception:
            pass

    # RS filter
    if use_rs and nifty_df is not None and not nifty_df.empty:
        try:
            stock_pct = df["Close"].pct_change(rs_lookback).iloc[-1]
            nifty_pct = nifty_df["Close"].pct_change(rs_lookback).iloc[-1]
            if np.isfinite(stock_pct) and np.isfinite(nifty_pct) and (stock_pct - nifty_pct) > 0:
                reasons.append("💪 Outperforming NIFTY")
                score += 1
        except Exception:
            pass

    patterns = check_candle_patterns(df)
    if patterns:
        reasons.extend(patterns)
        score += 1

    entry_price = last_close
    if last_atr and last_atr > 0:
        stop_loss = entry_price - (atr_mult * last_atr)
        target_price = entry_price + 2 * (entry_price - stop_loss)
    else:
        stop_loss = entry_price * 0.98
        target_price = entry_price * 1.04

    if not any([use_volume, use_breakout, use_ema_rsi, use_rs]):
        reasons.append("🕵️ Filter-free mode active")
        score = 1

    signal = {
        "score": score,
        "mode": "confirmation"
    }

    return score, reasons, entry_price, stop_loss, target_price, signal

# -------------------------
# Early Detection 🐇 SCAN LOGIC
# -------------------------
def scan_stock_early(sym, df_stock, **kwargs):
    """Enhanced scanning logic - catches stocks early"""
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

    # 1. EARLY MOMENTUM - MACD crossing
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

    # 2. MODIFIED RSI - Early Detection 🐇
    if use_ema_rsi:
        try:
            rsi7_val = df["RSI7"].iloc[-1]
            rsi7_prev = df["RSI7"].iloc[-2] if len(df) >= 2 else rsi7_val
            
            if 50 < rsi7_val < 65 and rsi7_prev <= 50:
                reasons.append("📈 RSI early bullish (50-65)")
                score += 2
            elif 35 < rsi7_val < 50 and rsi7_prev <= 35:
                reasons.append("🔄 RSI recovering from oversold")
                score += 1
            elif rsi7_val >= 70:
                reasons.append("💥 RSI (7) > 70 (Strong momentum)")
                score += 1
                
            ema_ok = last_close > df["EMA20"].iloc[-1]
            if ema_ok:
                reasons.append("📈 Price above EMA20")
                score += 1
        except Exception:
            pass

    # 3. VOLUME ACCUMULATION
    if use_volume:
        try:
            vol_trend = df["Vol_Trend"].iloc[-1]
            if 1.2 < vol_trend < 2.0:
                reasons.append("📊 Volume accumulation phase")
                score += 2
            elif avg_vol > 0 and vol_std > 0:
                z = (last_vol - avg_vol) / vol_std
                if np.isfinite(z) and z >= vol_zscore_threshold:
                    reasons.append(f"📊 Volume spike (z={z:.2f})")
                    score += 1
        except Exception:
            pass

    # 4. CONSOLIDATION CHECK
    try:
        is_consolidating, range_pct = check_consolidation(df)
        if is_consolidating:
            reasons.append(f"🔄 Consolidating near highs ({range_pct*100:.1f}% range)")
            score += 2
    except:
        pass

    # 5. EARLY TREND FORMATION - ADX
    try:
        adx_val = df["ADX"].iloc[-1]
        adx_prev = df["ADX"].iloc[-2] if len(df) >= 2 else adx_val
        if 20 < adx_val < 30 and adx_val > adx_prev:
            reasons.append("💪 New trend forming (ADX rising)")
            score += 2
    except:
        pass

    # 6. PRE-BREAKOUT & BREAKOUT DETECTION
    if use_breakout:
        try:
            rolling_high = df["High"].rolling(momentum_lookback).max()
            if len(rolling_high) >= 2:
                prev_high = float(rolling_high.iloc[-2])
                margin_to_breakout = (prev_high - last_close) / prev_high
                
                if 0 < margin_to_breakout < 0.01:
                    reasons.append("🎯 Approaching breakout level")
                    score += 3
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

    if not any([use_volume, use_breakout, use_ema_rsi, use_rs]):
        reasons.append("🕵️ Filter-free mode active")
        score = 1

    signal = {
        "score": score,
        "early_momentum": score >= 4,
        "mode": "early"
    }

    return score, reasons, entry_price, stop_loss, target_price, signal

# -------------------------
# UPDATE GLOBALS BEFORE SCANNING
# -------------------------
# Make sure we use the latest values from session state
notify_desktop = st.session_state.get('notify_desktop', True)
notify_telegram = st.session_state.get('notify_telegram', True)
BOT_TOKEN = st.session_state.get('BOT_TOKEN', '')
CHAT_ID = st.session_state.get('CHAT_ID', '')

# Print debug info to verify values
print(f"🔍 PRE-SCAN CHECK:")
print(f"   notify_desktop: {notify_desktop}")
print(f"   notify_telegram: {notify_telegram}")
print(f"   BOT_TOKEN set: {bool(BOT_TOKEN)}")
print(f"   CHAT_ID set: {bool(CHAT_ID)}")

# --- Refresh notification settings dynamically before scan ---
st.session_state.notify_desktop = st.session_state.get("notify_desktop", True)
st.session_state.notify_telegram = st.session_state.get("notify_telegram", True)
st.session_state.BOT_TOKEN = st.session_state.get("BOT_TOKEN", "")
st.session_state.CHAT_ID = st.session_state.get("CHAT_ID", "")

notify_desktop = st.session_state.notify_desktop
notify_telegram = st.session_state.notify_telegram
BOT_TOKEN = st.session_state.BOT_TOKEN
CHAT_ID = st.session_state.CHAT_ID

print(f"[DEBUG] Refreshed settings → Desktop={notify_desktop}, Telegram={notify_telegram}, "
      f"Token={bool(BOT_TOKEN)}, ChatID={bool(CHAT_ID)}")


# -------------------------
# Scan Universe (batch)
# -------------------------
st.subheader(f"🕵️ Scanning Stocks ({custom_name})")

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
            if st.session_state.get('notify_desktop', True):
                safe_notify("Trade Alert", message)
            if st.session_state.get('notify_telegram', True):
                # Update globals
                notify_telegram = st.session_state.notify_telegram
                BOT_TOKEN = st.session_state.BOT_TOKEN
                CHAT_ID = st.session_state.CHAT_ID
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

# Choose which scanner to use based on mode
scan_function = scan_stock_early if scan_mode == "Early Detection 🐇" else scan_stock_original

for i, sym in enumerate(fo_symbols):
    status_text.text(f"Scanning {sym} ({i+1}/{len(fo_symbols)})")
    progress.progress((i + 1) / len(fo_symbols))

    df_sym = extract_symbol_df(df_batch, sym)
    
    if df_sym is None or df_sym.empty or len(df_sym) < 25:
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

    score, reasons, entry, stop, target, signal = scan_function(sym, df_sym, nifty_df=nifty_df)

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
            notify_stock(sym, last_close, entry, stop, target, score, reasons)
            st.session_state.notified_today.add(sym)

progress.empty()
status_text.text("✅ Scan complete!")

if "watchlist" in st.session_state:
    check_watchlist_hits(df_batch)

if not candidates:
    safe_notify("Scan Complete", "🐸 No new stocks met the entry criteria right now.") 
    safe_telegram_send("✅ Scan finished. No new stocks meet the criteria.")

if candidates:
    with st.expander("📈 Qualified Stocks", expanded=True): 
        df_candidates = pd.DataFrame(candidates).set_index("Symbol").sort_values(by="Score", ascending=False)
        
        # Filter ONLY qualified stocks
        qualified_df = df_candidates[df_candidates['Score'] >= signal_score_threshold]
        
        if len(qualified_df) > 0:
            # One-line compact header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ {len(qualified_df)} qualified (of {len(df_candidates)} scanned) | Threshold: {signal_score_threshold}")
            with col2:
                st.download_button(
                    "💾 CSV", 
                    qualified_df.to_csv(index=True),
                    file_name=f"qualified_{datetime.now(IST).strftime('%H%M%S')}.csv",
                    use_container_width=True
                )
            
            # Format dataframe for display
            display_df = qualified_df.copy()
            
            # Format prices
            for col in ['Last Close', 'Entry', 'Stop Loss', 'Target']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: f"₹{x:.1f}" if isinstance(x, (int, float)) else x
                    )
            
            # Compact reasons (first 2 only, truncated)
            display_df['Reasons'] = display_df['Reasons'].apply(
                lambda x: " | ".join([str(r)[:35] for r in x[:8]]) if isinstance(x, list) else str(x)[:50]
            )
            
            # Rename columns for compactness
            display_df = display_df.rename(columns={
                'Last Close': 'Last',
                'Stop Loss': 'SL',
                'Target': 'Tgt',
                'Reasons': 'Signals'
            })
            
            # Display ultra-compact table
            st.dataframe(
                display_df,
                column_config={
                    "Score": st.column_config.NumberColumn(width="small"),
                    "Last": st.column_config.TextColumn(width="small"),
                    "Entry": st.column_config.TextColumn(width="small"),
                    "SL": st.column_config.TextColumn(width="small"),
                    "Tgt": st.column_config.TextColumn(width="small"),
                    "Signals": st.column_config.TextColumn(width="large"),
                },
                use_container_width=True,
                height=min(400, len(qualified_df) * 35 + 38)  # Auto-height based on rows
            )
            
        else:
            st.warning(f"No stocks qualified (Threshold: {signal_score_threshold}). Scanned: {len(df_candidates)}")

else:
    st.info("⚠️ No scan results.")


# -------------------------
# Technical Predictions
# -------------------------
if show_technical_predictions:
    with st.expander("📈 Technical Predictions for Shortlisted Stocks", expanded=False):
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
                    score = candidate_row['Score']
                    reasons = candidate_row['Reasons']
                except KeyError:
                    st.warning(f"Trade levels for {stock} not found in candidates list.")
                    continue
                
                df_for_pred = extract_symbol_df(df_batch, stock)
                if df_for_pred is None or df_for_pred.empty:
                    st.warning(f"No data found for {stock}")
                    continue
                    
                df_for_pred = compute_indicators(df_for_pred)
                
                # Get values
                last_close = float(df_for_pred["Close"].iloc[-1])
                ema20 = float(df_for_pred["EMA20"].iloc[-1]) if "EMA20" in df_for_pred else np.nan
                rsi7 = float(df_for_pred["RSI7"].dropna().iloc[-1]) if "RSI7" in df_for_pred and not df_for_pred["RSI7"].dropna().empty else np.nan
                rsi10 = float(df_for_pred["RSI10"].dropna().iloc[-1]) if "RSI10" in df_for_pred and not df_for_pred["RSI10"].dropna().empty else np.nan
                atr = float(df_for_pred["ATR"].iloc[-1]) if "ATR" in df_for_pred and not np.isnan(df_for_pred["ATR"].iloc[-1]) else np.nan
                macd = float(df_for_pred["MACD"].iloc[-1]) if "MACD" in df_for_pred and not np.isnan(df_for_pred["MACD"].iloc[-1]) else np.nan
                macd_signal = float(df_for_pred["MACD_signal"].iloc[-1]) if "MACD_signal" in df_for_pred and not np.isnan(df_for_pred["MACD_signal"].iloc[-1]) else np.nan
                adx = float(df_for_pred["ADX"].iloc[-1]) if "ADX" in df_for_pred and not np.isnan(df_for_pred["ADX"].iloc[-1]) else np.nan
                
                # Determine trend
                price_vs_ema = "🟢 Above" if last_close > ema20 else "🔴 Below"
                rsi_status = "🔥 Overbought" if rsi7 > 70 else ("🟢 Bullish" if rsi7 > 50 else ("⚠️ Neutral" if rsi7 > 30 else "❄️ Oversold"))
                macd_status = "🟢 Bullish" if macd > macd_signal else "🔴 Bearish"
                
                 # Calculate percentages and R:R
                if isinstance(entry_for_wl, (int, float)) and isinstance(sl_for_wl, (int, float)) and isinstance(target_for_wl, (int, float)):
                    sl_pct = ((entry_for_wl - sl_for_wl) / entry_for_wl * 100)
                    target_pct = ((target_for_wl - entry_for_wl) / entry_for_wl * 100)
                    risk_reward = f"{(target_pct / sl_pct):.1f}:1" if sl_pct > 0 else "N/A"
                    # Format values before f-string
                    entry_display = f"₹{entry_for_wl:.2f}"
                    sl_display = f"₹{sl_for_wl:.2f}"
                    target_display = f"₹{target_for_wl:.2f}"
                    sl_pct_display = f"-{sl_pct:.1f}%"
                    target_pct_display = f"+{target_pct:.1f}%"
                else:
                    entry_display = "N/A"
                    sl_display = "N/A"
                    target_display = "N/A"
                    sl_pct_display = ""
                    target_pct_display = ""
                    risk_reward = "N/A"
                
                # Create beautiful banner with all info
                banner_html = f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding:15px 20px;border-radius:10px;margin-bottom:15px;box-shadow:0 4px 8px rgba(0,0,0,0.2);">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                        <h2 style="color:white;margin:0;font-size:26px;">📊 {stock}</h2>
                        <span style="background:rgba(255,215,0,0.3);color:#ffd700;padding:4px 14px;
                                     border-radius:20px;font-size:14px;font-weight:700;">
                            Score: {score}
                        </span>
                    </div>
                    <div style="color:#e0e0e0;font-size:13px;margin-bottom:12px;">
                        Last Close: <strong style="color:white;">₹{last_close:.2f}</strong>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;">
                        <div style="background:rgba(255,255,255,0.12);padding:8px;border-radius:6px;text-align:center;">
                            <div style="color:#ddd;font-size:10px;margin-bottom:3px;">💰 ENTRY</div>
                            <div style="color:white;font-size:16px;font-weight:700;">{entry_display}</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.12);padding:8px;border-radius:6px;text-align:center;">
                            <div style="color:#ddd;font-size:10px;margin-bottom:3px;">🛑 SL</div>
                            <div style="color:#ff6b6b;font-size:16px;font-weight:700;">{sl_display}</div>
                            <div style="color:#ffcccc;font-size:9px;">{sl_pct_display}</div>
                        </div>
                        <div style="background:rgba(255,255,255,0.12);padding:8px;border-radius:6px;text-align:center;">
                            <div style="color:#ddd;font-size:10px;margin-bottom:3px;">🎯 TARGET</div>
                            <div style="color:#51cf66;font-size:16px;font-weight:700;">{target_display}</div>
                            <div style="color:#d0f4d0;font-size:9px;">{target_pct_display}</div>
                        </div>
                        <div style="background:rgba(255,215,0,0.2);padding:8px;border-radius:6px;text-align:center;
                                    border:1px solid rgba(255,215,0,0.4);">
                            <div style="color:#ffe066;font-size:10px;margin-bottom:3px;">⚖️ R:R</div>
                            <div style="color:#ffd700;font-size:18px;font-weight:700;">{risk_reward}</div>
                        </div>
                    </div>
                </div>
                """
                st.markdown(banner_html, unsafe_allow_html=True)


                
                # Technical indicators in expandable section
                with st.expander("🔍 Technical Analysis Details", expanded=False):
                    col_ta1, col_ta2, col_ta3 = st.columns(3)
                    
                    with col_ta1:
                        st.markdown("#### 📈 Trend Indicators")
                        st.markdown(f"**EMA20:** ₹{ema20:.2f}")
                        st.markdown(f"**Price vs EMA:** {price_vs_ema}")
                        if not np.isnan(adx):
                            adx_strength = "💪 Strong" if adx > 25 else ("📊 Moderate" if adx > 20 else "📉 Weak")
                            st.markdown(f"**ADX:** {adx:.1f} {adx_strength}")
                    
                    with col_ta2:
                        st.markdown("#### 🎯 Momentum")
                        if not np.isnan(rsi7):
                            st.markdown(f"**RSI(7):** {rsi7:.1f} {rsi_status}")
                            # RSI bar
                            rsi_color = "#ff4444" if rsi7 > 70 else ("#44ff44" if rsi7 > 50 else ("#ffaa44" if rsi7 > 30 else "#4444ff"))
                            st.markdown(f"""
                            <div style="background: #ddd; border-radius: 10px; height: 20px; width: 100%;">
                                <div style="background: {rsi_color}; width: {rsi7}%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            """, unsafe_allow_html=True)
                        if not np.isnan(rsi10):
                            st.markdown(f"**RSI(10):** {rsi10:.1f}")
                    
                    with col_ta3:
                        st.markdown("#### 📊 MACD & Volatility")
                        if not np.isnan(macd) and not np.isnan(macd_signal):
                            st.markdown(f"**MACD:** {macd:.2f}")
                            st.markdown(f"**Signal:** {macd_signal:.2f}")
                            st.markdown(f"**Status:** {macd_status}")
                        if not np.isnan(atr):
                            st.markdown(f"**ATR:** {atr:.2f}")
                
                # Signal reasons - horizontal badge style
                st.markdown("#### 🎯 Signal Reasons")
                reasons_list = reasons if isinstance(reasons, list) else [reasons]
                
                # Create HTML badges with proper escaping
                badges_html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;">'
                
                for reason in reasons_list:
                    # Clean the reason text
                    reason_text = str(reason).replace('"', '&quot;').replace("'", "&#39;")
                    
                    # Color coding based on reason type
                    if "MACD" in reason or "reversal" in reason:
                        badge_color = "#4CAF50"  # Green
                    elif "breakout" in reason or "Approaching" in reason:
                        badge_color = "#FF9800"  # Orange
                    elif "RSI" in reason:
                        badge_color = "#2196F3"  # Blue
                    elif "Volume" in reason:
                        badge_color = "#9C27B0"  # Purple
                    elif "Consolidating" in reason:
                        badge_color = "#00BCD4"  # Cyan
                    elif "trend" in reason or "ADX" in reason:
                        badge_color = "#FF5722"  # Deep Orange
                    elif "EMA" in reason:
                        badge_color = "#607D8B"  # Blue Grey
                    else:
                        badge_color = "#757575"  # Grey
                    
                    badges_html += f'<span style="display: inline-block; background: {badge_color}; color: white; padding: 6px 12px; border-radius: 16px; font-size: 13px; font-weight: 500; box-shadow: 0 2px 4px rgba(0,0,0,0.2); margin-right: 8px; margin-bottom: 8px;">✓ {reason_text}</span>'
                
                badges_html += '</div>'
                st.markdown(badges_html, unsafe_allow_html=True)

                
                # Action buttons
                col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 6])
                with col_btn1:
                    if stock in st.session_state.watchlist:
                        st.success("✅ In Watchlist")
                    else:
                        if st.button(f"➕ Watchlist", key=f"add_wl_from_pred_{stock}", use_container_width=True):
                            st.session_state.watchlist[stock] = {
                                "entry": entry_for_wl,
                                "sl": sl_for_wl,
                                "target": target_for_wl,
                                "status": "Active"
                            }
                            st.success(f"Added {stock} to watchlist!")
                            st.rerun()
                
                with col_btn2:
                    if st.button(f"📊 View Chart", key=f"chart_{stock}", use_container_width=True):
                        st.info(f"Opening TradingView for {stock}...")
                        st.markdown(f"[Open in TradingView](https://www.tradingview.com/chart/?symbol=NSE%3A{stock})", unsafe_allow_html=True)
                
                # Separator
                st.markdown("---")

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

        score, reasons, entry, stop_loss, target, signal = scan_function(manual_symbol, df_manual, nifty_df=nifty_df)

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
