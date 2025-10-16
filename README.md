-----

# 🚀 Automated Intraday Stock Picker & Notifier (NSE)

An advanced, real-time stock screener built with Python and Streamlit to find high-probability intraday trading candidates on the NSE F\&O segment.

| Feature | Status |
| :--- | :--- |
| **Technology** | Python, Streamlit, Pandas, TA-Lib |
| **Purpose** | **Confluence-Based Intraday Signals** |
| **Trade Management** | Volatility-Adjusted SL/Target (ATR) |
| **Alerts** | Desktop & Telegram |

-----

## ✨ Core Logic: Confluence Scoring

The picker uses a powerful **Confluence Scoring** system—meaning a stock must pass *multiple* independent technical "tests" at the same time to qualify. It's like a job interview where the candidate needs high marks from five different managers\!

### 1\. The Scoring System

  * Each active filter (e.g., Volume, RSI, Breakout) acts as a test.
  * If a stock passes a test, it receives **+1 Score**.
  * The stock is shortlisted only if its **Total Score** meets or exceeds the **Signal Score Threshold** set in the sidebar.

### 2\. The Scoreboard (Main Filters)

The following criteria are used to build the final score for each stock:

| Filter / Indicator | Condition For Pick | Purpose |
| :--- | :--- | :--- |
| **Volume Spike** | Current volume \> **20-bar average volume × Multiplier** | Identifies sudden institutional interest/fresh money entry. |
| **ATR Breakout** | **ATR \> Percentile Threshold** | Ensures the stock is volatile enough *right now* to give an intraday move. |
| **Relative Strength** | `% change stock close > % change NIFTY close` | Selects stocks that are currently outperforming the index. |
| **Price Breakout** | Last close \> **Max Close of the previous N bars** | Detects a clear momentum breakout (making a fresh high/low). |
| **EMA20 + RSI10** | **Close \> EMA(20)** AND **RSI(10) \> 50** | Confirms a strong, established short-term bullish trend. |

-----

## ⚙️ Configuration & Parameter Guide

All parameters are adjusted in the Streamlit sidebar. Finding the perfect combination is key to successful screening.

| Parameter | Suggested Value | Why |
| :--- | :--- | :--- |
| **Signal Score Threshold** | `3` or `4` | Controls sensitivity. Higher score = fewer, higher-quality signals. |
| **Volume Spike Multiplier** | `1.5x – 2x` | Filters for genuine spikes; a 1.5x spike is 50% more volume than average. |
| **ATR Multiplier (Stop Loss)** | `1.8x – 2x` | This sets your SL distance. A 2x buffer avoids being stopped out by normal intraday noise. |
| **ATR Percentile Threshold** | `30 – 40` | Filters out 'dead' stocks and keeps moderate-to-high volatility candidates. |
| **Risk-Reward Ratio (Target)** | `2.0` (for 1:2 RRR) | Automatically sets Target distance as `2 × Stop Loss` distance. |

### Filter Presets

The app allows you to **Save and Load** various filter and parameter combinations to quickly switch between aggressive, moderate, and conservative screening setups.

-----

## 🧠 Technical Prediction Module (Directional Bias)

When enabled, this module runs a separate analysis on the shortlisted stocks to provide a quick high-level view of the directional bias *before* trading.

| Indicator | Meaning |
| :--- | :--- |
| **RSI (7)** | Checks for extreme overbought/oversold conditions (fast-reacting). |
| **Support / Resistance** | Analyzes proximity to key historical price zones. |
| **Double Top / Bottom** | Identifies classic reversal patterns. |
| **Trend Line** | Finds the current short-term trend slope. |
| **Verdict** | Combines all factors into a final bias (**Buy / Sell / Neutral**). |

-----

## 🛠️ Setup and Running the App

### 1\. Installation

```bash
# Install the necessary libraries
pip install streamlit pandas yfinance numpy requests plyer streamlit-autorefresh ta-lib
```

### 2\. Execution

Save your script as `nse_intraday_picker_streamlit.py` and run it:

```bash
streamlit run nse_intraday_picker_streamlit.py
```

### 3\. Usage Tip

Remember to **enable Desktop and Telegram Notifications** in the sidebar if you want instant alerts when a stock meets your scoring threshold\!