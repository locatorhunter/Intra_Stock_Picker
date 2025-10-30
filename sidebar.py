"""
sidebar.py - Sidebar UI components
"""
import streamlit as st
import os
import json  # ← ADD THIS
from ai_predictor import StockPredictor
import pandas as pd
import numpy as np
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


def train_ai_models():
    """
    Train AI models using the SAME TIMEFRAME as scanner settings
    Returns: (success: bool, message: str)
    """
    try:
        from functions import get_fo_symbols, get_batch_price_data, extract_symbol_df, compute_indicators
        import yfinance as yf
        
        predictor = StockPredictor()
        
        # Get current scanner settings
        scan_interval = st.session_state.get('scan_interval', '5m')  # Use current scanner interval
        
        # Map intervals to training parameters
        interval_config = {
            '5m': {'period': '5d', 'prediction_candles': 12, 'label_threshold': 0.015},    # 5min: predict next hour (12 candles), 1.5% move
            '15m': {'period': '10d', 'prediction_candles': 8, 'label_threshold': 0.02},   # 15min: predict next 2 hours (8 candles), 2% move
            '30m': {'period': '20d', 'prediction_candles': 6, 'label_threshold': 0.025},  # 30min: predict next 3 hours (6 candles), 2.5% move
            '1h': {'period': '1mo', 'prediction_candles': 5, 'label_threshold': 0.03},    # 1hour: predict next 5 hours, 3% move
            '1d': {'period': '6mo', 'prediction_candles': 5, 'label_threshold': 0.02}     # Daily: predict next 5 days, 2% move
        }
        
        config = interval_config.get(scan_interval, interval_config['5m'])
        
        st.info(f"🔧 Training AI for **{scan_interval}** timeframe...")
        
        symbols = get_fo_symbols(30)
        training_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.info(f"📊 Phase 1/2: Collecting {scan_interval} data...")
        
        for i, symbol in enumerate(symbols):
            status_text.text(f"📥 Downloading {symbol} {scan_interval} data... ({i+1}/{len(symbols)})")
            progress_bar.progress((i + 1) / (len(symbols) * 2))
            
            try:
                # Download data for the CURRENT SCANNER INTERVAL
                ticker = yf.Ticker(f"{symbol}.NS")
                df = ticker.history(period=config['period'], interval=scan_interval)
                
                if df is None or len(df) < 100:
                    continue
                
                # Compute indicators
                df = df.rename(columns=str.title)
                df = compute_indicators(df, atr_period=14)
                
                if df.empty or len(df) < 100:
                    continue
                
                # Create training samples
                train_end = int(len(df) * 0.8)
                
                for j in range(60, train_end - config['prediction_candles']):
                    try:
                        # Extract features from candle j
                        window_df = df.iloc[:j+1].copy()
                        features = predictor.prepare_features(window_df)
                        
                        if features is None:
                            continue
                        
                        # Label: Did price move up by threshold% in next N candles?
                        current_price = df['Close'].iloc[j]
                        future_prices = df['Close'].iloc[j+1:j+1+config['prediction_candles']]
                        max_future_price = future_prices.max()
                        
                        # Positive label if price went up by threshold within prediction window
                        label = 1 if max_future_price > current_price * (1 + config['label_threshold']) else 0
                        
                        training_data.append((features, label))
                    
                    except Exception as e:
                        continue
            
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        status_text.text(f"✅ Collected {len(training_data)} training samples ({scan_interval} data)")
        progress_bar.progress(0.5)
        
        if len(training_data) < 100:
            progress_bar.empty()
            status_text.empty()
            return False, f"Insufficient training data (got {len(training_data)} samples, need 100+)"
        
        # Phase 2: Train models
        status_text.info(f"🤖 Phase 2/2: Training AI for {scan_interval} trading...")
        progress_bar.progress(0.75)
        
        success, msg = predictor.train_models(training_data)
        
        # Save training config
        if success:
            import json
            import os
            if not os.path.exists("ai_models"):
                os.makedirs("ai_models")
            
            with open("ai_models/training_config.json", 'w') as f:
                json.dump({
                    'interval': scan_interval,
                    'prediction_candles': config['prediction_candles'],
                    'threshold': config['label_threshold'],
                    'trained_date': datetime.now(IST).isoformat()
                }, f)
        
        progress_bar.progress(1.0)
        progress_bar.empty()
        status_text.empty()
        
        return success, f"{msg} (Trained for {scan_interval} timeframe)"
    
    except Exception as e:
        return False, f"Training error: {str(e)}"



def render_ai_training_section():
    """AI Model Training Interface"""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🤖 AI Model Training")
    
    # Check training config
    models_exist = os.path.exists("ai_models/rf_model.pkl")
    
    if models_exist:
        st.sidebar.success("✅ Models Trained!")
        
        # Show training config
        try:
            if os.path.exists("ai_models/training_config.json"):
                with open("ai_models/training_config.json", 'r') as f:
                    config = json.load(f)
                
                trained_interval = config.get('interval', 'Unknown')
                current_interval = st.session_state.get('scan_interval', '5m')
                
                # Warning if mismatch
                if trained_interval != current_interval:
                    st.sidebar.warning(f"⚠️ Trained for **{trained_interval}** but scanning with **{current_interval}**")
                    st.sidebar.info("💡 Retrain for current timeframe for best results")
                else:
                    st.sidebar.info(f"📊 Trained for: **{trained_interval}** timeframe ✅")
        except:
            pass
        
        with st.sidebar.expander("⚙️ Model Management", expanded=False):
            st.markdown("""
<div style="background:rgba(59,130,246,0.1);padding:10px;border-radius:6px;font-size:11px;margin-bottom:10px;">
<strong>ℹ️ When to retrain:</strong><br>
• Weekly (adapt to market changes)<br>
• After major market events<br>
• If accuracy drops below 55%
</div>
""", unsafe_allow_html=True)
            
            col_retrain, col_clear = st.columns(2)
            
            with col_retrain:
                if st.button("🔄 Retrain", use_container_width=True, help="Retrain with latest data", key="sidebar_retrain"):
                    with st.spinner("Training..."):
                        success, msg = train_ai_models()
                        if success:
                            st.success("✅ Retrained!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
            
            with col_clear:
                if st.button("🗑️ Clear", use_container_width=True, help="Delete models", key="sidebar_clear"):
                    try:
                        import shutil
                        if os.path.exists("ai_models"):
                            shutil.rmtree("ai_models")
                        st.success("✅ Cleared")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
    
    else:
        st.sidebar.warning("⚠️ Not Trained")

        current_interval = st.session_state.get('scan_interval', '5m')
        
        st.sidebar.markdown(f"""
<div style="background:rgba(245,158,11,0.1);padding:12px;border-radius:8px;margin:10px 0;font-size:11px;">
<strong>📋 Will train for:</strong><br>
• Timeframe: <strong>{current_interval}</strong><br>
• Same as your scanner settings<br>
• Prediction horizon: Few candles ahead<br><br>
<strong>⏱️ Time:</strong> 3-5 minutes
</div>
""", unsafe_allow_html=True)
        
        if st.sidebar.button("🚀 Train AI Models", use_container_width=True, type="primary", key="sidebar_train"):
            success, msg = train_ai_models()
            
            if success:
                st.success("✅ Training complete!")
                st.balloons()
                st.info("🔄 Refresh or go to AI Predictions tab!")
                st.rerun()
            else:
                st.error(f"❌ Training failed: {msg}")
                st.info("💡 Try again or check your internet connection")


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
    
    # Store interval in session state
    st.session_state['scan_interval'] = interval
    # AI Training Section
    render_ai_training_section()
    
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
        'custom_name': custom_name,
        'interval': interval
    }
