"""
ui_components.py - UI display components for main content area
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from functions import extract_symbol_df, compute_indicators, remove_from_watchlist
from scanning_logic import scan_stock_original, scan_stock_early
from datetime import datetime
import pytz
import paper

IST = pytz.timezone("Asia/Kolkata")

def render_header(refresh_count, auto_refresh_sec, last_refresh_time, scan_mode):
    """Render the header banner"""
    st.markdown(f"""
    <div class="header-banner" style="
        margin-top:0px;
        padding:4px 12px;
        border-radius:10px;">
        <h1 style='font-size:22px; margin-bottom:4px;'>Stock Hunter Dashboard</h1>
        <p style='text-align:center; font-size:13px; margin-top:0px; line-height:1.3;'>
            ⏰ Refreshed <b>{refresh_count}</b> times |
            🔁 Interval: <b>{auto_refresh_sec}</b> sec |
            🕒 Last Run: <b>{last_refresh_time}</b> |
            ⚙️ Mode: <b>{scan_mode}</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_qualified_stocks(df_candidates, signal_score_threshold):
    """Render qualified stocks table"""
    with st.expander("📈 Qualified Stocks", expanded=True):
        qualified_df = df_candidates[df_candidates['Score'] >= signal_score_threshold]
        
        if len(qualified_df) > 0:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ {len(qualified_df)} qualified (of {len(df_candidates)} scanned) | Threshold: {signal_score_threshold}")
            with col2:
                st.download_button(
                    "💾 CSV",
                    qualified_df.to_csv(index=True),
                    file_name=f"qualified_{datetime.now(IST).strftime('%H%M%S')}.csv",
                    use_container_width=True
                )
            
            display_df = qualified_df.copy()
            
            for col in ['Last Close', 'Entry', 'Stop Loss', 'Target']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: f"₹{x:.1f}" if isinstance(x, (int, float)) else x
                    )
            
            display_df['Reasons'] = display_df['Reasons'].apply(
                lambda x: " | ".join([str(r)[:35] for r in x[:8]]) if isinstance(x, list) else str(x)[:50]
            )
            
            display_df = display_df.rename(columns={
                'Last Close': 'Last',
                'Stop Loss': 'SL',
                'Target': 'Tgt',
                'Reasons': 'Signals'
            })
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=min(400, len(qualified_df) * 35 + 38)
            )
        else:
            st.warning(f"No stocks qualified (Threshold: {signal_score_threshold})")

def render_technical_predictions(shortlisted_stocks, df_candidates, df_batch):
    """Ultra-compact technical predictions - minimal space usage"""
    with st.expander("🔮 Technical Predictions", expanded=True):
        if not shortlisted_stocks:
            st.info("No shortlisted stocks to show predictions for.")
            return
        
        for idx, stock in enumerate(shortlisted_stocks):
            # Get all data
            try:
                candidate_row = df_candidates.loc[stock]
                entry_for_wl = candidate_row['Entry']
                sl_for_wl = candidate_row['Stop Loss']
                target_for_wl = candidate_row['Target']
                score = candidate_row['Score']
                reasons = candidate_row['Reasons']
            except KeyError:
                continue
            
            df_for_pred = extract_symbol_df(df_batch, stock)
            if df_for_pred is None or df_for_pred.empty:
                continue
            
            df_for_pred = compute_indicators(df_for_pred)
            
            # Get technical values
            last_close = float(df_for_pred["Close"].iloc[-1])
            rsi7 = float(df_for_pred["RSI7"].dropna().iloc[-1]) if "RSI7" in df_for_pred and not df_for_pred["RSI7"].dropna().empty else np.nan
            ema20 = float(df_for_pred["EMA20"].iloc[-1]) if "EMA20" in df_for_pred else np.nan
            
            # Calculate R:R
            if isinstance(entry_for_wl, (int, float)) and isinstance(sl_for_wl, (int, float)) and isinstance(target_for_wl, (int, float)):
                sl_pct = ((entry_for_wl - sl_for_wl) / entry_for_wl) * 100
                target_pct = ((target_for_wl - entry_for_wl) / entry_for_wl) * 100
                risk_reward = f"{(target_pct / sl_pct):.1f}:1" if sl_pct > 0 else "N/A"
            else:
                risk_reward = "N/A"
            
            # Pre-format conditional values
            rsi_display = f"{rsi7:.0f}" if not np.isnan(rsi7) else "N/A"
            rsi_color = "#ef4444" if not np.isnan(rsi7) and rsi7 >= 70 else "#10b981" if not np.isnan(rsi7) and rsi7 >= 50 else "#f59e0b" if not np.isnan(rsi7) else "#94a3b8"
            
            # ========== ULTRA COMPACT CARD ==========
            compact_card = f"""
<div style="background:linear-gradient(90deg, #667eea 0%, #764ba2 100%);padding:12px;border-radius:8px;margin-bottom:12px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
<h3 style="color:white;margin:0;font-size:20px;">📊 {stock}</h3>
<div style="display:flex;gap:6px;">
<span style="background:rgba(255,255,255,0.2);color:white;padding:3px 8px;border-radius:12px;font-size:11px;">Score: {score}</span>
<span style="background:rgba(255,215,0,0.3);color:#ffd700;padding:3px 8px;border-radius:12px;font-size:11px;">R:R {risk_reward}</span>
</div>
</div>
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;font-size:12px;">
<div style="text-align:center;color:#e2e8f0;">
<div style="font-size:10px;color:#cbd5e1;">Last</div>
<div style="font-weight:600;">₹{last_close:.0f}</div>
</div>
<div style="text-align:center;color:#10b981;">
<div style="font-size:10px;color:#cbd5e1;">Entry</div>
<div style="font-weight:600;">₹{entry_for_wl:.0f}</div>
</div>
<div style="text-align:center;color:#ef4444;">
<div style="font-size:10px;color:#cbd5e1;">SL</div>
<div style="font-weight:600;">₹{sl_for_wl:.0f}</div>
</div>
<div style="text-align:center;color:#22c55e;">
<div style="font-size:10px;color:#cbd5e1;">Target</div>
<div style="font-weight:600;">₹{target_for_wl:.0f}</div>
</div>
<div style="text-align:center;color:{rsi_color};">
<div style="font-size:10px;color:#cbd5e1;">RSI</div>
<div style="font-weight:600;">{rsi_display}</div>
</div>
</div>
</div>
"""
            st.markdown(compact_card, unsafe_allow_html=True)
            
            # ========== COMPACT SIGNALS & BUTTONS ==========
            col_signals, col_buttons = st.columns([2.5, 1])

            with col_signals:
                reasons_list = reasons if isinstance(reasons, list) else [reasons]

                # Create compact colored badges
                badges_html = '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:2px;">'
                for reason in reasons_list:
                    reason_text = str(reason)
                    # Color coding
                    if "MACD" in reason_text or "reversal" in reason_text:
                        color = "#4CAF50"
                    elif "breakout" in reason_text or "Approaching" in reason_text:
                        color = "#FF9800"
                    elif "RSI" in reason_text:
                        color = "#2196F3"
                    elif "Volume" in reason_text:
                        color = "#9C27B0"
                    elif "Consolidating" in reason_text:
                        color = "#00BCD4"
                    elif "trend" in reason_text or "ADX" in reason_text:
                        color = "#FF5722"
                    elif "EMA" in reason_text or "Price above" in reason_text:
                        color = "#607D8B"
                    else:
                        color = "#757575"

                    badges_html += f'<span style="background:{color};color:white;padding:3px 7px;border-radius:10px;font-size:10px;font-weight:500;">{reason_text}</span>'

                badges_html += "</div>"
                st.markdown(badges_html, unsafe_allow_html=True)

            with col_buttons:
                # Compact button row
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                with btn_col1:
                    if st.button("🟢", key=f"buy_{stock}_{idx}", help="Buy", use_container_width=True):
                        st.session_state['pending_trade'] = {
                            'symbol': stock, 'action': 'BUY', 'entry': entry_for_wl,
                            'sl': sl_for_wl, 'target': target_for_wl, 'last_price': last_close,
                            'switch_to_paper': True
                        }
                        st.success(f"✅ {stock} ready for BUY!")
                
                with btn_col2:
                    if st.button("🔴", key=f"sell_{stock}_{idx}", help="Sell", use_container_width=True):
                        st.session_state['pending_trade'] = {
                            'symbol': stock, 'action': 'SELL', 'entry': entry_for_wl,
                            'sl': sl_for_wl, 'target': target_for_wl, 'last_price': last_close,
                            'switch_to_paper': True
                        }
                        st.success(f"✅ {stock} ready for SELL!")
                
                with btn_col3:
                    if stock in st.session_state.watchlist:
                        st.button("✅", key=f"in_wl_{stock}_{idx}", disabled=True, help="In Watchlist", use_container_width=True)
                    else:
                        if st.button("➕", key=f"add_wl_{stock}_{idx}", help="Add to Watchlist", use_container_width=True):
                            st.session_state.watchlist[stock] = {
                                "entry": entry_for_wl, "sl": sl_for_wl, "target": target_for_wl, "status": "Active"
                            }
                            st.success(f"Added {stock}!")
                            st.rerun()
            
                    # ========== COLLAPSIBLE DETAILS WITH VISUALS ==========
            with st.expander(f"📊 {stock} Details", expanded=False):
                try:
                    ticker = yf.Ticker(f"{stock}.NS")
                    info = ticker.info
                    
                    # Get all needed data
                    pe_ratio = info.get('trailingPE', 0)
                    eps = info.get('trailingEps', 0)
                    market_cap = info.get('marketCap', 0)
                    week_52_high = info.get('fiftyTwoWeekHigh', 0)
                    week_52_low = info.get('fiftyTwoWeekLow', 0)
                    sector = info.get('sector', 'N/A')
                    
                    # Pre-format all values BEFORE using in f-strings
                    pe_display = f"{pe_ratio:.1f}" if isinstance(pe_ratio, (int, float)) and pe_ratio > 0 else "N/A"
                    eps_display = f"₹{eps:.1f}" if isinstance(eps, (int, float)) and eps > 0 else "N/A"
                    mcap_display = f"₹{market_cap/10000000:.0f}Cr" if isinstance(market_cap, (int, float)) and market_cap > 0 else "N/A"
                    high_52w_display = f"₹{week_52_high:.0f}" if isinstance(week_52_high, (int, float)) and week_52_high > 0 else "N/A"
                    low_52w_display = f"₹{week_52_low:.0f}" if isinstance(week_52_low, (int, float)) and week_52_low > 0 else "N/A"
                    ema_display_detail = f"₹{ema20:.0f}" if not np.isnan(ema20) else "N/A"
                    
                    # Calculate position in 52W range
                    if isinstance(week_52_high, (int, float)) and isinstance(week_52_low, (int, float)) and week_52_high > 0 and week_52_low > 0:
                        range_position = ((last_close - week_52_low) / (week_52_high - week_52_low)) * 100
                    else:
                        range_position = 50
                    
                    # Price vs EMA
                    price_above_ema = not np.isnan(ema20) and last_close > ema20
                    ema_bg_color = "16,185,129" if price_above_ema else "239,68,68"
                    ema_border_color = "#10b981" if price_above_ema else "#ef4444"
                    ema_text_color = "#10b981" if price_above_ema else "#ef4444"
                    ema_status = "Above ↑" if price_above_ema else "Below ↓"
                    
                    col_fund, col_tech, col_chart = st.columns([1, 1, 1])
                    
                    # ========== FUNDAMENTALS WITH VISUAL CARDS ==========
                    with col_fund:
                        st.markdown("**📊 Fundamentals**")
                        
                        fund_visual = f"""
            <div style="background:rgba(59,130,246,0.1);padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #3b82f6;">
            <div style="display:flex;justify-content:space-between;">
            <span style="color:#93c5fd;font-size:11px;">P/E Ratio</span>
            <span style="color:white;font-size:14px;font-weight:700;">{pe_display}</span>
            </div>
            </div>
            <div style="background:rgba(16,185,129,0.1);padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #10b981;">
            <div style="display:flex;justify-content:space-between;">
            <span style="color:#6ee7b7;font-size:11px;">EPS (TTM)</span>
            <span style="color:white;font-size:14px;font-weight:700;">{eps_display}</span>
            </div>
            </div>
            <div style="background:rgba(168,85,247,0.1);padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #a855f7;">
            <div style="display:flex;justify-content:space-between;">
            <span style="color:#c4b5fd;font-size:11px;">Market Cap</span>
            <span style="color:white;font-size:14px;font-weight:700;">{mcap_display}</span>
            </div>
            </div>
            <div style="background:rgba(245,158,11,0.1);padding:10px;border-radius:6px;border-left:3px solid #f59e0b;">
            <div style="display:flex;justify-content:space-between;">
            <span style="color:#fcd34d;font-size:11px;">Sector</span>
            <span style="color:white;font-size:12px;font-weight:600;">{str(sector)[:15]}</span>
            </div>
            </div>
            """
                        st.markdown(fund_visual, unsafe_allow_html=True)
                    
                    # ========== TECHNICALS WITH PROGRESS BARS ==========
                    with col_tech:
                        st.markdown("**📈 Technical Indicators**")
                        
                        # RSI values
                        rsi_val = rsi7 if not np.isnan(rsi7) else 50
                        rsi_color = "#ef4444" if rsi_val >= 70 else "#10b981" if rsi_val >= 50 else "#f59e0b" if rsi_val >= 30 else "#3b82f6"
                        
                        tech_visual = f"""
            <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:#94a3b8;font-size:11px;">RSI(7)</span>
            <span style="color:white;font-size:12px;font-weight:600;">{rsi_display}</span>
            </div>
            <div style="background:#334155;border-radius:10px;height:8px;overflow:hidden;">
            <div style="background:{rsi_color};width:{rsi_val:.0f}%;height:100%;border-radius:10px;"></div>
            </div>
            </div>
            <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:#94a3b8;font-size:11px;">52W Position</span>
            <span style="color:white;font-size:12px;font-weight:600;">{range_position:.0f}%</span>
            </div>
            <div style="background:#334155;border-radius:10px;height:8px;overflow:hidden;">
            <div style="background:linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);width:{range_position:.0f}%;height:100%;border-radius:10px;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:2px;">
            <span style="color:#64748b;font-size:9px;">{low_52w_display}</span>
            <span style="color:#64748b;font-size:9px;">{high_52w_display}</span>
            </div>
            </div>
            <div style="background:rgba(99,102,241,0.1);padding:10px;border-radius:6px;margin-bottom:8px;border-left:3px solid #6366f1;">
            <div style="display:flex;justify-content:space-between;">
            <span style="color:#c7d2fe;font-size:11px;">EMA20</span>
            <span style="color:white;font-size:14px;font-weight:700;">{ema_display_detail}</span>
            </div>
            </div>
            <div style="background:rgba({ema_bg_color},0.1);padding:10px;border-radius:6px;border-left:3px solid {ema_border_color};">
            <div style="display:flex;justify-content:space-between;">
            <span style="color:#cbd5e1;font-size:11px;">Price vs EMA</span>
            <span style="color:{ema_text_color};font-size:14px;font-weight:700;">{ema_status}</span>
            </div>
            </div>
            """
                        st.markdown(tech_visual, unsafe_allow_html=True)
                    
                    # ========== QUICK ACTIONS ==========
                    with col_chart:
                        st.markdown("**Price History**")
                        
                        # Quick stats in cards
                        quick_stats = f"""
            <div style="margin-top:12px;">
            <div style="background:rgba(34,197,94,0.1);padding:8px;border-radius:6px;margin-bottom:6px;">
            <div style="color:#86efac;font-size:10px;">52W High</div>
            <div style="color:#22c55e;font-size:16px;font-weight:700;">{high_52w_display}</div>
            </div>
            <div style="background:rgba(239,68,68,0.1);padding:8px;border-radius:6px;margin-bottom:6px;">
            <div style="color:#fca5a5;font-size:10px;">52W Low</div>
            <div style="color:#ef4444;font-size:16px;font-weight:700;">{low_52w_display}</div>
            </div>
            <div style="background:rgba(99,102,241,0.1);padding:8px;border-radius:6px;">
            <div style="color:#c7d2fe;font-size:10px;">Current Price</div>
            <div style="color:#818cf8;font-size:16px;font-weight:700;">₹{last_close:.0f}</div>
            </div>
            </div>
            """
                        st.markdown(quick_stats, unsafe_allow_html=True)
                
                except Exception as e:
                    st.error(f"Unable to load details: {str(e)}")
#########################
# Manual Analysis Section
#########################
def render_manual_search(df_batch, settings):
    """Enhanced manual stock analyzer with comprehensive details"""
    with st.expander("🔍 Manual Stock Analyzer", expanded=True):
        
        # ========== HEADER WITH INLINE SETTINGS ==========
        header_html = f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;padding:12px;
            background:linear-gradient(90deg, #667eea 0%, #764ba2 100%);border-radius:8px;">
<h3 style="color:white;margin:0;font-size:20px;">🔍 Search & Analyze Stocks</h3>
<div style="display:flex;gap:12px;">
<div style="background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:12px;">
<span style="color:rgba(255,255,255,0.7);font-size:10px;">MODE</span>
<div style="color:white;font-weight:700;font-size:13px;">{settings['scan_mode']}</div>
</div>
<div style="background:rgba(255,215,0,0.3);padding:6px 12px;border-radius:12px;">
<span style="color:rgba(255,215,0,0.7);font-size:10px;">THRESHOLD</span>
<div style="color:#ffd700;font-weight:700;font-size:13px;">{settings['signal_score_threshold']}</div>
</div>
</div>
</div>
"""
        st.markdown(header_html, unsafe_allow_html=True)
        
        # ========== INPUT SECTION ==========
        manual_symbols = st.text_input(
            "📊 Enter stock symbols (comma-separated)",
            placeholder="e.g., RELIANCE, TCS, INFY, HDFCBANK, WIPRO",
            help="Enter multiple symbols separated by commas for batch analysis"
        )
        
        manual_list = [s.strip().upper() for s in manual_symbols.split(',') if s.strip()] if manual_symbols else []
        
        if not manual_list:
            st.info("💡 **How to use:** Enter stock symbols above to analyze. You can analyze multiple stocks at once!")
            st.markdown("""
            **Analysis includes:**
            - 📊 Technical Indicators (RSI, MACD, EMA, ADX)
            - 📈 Trend Analysis (Momentum, Strength, Direction)
            - 🎯 Entry, Stop Loss, and Target suggestions
            - 💼 Fundamental metrics
            - 🔔 Real-time scoring based on your filter settings
            """)
            return
        
        # Show analysis count
        st.success(f"🔍 Analyzing **{len(manual_list)}** stock{'s' if len(manual_list) > 1 else ''}...")
        
        for idx, manual_symbol in enumerate(manual_list):
            # Get data
            df_manual = extract_symbol_df(df_batch, manual_symbol)
            
            if df_manual is None or df_manual.empty:
                @st.cache_data(ttl=300)
                def get_single(sym, interval_local):
                    try:
                        dd = yf.download(f"{sym}.NS", period="5d", interval=interval_local, progress=False)
                        return dd
                    except Exception:
                        return pd.DataFrame()
                
                df_manual = get_single(manual_symbol, settings['interval'])
            
            if df_manual is None or df_manual.empty:
                st.warning(f"⚠️ No data available for **{manual_symbol}**")
                continue
            
            # Compute indicators
            df_manual = compute_indicators(df_manual)
            
            # Run scan
            scan_function = scan_stock_early if settings['scan_mode'] == "Early Detection 🐇" else scan_stock_original
            
            score, reasons, entry, stop_loss, target, signal = scan_function(
                manual_symbol, df_manual,
                nifty_df=None,
                use_volume=settings['use_volume'],
                use_breakout=settings['use_breakout'],
                use_ema_rsi=settings['use_ema_rsi'],
                use_rs=settings['use_rs'],
                vol_zscore_threshold=settings['vol_zscore_threshold'],
                breakout_margin_pct=settings['breakout_margin_pct'],
                momentum_lookback=settings['momentum_lookback'],
                rs_lookback=settings['rs_lookback'],
                atr_mult=settings['atr_mult'],
                atr_period=settings['atr_period']
            )
            
            # Get all technical values
            last_price = float(df_manual["Close"].iloc[-1])
            volume = float(df_manual["Volume"].iloc[-1]) if "Volume" in df_manual else 0
            rsi7 = float(df_manual["RSI7"].dropna().iloc[-1]) if "RSI7" in df_manual and not df_manual["RSI7"].dropna().empty else np.nan
            rsi10 = float(df_manual["RSI10"].dropna().iloc[-1]) if "RSI10" in df_manual and not df_manual["RSI10"].dropna().empty else np.nan
            ema20 = float(df_manual["EMA20"].iloc[-1]) if "EMA20" in df_manual else np.nan
            ema50 = float(df_manual["EMA50"].iloc[-1]) if "EMA50" in df_manual else np.nan
            macd = float(df_manual["MACD"].iloc[-1]) if "MACD" in df_manual and not np.isnan(df_manual["MACD"].iloc[-1]) else np.nan
            macd_signal = float(df_manual["MACD_signal"].iloc[-1]) if "MACD_signal" in df_manual and not np.isnan(df_manual["MACD_signal"].iloc[-1]) else np.nan
            adx = float(df_manual["ADX"].iloc[-1]) if "ADX" in df_manual and not np.isnan(df_manual["ADX"].iloc[-1]) else np.nan
            atr = float(df_manual["ATR"].iloc[-1]) if "ATR" in df_manual and not np.isnan(df_manual["ATR"].iloc[-1]) else np.nan
            
            # Get fundamentals
            try:
                ticker = yf.Ticker(f"{manual_symbol}.NS")
                info = ticker.info
                pe_ratio = info.get('trailingPE', 0)
                market_cap = info.get('marketCap', 0)
                week_52_high = info.get('fiftyTwoWeekHigh', 0)
                week_52_low = info.get('fiftyTwoWeekLow', 0)
                sector = info.get('sector', 'N/A')
            except:
                pe_ratio = market_cap = week_52_high = week_52_low = 0
                sector = 'N/A'
            
            # Calculate additional metrics
            if isinstance(entry, (int, float)) and isinstance(stop_loss, (int, float)) and isinstance(target, (int, float)):
                sl_pct = ((entry - stop_loss) / entry) * 100
                target_pct = ((target - entry) / entry) * 100
                risk_reward = f"{(target_pct / sl_pct):.1f}:1" if sl_pct > 0 else "N/A"
            else:
                sl_pct = target_pct = 0
                risk_reward = "N/A"
            
            # Format displays
            entry_display = f"₹{entry:.0f}" if entry else "N/A"
            sl_display = f"₹{stop_loss:.0f}" if stop_loss else "N/A"
            target_display = f"₹{target:.0f}" if target else "N/A"
            
            # Qualification status
            qualified = score >= settings['signal_score_threshold']
            status_bg = "#059669" if qualified else "#dc2626"
            status_text = "✅ QUALIFIED" if qualified else "❌ NOT QUALIFIED"
            status_emoji = "🎯" if qualified else "⚠️"
            
            # 52W position
            if week_52_high and week_52_low and week_52_high > week_52_low:
                range_position = ((last_price - week_52_low) / (week_52_high - week_52_low)) * 100
            else:
                range_position = 50
            
            # ========== COMPREHENSIVE ANALYSIS CARD ==========
            analysis_card = f"""
<div style="background:linear-gradient(135deg, {status_bg} 0%, {"#10b981" if qualified else "#ef4444"} 100%);
padding:18px;border-radius:12px;margin-bottom:18px;box-shadow:0 6px 16px rgba(0,0,0,0.4);">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
<div>
<h2 style="color:white;margin:0 0 4px 0;font-size:28px;">{status_emoji} {manual_symbol}</h2>
<span style="color:rgba(255,255,255,0.8);font-size:12px;">{sector}</span>
</div>
<div style="display:flex;gap:8px;flex-direction:column;align-items:flex-end;">
<span style="background:rgba(255,255,255,0.25);color:white;padding:5px 12px;border-radius:14px;font-size:13px;font-weight:700;">
Score: {score}/{settings['signal_score_threshold']}
</span>
<span style="background:rgba(255,255,255,0.25);color:white;padding:5px 12px;border-radius:14px;font-size:12px;font-weight:700;">
{status_text}
</span>
</div>
</div>

<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:12px;">
<div style="background:rgba(255,255,255,0.15);padding:10px;border-radius:8px;text-align:center;">
<div style="color:rgba(255,255,255,0.7);font-size:10px;margin-bottom:2px;">LAST PRICE</div>
<div style="color:white;font-weight:700;font-size:18px;">₹{last_price:.0f}</div>
</div>
<div style="background:rgba(16,185,129,0.3);padding:10px;border-radius:8px;text-align:center;border:1px solid rgba(16,185,129,0.5);">
<div style="color:rgba(255,255,255,0.7);font-size:10px;margin-bottom:2px;">ENTRY</div>
<div style="color:white;font-weight:700;font-size:18px;">{entry_display}</div>
</div>
<div style="background:rgba(239,68,68,0.3);padding:10px;border-radius:8px;text-align:center;border:1px solid rgba(239,68,68,0.5);">
<div style="color:rgba(255,255,255,0.7);font-size:10px;margin-bottom:2px;">STOP LOSS</div>
<div style="color:white;font-weight:700;font-size:18px;">{sl_display}</div>
<div style="color:rgba(255,255,255,0.6);font-size:9px;">{f"-{sl_pct:.1f}%" if sl_pct > 0 else ""}</div>
</div>
<div style="background:rgba(34,197,94,0.3);padding:10px;border-radius:8px;text-align:center;border:1px solid rgba(34,197,94,0.5);">
<div style="color:rgba(255,255,255,0.7);font-size:10px;margin-bottom:2px;">TARGET</div>
<div style="color:white;font-weight:700;font-size:18px;">{target_display}</div>
<div style="color:rgba(255,255,255,0.6);font-size:9px;">{f"+{target_pct:.1f}%" if target_pct > 0 else ""}</div>
</div>
<div style="background:rgba(245,158,11,0.3);padding:10px;border-radius:8px;text-align:center;border:1px solid rgba(245,158,11,0.5);">
<div style="color:rgba(255,255,255,0.7);font-size:10px;margin-bottom:2px;">R:R RATIO</div>
<div style="color:white;font-weight:700;font-size:18px;">{risk_reward}</div>
</div>
<div style="background:rgba(139,92,246,0.3);padding:10px;border-radius:8px;text-align:center;border:1px solid rgba(139,92,246,0.5);">
<div style="color:rgba(255,255,255,0.7);font-size:10px;margin-bottom:2px;">52W POS</div>
<div style="color:white;font-weight:700;font-size:18px;">{range_position:.0f}%</div>
</div>
</div>
</div>
"""
            st.markdown(analysis_card, unsafe_allow_html=True)
            
            # ========== SIGNAL REASONS ==========
            if reasons:
                st.markdown("#### 🎯 Detection Signals")
                reasons_list = reasons if isinstance(reasons, list) else [reasons]
                
                badges_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px;">'
                for reason in reasons_list:
                    reason_text = str(reason)
                    if "MACD" in reason_text:
                        color = "#4CAF50"
                    elif "breakout" in reason_text or "Approaching" in reason_text:
                        color = "#FF9800"
                    elif "RSI" in reason_text:
                        color = "#2196F3"
                    elif "Volume" in reason_text:
                        color = "#9C27B0"
                    elif "Consolidating" in reason_text:
                        color = "#00BCD4"
                    elif "trend" in reason_text or "ADX" in reason_text:
                        color = "#FF5722"
                    elif "EMA" in reason_text or "Price above" in reason_text:
                        color = "#607D8B"
                    else:
                        color = "#757575"
                    
                    badges_html += f'<span style="background:{color};color:white;padding:6px 12px;border-radius:14px;font-size:11px;font-weight:500;box-shadow:0 2px 4px rgba(0,0,0,0.2);">{reason_text}</span>'
                
                badges_html += "</div>"
                st.markdown(badges_html, unsafe_allow_html=True)
            else:
                st.info(f"ℹ️ No signals detected for {manual_symbol}. Stock doesn't meet current filter criteria (Threshold: {settings['signal_score_threshold']}).")
            
                # ========== DETAILED TECHNICAL ANALYSIS (CONTINUED) ==========
                
                col_momentum, col_trend, col_strength, col_fundamentals = st.columns(4)
                
                # === MOMENTUM INDICATORS ===
                with col_momentum:
                    st.markdown("#### 📈 Momentum")
                    
                    # RSI Analysis
                    rsi_val = rsi7 if not np.isnan(rsi7) else 50
                    rsi10_val = rsi10 if not np.isnan(rsi10) else 50
                    rsi_color = "#ef4444" if rsi_val >= 70 else "#10b981" if rsi_val >= 50 else "#f59e0b" if rsi_val >= 30 else "#3b82f6"
                    rsi_status = "Overbought ⚠️" if rsi_val >= 70 else "Bullish ✅" if rsi_val >= 50 else "Neutral ⚖️" if rsi_val >= 30 else "Oversold 🔻"
                    rsi_note = "Strong momentum" if rsi_val >= 70 else "Positive" if rsi_val >= 50 else "Weak" if rsi_val >= 30 else "Very weak"
                    
                    rsi_html = f"""
<div style="background:rgba(255,255,255,0.03);padding:12px;border-radius:8px;margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;margin-bottom:6px;">
<span style="color:#94a3b8;font-size:12px;font-weight:600;">RSI (7)</span>
<span style="color:white;font-size:14px;font-weight:700;">{rsi_val:.1f}</span>
</div>
<div style="background:#1e293b;border-radius:8px;height:10px;overflow:hidden;margin-bottom:6px;">
<div style="background:{rsi_color};width:{rsi_val:.0f}%;height:100%;transition:width 0.3s;"></div>
</div>
<div style="display:flex;justify-content:space-between;margin-bottom:8px;">
<span style="color:{rsi_color};font-size:11px;font-weight:600;">{rsi_status}</span>
<span style="color:#64748b;font-size:10px;">{rsi_note}</span>
</div>
<div style="padding:6px 8px;background:rgba(59,130,246,0.1);border-radius:6px;border-left:2px solid #3b82f6;">
<span style="color:#93c5fd;font-size:9px;">💡 RSI > 70: Overbought (sell signal)</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 RSI 50-70: Bullish (strong)</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 RSI 30-50: Neutral (wait)</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 RSI < 30: Oversold (buy signal)</span>
</div>
</div>

<div style="background:rgba(255,255,255,0.03);padding:10px;border-radius:8px;">
<div style="display:flex;justify-content:space-between;">
<span style="color:#94a3b8;font-size:11px;">RSI (10)</span>
<span style="color:white;font-size:13px;font-weight:600;">{rsi10_val:.1f}</span>
</div>
</div>
"""
                    st.markdown(rsi_html, unsafe_allow_html=True)
                
                # === TREND INDICATORS ===
                with col_trend:
                    st.markdown("#### 📉 Trend Direction")
                    
                    # EMA Analysis
                    ema_diff = ((last_price - ema20) / ema20 * 100) if not np.isnan(ema20) else 0
                    ema50_diff = ((last_price - ema50) / ema50 * 100) if not np.isnan(ema50) else 0
                    ema_status = "Above ✅" if ema_diff > 0 else "Below ❌"
                    ema_color = "#10b981" if ema_diff > 0 else "#ef4444"
                    ema_note = "Strong uptrend" if ema_diff > 2 else "Uptrend" if ema_diff > 0 else "Downtrend" if ema_diff > -2 else "Strong downtrend"
                    
                    # MACD Analysis
                    macd_diff = macd - macd_signal if not np.isnan(macd) and not np.isnan(macd_signal) else 0
                    macd_status = "Bullish ✅" if macd_diff > 0 else "Bearish ❌"
                    macd_color = "#10b981" if macd_diff > 0 else "#ef4444"
                    macd_strength = "Strong" if abs(macd_diff) > 1 else "Moderate" if abs(macd_diff) > 0.5 else "Weak"
                    
                    trend_html = f"""
<div style="background:rgba(255,255,255,0.03);padding:12px;border-radius:8px;margin-bottom:10px;">
<div style="margin-bottom:12px;">
<div style="display:flex;justify-content:space-between;margin-bottom:4px;">
<span style="color:#94a3b8;font-size:12px;font-weight:600;">Price vs EMA20</span>
<span style="color:{ema_color};font-size:12px;font-weight:600;">{ema_status}</span>
</div>
<div style="color:white;font-size:14px;font-weight:700;margin-bottom:2px;">
{f"₹{ema20:.0f}" if not np.isnan(ema20) else "N/A"} ({ema_diff:+.1f}%)
</div>
<span style="color:#64748b;font-size:10px;">{ema_note}</span>
</div>

<div style="padding:8px;background:rgba(99,102,241,0.1);border-radius:6px;margin-bottom:8px;border-left:2px solid #6366f1;">
<div style="display:flex;justify-content:space-between;margin-bottom:4px;">
<span style="color:#94a3b8;font-size:11px;">EMA50</span>
<span style="color:white;font-size:12px;font-weight:600;">{f"₹{ema50:.0f}" if not np.isnan(ema50) else "N/A"}</span>
</div>
<span style="color:#64748b;font-size:9px;">Diff: {ema50_diff:+.1f}%</span>
</div>

<div style="padding:8px;background:rgba({macd_color[1:]},0.1);border-radius:6px;margin-bottom:8px;border-left:2px solid {macd_color};">
<div style="display:flex;justify-content:space-between;margin-bottom:2px;">
<span style="color:#94a3b8;font-size:11px;font-weight:600;">MACD</span>
<span style="color:{macd_color};font-size:11px;font-weight:600;">{macd_status}</span>
</div>
<div style="display:flex;justify-content:space-between;">
<span style="color:#64748b;font-size:9px;">Signal: {f"{macd_signal:.2f}" if not np.isnan(macd_signal) else "N/A"}</span>
<span style="color:#64748b;font-size:9px;">{macd_strength}</span>
</div>
</div>

<div style="padding:6px 8px;background:rgba(59,130,246,0.1);border-radius:6px;border-left:2px solid #3b82f6;">
<span style="color:#93c5fd;font-size:9px;">💡 Price > EMA: Bullish trend</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 MACD > Signal: Upward momentum</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 EMA20 > EMA50: Strong uptrend</span>
</div>
</div>
"""
                    st.markdown(trend_html, unsafe_allow_html=True)
                
                # === STRENGTH INDICATORS ===
                with col_strength:
                    st.markdown("#### 💪 Trend Strength")
                    
                    # ADX Analysis
                    adx_val = adx if not np.isnan(adx) else 0
                    adx_status = "Strong 💪" if adx_val >= 25 else "Moderate ⚖️" if adx_val >= 20 else "Weak 🔻"
                    adx_color = "#10b981" if adx_val >= 25 else "#f59e0b" if adx_val >= 20 else "#ef4444"
                    adx_note = "Strong trending market" if adx_val >= 25 else "Developing trend" if adx_val >= 20 else "Ranging/No clear trend"
                    adx_advice = "Good for trend trading" if adx_val >= 25 else "Wait for confirmation" if adx_val >= 20 else "Avoid trend trades"
                    
                    # ATR Analysis
                    atr_val = atr if not np.isnan(atr) else 0
                    atr_pct = (atr_val / last_price * 100) if last_price > 0 else 0
                    volatility_level = "High" if atr_pct > 3 else "Medium" if atr_pct > 1.5 else "Low"
                    
                    strength_html = f"""
<div style="background:rgba(255,255,255,0.03);padding:12px;border-radius:8px;margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;margin-bottom:6px;">
<span style="color:#94a3b8;font-size:12px;font-weight:600;">ADX (Trend Strength)</span>
<span style="color:white;font-size:14px;font-weight:700;">{adx_val:.1f}</span>
</div>
<div style="background:#1e293b;border-radius:8px;height:10px;overflow:hidden;margin-bottom:6px;">
<div style="background:{adx_color};width:{min(adx_val * 2, 100):.0f}%;height:100%;transition:width 0.3s;"></div>
</div>
<div style="display:flex;justify-content:space-between;margin-bottom:8px;">
<span style="color:{adx_color};font-size:11px;font-weight:600;">{adx_status}</span>
<span style="color:#64748b;font-size:10px;">{adx_note}</span>
</div>
<div style="padding:6px 8px;background:rgba(59,130,246,0.1);border-radius:6px;border-left:2px solid #3b82f6;margin-bottom:10px;">
<span style="color:#93c5fd;font-size:9px;">💡 ADX > 25: {adx_advice}</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 ADX 20-25: Moderate strength</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 ADX < 20: Weak/ranging market</span>
</div>

<div style="padding:10px;background:rgba(168,85,247,0.1);border-radius:6px;border-left:2px solid #a855f7;">
<div style="display:flex;justify-content:space-between;margin-bottom:2px;">
<span style="color:#c4b5fd;font-size:11px;font-weight:600;">ATR (Volatility)</span>
<span style="color:white;font-size:13px;font-weight:600;">₹{atr_val:.2f}</span>
</div>
<div style="display:flex;justify-content:space-between;">
<span style="color:#a78bfa;font-size:9px;">{atr_pct:.2f}% of price</span>
<span style="color:#a78bfa;font-size:9px;">{volatility_level} volatility</span>
</div>
</div>
</div>
"""
                    st.markdown(strength_html, unsafe_allow_html=True)
                
                # === FUNDAMENTALS ===
                with col_fundamentals:
                    st.markdown("#### 💼 Fundamentals")
                    
                    # Format displays
                    pe_display = f"{pe_ratio:.1f}" if isinstance(pe_ratio, (int, float)) and pe_ratio > 0 else "N/A"
                    mcap_display = f"₹{market_cap/10000000:.0f}Cr" if isinstance(market_cap, (int, float)) and market_cap > 0 else "N/A"
                    high_52w = f"₹{week_52_high:.0f}" if week_52_high > 0 else "N/A"
                    low_52w = f"₹{week_52_low:.0f}" if week_52_low > 0 else "N/A"
                    
                    # PE evaluation
                    pe_status = "Overvalued" if isinstance(pe_ratio, (int, float)) and pe_ratio > 30 else "Fair" if isinstance(pe_ratio, (int, float)) and pe_ratio > 15 else "Undervalued" if isinstance(pe_ratio, (int, float)) else "N/A"
                    pe_color = "#ef4444" if pe_status == "Overvalued" else "#f59e0b" if pe_status == "Fair" else "#10b981"
                    
                    fundamentals_html = f"""
<div style="background:rgba(59,130,246,0.08);padding:10px;border-radius:8px;margin-bottom:8px;border-left:3px solid #3b82f6;">
<div style="display:flex;justify-content:space-between;margin-bottom:2px;">
<span style="color:#93c5fd;font-size:11px;">P/E Ratio</span>
<span style="color:white;font-size:13px;font-weight:700;">{pe_display}</span>
</div>
<span style="color:{pe_color};font-size:9px;">{pe_status}</span>
</div>

<div style="background:rgba(168,85,247,0.08);padding:10px;border-radius:8px;margin-bottom:8px;border-left:3px solid #a855f7;">
<div style="display:flex;justify-content:space-between;">
<span style="color:#c4b5fd;font-size:11px;">Market Cap</span>
<span style="color:white;font-size:13px;font-weight:700;">{mcap_display}</span>
</div>
</div>

<div style="background:rgba(34,197,94,0.08);padding:10px;border-radius:8px;margin-bottom:8px;border-left:3px solid #22c55e;">
<div style="display:flex;justify-content:space-between;margin-bottom:2px;">
<span style="color:#86efac;font-size:11px;">52W High</span>
<span style="color:white;font-size:13px;font-weight:700;">{high_52w}</span>
</div>
<div style="display:flex;justify-content:space-between;">
<span style="color:#6ee7b7;font-size:9px;">Distance</span>
<span style="color:#6ee7b7;font-size:9px;">{((week_52_high - last_price) / last_price * 100):.1f}% away</span>
</div>
</div>

<div style="background:rgba(239,68,68,0.08);padding:10px;border-radius:8px;margin-bottom:8px;border-left:3px solid #ef4444;">
<div style="display:flex;justify-content:space-between;margin-bottom:2px;">
<span style="color:#fca5a5;font-size:11px;">52W Low</span>
<span style="color:white;font-size:13px;font-weight:700;">{low_52w}</span>
</div>
<div style="display:flex;justify-content:space-between;">
<span style="color:#f87171;font-size:9px;">Distance</span>
<span style="color:#f87171;font-size:9px;">{((last_price - week_52_low) / last_price * 100):.1f}% above</span>
</div>
</div>

<div style="padding:6px 8px;background:rgba(59,130,246,0.1);border-radius:6px;border-left:2px solid #3b82f6;">
<span style="color:#93c5fd;font-size:9px;">💡 P/E < 15: Undervalued</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 Near 52W high: Bullish</span><br>
<span style="color:#93c5fd;font-size:9px;">💡 Near 52W low: Bearish</span>
</div>
"""
                    st.markdown(fundamentals_html, unsafe_allow_html=True)
            
            # ========== ACTION BUTTONS ==========
            st.markdown("#### 🎬 Quick Actions")
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
            
            with col_btn1:
                if st.button("🟢 Setup Buy Trade", key=f"buy_manual_{manual_symbol}_{idx}", use_container_width=True, type="primary"):
                    st.session_state['pending_trade'] = {
                        'symbol': manual_symbol, 'action': 'BUY',
                        'entry': entry if entry else last_price,
                        'sl': stop_loss if stop_loss else last_price * 0.98,
                        'target': target if target else last_price * 1.04,
                        'last_price': last_price, 'switch_to_paper': True
                    }
                    st.success(f"✅ {manual_symbol} ready for BUY! Go to Paper Trading tab.")
            
            with col_btn2:
                if st.button("🔴 Setup Sell Trade", key=f"sell_manual_{manual_symbol}_{idx}", use_container_width=True):
                    st.session_state['pending_trade'] = {
                        'symbol': manual_symbol, 'action': 'SELL',
                        'entry': entry if entry else last_price,
                        'sl': stop_loss if stop_loss else last_price * 1.02,
                        'target': target if target else last_price * 0.96,
                        'last_price': last_price, 'switch_to_paper': True
                    }
                    st.success(f"✅ {manual_symbol} ready for SELL! Go to Paper Trading tab.")
            
            with col_btn3:
                if manual_symbol in st.session_state.watchlist:
                    st.button("✅ In Watchlist", key=f"in_wl_manual_{manual_symbol}_{idx}", disabled=True, use_container_width=True)
                else:
                    if st.button("➕ Add to Watchlist", key=f"add_manual_{manual_symbol}_{idx}", use_container_width=True):
                        entry_to_save = entry if entry else last_price
                        sl_to_save = stop_loss if stop_loss else last_price * 0.98
                        target_to_save = target if target else last_price * 1.04
                        
                        st.session_state.watchlist[manual_symbol] = {
                            "entry": entry_to_save, "sl": sl_to_save,
                            "target": target_to_save, "status": "Active"
                        }
                        st.success(f"✅ Added {manual_symbol} to watchlist!")
                        st.rerun()
            
            with col_btn4:
                if st.button("📈 Open TradingView", key=f"chart_manual_{manual_symbol}_{idx}", use_container_width=True):
                    st.markdown(f'<a href="https://www.tradingview.com/chart/?symbol=NSE%3A{manual_symbol}" target="_blank">Open Chart →</a>', unsafe_allow_html=True)
            
            st.markdown("---")


def render_watchlist(df_batch):
    """Render watchlist section"""
    with st.expander("📑 Watchlist & Alerts - Click to manage trades", expanded=True):
        st.markdown("<div class='watchlist-container'>", unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
        with col1:
            st.markdown("**Symbol**")
        with col2:
            st.markdown("**Entry**")
        with col3:
            st.markdown("**Stop Loss**")
        with col4:
            st.markdown("**Target**")
        with col5:
            st.markdown("**Status**")
        with col6:
            st.markdown("**Action**")
        
        for sym, info in st.session_state.watchlist.items():
            try:
                df_watch = extract_symbol_df(df_batch, sym)
            except Exception:
                df_watch = pd.DataFrame()
            
            entry_val = info.get("entry", "N/A")
            sl_val = info.get("sl", "N/A")
            tgt_val = info.get("target", "N/A")
            status = info.get("status", "Active")
            
            entry = f"₹{entry_val:.2f}" if isinstance(entry_val, (float, int)) else entry_val
            sl = f"₹{sl_val:.2f}" if isinstance(sl_val, (float, int)) else sl_val
            tgt = f"₹{tgt_val:.2f}" if isinstance(tgt_val, (float, int)) else tgt_val
            
            col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
            with col1:
                st.markdown(f"**{sym}**")
            with col2:
                st.markdown(f"{entry}")
            with col3:
                st.markdown(f"{sl}")
            with col4:
                st.markdown(f"{tgt}")
            with col5:
                st.markdown(f"{status}")
            with col6:
                st.button("🗑️ Remove", key=f"remove_{sym}", 
                         on_click=remove_from_watchlist, args=(sym,))
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.info("📌 Page auto-refresh will re-check alerts and prices.")


def render_paper_trading_tab():
    """Render Paper Trading tab with pre-filled trade from scanner"""
    st.title("📊 Paper Trading")
    
    # Check if there's a pending trade from scanner
    if st.session_state.get('pending_trade') and st.session_state['pending_trade'].get('switch_to_paper'):
        trade = st.session_state['pending_trade']
        
        st.success(f"🎯 Trade Ready: {trade['action']} {trade['symbol']}")
        
        # Display trade card
        trade_card = f"""
        <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding:20px;border-radius:12px;margin-bottom:20px;">
            <h2 style="color:white;margin-bottom:15px;">
                {'🟢 BUY' if trade['action'] == 'BUY' else '🔴 SELL'} {trade['symbol']}
            </h2>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                <div style="background:rgba(255,255,255,0.15);padding:12px;border-radius:8px;text-align:center;">
                    <div style="color:#ddd;font-size:11px;">ENTRY</div>
                    <div style="color:white;font-size:20px;font-weight:700;">₹{trade['entry']:.2f}</div>
                </div>
                <div style="background:rgba(255,255,255,0.15);padding:12px;border-radius:8px;text-align:center;">
                    <div style="color:#ddd;font-size:11px;">STOP LOSS</div>
                    <div style="color:#ff6b6b;font-size:20px;font-weight:700;">₹{trade['sl']:.2f}</div>
                </div>
                <div style="background:rgba(255,255,255,0.15);padding:12px;border-radius:8px;text-align:center;">
                    <div style="color:#ddd;font-size:11px;">TARGET</div>
                    <div style="color:#51cf66;font-size:20px;font-weight:700;">₹{trade['target']:.2f}</div>
                </div>
            </div>
        </div>
        """
        st.markdown(trade_card, unsafe_allow_html=True)
        
        # Quantity input
        st.markdown("### Enter Trade Details")
        quantity = st.number_input("📦 Quantity", min_value=1, value=1, step=1, key="paper_qty")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Execute Trade", use_container_width=True, type="primary"):
                # Execute trade using paper module
                try:
                    paper.execute_trade(
                        symbol=trade['symbol'],
                        action=trade['action'],
                        quantity=quantity,
                        price=trade['entry'],
                        sl=trade['sl'],
                        target=trade['target']
                    )
                    st.success(f"✅ {trade['action']} {quantity} x {trade['symbol']} @ ₹{trade['entry']:.2f}")
                    st.balloons()
                    # Clear pending trade
                    st.session_state['pending_trade'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Trade execution failed: {e}")
        
        with col2:
            if st.button("❌ Cancel Trade", use_container_width=True):
                st.session_state['pending_trade'] = None
                st.rerun()
        
        with col3:
            if st.button("🔄 Modify Levels", use_container_width=True):
                st.session_state['pending_trade']['switch_to_paper'] = False
                st.info("You can now modify entry, SL, and target below.")
    
    else:
        st.info("No pending trade. Use the scanner to find opportunities or enter trade details manually below.")
    
    # Manual trade entry section
    st.markdown("---")
    st.markdown("### Manual Trade Entry")
    
    col_manual1, col_manual2 = st.columns(2)
    
    with col_manual1:
        manual_symbol = st.text_input("Stock Symbol", "")
        manual_action = st.selectbox("Action", ["BUY", "SELL"])
        manual_quantity = st.number_input("Quantity", min_value=1, value=1)
    
    with col_manual2:
        manual_entry = st.number_input("Entry Price", min_value=0.0, value=0.0, step=0.1)
        manual_sl = st.number_input("Stop Loss", min_value=0.0, value=0.0, step=0.1)
        manual_target = st.number_input("Target", min_value=0.0, value=0.0, step=0.1)
    
    if st.button("📝 Place Manual Order", use_container_width=True):
        if manual_symbol and manual_entry > 0:
            try:
                paper.execute_trade(manual_symbol, manual_action, manual_quantity, manual_entry, manual_sl, manual_target)
                st.success(f"✅ Manual {manual_action} order placed for {manual_quantity} x {manual_symbol}")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please fill in all required fields!")
