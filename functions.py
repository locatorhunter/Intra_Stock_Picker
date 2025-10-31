"""
functions.py - Core utility functions and business logic
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
import logging
from typing import List, Dict, Tuple, Optional, Union
from datetime import datetime, date
import pytz
import json
import os
import paper

# Try to import plyer for desktop notifications
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

# Set up logging before any other operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import optional dependencies with fallbacks
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
    logger.info("pandas_ta loaded successfully")
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.warning("pandas_ta not available - attempting to use basic calculations")

# Make talib optional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Make talib optional - use pandas-ta instead on cloud
try:
    import talib
    TALIB_AVAILABLE = True
    print("[✓] TA-Lib loaded successfully")
except ImportError:
    TALIB_AVAILABLE = False
    print("[INFO] TA-Lib not available - using pandas-ta for indicators")


# --- GLOBAL DEFINITIONS ---
IST = pytz.timezone("Asia/Kolkata")
FILTER_DIR = "filter_presets"

# -------------------------
# Enhanced Notification Functions
# -------------------------

def safe_notify(title: str, msg: str, timeout: int = 8, icon: Optional[str] = None) -> bool:
    """
    Send desktop notification with enhanced error handling and logging
    
    Args:
        title: Notification title
        msg: Notification message
        timeout: How long notification should remain visible (seconds)
        icon: Path to .ico file for notification icon
    
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
def safe_notify(title: str, msg: str, timeout: int = 8, icon: Optional[str] = None) -> bool:
    """
    Send desktop notification with enhanced error handling and logging
    Args:
        title: Notification title
        msg: Notification message
        timeout: How long notification should remain visible (seconds)
        icon: Path to .ico file for notification icon
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    notify_desktop = st.session_state.get("notify_desktop", True)
    if not notify_desktop:
        logger.info("Desktop notifications are disabled")
        return False
    try:
        # Validate inputs
        if not isinstance(title, str) or not isinstance(msg, str):
            raise ValueError("Title and message must be strings")
        # Truncate message if too long (Windows has ~256 char limit)
        max_len = 250
        if len(msg) > max_len:
            msg = msg[:max_len-3] + "..."
            logger.debug(f"Message truncated to {max_len} characters")
        if 'PLYER_AVAILABLE' in globals() and PLYER_AVAILABLE:
            notification.notify(
                title=title,
                message=msg,
                timeout=max(1, min(timeout, 30)),  # Ensure timeout is between 1-30
                app_icon=icon
            )
            logger.info(f"Desktop notification sent: {title}")
            return True
        else:
            # Fallback: use Streamlit notification
            try:
                st.toast(f"{title}: {msg}")
            except Exception:
                st.info(f"{title}: {msg}")
            logger.info(f"Streamlit notification sent: {title}")
            return True
    except ValueError as ve:
        logger.error(f"Validation error in safe_notify: {ve}")
        return False
    except Exception as e:
        logger.error(f"Notification error: {str(e)}", exc_info=True)
        return False


def safe_telegram_send(text, parse_mode="HTML", disable_preview=True):
    """Enhanced Telegram notification with better formatting"""
    notify_telegram = st.session_state.get("notify_telegram", False)
    BOT_TOKEN = st.session_state.get("BOT_TOKEN", "")
    CHAT_ID = st.session_state.get("CHAT_ID", "")
    
    if not notify_telegram:
        return False, "Telegram notifications disabled"
    
    if not BOT_TOKEN or not CHAT_ID:
        return False, "Missing Telegram credentials"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    try:
        params = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview
        }
        
        resp = requests.post(url, json=params, timeout=10)
        
        if resp.status_code == 200:
            print(f"[✓] Telegram sent successfully")
            return True, "Message sent"
        else:
            error_data = resp.json()
            error_msg = error_data.get("description", f"HTTP {resp.status_code}")
            print(f"[✗] Telegram error: {error_msg}")
            return False, error_msg
            
    except requests.Timeout:
        return False, "Request timeout"
    except requests.ConnectionError:
        return False, "Connection error"
    except Exception as e:
        return False, str(e)


def notify_stock(symbol, last_price, entry=None, stop_loss=None, target=None, score=None, reasons=None):
    """Enhanced stock notification with rich formatting and better structure"""
    timestamp = datetime.now(IST).strftime('%d %b %Y, %I:%M %p')
    
    # Calculate R:R ratio
    risk_reward = "N/A"
    if entry and stop_loss and target:
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)
        if risk > 0:
            risk_reward = f"{(reward/risk):.1f}:1"
    
    # ========== TELEGRAM MESSAGE (Rich HTML) ==========
    telegram_msg = f"""
🚀 <b>TRADE SIGNAL: {symbol}</b>

📊 <b>Price Details</b>
💵 Current: ₹{last_price:.2f}
"""
    
    if entry:
        telegram_msg += f"🟢 Entry: ₹{entry:.2f}\n"
    if stop_loss:
        telegram_msg += f"🛑 Stop Loss: ₹{stop_loss:.2f}\n"
    if target:
        telegram_msg += f"🎯 Target: ₹{target:.2f}\n"
    
    # Add R:R and Score
    if risk_reward != "N/A":
        telegram_msg += f"\n⚖️ <b>Risk:Reward:</b> {risk_reward}"
    if score is not None:
        telegram_msg += f"\n🎯 <b>Signal Score:</b> {score}"
    
    # Add reasons/criteria
    if reasons:
        telegram_msg += "\n\n📋 <b>Key Signals:</b>"
        
        if isinstance(reasons, list):
            # Show max 6 reasons to keep it compact
            display_reasons = reasons[:6]
            for idx, reason in enumerate(display_reasons, 1):
                # Clean up reason text
                clean_reason = str(reason).replace("💥", "").replace("📈", "").replace("📊", "").strip()
                telegram_msg += f"\n{idx}. {clean_reason}"
            
            if len(reasons) > 6:
                telegram_msg += f"\n<i>...and {len(reasons) - 6} more signals</i>"
        else:
            telegram_msg += f"\n• {reasons}"
    
    # Add timestamp
    telegram_msg += f"\n\n🕐 <i>{timestamp}</i>"
    
    # Add quick action hint
    telegram_msg += "\n\n<i>💡 Check your app for detailed analysis</i>"
    
    # ========== DESKTOP MESSAGE (Plain Text) ==========
    desktop_msg = f"""
{symbol} - Signal Alert

Price: ₹{last_price:.2f}
"""
    
    if entry:
        desktop_msg += f"Entry: ₹{entry:.2f}\n"
    if stop_loss:
        desktop_msg += f"Stop Loss: ₹{stop_loss:.2f}\n"
    if target:
        desktop_msg += f"Target: ₹{target:.2f}\n"
    
    if risk_reward != "N/A":
        desktop_msg += f"R:R: {risk_reward}\n"
    
    if score is not None:
        desktop_msg += f"Score: {score}\n"
    
    desktop_msg += f"\nTime: {timestamp}"
    
    # ========== SEND NOTIFICATIONS ==========
    # Desktop
    safe_notify(f"📈 {symbol} Signal", desktop_msg, timeout=10)
    
    # Telegram
    safe_telegram_send(telegram_msg, parse_mode="HTML")
    
    print(f"[✓] Notifications sent for {symbol}")


def notify_watchlist_alert(symbol, alert_type, current_price, trigger_price):
    """Enhanced watchlist alert notification"""
    timestamp = datetime.now(IST).strftime('%d %b %Y, %I:%M %p')
    
    # Determine emoji and message
    if alert_type == "TARGET":
        emoji = "🎯"
        title = "TARGET HIT"
        color_code = "🟢"
    else:  # STOP LOSS
        emoji = "🛑"
        title = "STOP LOSS HIT"
        color_code = "🔴"
    
    # ========== TELEGRAM MESSAGE ==========
    telegram_msg = f"""
{emoji} <b>{title}: {symbol}</b>

{color_code} <b>Alert Details</b>
💰 Current Price: ₹{current_price:.2f}
📍 Trigger Level: ₹{trigger_price:.2f}
🕐 Time: {timestamp}

<i>💡 Position has been removed from watchlist</i>
"""
    
    # ========== DESKTOP MESSAGE ==========
    desktop_msg = f"""
{title}!

{symbol}
Current: ₹{current_price:.2f}
Trigger: ₹{trigger_price:.2f}

Removed from watchlist
"""
    
    # Send notifications
    safe_notify(f"{emoji} {symbol} - {title}", desktop_msg, timeout=15)
    safe_telegram_send(telegram_msg, parse_mode="HTML")
    
    print(f"[✓] Watchlist alert sent for {symbol} - {alert_type}")


def notify_trade_execution(symbol, action, quantity, price, trade_type="paper"):
    """Notification when trade is executed"""
    timestamp = datetime.now(IST).strftime('%d %b %Y, %I:%M %p')
    
    action_emoji = "🟢" if action == "BUY" else "🔴"
    trade_emoji = "📝" if trade_type == "paper" else "💰"
    
    # ========== TELEGRAM MESSAGE ==========
    telegram_msg = f"""
{trade_emoji} <b>TRADE EXECUTED</b>

{action_emoji} <b>{action}</b> {quantity} x <b>{symbol}</b>
💵 Price: ₹{price:.2f}
💼 Total: ₹{(quantity * price):.2f}
📊 Type: {trade_type.upper()} Trading
🕐 {timestamp}
"""
    
    # ========== DESKTOP MESSAGE ==========
    desktop_msg = f"""
Trade Executed

{action} {quantity} x {symbol}
Price: ₹{price:.2f}
Total: ₹{(quantity * price):.2f}

{timestamp}
"""
    
    # Send only if enabled
    if st.session_state.get("notify_trades", True):
        safe_notify(f"{action_emoji} {action} {symbol}", desktop_msg)
        safe_telegram_send(telegram_msg, parse_mode="HTML")
        
        print(f"[✓] Trade execution notification sent for {symbol}")


def notify_trade_closed(symbol, action, entry, exit_price, pl, pl_pct):
    """Notification when trade is closed"""
    timestamp = datetime.now(IST).strftime('%d %b %Y, %I:%M %p')
    
    # Determine if profit or loss
    is_profit = pl > 0
    result_emoji = "🎉" if is_profit else "😞"
    result_text = "PROFIT" if is_profit else "LOSS"
    color = "🟢" if is_profit else "🔴"
    
    # ========== TELEGRAM MESSAGE ==========
    telegram_msg = f"""
{result_emoji} <b>TRADE CLOSED: {symbol}</b>

{color} <b>{result_text}</b>
📊 Type: {action}
💵 Entry: ₹{entry:.2f}
💰 Exit: ₹{exit_price:.2f}

📈 <b>P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)</b>

🕐 {timestamp}
"""
    
    # ========== DESKTOP MESSAGE ==========
    desktop_msg = f"""
Trade Closed: {symbol}

{result_text}
P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)

Entry: ₹{entry:.2f}
Exit: ₹{exit_price:.2f}

{timestamp}
"""
    
    # Send notifications
    safe_notify(f"{result_emoji} {symbol} - {result_text}", desktop_msg, timeout=15)
    safe_telegram_send(telegram_msg, parse_mode="HTML")
    
    print(f"[✓] Trade closure notification sent for {symbol}")


# -------------------------
# Enhanced Watchlist Functions with Notifications
# -------------------------

def check_watchlist_hits(df_batch):
    """Enhanced watchlist monitoring with better notifications"""
    if not st.session_state.get("watchlist"):
        return
    
    keys_to_remove = []
    
    for sym, info in st.session_state.watchlist.items():
        target = info.get("target")
        sl = info.get("sl")
        
        # Extract symbol data
        df_sym = extract_symbol_df(df_batch, sym)
        if df_sym is None or df_sym.empty:
            continue
        
        try:
            latest_price = float(df_sym["Close"].iloc[-1])
        except:
            continue
        
        # Check target hit
        if target and latest_price >= target:
            notify_watchlist_alert(sym, "TARGET", latest_price, target)
            keys_to_remove.append(sym)
            info["status"] = "Closed - Target Hit"
            
        # Check stop loss hit
        elif sl and latest_price <= sl:
            notify_watchlist_alert(sym, "STOP_LOSS", latest_price, sl)
            keys_to_remove.append(sym)
            info["status"] = "Closed - Stop Loss Hit"
    
    # Remove closed positions
    for key in keys_to_remove:
        del st.session_state.watchlist[key]
    
    if keys_to_remove:
        print(f"[✓] Watchlist: {len(keys_to_remove)} position(s) closed")


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

def compute_indicators(df: pd.DataFrame, atr_period: int = 7) -> pd.DataFrame:
    """
    Compute technical indicators on price data with fallback options
    
    Args:
        df: DataFrame with OHLCV data
        atr_period: Period for ATR calculation
    
    Returns:
        DataFrame with additional technical indicator columns
    """
    try:
        df = df.rename(columns=str.title).copy()
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in df.columns for col in required_cols):
            logger.error("Missing required columns in dataframe")
            return df
        
        # Convert to float to ensure compatibility
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # EMA calculation (pandas native)
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        
        # ATR calculation
        if TALIB_AVAILABLE:
            try:
                df["ATR"] = talib.ATR(df["High"].values, df["Low"].values, 
                                     df["Close"].values, timeperiod=atr_period)
            except Exception as e:
                logger.warning(f"TALib ATR calculation failed: {e}")
                if PANDAS_TA_AVAILABLE:
                    df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], length=atr_period)
                else:
                    # Basic ATR calculation if neither library is available
                    tr1 = df["High"] - df["Low"]
                    tr2 = abs(df["High"] - df["Close"].shift(1))
                    tr3 = abs(df["Low"] - df["Close"].shift(1))
                    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                    df["ATR"] = tr.rolling(window=atr_period).mean()
        else:
            if PANDAS_TA_AVAILABLE:
                df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], length=atr_period)
            else:
                # Basic ATR calculation
                tr1 = df["High"] - df["Low"]
                tr2 = abs(df["High"] - df["Close"].shift(1))
                tr3 = abs(df["Low"] - df["Close"].shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                df["ATR"] = tr.rolling(window=atr_period).mean()
        
        # RSI calculations
        if TALIB_AVAILABLE:
            try:
                df["RSI7"] = talib.RSI(df["Close"].values, timeperiod=7)
                df["RSI10"] = talib.RSI(df["Close"].values, timeperiod=10)
            except Exception as e:
                logger.warning(f"TALib RSI calculation failed: {e}")
                if PANDAS_TA_AVAILABLE:
                    df["RSI7"] = ta.rsi(df["Close"], length=7)
                    df["RSI10"] = ta.rsi(df["Close"], length=10)
                else:
                    # Basic RSI calculation if neither library is available
                    def calculate_rsi(series, periods):
                        delta = series.diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
                        rs = gain / loss
                        return 100 - (100 / (1 + rs))
                    
                    df["RSI7"] = calculate_rsi(df["Close"], 7)
                    df["RSI10"] = calculate_rsi(df["Close"], 10)
        else:
            if PANDAS_TA_AVAILABLE:
                df["RSI7"] = ta.rsi(df["Close"], length=7)
                df["RSI10"] = ta.rsi(df["Close"], length=10)
            else:
                # Basic RSI calculation
                def calculate_rsi(series, periods):
                    delta = series.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
                    rs = gain / loss
                    return 100 - (100 / (1 + rs))
                
                df["RSI7"] = calculate_rsi(df["Close"], 7)
                df["RSI10"] = calculate_rsi(df["Close"], 10)
            
        # Volume indicators
        df["AvgVol20"] = df["Volume"].rolling(20).mean()
        df["VolStd20"] = df["Volume"].rolling(20).std()
        df["Vol_Trend"] = df["Volume"].rolling(5).mean() / df["Volume"].rolling(20).mean()
        
    except Exception as e:
        logger.error(f"Error computing basic indicators: {str(e)}", exc_info=True)
        return df
    
    # MACD calculation
    try:
        if TALIB_AVAILABLE:
            try:
                macd, signal, hist = talib.MACD(df["Close"].astype(float).values, 
                                               fastperiod=12, slowperiod=26, signalperiod=9)
                df["MACD"] = macd
                df["MACD_signal"] = signal
                df["MACD_hist"] = hist
            except Exception as e:
                logger.warning(f"TALib MACD calculation failed: {e}")
                macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
                df["MACD"] = macd["MACD_12_26_9"]
                df["MACD_signal"] = macd["MACDs_12_26_9"]
                df["MACD_hist"] = macd["MACDh_12_26_9"]
        else:
            macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
            df["MACD"] = macd["MACD_12_26_9"]
            df["MACD_signal"] = macd["MACDs_12_26_9"]
            df["MACD_hist"] = macd["MACDh_12_26_9"]
    except Exception as e:
        logger.error(f"Error calculating MACD: {str(e)}")
        df["MACD"] = np.nan
        df["MACD_signal"] = np.nan
        df["MACD_hist"] = np.nan
    
    # ADX calculation
    try:
        if TALIB_AVAILABLE:
            try:
                df["ADX"] = talib.ADX(df["High"].astype(float).values, 
                                    df["Low"].astype(float).values, 
                                    df["Close"].astype(float).values, 
                                    timeperiod=14)
            except Exception as e:
                logger.warning(f"TALib ADX calculation failed: {e}")
                df["ADX"] = ta.adx(df["High"], df["Low"], df["Close"], length=14)["ADX_14"]
        else:
            df["ADX"] = ta.adx(df["High"], df["Low"], df["Close"], length=14)["ADX_14"]
    except Exception as e:
        logger.error(f"Error calculating ADX: {str(e)}")
        df["ADX"] = np.nan
    
    return df


def check_candle_patterns(df: pd.DataFrame) -> List[str]:
    """
    Check for bullish candlestick patterns with fallback to manual calculation
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        List[str]: List of detected candlestick patterns
    """
    patterns = []
    
    try:
        # Ensure data types
        ohlc = {col: df[col].astype(float) for col in ["Open", "High", "Low", "Close"]}
        
        if TALIB_AVAILABLE:
            try:
                # TALib pattern detection
                eng = talib.CDLENGULFING(ohlc["Open"], ohlc["High"],
                                       ohlc["Low"], ohlc["Close"])
                morning = talib.CDLMORNINGSTAR(ohlc["Open"], ohlc["High"],
                                             ohlc["Low"], ohlc["Close"])
                
                last_eng = int(eng[-1]) if len(eng) else 0
                last_morning = int(morning[-1]) if len(morning) else 0
                
                if last_eng > 0:
                    patterns.append("🟢 Bullish Engulfing")
                if last_morning > 0:
                    patterns.append("🟢 Morning Star")
                    
            except Exception as e:
                logger.warning(f"TALib pattern detection failed: {e}")
                # Fall back to manual pattern detection
                patterns.extend(manual_pattern_detection(df))
        else:
            # Manual pattern detection when TALib is not available
            patterns.extend(manual_pattern_detection(df))
            
    except Exception as e:
        logger.error(f"Error in candlestick pattern detection: {str(e)}", exc_info=True)
    
    return patterns

def manual_pattern_detection(df: pd.DataFrame) -> List[str]:
    """
    Manual implementation of candlestick pattern detection
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        List[str]: List of detected patterns
    """
    patterns = []
    try:
        # Get last 3 candles
        last3 = df.tail(3)
        
        # Bullish Engulfing Detection
        if len(last3) >= 2:
            prev_candle = last3.iloc[-2]
            curr_candle = last3.iloc[-1]
            
            prev_bearish = prev_candle["Close"] < prev_candle["Open"]
            curr_bullish = curr_candle["Close"] > curr_candle["Open"]
            engulfing = (curr_candle["Open"] <= prev_candle["Close"] and 
                        curr_candle["Close"] >= prev_candle["Open"])
            
            if prev_bearish and curr_bullish and engulfing:
                patterns.append("🟢 Bullish Engulfing")
        
        # Add more manual pattern detection logic here
        
    except Exception as e:
        logger.error(f"Error in manual pattern detection: {str(e)}")
    
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
        target = info.get
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
