# 📊 Stock Hunter Dashboard

A powerful, real-time stock screening and analysis platform for NSE India F&O stocks with integrated paper trading capabilities.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🎯 Overview

Stock Hunter Dashboard is an advanced trading tool that combines technical analysis, real-time scanning, and paper trading in one comprehensive platform. Built with Streamlit and powered by YFinance, it helps traders identify high-probability setups across multiple timeframes using a sophisticated scoring system.

## ✨ Key Features

### 🔍 **Auto Scanner**
- **Dual Scanning Modes:**
  - 🐇 **Early Detection**: Catch trends before they happen
  - ✅ **Confirmation**: Wait for validated signals
- **Real-time scoring system** (0-15 points)
- **Multiple technical indicators**: RSI, MACD, EMA, ADX, ATR, Volume analysis
- **Auto-refresh** with configurable intervals
- **Customizable filters** and thresholds

### 💹 **Paper Trading**
- **Virtual trading environment** with real-time prices
- **Automatic SL/Target tracking** with P/L calculation
- **Trade management** with one-click execution
- **Position monitoring** with live updates
- **Trade history** and performance tracking
- **Pre-filled trade setups** from scanner signals

### 🔎 **Manual Stock Analyzer**
- **Deep-dive technical analysis** with visual indicators
- **Batch analysis** (multiple stocks at once)
- **Comprehensive metrics:**
  - Momentum indicators (RSI 7/10)
  - Trend indicators (EMA 20/50, MACD)
  - Strength indicators (ADX, ATR)
  - Fundamental metrics (P/E, Market Cap, 52W range)
- **Educational notes** for each indicator
- **Visual progress bars** and color-coded signals

### 📋 **Watchlist & Alerts**
- **Custom watchlist** with entry/SL/target levels
- **Price alerts** (target hit, stop loss triggered)
- **Auto-monitoring** during market hours
- **Desktop & Telegram notifications**

### 📚 **Trade Guide**
- **Complete scoring system** explanation
- **Technical indicators encyclopedia**
- **6 optimized trading presets:**
  - ⚡ Scalping (minutes)
  - 📊 Intraday (hours)
  - 🔄 Swing (2-7 days)
  - 📅 Positional (weeks)
  - 🏔️ Long-term (months)
- **Risk management guidelines**
- **Trading psychology tips**
- **Best market timing** (IST zones)

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
- git clone https://github.com/yourusername/stock-hunter-dashboard.git
- cd stock-hunter-dashboard


### Step 2: Install Dependencies
- pip install -r requirements.txt


### Step 3: Run the Application
- streamlit run main.py


The app will open in your default browser at `http://localhost:8501`

## 📦 Requirements

Create a `requirements.txt` file with:

streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.23.0
yfinance>=0.2.28
pandas-ta>=0.3.14b0
streamlit-autorefresh>=0.0.1
pytz>=2023.3
requests>=2.31.0


## 📁 Project Structure

stock-hunter-dashboard/
├── main.py # Main application entry point
├── sidebar.py # Sidebar configuration & presets
├── ui_components.py # UI rendering components
├── scanning_logic.py # Stock scanning algorithms
├── functions.py # Core utility functions
├── paper.py # Paper trading module
├── trade_guide.py # Educational guide
├── styles.py # CSS styling
├── requirements.txt # Python dependencies
├── paper_trades.csv # Paper trading data (auto-generated)
└── README.md # This file


## 🎮 Usage Guide

### 1. **Configure Your Settings**

**Sidebar → Scanner Settings:**
- Choose **Scan Mode** (Early Detection or Confirmation)
- Set **Timeframe** (5m, 15m, 30m, 1h)
- Adjust **Signal Threshold** (4-10)
- Enable/disable filters (Volume, Breakout, EMA+RSI, RS)

**Or Load a Preset:**
- Select from 6 pre-configured strategies
- Modify and save custom presets

### 2. **Scan Stocks**

**Auto Scanner Tab:**
- Scanner automatically runs on page load
- View **Qualified Stocks** table
- Check **Technical Predictions** for detailed analysis
- Click **🟢 BUY** or **🔴 SELL** to setup trades

### 3. **Analyze Manually**

**Manual Analysis Tab:**
- Enter stock symbols (comma-separated)
- View comprehensive analysis with:
  - Visual progress bars for RSI/ADX
  - Trend direction indicators
  - Fundamental metrics
  - Educational notes

### 4. **Paper Trade**

**Paper Trading Tab:**
- Execute trades from scanner or manually
- Monitor live P/L
- Manage positions
- Track performance

### 5. **Learn & Improve**

**Trade Guide Tab:**
- Understand the scoring system
- Learn technical indicators
- Review trading strategies
- Master risk management

## 📊 Scoring System

**How Stocks are Scored (0-15 points):**

| Indicator | Max Points | Criteria |
|-----------|-----------|----------|
| Volume Surge | 3 | Z-score > threshold |
| Price Breakout | 3 | Above resistance |
| MACD Crossover | 2 | Bullish cross |
| RSI Momentum | 2 | Optimal range (50-70) |
| EMA Alignment | 2 | Price > EMA20 > EMA50 |
| ADX Strength | 1 | ADX > 25 |
| Consolidation | 1 | Tight range |
| Relative Strength | 1 | Outperforming market |

**Qualification:** Stocks scoring above your threshold are flagged as opportunities.

## ⚙️ Configuration Examples

### Intraday Trading
Scan Mode: Early Detection
Interval: 15m
Signal Threshold: 6
Stop Loss: 2.0%
Target: 5.0%


### Positional Trading
Scan Mode: Early Detection
Interval: 1h
Signal Threshold: 6
Stop Loss: 3.5%
Target: 10.0%


## 🔔 Notifications

### Desktop Notifications
Enable in sidebar → Notifications section

### Telegram Notifications
1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your Chat ID from [@userinfobot](https://t.me/userinfobot)
3. Enter Bot Token and Chat ID in sidebar
4. Enable Telegram notifications

## 🛡️ Risk Management

**Never risk more than 2% of capital per trade**

| Trading Style | Max Positions | Capital/Trade | Daily Loss Limit |
|--------------|---------------|---------------|------------------|
| Scalping | 2-3 | 5-10% | 1.5% |
| Intraday | 2-4 | 10-15% | 2% |
| Swing | 3-5 | 15-20% | 5% |
| Positional | 4-6 | 15-25% | 10% |
| Long-Term | 5-8 | 20-30% | No daily limit |

## 🎯 Best Trading Times (IST)

- **9:15-10:30 AM**: Opening volatility (Scalping, Intraday)
- **10:30 AM-2:00 PM**: Consolidation (Setup identification)
- **2:00-3:30 PM**: Afternoon push (Intraday, Swing entries)

## 🔧 Customization

### Add Custom Indicators
Edit `functions.py` → `compute_indicators()` function

### Create New Presets
1. Configure settings in sidebar
2. Enter preset name
3. Click "💾 Save as [name]"

### Modify Scoring Logic
Edit `scanning_logic.py` → `scan_stock_original()` or `scan_stock_early()`

## 📈 Performance Tips

1. **Start with Paper Trading** - Practice for 2 weeks minimum
2. **Use Conservative Presets** - Begin with higher thresholds
3. **Focus on Quality** - Don't chase every signal
4. **Keep a Journal** - Track your decisions and outcomes
5. **Review Weekly** - Analyze performance and adjust

## ⚠️ Important Notes

- **Market Hours**: Best results during NSE trading hours (9:15 AM - 3:30 PM IST)
- **Internet Required**: Fetches real-time data from Yahoo Finance
- **For Educational Use**: Not financial advice - use at your own risk
- **Paper Trade First**: Always test strategies before risking real money

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

**IMPORTANT:** This software is for educational and research purposes only. 

- This is **NOT financial advice**
- Past performance does not guarantee future results
- Trading stocks involves risk of loss
- The developers are not responsible for any financial losses
- Always consult with a qualified financial advisor
- Use paper trading to test strategies before risking real money

**By using this software, you acknowledge that you understand the risks involved in trading and accept full responsibility for your trading decisions.**

## 📞 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Email: your.email@example.com

## 🌟 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Market data from [Yahoo Finance](https://finance.yahoo.com/)
- Technical indicators via [Pandas TA](https://github.com/twopirllc/pandas-ta)

---

**Made with ❤️ for Indian stock traders**

**Happy Trading! 📈🚀**
**Vijay S**
