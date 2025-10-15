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


### 🧠 Technical Prediction Module

If you enable **“Show Technical Predictions”** from the sidebar,  
the app analyzes shortlisted stocks for:

| Indicator | Meaning |
|------------|----------|
| **RSI (7)** | Detects overbought/oversold conditions |
| **Support / Resistance** | Checks proximity to key zones |
| **Double Top / Bottom** | Identifies reversal patterns |
| **Trend Line** | Finds short-term up/down trends |
| **Verdict** | Combines all factors into a clear bias (Buy / Sell / Neutral) |

This gives a quick high-level *directional view* before intraday entry.


Filter / Indicator          |  Calculation                                                    |  Condition For Pick            |  Purpose                       
----------------------------+-----------------------------------------------------------------+--------------------------------+--------------------------------
Volume Spike                |  Current volume vs 20-bar average volume × multiplier           |  Current volume > threshold    |  Identify unusual volume spikes
ATR Breakout                |  ATR value compared to percentile threshold × multiplier        |  ATR > threshold               |  Filter volatile stocks        
Relative Strength           |  % change stock close – % change NIFTY close over RS lookback   |  Difference > 0                |  Select outperforming stocks   
Price Breakout              |  Last close > max close of previous N bars (momentum lookback)  |  Last close > previous high    |  Detect breakout               
EMA20 + RSI10 Confirmation  |  Last close > EMA20 and RSI(10) > 50                            |  Both true                     |  Confirm bullish momentum      
RSI Indicator               |  RSI(7) with overbought and oversold zones                      |  RSI > 80 sell, RSI < 20 buy   |  Identify extreme momentum     
Support/Resistance Zones    |  Price within 1% of support or resistance from last 20 bars     |  Near support or resistance    |  Price action zones            
Double Tops / Bottoms       |  Pattern match on last 10 highs/lows                            |  Double top or bottom pattern  |  Potential reversal signals    
Trend Line                  |  Linear slope of last 15 closes                                 |  Positive slope = uptrend      |  Confirm trend direction       

Test Case  |  ATR Period  |  ATR Multiplier (Stop Loss)  |  Risk-Reward Ratio (Target)  |  Notes                           
-----------+--------------+------------------------------+------------------------------+----------------------------------
1          |  7           |  1.5                         |  2.0                         |  Faster stops, moderate RR       
2          |  7           |  2.0                         |  2.0                         |  Default aggressive stops        
3          |  10          |  1.5                         |  2.5                         |  Slightly smoother ATR, higher RR
4          |  10          |  2.0                         |  3.0                         |  Balanced TR and RR              
5          |  14          |  2.0                         |  2.0                         |  Smoother ATR, standard RR       
6          |  14          |  2.5                         |  3.5                         |  Conservative stops, high RR     
7          |  21          |  3.0                         |  4.0                         |  Long ATR period, wide stops     
8          |  7           |  1.0                         |  1.5                         |  Tighter stops, lower reward     

How to use:

Vary the ATR Period parameter (lookback length on ATR calculation).

Vary the ATR Multiplier which controls how far your stop loss is below entry price.

Vary the Risk-Reward Ratio which sets how far your target is from entry relative to stop loss risk.

| Parameter                        | Suggested Value                          | Why                                                                                                            |
| -------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Volume Spike Multiplier**      | `1.5x – 2x`                              | Filters only genuine spikes — e.g., if average 10-min volume = 100k, today’s bar should be >150k–200k.         |
| **ATR Period**                   | `14`                                     | Standard. Keeps volatility smooth.                                                                             |
| **ATR Multiplier for Stop Loss** | `1.8x – 2x`                              | A 2× buffer avoids getting stopped out by random intraday wiggles.                                             |
| **ATR Percentile Threshold**     | `30 – 40`                                | Keeps moderate-to-high volatility stocks; not too crazy, not dead.                                             |
| **Momentum Lookback (bars)**     | `20 – 40`                                | Captures a short trend burst (approx. last 30–60 mins on 5-min chart).                                         |
| **RSI (7)**                      | Overbought >80, Oversold <20, Neutral 50 | For intraday moves, RSI 7 reacts quickly — over 80 means “maybe short soon,” below 20 means “maybe long soon.” |
| **Double Bottom / Top**          | Confirm with volume divergence           | When RSI diverges or volume spikes near 2nd bottom/top — it’s a strong reversal clue.                          |
| **Support / Resistance**         | From 1D and 1H timeframe                 | For intraday, plot S/R from previous day’s highs/lows, not weekly.                                             |
| **Max F&O Symbols to Scan**      | `100–150`                                | Keeps your scanner efficient and avoids clutter.                                                               |
