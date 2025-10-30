"""
scanning_logic.py - Stock scanning algorithms (Original and Early Detection)

Improvements:
- Centralized parameter parsing and entry/SL/target calculation
- Added safe_float used by validate_scan_data
- Stronger NaN/rolling checks and finite value checks
- Reduced duplication and improved logging of exceptions
- Removed unused imports
"""

import logging
from typing import Dict, List, Tuple, Optional, Union

import numpy as np
import pandas as pd

from functions import (
    compute_indicators, check_candle_patterns, check_consolidation
)

# Set up logging
logger = logging.getLogger(__name__)

# Type aliases
ScanResult = Tuple[int, List[str], Optional[float], Optional[float], Optional[float], Dict]
DataFrame = pd.DataFrame


# Utility helpers
def safe_float(series_or_val, idx: int = -1) -> float:
    """Safely extract a float from a pandas Series (by iloc index) or a numeric value."""
    try:
        if hasattr(series_or_val, "iloc"):
            v = series_or_val.iloc[idx]
        else:
            v = series_or_val
        if pd.isna(v):
            return float("nan")
        return float(v)
    except Exception:
        return float("nan")


def _parse_params(kwargs: Dict, *, logger_ctx: str = "") -> Dict:
    """Centralize parameter extraction and type coercion with defaults."""
    try:
        return {
            "nifty_df": kwargs.get("nifty_df"),
            "use_volume": bool(kwargs.get("use_volume", True)),
            "use_breakout": bool(kwargs.get("use_breakout", True)),
            "use_ema_rsi": bool(kwargs.get("use_ema_rsi", True)),
            "use_rs": bool(kwargs.get("use_rs", True)),
            "vol_zscore_threshold": float(kwargs.get("vol_zscore_threshold", 1.2)),
            "breakout_margin_pct": float(kwargs.get("breakout_margin_pct", 0.2)),
            "momentum_lookback": int(kwargs.get("momentum_lookback", 3)),
            "rs_lookback": int(kwargs.get("rs_lookback", 3)),
            "atr_mult": float(kwargs.get("atr_mult", 0.9)),
            "atr_period": int(kwargs.get("atr_period", 7)),
        }
    except (ValueError, TypeError) as e:
        logger.error("%s: Parameter validation failed: %s", logger_ctx, e)
        raise


def _calc_entry_stop_target(entry_price: float, last_atr: float, atr_mult: float) -> Tuple[float, float]:
    """Return (stop_loss, target_price) computed using ATR if available otherwise defaults."""
    if last_atr and np.isfinite(last_atr) and last_atr > 0:
        stop_loss = entry_price - (atr_mult * last_atr)
        target_price = entry_price + 2 * (entry_price - stop_loss)
    else:
        stop_loss = entry_price * 0.98
        target_price = entry_price * 1.04
    return stop_loss, target_price


def _safe_rolling_prev_max(series: pd.Series, window: int, shift: int = 1) -> Optional[float]:
    """Return the previous rolling max (non-NaN) or None if insufficient data."""
    try:
        if window < 1:
            return None
        rolling = series.rolling(window).max().dropna()
        if len(rolling) >= shift + 1:
            return float(rolling.iloc[-1 - shift])
    except Exception:
        pass
    return None


def scan_stock_original(
    sym: str,
    df_stock: DataFrame,
    **kwargs: Dict[str, Union[bool, float, int, DataFrame]]
) -> ScanResult:
    logger.debug("Starting original scan for %s", sym)

    # Params
    try:
        params = _parse_params(kwargs, logger_ctx=f"{sym} [original]")
    except Exception:
        return 0, ["⚠️ Invalid parameters"], None, None, None, {}

    if df_stock is None or df_stock.empty or len(df_stock) < 25:
        return 0, ["⚠️ Not enough data"], None, None, None, {}

    df = compute_indicators(df_stock, params["atr_period"])
    if df is None or df.empty:
        return 0, ["⚠️ Indicator computation failed"], None, None, None, {}

    try:
        last_close = safe_float(df["Close"], -1)
        prev_close = safe_float(df["Close"], -2)
        last_vol = safe_float(df["Volume"], -1)
        avg_vol = safe_float(df.get("AvgVol20", pd.Series([np.nan])), -1)
        vol_std = safe_float(df.get("VolStd20", pd.Series([np.nan])), -1)
        last_atr = safe_float(df.get("ATR", pd.Series([np.nan])), -1)
    except Exception as e:
        logger.exception("%s: Data extraction failed in original scan: %s", sym, e)
        return 0, ["⚠️ Data extraction failed"], None, None, None, {}

    reasons: List[str] = []
    score = 0

    # EMA + RSI
    if params["use_ema_rsi"]:
        try:
            rsi7_val = safe_float(df.get("RSI7", pd.Series([np.nan])), -1)
            if np.isfinite(rsi7_val) and rsi7_val >= 70:
                reasons.append("💥 RSI (7) > 70")
                score += 2
            ema_ok = np.isfinite(last_close) and np.isfinite(safe_float(df.get("EMA20", pd.Series([np.nan])), -1)) and last_close > safe_float(df["EMA20"], -1)
            if ema_ok:
                reasons.append("📈 Price above EMA20")
                score += 1
        except Exception:
            logger.debug("%s: EMA/RSI check failed", sym)

    # Volume spike
    if params["use_volume"]:
        try:
            if avg_vol > 0 and vol_std > 0:
                z = (last_vol - avg_vol) / vol_std
                if np.isfinite(z) and z >= params["vol_zscore_threshold"]:
                    reasons.append(f"📊 Volume spike (z={z:.2f})")
                    score += 2
        except Exception:
            logger.debug("%s: Volume check failed", sym)

    # Breakout
    if params["use_breakout"]:
        try:
            prev_high = _safe_rolling_prev_max(df["High"], params["momentum_lookback"], shift=1)
            if prev_high is not None:
                if last_close > (prev_high * (1 + params["breakout_margin_pct"] / 100)) and last_close > prev_close:
                    reasons.append(f"🚀 Breakout ({params['breakout_margin_pct']:.2f}%)")
                    score += 2
        except Exception:
            logger.debug("%s: Breakout check failed", sym)

    # RS vs NIFTY
    nifty_df = params["nifty_df"]
    if params["use_rs"] and nifty_df is not None and not nifty_df.empty:
        try:
            stock_pct = df["Close"].pct_change(params["rs_lookback"]).iloc[-1]
            nifty_pct = nifty_df["Close"].pct_change(params["rs_lookback"]).iloc[-1]
            if np.isfinite(stock_pct) and np.isfinite(nifty_pct) and (stock_pct - nifty_pct) > 0:
                reasons.append("💪 Outperforming NIFTY")
                score += 1
        except Exception:
            logger.debug("%s: RS check failed", sym)

    # Candle patterns
    try:
        patterns = check_candle_patterns(df)
        if patterns:
            reasons.extend(patterns)
            score += 1
    except Exception:
        logger.debug("%s: Candle pattern check failed", sym)

    entry_price = last_close
    stop_loss, target_price = _calc_entry_stop_target(entry_price, last_atr, params["atr_mult"])

    if not any([params["use_volume"], params["use_breakout"], params["use_ema_rsi"], params["use_rs"]]):
        reasons.append("🕵️ Filter-free mode active")
        score = max(score, 1)

    signal = {"score": score, "mode": "confirmation"}

    return score, reasons, entry_price, stop_loss, target_price, signal


def validate_scan_data(sym: str, df: DataFrame, required_cols: List[str]) -> Tuple[bool, List[str], Dict[str, float]]:
    """Validate scanning input data and extract key metrics."""
    if not isinstance(df, pd.DataFrame):
        return False, ["⚠️ Invalid input data"], {}

    if df.empty:
        return False, ["⚠️ No data available"], {}

    if len(df) < 25:
        return False, [f"⚠️ Insufficient data points ({len(df)} < 25)"], {}

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return False, [f"⚠️ Missing columns: {', '.join(missing)}"], {}

    metrics: Dict[str, float] = {}
    try:
        for col in required_cols:
            metrics[f"last_{col.lower()}"] = safe_float(df[col], -1)
            if col in ["Close", "High", "Low"]:
                metrics[f"prev_{col.lower()}"] = safe_float(df[col], -2)

        if not np.isfinite(metrics.get("last_close", np.nan)) or metrics.get("last_close", 0.0) <= 0:
            return False, ["⚠️ Invalid price data"], {}

    except Exception as e:
        logger.error("%s: Data extraction failed - %s", sym, e)
        return False, ["⚠️ Data extraction failed"], {}

    return True, [], metrics


def scan_stock_early(sym: str, df_stock: DataFrame,
                    **kwargs: Dict[str, Union[bool, float, int, DataFrame]]) -> ScanResult:
    logger.debug("Starting early detection scan for %s", sym)

    try:
        params = _parse_params(kwargs, logger_ctx=f"{sym} [early]")
    except Exception:
        return 0, ["⚠️ Invalid parameters"], None, None, None, {}

    if df_stock is None or df_stock.empty or len(df_stock) < 25:
        return 0, ["⚠️ Not enough data"], None, None, None, {}

    df = compute_indicators(df_stock, params["atr_period"])
    if df is None or df.empty:
        return 0, ["⚠️ Indicator computation failed"], None, None, None, {}

    try:
        last_close = safe_float(df["Close"], -1)
        prev_close = safe_float(df["Close"], -2)
        last_vol = safe_float(df["Volume"], -1)
        avg_vol = safe_float(df.get("AvgVol20", pd.Series([np.nan])), -1)
        vol_std = safe_float(df.get("VolStd20", pd.Series([np.nan])), -1)
        last_atr = safe_float(df.get("ATR", pd.Series([np.nan])), -1)
    except Exception as e:
        logger.exception("%s: Data extraction failed in early scan: %s", sym, e)
        return 0, ["⚠️ Data extraction failed"], None, None, None, {}

    reasons: List[str] = []
    score = 0

    # 1. Early MACD crossing
    try:
        if len(df) >= 3 and "MACD" in df.columns and "MACD_signal" in df.columns:
            macd_curr = safe_float(df["MACD"], -1)
            macd_sig_curr = safe_float(df["MACD_signal"], -1)
            macd_prev = safe_float(df["MACD"], -2)
            macd_sig_prev = safe_float(df["MACD_signal"], -2)
            if np.isfinite(macd_curr) and np.isfinite(macd_sig_curr) and np.isfinite(macd_prev) and np.isfinite(macd_sig_prev):
                if macd_curr > macd_sig_curr and macd_prev <= macd_sig_prev:
                    if macd_curr < 0:
                        reasons.append("🔄 Early reversal (MACD cross below zero)")
                        score += 3
                    else:
                        reasons.append("📈 MACD momentum confirmed")
                        score += 1
    except Exception:
        logger.debug("%s: MACD check failed", sym)

    # 2. Modified RSI
    if params["use_ema_rsi"]:
        try:
            rsi7_val = safe_float(df.get("RSI7", pd.Series([np.nan])), -1)
            rsi7_prev = safe_float(df.get("RSI7", pd.Series([np.nan])), -2)
            if np.isfinite(rsi7_val):
                if 50 < rsi7_val < 65 and (not np.isfinite(rsi7_prev) or rsi7_prev <= 50):
                    reasons.append("📈 RSI early bullish (50-65)")
                    score += 2
                elif 35 < rsi7_val < 50 and (not np.isfinite(rsi7_prev) or rsi7_prev <= 35):
                    reasons.append("🔄 RSI recovering from oversold")
                    score += 1
                elif rsi7_val >= 70:
                    reasons.append("💥 RSI (7) > 70 (Strong momentum)")
                    score += 1

            ema_ok = np.isfinite(last_close) and np.isfinite(safe_float(df.get("EMA20", pd.Series([np.nan])), -1)) and last_close > safe_float(df["EMA20"], -1)
            if ema_ok:
                reasons.append("📈 Price above EMA20")
                score += 1
        except Exception:
            logger.debug("%s: RSI/EMA check failed", sym)

    # 3. Volume accumulation / spikes
    if params["use_volume"]:
        try:
            vol_trend = safe_float(df.get("Vol_Trend", pd.Series([np.nan])), -1)
            if np.isfinite(vol_trend) and 1.2 < vol_trend < 2.0:
                reasons.append("📊 Volume accumulation phase")
                score += 2
            elif avg_vol > 0 and vol_std > 0:
                z = (last_vol - avg_vol) / vol_std
                if np.isfinite(z) and z >= params["vol_zscore_threshold"]:
                    reasons.append(f"📊 Volume spike (z={z:.2f})")
                    score += 1
        except Exception:
            logger.debug("%s: Volume accumulation check failed", sym)

    # 4. Consolidation
    try:
        is_consolidating, range_pct = check_consolidation(df)
        if is_consolidating:
            reasons.append(f"🔄 Consolidating near highs ({range_pct*100:.1f}% range)")
            score += 2
    except Exception:
        logger.debug("%s: Consolidation check failed", sym)

    # 5. ADX trend formation
    try:
        adx_val = safe_float(df.get("ADX", pd.Series([np.nan])), -1)
        adx_prev = safe_float(df.get("ADX", pd.Series([np.nan])), -2)
        if np.isfinite(adx_val) and 20 < adx_val < 30 and np.isfinite(adx_prev) and adx_val > adx_prev:
            reasons.append("💪 New trend forming (ADX rising)")
            score += 2
    except Exception:
        logger.debug("%s: ADX check failed", sym)

    # 6. Pre-breakout & breakout detection
    if params["use_breakout"]:
        try:
            prev_high = _safe_rolling_prev_max(df["High"], params["momentum_lookback"], shift=1)
            if prev_high is not None and np.isfinite(prev_high) and prev_high > 0:
                margin_to_breakout = (prev_high - last_close) / prev_high if np.isfinite(last_close) else np.nan
                if np.isfinite(margin_to_breakout) and 0 < margin_to_breakout < 0.01:
                    reasons.append("🎯 Approaching breakout level")
                    score += 3
                elif last_close > (prev_high * (1 + params["breakout_margin_pct"] / 100)) and last_close > prev_close:
                    reasons.append(f"🚀 Fresh breakout ({params['breakout_margin_pct']:.2f}%)")
                    score += 2
        except Exception:
            logger.debug("%s: Breakout/pre-breakout check failed", sym)

    # 7. RS filter
    nifty_df = params["nifty_df"]
    if params["use_rs"] and nifty_df is not None and not nifty_df.empty:
        try:
            stock_pct = df["Close"].pct_change(params["rs_lookback"]).iloc[-1]
            nifty_pct = nifty_df["Close"].pct_change(params["rs_lookback"]).iloc[-1]
            if np.isfinite(stock_pct) and np.isfinite(nifty_pct) and (stock_pct - nifty_pct) > 0:
                reasons.append("💪 Outperforming NIFTY")
                score += 1
        except Exception:
            logger.debug("%s: RS check failed (early)", sym)

    # 8. Candle patterns
    try:
        patterns = check_candle_patterns(df)
        if patterns:
            reasons.extend(patterns)
            score += 1
    except Exception:
        logger.debug("%s: Candle pattern check failed (early)", sym)

    # 9. Entry/SL/target
    entry_price = last_close
    stop_loss, target_price = _calc_entry_stop_target(entry_price, last_atr, params["atr_mult"])

    if not any([params["use_volume"], params["use_breakout"], params["use_ema_rsi"], params["use_rs"]]):
        reasons.append("🕵️ Filter-free mode active")
        score = max(score, 1)

    signal = {"score": score, "early_momentum": score >= 4, "mode": "early"}

    return score, reasons, entry_price, stop_loss, target_price, signal
