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
    # Default to False to avoid accidental Telegram messages until user configures
    st.session_state.notify_telegram = False
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

# ===== ADD THIS SECTION FOR AI =====
# Initialize AI components
if 'predictor' not in st.session_state:
    try:
        from ai_predictor import StockPredictor
        st.session_state.predictor = StockPredictor()
        print("[✓] AI Predictor initialized")
    except Exception as e:
        st.session_state.predictor = None
        print(f"[✗] AI Predictor failed to initialize: {e}")

if 'tracker' not in st.session_state:
    try:
        from ai_predictor import PredictionTracker
        st.session_state.tracker = PredictionTracker()
        print("[✓] AI Tracker initialized")
    except Exception as e:
        st.session_state.tracker = None
        print(f"[✗] AI Tracker failed to initialize: {e}")

# ===== END AI INITIALIZATION =====

# Initialize paper trading
paper.init_paper_trades()

# Reset notifications daily
today_iso = date.today().isoformat()
if st.session_state.notified_date != today_iso:
    st.session_state.notified_today = set()
    st.session_state.notified_date = today_iso

# Render sidebar and get settings
try:
    settings = render_sidebar()
except Exception as e:
    # Sidebar failed — fall back to conservative defaults and show message
    st.error(f"Sidebar load failed, using defaults: {e}")
    settings = {
        'auto_refresh_sec': 60,
        'max_symbols': 80,
        'interval': '5m',
        'use_volume': True,
        'use_breakout': True,
        'use_ema_rsi': True,
        'use_rs': True,
        'vol_zscore_threshold': 1.2,
        'breakout_margin_pct': 0.2,
        'momentum_lookback': 3,
        'rs_lookback': 3,
        'atr_mult': 0.9,
        'atr_period': 7,
        'signal_score_threshold': 10,
        'show_technical_predictions': True,
        'custom_name': 'Default Scan',
        'scan_mode': st.session_state.get('scan_mode', 'Early Detection 🐇')
    }

# Validate settings keys and provide defaults for any missing
def _get_setting(key, default):
    try:
        return settings.get(key, default)
    except Exception:
        return default

settings['auto_refresh_sec'] = int(_get_setting('auto_refresh_sec', 60))
settings['max_symbols'] = int(_get_setting('max_symbols', 80))
settings['interval'] = _get_setting('interval', '5m')
settings['use_volume'] = bool(_get_setting('use_volume', True))
settings['use_breakout'] = bool(_get_setting('use_breakout', True))
settings['use_ema_rsi'] = bool(_get_setting('use_ema_rsi', True))
settings['use_rs'] = bool(_get_setting('use_rs', True))
settings['vol_zscore_threshold'] = float(_get_setting('vol_zscore_threshold', 1.2))
settings['breakout_margin_pct'] = float(_get_setting('breakout_margin_pct', 0.2))
settings['momentum_lookback'] = int(_get_setting('momentum_lookback', 3))
settings['rs_lookback'] = int(_get_setting('rs_lookback', 3))
settings['atr_mult'] = float(_get_setting('atr_mult', 0.9))
settings['atr_period'] = int(_get_setting('atr_period', 7))
settings['signal_score_threshold'] = int(_get_setting('signal_score_threshold', 10))
settings['show_technical_predictions'] = bool(_get_setting('show_technical_predictions', True))
settings['custom_name'] = _get_setting('custom_name', 'Default Scan')
settings['scan_mode'] = _get_setting('scan_mode', st.session_state.get('scan_mode', 'Early Detection 🐇'))

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

# Scan all symbols with robust error handling so a single error doesn't crash the app
try:
    for i, sym in enumerate(fo_symbols):
        try:
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
                    try:
                        notify_stock(sym, last_close, entry, stop, target, score, reasons)
                    except Exception as e:
                        # Notification failures shouldn't break scanning
                        st.error(f"Failed to send notification for {sym}: {e}")
                    st.session_state.notified_today.add(sym)
        except Exception as e_sym:
            # Per-symbol error handling
            logger_msg = f"Error scanning {sym}: {e_sym}"
            print(logger_msg)
            candidates.append({
                "Symbol": sym,
                "Score": 0,
                "Last Close": "N/A",
                "Entry": "N/A",
                "Stop Loss": "N/A",
                "Target": "N/A",
                "Reasons": f"⚠️ Error: {e_sym}"
            })
            continue
finally:
    progress.empty()
    status_text.text("✅ Scan complete!")

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
tab_main, tab_paper, tab_manual, tab_watchlist, tab_ai, tab_guide = st.tabs([
    "📊 Auto Scanner", 
    "💹 Paper Trading", 
    "🔍 Manual Analysis", 
    "📋 Watchlist",
    "🤖 AI Predictions",
    "📚 Trade Guide" 
])
# -----------------------------------------------------------------------------
# TAB 1: AUTO SCANNER
# -----------------------------------------------------------------------------
with tab_main:
    st.markdown("### Qualified Stocks")
    
    if not df_candidates.empty:
        try:
            render_qualified_stocks(df_candidates, settings['signal_score_threshold'])
        except Exception as e:
            st.error(f"Qualified stocks UI failed: {e}")
        
        # Render technical predictions if enabled
        if settings['show_technical_predictions'] and shortlisted_stocks:
            try:
                render_technical_predictions(shortlisted_stocks, df_candidates, df_batch)
            except Exception as e:
                st.error(f"Technical predictions UI failed: {e}")
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
    try:
        paper.paper_trading_interface()
    except Exception as e:
        st.error(f"Paper trading UI failed: {e}")

# -----------------------------------------------------------------------------
# TAB 3: MANUAL ANALYSIS
# -----------------------------------------------------------------------------
with tab_manual:
    st.markdown("### 🔍 Manual Stock Analysis")
    try:
        render_manual_search(df_batch, settings)
    except Exception as e:
        st.error(f"Manual search UI failed: {e}")

# -----------------------------------------------------------------------------
# TAB 4: WATCHLIST
# -----------------------------------------------------------------------------
with tab_watchlist:
    st.markdown("### 📋 Active Watchlist")
    try:
        render_watchlist(df_batch)
    except Exception as e:
        st.error(f"Watchlist UI failed: {e}")
# -----------------------------------------------------------------------------
# TAB 5: AI PREDICTIONS
# -----------------------------------------------------------------------------
with tab_ai:
    st.markdown("### 🤖 AI-Powered Stock Predictions")
    
    if shortlisted_stocks:
        st.info(f"📊 Analyzing {len(shortlisted_stocks)} qualified stocks from scanner")
        
        # Import AI module
        try:
            from ai_dashboard import render_ai_dashboard
            render_ai_dashboard(shortlisted_stocks, df_candidates, df_batch)
        except Exception as e:
            st.error(f"AI dashboard failed: {e}")
    else:
        st.warning("⚠️ No qualified stocks from scanner. Run a scan first!")
        
        # Still show training interface
        try:
            from ai_dashboard import render_ai_training_interface
            render_ai_training_interface()
        except Exception as e:
            st.error(f"AI training interface failed: {e}")
# -----------------------------------------------------------------------------
# TAB 6: TRADE GUIDE
# -----------------------------------------------------------------------------
with tab_guide:
    try:
        trade_guide.render_trade_guide()
    except Exception as e:
        st.error(f"Trade guide UI failed: {e}")