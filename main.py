"""
main.py - Main application file
Run this file with: streamlit run main.py
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, date
import pytz
import pandas as pd
import paper
import trade_guide

# Import custom modules
from styles import APP_STYLE, COMPACT_HEADER_STYLE
from functions import (
    get_fo_symbols, get_batch_price_data, get_nifty_daily,
    extract_symbol_df, notify_stock, safe_notify, check_watchlist_hits
)
from scanning_logic import scan_stock_original, scan_stock_early
from sidebar import render_sidebar
from ui_components import (
    render_header, render_qualified_stocks, render_watchlist,
    render_technical_predictions, render_manual_search
)

# Page config
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="Stock Hunter Dashboard",
    page_icon="📊"
)

# Apply styles
st.markdown(APP_STYLE, unsafe_allow_html=True)
st.markdown(COMPACT_HEADER_STYLE, unsafe_allow_html=True)

# Initialize session state
IST = pytz.timezone("Asia/Kolkata")

if 'notify_desktop' not in st.session_state:
    st.session_state.notify_desktop = True
if 'notify_telegram' not in st.session_state:
    st.session_state.notify_telegram = True
if 'BOT_TOKEN' not in st.session_state:
    st.session_state.BOT_TOKEN = ""
if 'CHAT_ID' not in st.session_state:
    st.session_state.CHAT_ID = ""
if "watchlist" not in st.session_state:
    st.session_state.watchlist = {}
if "notified_today" not in st.session_state:
    st.session_state.notified_today = set()
if "notified_date" not in st.session_state:
    st.session_state.notified_date = date.today().isoformat()
if 'current_preset_name' not in st.session_state:
    st.session_state['current_preset_name'] = 'Default'
if 'scan_mode' not in st.session_state:
    st.session_state['scan_mode'] = 'Early Detection 🐇'
if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = datetime.now(IST).strftime("%I:%M:%S %p")
if 'pending_trade' not in st.session_state:
    st.session_state['pending_trade'] = None

# Initialize paper trading
paper.init_paper_trades()

# Reset notifications daily
today_iso = date.today().isoformat()
if st.session_state.notified_date != today_iso:
    st.session_state.notified_today = set()
    st.session_state.notified_date = today_iso

# Render sidebar and get settings
settings = render_sidebar()

# Auto-refresh setup
if 'prev_refresh_count' not in st.session_state:
    st.session_state.prev_refresh_count = 0

refresh_count = st_autorefresh(interval=settings['auto_refresh_sec'] * 1000, limit=None, key="auto_refresh")
current_timestamp = datetime.now(IST).strftime("%I:%M:%S %p")

if refresh_count > st.session_state.prev_refresh_count:
    st.session_state.last_refresh_time = current_timestamp
    st.session_state.prev_refresh_count = refresh_count

# Render header
render_header(refresh_count, settings['auto_refresh_sec'], 
              st.session_state.last_refresh_time, settings['scan_mode'])

# Refresh notification
if refresh_count > 0:
    timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
    msg = f"Scan Refreshed at {timestamp}. Mode: {settings['scan_mode']}."
    safe_notify("NSE Picker Status", msg)

# =============================================================================
# MAIN SCANNING LOGIC (Run Once for All Tabs)
# =============================================================================
st.subheader(f"🕵️ Scanning Stocks ({settings['custom_name']})")

fo_symbols = get_fo_symbols(settings['max_symbols'])
tickers = [f"{s}.NS" for s in fo_symbols]

progress = st.progress(0)
status_text = st.empty()

df_batch = get_batch_price_data(tickers, settings['interval'])
nifty_df = get_nifty_daily()

candidates = []
shortlisted_stocks = []

# Choose scanner based on mode
scan_function = scan_stock_early if settings['scan_mode'] == "Early Detection 🐇" else scan_stock_original

# Scan all symbols
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
            "Reasons": "⚠️ No data available"
        })
        continue
    
    score, reasons, entry, stop, target, signal = scan_function(
        sym, df_sym, 
        nifty_df=nifty_df,
        use_volume=settings['use_volume'],
        use_breakout=settings['use_breakout'],
        use_ema_rsi=settings['use_ema_rsi'],
        use_rs=settings['use_rs'],
        vol_zscore_threshold=settings['vol_zscore_threshold'],
        breakout_margin_pct=settings['breakout_margin_pct'],
        momentum_lookback=settings['momentum_lookback'],
        rs_lookback=settings['rs_lookback'],
        atr_mult=settings['atr_mult'],
        atr_period=settings['atr_period']
    )
    
    last_close = float(df_sym["Close"].iloc[-1])
    
    candidates.append({
        "Symbol": sym,
        "Score": score,
        "Last Close": last_close,
        "Entry": entry,
        "Stop Loss": stop,
        "Target": target,
        "Reasons": reasons
    })
    
    if score >= settings['signal_score_threshold']:
        shortlisted_stocks.append(sym)
        
        if sym not in st.session_state.notified_today:
            notify_stock(sym, last_close, entry, stop, target, score, reasons)
            st.session_state.notified_today.add(sym)

progress.empty()
status_text.text("✅ Scan complete!")

# Check watchlist hits
check_watchlist_hits(df_batch)

# Create DataFrame for all tabs to use
if candidates:
    df_candidates = pd.DataFrame(candidates).set_index("Symbol").sort_values(by="Score", ascending=False)
else:
    df_candidates = pd.DataFrame()

# =============================================================================
# TAB SECTION
# =============================================================================
tab_main, tab_paper, tab_manual, tab_watchlist, tab_guide = st.tabs([
    "📊 Auto Scanner", 
    "💹 Paper Trading", 
    "🔍 Manual Analysis", 
    "📋 Watchlist",
    "📚 Trade Guide" 
])

# -----------------------------------------------------------------------------
# TAB 1: AUTO SCANNER
# -----------------------------------------------------------------------------
with tab_main:
    st.markdown("### 📈 Qualified Stocks")
    
    if not df_candidates.empty:
        render_qualified_stocks(df_candidates, settings['signal_score_threshold'])
        
        # Render technical predictions if enabled
        if settings['show_technical_predictions'] and shortlisted_stocks:
            render_technical_predictions(shortlisted_stocks, df_candidates, df_batch)
    else:
        st.info("⚠️ No scan results available.")

# -----------------------------------------------------------------------------
# TAB 2: PAPER TRADING
# -----------------------------------------------------------------------------
with tab_paper:
    # Show pending trade notification if coming from scanner
    if st.session_state.get('pending_trade') and st.session_state['pending_trade'].get('switch_to_paper'):
        st.info("🎯 You have a pending trade from the scanner! Scroll down to execute it.")
    
    # Call the complete paper trading interface
    paper.paper_trading_interface()

# -----------------------------------------------------------------------------
# TAB 3: MANUAL ANALYSIS
# -----------------------------------------------------------------------------
with tab_manual:
    st.markdown("### 🔍 Manual Stock Analysis")
    render_manual_search(df_batch, settings)

# -----------------------------------------------------------------------------
# TAB 4: WATCHLIST
# -----------------------------------------------------------------------------
with tab_watchlist:
    st.markdown("### 📋 Active Watchlist")
    render_watchlist(df_batch)

# -----------------------------------------------------------------------------
# TAB 5: TRADE GUIDE
# -----------------------------------------------------------------------------
with tab_guide:
    trade_guide.render_trade_guide()