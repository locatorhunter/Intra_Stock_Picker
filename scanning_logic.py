"""
scanning_logic.py - Stock scanning algorithms (Original and Early Detection)
"""

import streamlit as st
import numpy as np
import paper
from functions import (
    compute_indicators, check_candle_patterns, check_consolidation
)


def scan_stock_original(sym, df_stock, **kwargs):
    """Original 🦖 scanning logic - waits for confirmation"""
    nifty_df = kwargs.get('nifty_df')
    use_volume = kwargs.get('use_volume', True)
    use_breakout = kwargs.get('use_breakout', True)
    use_ema_rsi = kwargs.get('use_ema_rsi', True)
    use_rs = kwargs.get('use_rs', True)
    vol_zscore_threshold = kwargs.get('vol_zscore_threshold', 1.2)
    breakout_margin_pct = kwargs.get('breakout_margin_pct', 0.2)
    momentum_lookback = kwargs.get('momentum_lookback', 3)
    rs_lookback = kwargs.get('rs_lookback', 3)
    atr_mult = kwargs.get('atr_mult', 0.9)
    atr_period = kwargs.get('atr_period', 7)
    
    if df_stock is None or df_stock.empty or len(df_stock) < 25:
        return 0, ["⚠️ Not enough data"], None, None, None, {}

    df = compute_indicators(df_stock, atr_period)
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


def scan_stock_early(sym, df_stock, **kwargs):
    """Enhanced scanning logic - catches stocks early"""
    nifty_df = kwargs.get('nifty_df')
    use_volume = kwargs.get('use_volume', True)
    use_breakout = kwargs.get('use_breakout', True)
    use_ema_rsi = kwargs.get('use_ema_rsi', True)
    use_rs = kwargs.get('use_rs', True)
    vol_zscore_threshold = kwargs.get('vol_zscore_threshold', 1.2)
    breakout_margin_pct = kwargs.get('breakout_margin_pct', 0.2)
    momentum_lookback = kwargs.get('momentum_lookback', 3)
    rs_lookback = kwargs.get('rs_lookback', 3)
    atr_mult = kwargs.get('atr_mult', 0.9)
    atr_period = kwargs.get('atr_period', 7)
    
    if df_stock is None or df_stock.empty or len(df_stock) < 25:
        return 0, ["⚠️ Not enough data"], None, None, None, {}

    df = compute_indicators(df_stock, atr_period)
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
# ---------------------------