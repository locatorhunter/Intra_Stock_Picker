# 🎯 Stock Hunter - NSE Intraday Stock Screener

An advanced real-time stock screening application for Indian NSE F&O stocks with **dual scanning modes** - catch stocks at early momentum or wait for strong confirmation signals.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-red)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🌟 Features

### 📊 Dual Scanning Modes
- **🎯 Early Detection Mode (Recommended)**: Catches stocks in accumulation/consolidation phase BEFORE major breakouts
- **✅ Confirmation Mode**: Waits for strong confirmation signals (traditional approach)

### 🔍 Advanced Technical Indicators
- **MACD Crossovers** - Early reversal detection
- **RSI Multi-Level Analysis** - 50-65 range for early bullish momentum
- **Volume Accumulation** - Detects "smart money" buying before spikes
- **Consolidation Detection** - Tight ranges near highs (pre-breakout pattern)
- **ADX Trend Formation** - Identifies emerging trends (20-30 range)
- **Pre-Breakout Detection** - Alerts when stocks are within 1% of breakout levels
- **Relative Strength** - Outperformance vs NIFTY 50
- **Candlestick Patterns** - Bullish Engulfing, Morning Star

### 📈 Smart Entry/Exit Management
- **ATR-based Stop Loss** - Dynamic risk management
- **2:1 Risk-Reward Targets** - Automatic target calculation
- **Live Watchlist** - Track multiple positions with real-time alerts
- **Auto SL/Target Alerts** - Desktop & Telegram notifications

### 🔔 Multi-Channel Notifications
- **Desktop Notifications** (via Plyer)
- **Telegram Alerts** - Get signals on mobile
- **Real-time Price Tracking** - Auto-refresh mechanism

### 💾 Filter Presets
- Save/Load custom filter configurations
- Multiple preset profiles
- Quick strategy switching

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download
```bash
git clone https://github.com/yourusername/stock-hunter.git
cd stock-hunter
```

### Step 2: Install Dependencies
```bash
pip install streamlit pandas yfinance numpy requests plyer streamlit-autorefresh pytz ta-lib
```

**Note**: `TA-Lib` installation can be tricky on Windows. Follow [this guide](https://github.com/cgohlke/talib-build/releases) for pre-built wheels.

### Step 3: Run the Application
```bash
streamlit run stock_hunter_early.py
```

The app will open in your default browser at `http://localhost:8501`

---

## 📖 Usage Guide

### 🎯 Quick Start

1. **Select Scanning Mode**
   - Choose between "Early Detection" or "Confirmation" mode in sidebar
   - Early Detection: Best for catching moves early (lower risk, earlier entries)
   - Confirmation: Best for high-confidence signals (fewer false positives)

2. **Configure Filters**
   - Adjust volume thresholds, breakout margins, RSI ranges
   - Set signal score threshold (5-7 recommended for early detection)

3. **Set Notifications**
   - Enable Desktop notifications (instant alerts)
   - Add Telegram Bot Token & Chat ID for mobile alerts

4. **Start Scanning**
   - App auto-refreshes based on your interval setting
   - Shortlisted stocks appear in real-time
   - Add promising stocks to watchlist

### 🔧 Configuration Options

#### Filters & Parameters
| Parameter | Description | Recommended Range |
|-----------|-------------|-------------------|
| **Volume z-score** | Volume spike threshold | 1.2 - 2.0 (Early), 2.0+ (Confirm) |
| **Breakout margin** | Price above previous high | 0.2% (Early), 0.5%+ (Confirm) |
| **Signal threshold** | Minimum score to qualify | 5-7 (Early), 7-9 (Confirm) |
| **ATR period** | Volatility calculation window | 7-14 bars |
| **ATR multiplier** | Stop-loss distance | 0.8-1.5x ATR |

#### Notification Setup

**Telegram Configuration:**
1. Create bot via [@BotFather](https://t.me/botfather)
2. Get your Chat ID from [@userinfobot](https://t.me/userinfobot)
3. Enter credentials in Notification Settings
4. Test connection with "Test Telegram Alert" button

---

## 🎓 Understanding the Modes

### 🎯 Early Detection Mode

**Philosophy**: Catch stocks BEFORE the crowd notices them

**Key Signals**:
- MACD crossing above signal line (even if negative)
- RSI crossing 50 upward (not waiting for 70)
- Volume accumulation (1.2-2x average)
- Price consolidating within 3% near highs
- ADX rising from 20-30 (trend forming)
- Within 1% of breakout level

**Best For**:
- Swing traders
- Position traders
- Those who want to enter before major moves

**Risk Profile**: Medium (earlier entries mean more false signals, but better risk/reward)

### ✅ Confirmation Mode

**Philosophy**: Wait for strong confirmation before entering

**Key Signals**:
- RSI > 70 (strong momentum)
- Volume spike (2+ standard deviations)
- Confirmed breakout above previous high
- Price decisively above EMA20

**Best For**:
- Conservative traders
- Those who prefer fewer, higher-quality signals
- Day traders who want confirmed momentum

**Risk Profile**: Lower (fewer false signals, but entries come later)

---

## 📊 Score Breakdown

### Early Detection Scoring
| Signal | Points |
|--------|--------|
| MACD early reversal | 3 |
| Approaching breakout (<1%) | 3 |
| Volume accumulation | 2 |
| RSI early bullish (50-65) | 2 |
| Consolidation near highs | 2 |
| ADX trend forming | 2 |
| Fresh breakout | 2 |
| Price above EMA20 | 1 |
| Outperforming NIFTY | 1 |
| Candle patterns | 1 |

**Total Possible**: 13+ points

### Confirmation Mode Scoring
| Signal | Points |
|--------|--------|
| Volume spike (2+ SD) | 2 |
| Breakout confirmed | 2 |
| RSI > 70 | 2 |
| Price above EMA20 | 1 |
| Outperforming NIFTY | 1 |
| Candle patterns | 1 |

**Total Possible**: 7+ points

---

## 🛠️ Advanced Features

### Filter Presets
Save your favorite configurations:
1. Configure all parameters
2. Enter preset name
3. Click "💾 Save as '[name]'"
4. Load anytime from "⚙️ Saved Filters"

### Manual Analyzer
Test any stock manually:
1. Expand "📝 Manual Stock Analyzer"
2. Enter comma-separated symbols (e.g., `RELIANCE,TCS,INFY`)
3. View detailed analysis with entry/exit levels
4. Add to watchlist if qualified

### Watchlist Management
- Automatically tracks entry, SL, target prices
- Real-time alerts when SL/Target hit
- Remove stocks manually or auto-remove on exit
- Persists across page refreshes

---

## 📱 Screenshots

### Main Dashboard
```
┌─────────────────────────────────────────┐
│  🎯 Scan Strategy: Early Detection      │
│  ✅ Scanned 80 stocks. 5 qualified     │
├─────────────────────────────────────────┤
│  Symbol  | Score | Last | Entry | SL   │
│  RELIANCE|   8   | 2450 | 2450  | 2420 │
│  TCS     |   7   | 3560 | 3560  | 3540 │
└─────────────────────────────────────────┘
```

---

## 🔬 Technical Details

### Architecture
- **Frontend**: Streamlit (reactive UI)
- **Data Source**: Yahoo Finance API (yfinance)
- **Indicators**: TA-Lib (technical analysis)
- **Refresh**: Auto-refresh with configurable intervals
- **State Management**: Streamlit session state

### Scan Flow
```
1. Fetch batch data (5-day history, configured interval)
2. Compute indicators (EMA, RSI, MACD, ATR, ADX, Volume)
3. Apply selected mode logic (Early/Confirmation)
4. Calculate scores
5. Filter by threshold
6. Generate entry/SL/target
7. Send notifications
8. Update watchlist
```

### Performance
- **Scan Speed**: ~80 stocks in 10-15 seconds
- **Memory Usage**: ~200-300 MB
- **Cache**: 5-minute TTL for price data

---

## 🔒 Security & Privacy

- **No data storage**: All data is fetched real-time
- **No account required**: Works standalone
- **API credentials**: Only stored in session (not persisted)
- **Open source**: Review code for transparency

---

## 🐛 Troubleshooting

### TA-Lib Installation Fails
**Windows**:
```bash
pip install TA_Lib-0.4.28-cp39-cp39-win_amd64.whl
```
Download wheel from [here](https://github.com/cgohlke/talib-build/releases)

**macOS**:
```bash
brew install ta-lib
pip install ta-lib
```

**Linux**:
```bash
sudo apt-get install ta-lib
pip install ta-lib
```

### No Stocks Shortlisted
- Lower the "Signal score threshold"
- Adjust volume/breakout margins
- Try Early Detection mode
- Check if market is open (9:15 AM - 3:30 PM IST)

### Telegram Not Working
- Verify bot token is correct
- Ensure you've started a chat with the bot
- Check Chat ID is correct (should be a number)
- Click "Test Telegram Alert" button

### App Crashes/Freezes
- Reduce "Max F&O symbols to scan" (try 50)
- Increase auto-refresh interval (180-300 sec)
- Close other resource-heavy applications

---

## 📚 Resources

### Learning Materials
- [Technical Analysis Basics](https://www.investopedia.com/technical-analysis-4689657)
- [RSI Strategy Guide](https://www.investopedia.com/terms/r/rsi.asp)
- [MACD Explained](https://www.investopedia.com/terms/m/macd.asp)
- [Volume Analysis](https://www.investopedia.com/articles/technical/02/010702.asp)

### Related Tools
- [TradingView](https://www.tradingview.com/) - Charting
- [Screener.in](https://www.screener.in/) - Fundamental analysis
- [ChartInk](https://chartink.com/) - Advanced screeners

---

## ⚠️ Disclaimer

**This tool is for educational and informational purposes only.**

- Not financial advice
- Past performance doesn't guarantee future results
- Always do your own research (DYOR)
- Consult a registered financial advisor
- Use at your own risk
- Developer not liable for trading losses

**Trading involves substantial risk of loss.**

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add more technical indicators (Bollinger Bands, Stochastic)
- [ ] Support for custom stock lists
- [ ] Backtesting functionality
- [ ] Machine learning predictions
- [ ] Mobile app version
- [ ] Database integration for historical tracking

**How to contribute**:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Vijay S**

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Amazing framework
- [Yahoo Finance](https://finance.yahoo.com/) - Free market data
- [TA-Lib](https://ta-lib.org/) - Technical analysis library
- Trading community for inspiration and feedback

---

## 📈 Roadmap

### Version 2.0 (Planned)
- [ ] Backtesting engine with historical data
- [ ] Multi-timeframe analysis
- [ ] Options chain analysis
- [ ] Portfolio tracking
- [ ] Custom indicator builder
- [ ] Export to Excel/PDF

### Version 3.0 (Future)
- [ ] Machine learning price predictions
- [ ] Sentiment analysis from news/social media
- [ ] Paper trading simulation
- [ ] Discord/Slack integration
- [ ] Web API for mobile apps

---

## ⭐ Star History

If you find this project helpful, please consider giving it a star!

---

**Happy Trading! 📈🎯**

*Remember: The best trade is the one that fits YOUR strategy and risk tolerance.*
