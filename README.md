# NSE Intraday Stock Picker

## 🧪 Preset Test Combinations

The app provides **12 ready-to-use test combos** to cover different intraday trading scenarios.  

| # | Name | Interval | Filters | Target Type | Notes |
|---|------|---------|--------|------------|------|
| 1 | Aggressive 5m All Filters | 5m | All True | ATR-based | Very sensitive, all filters enabled for high-quality signals |
| 2 | 5m Volume+Breakout+EMA-RSI | 5m | Volume, Breakout, EMA-RSI | Fixed % | Moderate aggressiveness, volume spike + breakout + trend |
| 3 | 5m EMA-RSI only | 5m | EMA-RSI | Fixed Rs | Trend-only, safer intraday setup |
| 4 | 15m All Filters | 15m | All True | ATR-based | Standard intraday, smoother than 5m |
| 5 | 15m Vol+ATR+RS | 15m | Volume, ATR, RS | Fixed % | Mid-volatility, combines momentum and strength |
| 6 | 15m EMA-RSI+Breakout | 15m | EMA-RSI + Breakout | Fixed Rs | Trend-following + breakout, moderate safety |
| 7 | 30m EMA-RSI only | 30m | EMA-RSI | ATR-based | Slower trend-following |
| 8 | 30m EMA-RSI+RS | 30m | EMA-RSI + RS | Fixed % | Trend + relative strength, moderate risk |
| 9 | 30m ATR+Breakout | 30m | ATR + Breakout | Fixed Rs | Momentum breakouts for larger moves |
| 10 | 1h EMA-RSI+RS | 1h | EMA-RSI + RS | ATR-based | Long intraday, slower signal, trend-confirmed |
| 11 | 1h EMA-RSI only | 1h | EMA-RSI | Fixed % | Minimal filters, selective setup |
| 12 | 5m Aggressive Max Sensitivity | 5m | All True | Fixed % | Aggressive breakout + volume + ATR, max sensitivity |

### 🔹 Notes:
- **Intervals:** 5m = sensitive, 15m = standard, 30m = slower, 1h = very selective  
- **Filters:** Volume Spike, ATR Breakout, EMA-RSI Trend, Technical Breakout, Relative Strength  
- **Profit Targets:**  
  - ATR-based → adapts to volatility  
  - Fixed % → fixed percentage of entry price  
  - Fixed Rs → fixed points amount for target  
- These presets allow **fast testing of multiple scenarios** without manually adjusting sliders or checkboxes.
