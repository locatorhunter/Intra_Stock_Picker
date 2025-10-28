"""
sidebar.py - Sidebar UI components
"""

import streamlit as st
from datetime import datetime
import pytz
import paper
from functions import (
    load_filters, get_available_presets, delete_filter, save_filters,
    safe_telegram_send
)

IST = pytz.timezone("Asia/Kolkata")

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

def render_sidebar():
    """Render complete sidebar with all controls"""
    display_live_clock()
    st.sidebar.markdown("---")
    
    # Load saved filters
    saved_filters = load_filters(st.session_state.current_preset_name)
    
    # Set defaults
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
    
    # === SCAN MODE SELECTOR ===
    with st.sidebar.expander("### 🎯 Scan Strategy", expanded=True):
        scan_mode = st.radio(
            "Choose scanning mode:",
            ["Early Detection 🐇", "Original 🦖"],
            index=0 if st.session_state['scan_mode'] == 'Early Detection 🐇' else 1,
            help="**Early Detection 🐇**: Catches stocks BEFORE major moves\n\n**Original 🦖**: Waits for confirmation signals"
        )
        
        if scan_mode != st.session_state['scan_mode']:
            st.session_state['scan_mode'] = scan_mode
    
    # === SAVED FILTERS ===
    with st.sidebar.expander("⚙️ Saved Filters", expanded=True):
        st.markdown("#### Load Saved filters:")
        available_presets = get_available_presets()
        display_presets = ['Default'] + available_presets
        
        selected_preset_key = st.radio(
            "Select a preset to load:",
            options=display_presets,
            index=display_presets.index(st.session_state.current_preset_name) if st.session_state.current_preset_name in display_presets else 0,
            key='preset_radio_selector',
            help="Click on a preset to load its settings."
        )
        
        if selected_preset_key != st.session_state.current_preset_name:
            st.session_state.current_preset_name = selected_preset_key
            st.rerun()
    
    # === MANAGE FILTERS ===
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
    
    # === SL AND TARGET ===
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
    
    # === FILTER PARAMETERS ===
    with st.sidebar.expander("Filter Parameters", expanded=False):
        use_volume = st.checkbox("📊 Use Volume Spike", default_use_volume)
        use_breakout = st.checkbox("🚀 Use Breakout Filter", default_use_breakout)
        use_ema_rsi = st.checkbox("📉 Use EMA+RSI Filters", default_use_ema_rsi)
        use_rs = st.checkbox("💪 Use Relative Strength vs NIFTY", default_use_rs)
        
        interval = st.selectbox("Intraday Interval (bars)", ["5m", "15m", "30m", "1h"], 
                               index=["5m", "15m", "30m", "1h"].index(default_interval))
        auto_refresh_sec = st.slider("Auto refresh (seconds)", 30, 600, 180, 10)
        max_symbols = st.slider("Max F&O symbols to scan", 30, 150, default_max_symbols)
        vol_zscore_threshold = st.slider("Volume z-score threshold", 0.5, 4.0, default_vol_zscore_threshold, 0.1)
        breakout_margin_pct = st.slider("Breakout margin (%)", 0.0, 3.0, default_breakout_margin_pct, 0.1)
        atr_period = st.slider("ATR period", 3, 15, default_atr_period, 1)
        atr_mult = st.slider("ATR multiplier (SL)", 0.1, 5.0, default_atr_mult, 0.1)
        momentum_lookback = st.slider("Momentum Lookback (bars)", 2, 20, default_momentum_lookback)
        rs_lookback = st.slider("RS lookback days", 2, 15, default_rs_lookback)
        signal_score_threshold = st.slider("Signal score threshold", 2, 10, default_signal_score_threshold)
    
    # === NOTIFICATION SETTINGS ===
    with st.sidebar.expander("Notification Settings", expanded=False):
        if 'notify_desktop' not in st.session_state:
            st.session_state.notify_desktop = True
        if 'notify_telegram' not in st.session_state:
            st.session_state.notify_telegram = True
        if 'BOT_TOKEN' not in st.session_state:
            st.session_state.BOT_TOKEN = ""
        if 'CHAT_ID' not in st.session_state:
            st.session_state.CHAT_ID = ""
        
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
        
        st.markdown("#### Test Notifications")
        test_message = "This is a test notification from the NSE Picker!"
        
        if st.button("Test Telegram Alert 📨"):
            if not st.session_state.notify_telegram or not st.session_state.BOT_TOKEN or not st.session_state.CHAT_ID:
                st.error("Please enable Telegram notification and fill in credentials!")
            else:
                st.info("Sending test message...")
                ok, info = safe_telegram_send(test_message)
                if ok:
                    st.success("✅ Telegram Test Success!")
                else:
                    st.error(f"❌ Telegram Test Failed. Response: {info}")
    
    # === SAVE SETTINGS ===
    st.sidebar.markdown("### Save Current Settings")
    custom_name = st.sidebar.text_input("Name for the Filter Preset", 
                                        value=st.session_state.current_preset_name, 
                                        max_chars=20)
    
    if st.sidebar.button(f"💾 Save as '{custom_name}'"):
        if not custom_name or custom_name == 'Default':
            st.sidebar.error("Please enter a valid, non-'Default' name!")
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
                'notify_desktop': st.session_state.notify_desktop,
                'notify_telegram': st.session_state.notify_telegram
            }
            if save_filters(custom_name, current_filters):
                st.session_state.current_preset_name = custom_name
                st.sidebar.success(f"Preset '{custom_name}' saved successfully!")
                st.rerun()
    
    show_technical_predictions = st.sidebar.checkbox("Show Technical Predictions", True)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("Happy Trading!!! -✏️ Vijay S")
    
    # Return all settings as a dictionary
    return {
        'scan_mode': scan_mode,
        'sl_percent': sl_percent,
        'target_percent': target_percent,
        'use_volume': use_volume,
        'use_breakout': use_breakout,
        'use_ema_rsi': use_ema_rsi,
        'use_rs': use_rs,
        'interval': interval,
        'auto_refresh_sec': auto_refresh_sec,
        'max_symbols': max_symbols,
        'vol_zscore_threshold': vol_zscore_threshold,
        'breakout_margin_pct': breakout_margin_pct,
        'atr_period': atr_period,
        'atr_mult': atr_mult,
        'momentum_lookback': momentum_lookback,
        'rs_lookback': rs_lookback,
        'signal_score_threshold': signal_score_threshold,
        'show_technical_predictions': show_technical_predictions,
        'custom_name': custom_name
    }
