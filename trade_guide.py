"""
trade_guide.py - Trading Strategy Guide and Education
"""

import streamlit as st
import pandas as pd

def render_trade_guide():
    """Render comprehensive trading guide with strategies and scoring system"""
    
    st.title("📚 Trading Strategy Guide")
    
    # ========== OVERVIEW SECTION ==========
    overview_html = """
<div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
padding:20px;border-radius:12px;margin-bottom:20px;color:white;">
<h2 style="margin:0 0 10px 0;">🎯 Welcome to Your Trading Command Center</h2>
<p style="margin:0;font-size:14px;line-height:1.6;">
This guide will help you understand our scoring system, technical indicators, 
and optimal configurations for different trading styles. Master these concepts 
to make informed trading decisions!
</p>
</div>
"""
    st.markdown(overview_html, unsafe_allow_html=True)
    
    # ========== TABS FOR DIFFERENT SECTIONS ==========
    guide_tab1, guide_tab2, guide_tab3, guide_tab4 = st.tabs([
        "📊 Scoring System",
        "📈 Indicators Guide", 
        "⚙️ Trading Presets",
        "💡 Best Practices"
    ])
    
    # ========== TAB 1: SCORING SYSTEM ==========
    with guide_tab1:
        st.markdown("## 📊 How Our Scoring System Works")
        
        scoring_intro = """
<div style="background:rgba(59,130,246,0.1);padding:16px;border-radius:8px;margin-bottom:20px;border-left:4px solid #3b82f6;">
<p style="margin:0;color:#93c5fd;font-size:14px;">
<strong>Score Range:</strong> 0-15 points<br>
<strong>Qualification:</strong> Stocks scoring above your threshold are flagged as opportunities<br>
<strong>Components:</strong> Each technical indicator contributes to the total score
</p>
</div>
"""
        st.markdown(scoring_intro, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Score Breakdown")
        
        # Score breakdown table
        score_data = {
            "Indicator": [
                "📊 Volume Surge",
                "📈 Price Breakout",
                "🔄 MACD Crossover",
                "💪 RSI Momentum",
                "📉 EMA Alignment",
                "💨 ADX Trend Strength",
                "🎯 Consolidation Pattern",
                "⚡ Relative Strength"
            ],
            "Max Points": [3, 3, 2, 2, 2, 1, 1, 1],
            "What It Measures": [
                "Unusual volume spike (accumulation/distribution)",
                "Price breaking above resistance levels",
                "Momentum shift from bearish to bullish",
                "Overbought/oversold conditions",
                "Price position relative to moving averages",
                "Strength of current trend",
                "Tight range before potential breakout",
                "Stock performance vs market index"
            ],
            "Good = High": [
                "✅ High volume = Strong interest",
                "✅ Breakout = New momentum",
                "✅ Bullish cross = Buy signal",
                "⚖️ 50-70 = Bullish (70+ overbought)",
                "✅ Above EMAs = Uptrend",
                "✅ ADX > 25 = Strong trend",
                "✅ Tight range = Energy building",
                "✅ Outperforming market"
            ]
        }
        
        df_score = pd.DataFrame(score_data)
        st.dataframe(df_score, use_container_width=True, hide_index=True)
        
        # Scoring examples
        st.markdown("### 💡 Example Scenarios")
        
        col_ex1, col_ex2, col_ex3 = st.columns(3)
        
        with col_ex1:
            example1 = """
<div style="background:rgba(16,185,129,0.1);padding:12px;border-radius:8px;border:2px solid #10b981;">
<h4 style="color:#10b981;margin-top:0;">🟢 Strong Signal (Score: 11)</h4>
<ul style="font-size:12px;color:#6ee7b7;margin:0;padding-left:20px;">
<li>Volume surge: +3</li>
<li>Breakout: +3</li>
<li>MACD bullish: +2</li>
<li>RSI 65: +2</li>
<li>Above EMA: +1</li>
</ul>
<p style="color:#10b981;font-size:11px;margin:8px 0 0 0;">
<strong>Action:</strong> High probability trade
</p>
</div>
"""
            st.markdown(example1, unsafe_allow_html=True)
        
        with col_ex2:
            example2 = """
<div style="background:rgba(245,158,11,0.1);padding:12px;border-radius:8px;border:2px solid #f59e0b;">
<h4 style="color:#f59e0b;margin-top:0;">🟡 Moderate Signal (Score: 6)</h4>
<ul style="font-size:12px;color:#fbbf24;margin:0;padding-left:20px;">
<li>Volume normal: +1</li>
<li>Near breakout: +2</li>
<li>RSI bullish: +2</li>
<li>Above EMA: +1</li>
</ul>
<p style="color:#f59e0b;font-size:11px;margin:8px 0 0 0;">
<strong>Action:</strong> Wait for confirmation
</p>
</div>
"""
            st.markdown(example2, unsafe_allow_html=True)
        
        with col_ex3:
            example3 = """
<div style="background:rgba(239,68,68,0.1);padding:12px;border-radius:8px;border:2px solid #ef4444;">
<h4 style="color:#ef4444;margin-top:0;">🔴 Weak Signal (Score: 3)</h4>
<ul style="font-size:12px;color:#fca5a5;margin:0;padding-left:20px;">
<li>Low volume: +0</li>
<li>No breakout: +0</li>
<li>RSI neutral: +1</li>
<li>Above EMA: +1</li>
<li>Weak trend: +1</li>
</ul>
<p style="color:#ef4444;font-size:11px;margin:8px 0 0 0;">
<strong>Action:</strong> Avoid - insufficient signals
</p>
</div>
"""
            st.markdown(example3, unsafe_allow_html=True)
    
    # ========== TAB 2: INDICATORS GUIDE ==========
    with guide_tab2:
        st.markdown("## 📈 Technical Indicators Explained")
        
        # RSI Section
        with st.expander("📊 RSI (Relative Strength Index)", expanded=True):
            rsi_guide = """
<div style="padding:16px;">
<h4 style="color:#3b82f6;">What is RSI?</h4>
<p style="font-size:13px;line-height:1.6;">
RSI measures the speed and magnitude of price changes on a scale of 0-100. 
It helps identify overbought and oversold conditions.
</p>

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0;">
<div style="background:rgba(239,68,68,0.1);padding:10px;border-radius:6px;border-left:3px solid #ef4444;">
<strong style="color:#ef4444;">RSI > 70</strong>
<p style="font-size:11px;margin:4px 0 0 0;">Overbought - Potential reversal</p>
</div>
<div style="background:rgba(16,185,129,0.1);padding:10px;border-radius:6px;border-left:3px solid #10b981;">
<strong style="color:#10b981;">RSI 50-70</strong>
<p style="font-size:11px;margin:4px 0 0 0;">Bullish - Strong momentum</p>
</div>
<div style="background:rgba(59,130,246,0.1);padding:10px;border-radius:6px;border-left:3px solid #3b82f6;">
<strong style="color:#3b82f6;">RSI < 30</strong>
<p style="font-size:11px;margin:4px 0 0 0;">Oversold - Potential buy</p>
</div>
</div>

<h4 style="color:#3b82f6;">How to Use:</h4>
<ul style="font-size:13px;line-height:1.8;">
<li>✅ <strong>BUY:</strong> RSI crosses above 30 (oversold recovery)</li>
<li>✅ <strong>HOLD:</strong> RSI between 50-70 (bullish momentum)</li>
<li>⚠️ <strong>CAUTION:</strong> RSI above 70 (overbought - take profits)</li>
<li>❌ <strong>AVOID:</strong> RSI below 30 in downtrend (falling knife)</li>
</ul>
</div>
"""
            st.markdown(rsi_guide, unsafe_allow_html=True)
        
        # EMA Section
        with st.expander("📉 EMA (Exponential Moving Average)"):
            ema_guide = """
<div style="padding:16px;">
<h4 style="color:#10b981;">What is EMA?</h4>
<p style="font-size:13px;line-height:1.6;">
EMA is a moving average that gives more weight to recent prices. We use EMA20 and EMA50 
to identify trends and support/resistance levels.
</p>

<h4 style="color:#10b981;">Key Signals:</h4>
<div style="background:rgba(16,185,129,0.1);padding:12px;border-radius:8px;margin:12px 0;">
<ul style="font-size:13px;line-height:1.8;margin:0;">
<li>✅ <strong>Price > EMA20 > EMA50:</strong> Strong uptrend</li>
<li>✅ <strong>Price > EMA20:</strong> Short-term bullish</li>
<li>⚖️ <strong>Price between EMAs:</strong> Consolidation</li>
<li>❌ <strong>Price < EMA20 < EMA50:</strong> Downtrend</li>
<li>🔄 <strong>EMA20 crosses EMA50:</strong> Trend change signal</li>
</ul>
</div>

<h4 style="color:#10b981;">Trading Strategy:</h4>
<p style="font-size:13px;">
<strong>BUY:</strong> When price pulls back to EMA20 in uptrend (support bounce)<br>
<strong>SELL:</strong> When price breaks below EMA20 decisively
</p>
</div>
"""
            st.markdown(ema_guide, unsafe_allow_html=True)
        
        # MACD Section
        with st.expander("🔄 MACD (Moving Average Convergence Divergence)"):
            macd_guide = """
<div style="padding:16px;">
<h4 style="color:#4CAF50;">What is MACD?</h4>
<p style="font-size:13px;line-height:1.6;">
MACD shows the relationship between two moving averages. It helps identify momentum changes and trend reversals.
</p>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0;">
<div style="background:rgba(16,185,129,0.1);padding:12px;border-radius:8px;">
<strong style="color:#10b981;">📈 Bullish Crossover</strong>
<p style="font-size:11px;margin:4px 0 0 0;">
MACD line crosses above signal line = Buy signal
</p>
</div>
<div style="background:rgba(239,68,68,0.1);padding:12px;border-radius:8px;">
<strong style="color:#ef4444;">📉 Bearish Crossover</strong>
<p style="font-size:11px;margin:4px 0 0 0;">
MACD line crosses below signal line = Sell signal
</p>
</div>
</div>

<h4 style="color:#4CAF50;">Best Use Cases:</h4>
<ul style="font-size:13px;line-height:1.8;">
<li>Confirm trend changes (works best with other indicators)</li>
<li>Identify divergences (price vs MACD direction)</li>
<li>Strong signal when crossing zero line</li>
</ul>
</div>
"""
            st.markdown(macd_guide, unsafe_allow_html=True)
        
        # ADX Section
        with st.expander("💪 ADX (Average Directional Index)"):
            adx_guide = """
<div style="padding:16px;">
<h4 style="color:#FF5722;">What is ADX?</h4>
<p style="font-size:13px;line-height:1.6;">
ADX measures trend strength (NOT direction). Values range from 0-100.
</p>

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0;">
<div style="background:rgba(16,185,129,0.1);padding:10px;border-radius:6px;text-align:center;">
<strong style="color:#10b981;">ADX > 25</strong>
<p style="font-size:11px;margin:4px 0 0 0;">Strong Trend<br>✅ Good for trend trading</p>
</div>
<div style="background:rgba(245,158,11,0.1);padding:10px;border-radius:6px;text-align:center;">
<strong style="color:#f59e0b;">ADX 20-25</strong>
<p style="font-size:11px;margin:4px 0 0 0;">Moderate Trend<br>⚖️ Wait for confirmation</p>
</div>
<div style="background:rgba(239,68,68,0.1);padding:10px;border-radius:6px;text-align:center;">
<strong style="color:#ef4444;">ADX < 20</strong>
<p style="font-size:11px;margin:4px 0 0 0;">Weak/Ranging<br>❌ Avoid trend trades</p>
</div>
</div>

<h4 style="color:#FF5722;">💡 Pro Tip:</h4>
<p style="background:rgba(255,87,34,0.1);padding:10px;border-radius:6px;font-size:13px;">
Use ADX to filter trades: Only take signals when ADX > 25 for higher success rates!
</p>
</div>
"""
            st.markdown(adx_guide, unsafe_allow_html=True)
    
    # ========== TAB 3: TRADING PRESETS ==========
    with guide_tab3:
        st.markdown("## ⚙️ Optimized Trading Configurations")
        
        preset_intro = """
<div style="background:rgba(245,158,11,0.1);padding:16px;border-radius:8px;margin-bottom:20px;border-left:4px solid #f59e0b;">
<h4 style="color:#f59e0b;margin-top:0;">📋 Choose Your Trading Style</h4>
<p style="margin:0;font-size:13px;">
Each preset is optimized for specific time frames and risk profiles. 
Start with conservative settings and adjust as you gain experience!
</p>
</div>
"""
        st.markdown(preset_intro, unsafe_allow_html=True)
        
        # Quick Reference Table
        st.markdown("### 📊 Quick Comparison Table")
        
        preset_comparison = {
            "Trading Style": ["Scalping", "Intraday", "Swing (Balanced)", "Swing (Conservative)", "Positional", "Long-Term"],
            "⏱️ Duration": ["Minutes", "Hours", "2-7 days", "3-10 days", "1-4 weeks", "Months"],
            "📊 Interval": ["5m", "5m", "15m", "30m", "1h", "1h"],
            "🎯 Threshold": [4, 5, 6, 7, 6, 7],
            "🛑 Stop Loss": ["0.5%", "1.0%", "2.0%", "2.5%", "3.5%", "5.0%"],
            "💰 Target": ["1.0%", "2.0%", "5.0%", "6.0%", "10.0%", "20.0%"],
            "📈 Risk:Reward": ["1:2", "1:2", "1:2.5", "1:2.4", "1:2.9", "1:4"],
            "🔔 Signals/Day": ["10-20", "3-8", "1-3", "0-2", "1-3/week", "1-2/week"]
        }
        
        df_presets = pd.DataFrame(preset_comparison)
        st.dataframe(df_presets, use_container_width=True, hide_index=True)
        
        # Detailed Preset Configurations
        st.markdown("### 🎯 Detailed Preset Configurations")
        
        preset_tabs = st.tabs(["⚡ Scalping", "📊 Intraday", "🔄 Swing", "📅 Positional", "🏔️ Long-Term"])
        
        # Scalping Preset
        with preset_tabs[0]:
            scalping_config = """
<div style="background:linear-gradient(135deg, #ef4444 0%, #dc2626 100%);padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0 0 8px 0;">⚡ Scalping - Ultra Fast Trading</h3>
<p style="margin:0;font-size:13px;">Quick 0.5-1.5% moves, multiple times per day. Requires constant monitoring!</p>
</div>
"""
            st.markdown(scalping_config, unsafe_allow_html=True)
            
            scalp_settings = {
                "Parameter": ["Scan Mode", "Interval", "Volume Z-Score", "Breakout Margin", "Signal Threshold", 
                             "ATR Period", "ATR Multiplier", "Momentum Lookback", "RS Lookback", "Auto-Refresh"],
                "Value": ["Confirmation", "5m", "2.5", "0.2%", "4", "3", "0.6", "2", "1", "30 sec"],
                "Why?": [
                    "Need immediate confirmed momentum",
                    "Fastest reliable timeframe",
                    "Strong volume spike required",
                    "Instant breakouts only",
                    "More signals for active trading",
                    "Ultra-fast volatility response",
                    "Very tight stops",
                    "Last 10 minutes only",
                    "Same-day strength",
                    "Real-time updates"
                ]
            }
            
            st.dataframe(pd.DataFrame(scalp_settings), use_container_width=True, hide_index=True)
            
            st.info("⚠️ **Best Time:** 9:30-10:30 AM and 2:30-3:15 PM | **Max Positions:** 2-3 | **Capital Per Trade:** 5-10%")
        
        # Intraday Preset
        with preset_tabs[1]:
            intraday_config = """
<div style="background:linear-gradient(135deg, #f59e0b 0%, #d97706 100%);padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0 0 8px 0;">📊 Intraday - Same Day Trading</h3>
<p style="margin:0;font-size:13px;">Catch 2-5% moves within market hours (9:15 AM - 3:30 PM IST)</p>
</div>
"""
            st.markdown(intraday_config, unsafe_allow_html=True)
            
            intraday_settings = {
                "Parameter": ["Scan Mode", "Interval", "Volume Z-Score", "Breakout Margin", "Signal Threshold", 
                             "ATR Period", "ATR Multiplier", "Stop Loss %", "Target %"],
                "Value": ["Early Detection", "5m", "1.5", "0.3%", "5", "5", "0.8", "1.0%", "2.0%"],
                "Why?": [
                    "Catch moves before they happen",
                    "Best for intraday momentum",
                    "Early accumulation detection",
                    "Tight margin for quick entries",
                    "Balance between signals & quality",
                    "Fast-reacting for intraday volatility",
                    "Tighter stop for same-day",
                    "Strict risk management",
                    "2:1 reward ratio"
                ]
            }
            
            st.dataframe(pd.DataFrame(intraday_settings), use_container_width=True, hide_index=True)
            
            st.success("✅ **Best Time:** 9:30-11:00 AM and 2:00-3:15 PM | **Expected:** 3-8 signals/day | **Hold:** 1-3 hours")
        
        # Swing Preset
        with preset_tabs[2]:
            swing_config = """
<div style="background:linear-gradient(135deg, #10b981 0%, #059669 100%);padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0 0 8px 0;">🔄 Swing Trading - Multi-Day Holds</h3>
<p style="margin:0;font-size:13px;">Capture 5-15% moves over 2-7 days with balanced risk</p>
</div>
"""
            st.markdown(swing_config, unsafe_allow_html=True)
            
            col_balanced, col_conservative = st.columns(2)
            
            with col_balanced:
                st.markdown("**📊 Swing Balanced**")
                balanced_settings = {
                    "Parameter": ["Interval", "Threshold", "Stop Loss", "Target", "Hold"],
                    "Value": ["15m", "6", "2.0%", "5.0%", "2-7 days"]
                }
                st.dataframe(pd.DataFrame(balanced_settings), hide_index=True, use_container_width=True)
            
            with col_conservative:
                st.markdown("**🛡️ Swing Conservative**")
                conservative_settings = {
                    "Parameter": ["Interval", "Threshold", "Stop Loss", "Target", "Hold"],
                    "Value": ["30m", "7", "2.5%", "6.0%", "3-10 days"]
                }
                st.dataframe(pd.DataFrame(conservative_settings), hide_index=True, use_container_width=True)
            
            st.info("💡 **Balanced:** More signals, moderate quality | **Conservative:** Fewer signals, higher win rate (65-75%)")
        
        # Positional & Long-Term
        with preset_tabs[3]:
            positional_config = """
<div style="background:linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0 0 8px 0;">📅 Positional Trading - Weekly Trends</h3>
<p style="margin:0;font-size:13px;">Ride medium-term trends for 10-30% gains over 1-4 weeks</p>
</div>
"""
            st.markdown(positional_config, unsafe_allow_html=True)
            
            positional_settings = {
                "Parameter": ["Scan Mode", "Interval", "Signal Threshold", "Stop Loss", "Target", "Holding Period"],
                "Value": ["Early Detection", "1h", "6", "3.5%", "10.0%", "1-4 weeks"],
                "Best For": ["Trend formation", "Daily trend development", "Quality over quantity", 
                            "Weekly swings", "Long-term targets", "Patient traders"]
            }
            
            st.dataframe(pd.DataFrame(positional_settings), use_container_width=True, hide_index=True)
            
            st.success("✅ **Scan Timing:** End of day (3:00-3:30 PM) | **Expected:** 1-3 signals/week")
        
        with preset_tabs[4]:
            longterm_config = """
<div style="background:linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);padding:16px;border-radius:10px;color:white;margin-bottom:16px;">
<h3 style="margin:0 0 8px 0;">🏔️ Long-Term Investing - Monthly Holds</h3>
<p style="margin:0;font-size:13px;">Major trend reversals and breakouts with 20%+ potential</p>
</div>
"""
            st.markdown(longterm_config, unsafe_allow_html=True)
            
            longterm_settings = {
                "Parameter": ["Interval", "Threshold", "Stop Loss", "Target", "ATR Multiplier", "Holding"],
                "Value": ["1h", "7", "5.0%", "20.0%", "2.0", "Months"],
                "Strategy": ["Smooth intraday", "Highest quality only", "Monthly volatility", 
                            "Patient gains", "Very wide stops", "Multi-month trends"]
            }
            
            st.dataframe(pd.DataFrame(longterm_settings), use_container_width=True, hide_index=True)
            
            st.info("📅 **Scan Frequency:** Weekly or at major market events | **Max Positions:** 5-8 stocks")
    
    # ========== TAB 4: BEST PRACTICES ==========
    with guide_tab4:
        st.markdown("## 💡 Trading Best Practices")
        
        # Risk Management
        with st.expander("🛡️ Risk Management Rules", expanded=True):
            risk_guide = """
<div style="padding:16px;">
<h4 style="color:#ef4444;">Never Risk More Than You Can Afford to Lose</h4>

<div style="background:rgba(239,68,68,0.1);padding:14px;border-radius:8px;margin:12px 0;border-left:4px solid #ef4444;">
<h5 style="margin:0 0 8px 0;color:#ef4444;">📊 Position Sizing by Style</h5>
<table style="width:100%;font-size:13px;">
<tr style="background:rgba(0,0,0,0.2);">
<th style="padding:8px;text-align:left;">Style</th>
<th style="padding:8px;">Max Positions</th>
<th style="padding:8px;">Capital Per Trade</th>
<th style="padding:8px;">Daily Loss Limit</th>
</tr>
<tr><td style="padding:8px;">Scalping</td><td style="padding:8px;text-align:center;">2-3</td><td style="padding:8px;text-align:center;">5-10%</td><td style="padding:8px;text-align:center;">1.5%</td></tr>
<tr><td style="padding:8px;">Intraday</td><td style="padding:8px;text-align:center;">2-4</td><td style="padding:8px;text-align:center;">10-15%</td><td style="padding:8px;text-align:center;">2%</td></tr>
<tr><td style="padding:8px;">Swing</td><td style="padding:8px;text-align:center;">3-5</td><td style="padding:8px;text-align:center;">15-20%</td><td style="padding:8px;text-align:center;">5%</td></tr>
<tr><td style="padding:8px;">Positional</td><td style="padding:8px;text-align:center;">4-6</td><td style="padding:8px;text-align:center;">15-25%</td><td style="padding:8px;text-align:center;">10%</td></tr>
<tr><td style="padding:8px;">Long-Term</td><td style="padding:8px;text-align:center;">5-8</td><td style="padding:8px;text-align:center;">20-30%</td><td style="padding:8px;text-align:center;">No daily limit</td></tr>
</table>
</div>

<h4 style="color:#10b981;">Golden Rules:</h4>
<ul style="font-size:13px;line-height:1.8;">
<li>✅ Never risk more than 2% of capital per trade</li>
<li>✅ Use stop losses on EVERY trade (no exceptions!)</li>
<li>✅ If you hit daily loss limit, STOP trading for the day</li>
<li>✅ Scale position size with account growth</li>
<li>⚠️ Don't average down on losing positions</li>
<li>❌ Never trade with borrowed money</li>
</ul>
</div>
"""
            st.markdown(risk_guide, unsafe_allow_html=True)
        
        # Trading Psychology
        with st.expander("🧠 Trading Psychology"):
            psychology_guide = """
<div style="padding:16px;">
<h4 style="color:#3b82f6;">Master Your Mind, Master the Market</h4>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0;">
<div style="background:rgba(16,185,129,0.1);padding:12px;border-radius:8px;">
<h5 style="color:#10b981;margin:0 0 8px 0;">✅ DO</h5>
<ul style="font-size:12px;line-height:1.6;margin:0;">
<li>Follow your trading plan</li>
<li>Accept small losses quickly</li>
<li>Keep a trading journal</li>
<li>Take regular breaks</li>
<li>Learn from every trade</li>
</ul>
</div>
<div style="background:rgba(239,68,68,0.1);padding:12px;border-radius:8px;">
<h5 style="color:#ef4444;margin:0 0 8px 0;">❌ DON'T</h5>
<ul style="font-size:12px;line-height:1.6;margin:0;">
<li>Trade on emotions (FOMO/revenge)</li>
<li>Overtrade after wins</li>
<li>Hold losing positions hoping</li>
<li>Trade without stop loss</li>
<li>Risk money you need</li>
</ul>
</div>
</div>

<h4 style="color:#3b82f6;">📝 Keep a Trading Journal:</h4>
<p style="font-size:13px;">Record for each trade:</p>
<ul style="font-size:13px;line-height:1.8;">
<li>Entry reason (which signals triggered)</li>
<li>Entry price, SL, target</li>
<li>Exit reason and actual P/L</li>
<li>What went right/wrong</li>
<li>Emotional state during trade</li>
</ul>
</div>
"""
            st.markdown(psychology_guide, unsafe_allow_html=True)
        
        # When to Trade
        with st.expander("⏰ Best Trading Times (IST)"):
            timing_guide = """
<div style="padding:16px;">
<h4 style="color:#f59e0b;">Optimal Market Hours</h4>

<div style="background:rgba(16,185,129,0.1);padding:12px;border-radius:8px;margin:12px 0;">
<strong style="color:#10b981;">🌅 9:15-10:30 AM - Opening Volatility</strong>
<p style="font-size:12px;margin:4px 0 0 0;">
<strong>Best for:</strong> Scalping, Intraday<br>
<strong>Characteristics:</strong> Highest volatility, many false breakouts<br>
<strong>Strategy:</strong> Wait for first 15 min, then trade clear setups
</p>
</div>

<div style="background:rgba(245,158,11,0.1);padding:12px;border-radius:8px;margin:12px 0;">
<strong style="color:#f59e0b;">☀️ 10:30 AM - 2:00 PM - Mid-Day Consolidation</strong>
<p style="font-size:12px;margin:4px 0 0 0;">
<strong>Best for:</strong> Swing setup identification<br>
<strong>Characteristics:</strong> Lower volume, ranging<br>
<strong>Strategy:</strong> Mark support/resistance for afternoon breakouts
</p>
</div>

<div style="background:rgba(168,85,247,0.1);padding:12px;border-radius:8px;">
<strong style="color:#a855f7;">🌆 2:00-3:30 PM - Afternoon Push</strong>
<p style="font-size:12px;margin:4px 0 0 0;">
<strong>Best for:</strong> Intraday, Swing entries<br>
<strong>Characteristics:</strong> Final move, institutions positioning<br>
<strong>Strategy:</strong> Follow strong trends from morning
</p>
</div>

<h4 style="color:#f59e0b;">📅 Weekly Patterns:</h4>
<ul style="font-size:13px;line-height:1.8;">
<li><strong>Monday:</strong> Often slow, cautious start (wait for direction)</li>
<li><strong>Tuesday-Thursday:</strong> Best trending days</li>
<li><strong>Friday:</strong> Profit booking, choppy (be cautious)</li>
<li><strong>Week after expiry:</strong> Generally bullish momentum</li>
<li><strong>Expiry week:</strong> High volatility, careful with positions</li>
</ul>
</div>
"""
            st.markdown(timing_guide, unsafe_allow_html=True)
        
        # Common Mistakes
        with st.expander("⚠️ Common Mistakes to Avoid"):
            mistakes_guide = """
<div style="padding:16px;">
<h4 style="color:#ef4444;">Learn From Others' Mistakes</h4>

<div style="background:rgba(239,68,68,0.1);padding:12px;border-radius:8px;margin:12px 0;border-left:4px solid #ef4444;">
<h5 style="color:#ef4444;margin:0 0 8px 0;">❌ Top 10 Trading Mistakes:</h5>
<ol style="font-size:13px;line-height:2;">
<li><strong>No Stop Loss:</strong> "It will come back" - Famous last words before big losses</li>
<li><strong>Overtrading:</strong> Taking every signal = death by 1000 cuts</li>
<li><strong>Revenge Trading:</strong> Trying to "get back" losses quickly = bigger losses</li>
<li><strong>Ignoring Trends:</strong> Fighting the trend = fighting the market</li>
<li><strong>FOMO:</strong> Chasing stocks after big moves = buying tops</li>
<li><strong>Lack of Patience:</strong> Closing winning trades too early</li>
<li><strong>Not Diversifying:</strong> All eggs in one basket</li>
<li><strong>Averaging Down:</strong> Adding to losing positions</li>
<li><strong>No Trading Plan:</strong> Random entries/exits</li>
<li><strong>Ignoring News:</strong> Trading through major events/results</li>
</ol>
</div>

<h4 style="color:#10b981;">✅ How to Avoid Them:</h4>
<ul style="font-size:13px;line-height:1.8;">
<li>Use paper trading tab to practice first</li>
<li>Start with swing/positional (easier than intraday)</li>
<li>Follow ONE preset configuration consistently</li>
<li>Review trades weekly, not daily</li>
<li>Focus on process, not profits</li>
</ul>
</div>
"""
            st.markdown(mistakes_guide, unsafe_allow_html=True)
    
    # ========== FOOTER TIPS ==========
    footer_html = """
<div style="background:linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
padding:20px;border-radius:12px;margin-top:30px;color:white;text-align:center;">
<h3 style="margin:0 0 10px 0;">🎯 Remember: Consistency Beats Complexity</h3>
<p style="margin:0;font-size:14px;">
Master ONE trading style before trying others. Paper trade for at least 2 weeks. 
Your edge comes from discipline, not from perfect signals!
</p>
<h3 style="margin:0 0 10px 0;">🍀 Vijay S</h3>
</div>
"""
    st.markdown(footer_html, unsafe_allow_html=True)
