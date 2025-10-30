"""
trade_guide.py - Trading Strategy Guide and Education
"""

import streamlit as st
import pandas as pd

def render_ai_guide():
            """Complete AI Predictions Guide"""

            st.markdown("""
        # 🤖 AI Predictions Guide

        ## What is AI-Powered Stock Prediction?

        Our AI system uses **Machine Learning** to analyze historical stock data and predict whether a stock's price is likely to move **UP** or **DOWN** in the near term (next few days).

        ---

        ## 🧠 How Does It Work?

        ### The Science Behind It

        The AI system uses two powerful machine learning algorithms:

        1. **Random Forest (RF)** 🌲
           - Analyzes patterns across multiple decision trees
           - Great at handling complex, non-linear relationships
           - Less prone to overfitting

        2. **Logistic Regression (LR)** 📊
           - Statistical model for binary classification
           - Fast and interpretable
           - Works well with linear trends

        ### The Process
        📥 Data Collection
        ↓
        🔍 Feature Extraction (17 indicators)
        ↓
        🤖 Model Training (RF + LR)
        ↓
        🎯 Ensemble Prediction (Average both models)
        ↓
        📊 Output: Direction + Confidence

        ---

        ## 🚀 How to Train the AI Models

        ### First-Time Setup

        **Step 1:** Navigate to **Sidebar** or **AI Predictions Tab**

        **Step 2:** Look for the AI Training section:
        - 🚀 **Train AI Models Now** button
        - Training status indicator

        **Step 3:** Click the button and wait (3-5 minutes)

        **What Happens During Training:**
        """)

            col_train1, col_train2, col_train3 = st.columns(3)

            with col_train1:
                st.markdown("""
        **Phase 1: Data Collection**
        - Downloads 6 months of daily data
        - Uses top 30 NSE F&O stocks
        - Collects OHLCV + indicators
        - Creates 1000+ training samples
        """)

            with col_train2:
                st.markdown("""
        **Phase 2: Model Training**
        - Trains Random Forest model
        - Trains Logistic Regression model
        - Validates on test data
        - Calculates accuracy metrics
        """)

            with col_train3:
                st.markdown("""
        **Phase 3: Saving**
        - Saves models to disk
        - Stores feature importance
        - Ready for instant predictions
        - Models persist across sessions
        """)

            st.markdown("""
        ---

        ## 📊 Understanding AI Predictions

        ### The Prediction Display

        When you view an AI prediction, you'll see:
        """)

            st.markdown("""
        <div style="background:rgba(59,130,246,0.1);padding:20px;border-radius:10px;margin:20px 0;">
        <h4 style="color:#3b82f6;">🤖 AI Prediction: BULLISH</h4>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:15px 0;">
        <div>
        <strong>Probability UP:</strong> 68.5%<br>
        <strong>Probability DOWN:</strong> 31.5%<br>
        <strong>AI Confidence:</strong> 74%
        </div>
        <div>
        <strong>Random Forest:</strong> 70% UP<br>
        <strong>Logistic Reg:</strong> 67% UP<br>
        <strong>Consensus:</strong> Both agree ✅
        </div>
        </div>
        </div>
        """, unsafe_allow_html=True)

            st.markdown("""
        ### Key Metrics Explained

        | Metric | Meaning | What to Look For |
        |--------|---------|-----------------|
        | **Probability UP** | Likelihood of price increase | >60% = Bullish signal |
        | **Probability DOWN** | Likelihood of price decrease | >60% = Bearish signal |
        | **AI Confidence** | How certain the AI is | >75% = Strong, 60-75% = Moderate, <60% = Weak |
        | **Consensus** | Technical + AI agreement | Both BULLISH = 🟢 Strong Buy |

        ---

        ## 🎯 How to Use AI Predictions in Trading

        ### Step-by-Step Trading Workflow

        **1. Run the Scanner** (Auto Scanner Tab)
           - Scanner finds stocks with good technical setup
           - Shows technical score (out of 15)

        **2. Check Technical Analysis**
           - Review entry, stop loss, target levels
           - Check signal reasons (RSI, MACD, Volume, etc.)

        **3. View AI Prediction** (AI Predictions Tab or Scanner summary)
           - See AI's directional prediction
           - Check confidence level
           - Review feature importance

        **4. Look for Consensus** ✅
           - **STRONG BUY**: Technical = BULLISH + AI = BULLISH + High Confidence (>70%)
           - **MODERATE BUY**: Technical = BULLISH + AI = BULLISH + Moderate Confidence (60-70%)
           - **WEAK/AVOID**: Mixed signals or low confidence (<60%)

        **5. Execute Trade**
           - Add to watchlist or paper trading
           - Follow your risk management rules
           - Track prediction accuracy

        ---

        ## ⚠️ Important Guidelines

        ### When to Trust AI Predictions

        ✅ **Trust More When:**
        - Confidence >75% (Strong signal)
        - Technical analysis agrees (Consensus)
        - Multiple indicators support the direction
        - Stock showing clear trend
        - High trading volume

        ❌ **Be Cautious When:**
        - Confidence <60% (Weak signal)
        - Mixed signals (Tech BULLISH, AI BEARISH)
        - Choppy/consolidating market
        - Low volume
        - Major news pending

        ### AI Limitations

        🚫 **AI CANNOT:**
        - Predict exact prices
        - Guarantee profits
        - Account for breaking news
        - Predict black swan events
        - Replace risk management

        ✅ **AI CAN:**
        - Identify high-probability setups
        - Detect complex patterns
        - Provide objective second opinion
        - Track its own accuracy
        - Learn from market data

        ---

        ## 📈 Interpreting Feature Importance

        When you expand **"What's Driving This Prediction?"**, you'll see:

        Top Contributing Factors:

        RSI 7 ████████░░ 42.3%

        Price Change 5 ██████░░░░ 28.1%

        Volume Ratio ████░░░░░░ 15.6%

        MACD Difference ███░░░░░░░ 8.2%

        Momentum 10 ██░░░░░░░░ 5.8%


        **What This Means:**
        - **RSI 7 (42.3%)**: Current RSI level is the most important factor
        - **Price Change 5 (28.1%)**: Recent 5-candle price movement matters
        - **Top 3 factors** usually account for 70-80% of the decision

        ---

        ## 🔄 Model Maintenance

        ### When to Retrain

        Retrain your AI models:
        - ✅ **Weekly** (recommended for active markets)
        - ✅ After major market events (budget, Fed decisions)
        - ✅ If accuracy drops below 55%
        - ✅ Market regime changes (bull to bear or vice versa)

        ### How to Retrain

        **Option 1: From Sidebar**
        1. Go to **🤖 AI Model Training** section
        2. Click **🔄 Retrain** button
        3. Wait 3-5 minutes

        **Option 2: From AI Predictions Tab**
        1. Go to **AI Predictions** tab
        2. Click **🔄 Retrain Models** button
        3. Monitor progress

        ---

        ## 📊 Tracking AI Performance

        ### View Accuracy Stats

        In the **AI Predictions Tab**, you'll see:

        | Metric | Description |
        |--------|-------------|
        | **Overall Accuracy** | % of correct predictions across all trades |
        | **Bullish Accuracy** | % correct when predicting UP |
        | **Bearish Accuracy** | % correct when predicting DOWN |
        | **Last 10 Predictions** | Recent performance (more reliable) |

        ### Save Predictions

        Click **📝 Save This Prediction** on any stock to:
        - Track AI's accuracy over time
        - Compare predicted vs actual outcomes
        - Build confidence in the system
        - Identify which patterns work best

        ---

        ## 💡 Pro Trading Tips with AI

        ### Strategy 1: High-Confidence Plays

        Filter: Confidence ≥ 75%

        Technical Score ≥ 10

        Consensus = STRONG BULLISH
        = Take larger position size (within risk limits)


        ### Strategy 2: Early Detection
        Scanner Mode: Early Detection 🐇

        AI Confidence 60-75%

        Technical Score 7-9
        = Enter with smaller size, wait for confirmation


        ### Strategy 3: Swing Trading

        Use AI for: Multi-day predictions

        Technical Analysis for: Entry/Exit timing

        Risk Management: Always set SL/Target

        ### Strategy 4: Filtering Noise
        Scanner finds 10 stocks
        AI shows 4 with High Confidence
        = Focus on those 4 stocks only
        = Reduces FOMO, improves quality


        ---

        ## 🧪 Testing AI Predictions

        ### Paper Trading Workflow

        1. **Get AI Prediction** (AI Predictions tab)
        2. **Add to Paper Trading** (Paper Trading tab)
        3. **Set Entry/SL/Target** based on technicals
        4. **Track Performance** automatically
        5. **Review Results** after 5-10 days
        6. **Calculate Win Rate** for AI predictions

        ### Recommended Testing Period

        Before using with real money:
        - Test for **2-3 weeks** minimum
        - Track at least **20 predictions**
        - Calculate **win rate** (aim for >60%)
        - Understand which confidence levels work best
        - Learn your edge with AI + Technical combo

        ---

        ## 🎓 Learning Resources

        ### Understanding Machine Learning

        **Random Forest:**
        - Decision tree ensemble method
        - Reduces overfitting
        - Handles non-linear relationships well

        **Logistic Regression:**
        - Binary classification algorithm
        - Fast and interpretable
        - Good for probability estimates

        ### Features Used by AI (17 Total)

        **Price-based (6):**
        - Price change 1, 5, 10, 20 periods
        - Price to SMA20, SMA50 ratio

        **Volatility (2):**
        - 20-period volatility
        - High-low range percentage

        **Volume (2):**
        - Volume ratio (current vs 20-period avg)
        - Volume change

        **Technical Indicators (5):**
        - RSI 7
        - MACD difference (MACD - Signal)
        - ADX (trend strength)
        - Momentum 5, 10 periods

        **Trend (2):**
        - Higher highs pattern
        - Higher lows pattern

        ---

        ## ❓ Common Questions

        **Q: How accurate is the AI?**
        A: Typically 55-65% accuracy. Better than random (50%), but not perfect. Use as one tool among many.

        **Q: Can I rely 100% on AI predictions?**
        A: No. Always combine with technical analysis, risk management, and your own judgment.

        **Q: What if Technical says BUY but AI says BEARISH?**
        A: Mixed signals = Higher risk. Either skip the trade or reduce position size significantly.

        **Q: How often should I retrain?**
        A: Weekly for active trading, monthly for swing trading. After major market events, retrain immediately.

        **Q: Why is confidence sometimes 0%?**
        A: Models aren't trained yet, or there's insufficient data for that stock. Train the models first.

        **Q: Does AI work for all stocks?**
        A: Works best for liquid F&O stocks with consistent trading patterns. Less reliable for penny stocks.

        ---

        ## 🎯 Quick Reference Card

        ### When to Use AI

        | Scenario | AI Usage | Confidence Level | Action |
        |----------|----------|------------------|---------|
        | Technical Score 12+ | Check AI | Any | Strong technical, AI confirms |
        | Technical Score 8-11 | Use AI heavily | >70% | Need AI validation |
        | Technical Score 6-7 | AI critical | >75% | Only trade if AI agrees |
        | Mixed technical signals | Use AI as tiebreaker | >65% | AI decides direction |

        ### Risk Management with AI

        High Confidence (>75%) → Normal position size
        Moderate (60-75%) → Reduce by 30-50%
        Low (<60%) → Skip or very small size
        No Consensus (Tech ≠ AI) → Skip trade


        ---

        ## 🚀 Getting Started Checklist

        - [ ] Train AI models (3-5 minutes, one-time)
        - [ ] Run a scan in Auto Scanner tab
        - [ ] Check AI predictions for qualified stocks
        - [ ] Compare Technical vs AI predictions
        - [ ] Start with paper trading (test 10-20 trades)
        - [ ] Track accuracy over 2-3 weeks
        - [ ] Retrain models weekly
        - [ ] Gradually increase confidence in the system
        - [ ] Develop your own AI + Technical strategy
        - [ ] Never skip risk management!

        ---

        ## 📞 Tips from Experienced Users

        > **Vijay S (Developer):** "I use AI confidence as a filter. If scanner finds 10 stocks but only 3 have >70% AI confidence, I focus on those 3. Quality over quantity!"

        > **Strategy:** Combine Early Detection scanner mode + AI predictions for catching moves early. Use Original scanner + High AI confidence for safer, confirmed trades.

        > **Risk Rule:** If AI confidence <60%, I reduce my position size by 50%. If AI and Technical disagree, I skip the trade entirely.

        ---

        **Remember:** AI is a powerful tool, but it's not magic. Use it as part of a complete trading system that includes:
        - ✅ Technical analysis
        - ✅ Risk management
        - ✅ Position sizing
        - ✅ Emotional discipline
        - ✅ Continuous learning

        Happy AI-Powered Trading! 🚀📈🤖
        """)

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
    guide_tab1, guide_tab2, guide_tab3, guide_tab4, guide_tab5 = st.tabs([
        "📊 Scoring System",
        "📈 Indicators Guide", 
        "⚙️ Trading Presets",
        "💡 Best Practices",
        "🤖 AI Predictions"
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
# ========== TAB 5: AI PREDICTIONS (NEW) ==========
    with guide_tab5:
        render_ai_guide()

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
