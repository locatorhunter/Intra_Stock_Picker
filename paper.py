# ---------------------------
# paper.py - Enhanced Paper Trading Module
# ---------------------------

import streamlit as st
import pandas as pd
import yfinance as yf
import os
from datetime import datetime
import pytz

TRADES_FILE = "paper_trades.csv"
IST = pytz.timezone("Asia/Kolkata")

def ensure_csv_exists():
    """Ensure CSV file exists with proper headers"""
    if not os.path.exists(TRADES_FILE):
        # Create empty CSV with headers
        df = pd.DataFrame(columns=["Symbol", "Qty", "Type", "Entry", "StopLoss", "Target", "Status", "Time"])
        df.to_csv(TRADES_FILE, index=False)
    else:
        # Check if file is empty or corrupted
        try:
            df = pd.read_csv(TRADES_FILE)
            if df.empty or len(df.columns) == 0:
                raise pd.errors.EmptyDataError
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            # Recreate with headers
            df = pd.DataFrame(columns=["Symbol", "Qty", "Type", "Entry", "StopLoss", "Target", "Status", "Time"])
            df.to_csv(TRADES_FILE, index=False)

# ---------------------------
# Initialization & Persistence
# ---------------------------
def init_paper_trades():
    """Initialize trade session & load from CSV with error handling"""
    if "trades" not in st.session_state:
        if os.path.exists(TRADES_FILE):
            try:
                # Try to read the CSV file
                df = pd.read_csv(TRADES_FILE)
                
                # Check if DataFrame is valid
                if df.empty or len(df.columns) == 0:
                    st.session_state.trades = []
                else:
                    st.session_state.trades = df.to_dict("records")
            except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                # If file is corrupted or empty, start fresh
                print(f"Warning: Trade history file corrupted. Starting fresh. Error: {e}")
                st.session_state.trades = []
                # Remove the corrupted file
                try:
                    os.remove(TRADES_FILE)
                except:
                    pass
            except Exception as e:
                # Catch any other errors
                print(f"Error loading trades: {e}")
                st.session_state.trades = []
        else:
            st.session_state.trades = []

def save_trades():
    """Save trades to CSV persistently with error handling"""
    try:
        if "trades" in st.session_state and st.session_state.trades:
            df = pd.DataFrame(st.session_state.trades)
            df.to_csv(TRADES_FILE, index=False)
        elif "trades" in st.session_state and not st.session_state.trades:
            # If trades list is empty, create empty CSV with headers
            df = pd.DataFrame(columns=["Symbol", "Qty", "Type", "Entry", "StopLoss", "Target", "Status", "Time"])
            df.to_csv(TRADES_FILE, index=False)
    except Exception as e:
        print(f"Error saving trades: {e}")
        st.error(f"Failed to save trades: {e}")


# ---------------------------
# Execute Trade Function
# ---------------------------
def execute_trade(symbol, action, quantity, price, sl=0.0, target=0.0):
    """Execute a trade from the scanner or manual entry"""
    init_paper_trades()
    
    trade = {
        "Symbol": symbol.upper(),
        "Qty": quantity,
        "Type": action.upper(),
        "Entry": price,
        "StopLoss": sl if sl > 0 else price * 0.97,
        "Target": target if target > 0 else price * 1.05,
        "Status": "OPEN",
        "Time": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state.trades.append(trade)
    save_trades()
    return True

# ---------------------------
# Delete Closed Trades
# ---------------------------
def clear_closed_trades():
    """Remove all closed trades from history"""
    st.session_state.trades = [t for t in st.session_state.trades if t["Status"].startswith("OPEN")]
    save_trades()

# ---------------------------
# Manual Trade Entry Form
# ---------------------------
def paper_trade_manual():
    """Enhanced manual trade entry with better UI"""
    st.markdown("### 📝 Quick Trade Entry")
    
    # Compact form layout
    with st.form("manual_trade_form", clear_on_submit=True):
        col_input1, col_input2 = st.columns(2)
        
        with col_input1:
            symbol = st.text_input("📊 Stock Symbol", placeholder="e.g., TCS, RELIANCE", 
                                  help="Enter NSE stock symbol")
            action = st.selectbox("📈 Action", ["BUY", "SELL"], help="Trade direction")
            quantity = st.number_input("📦 Quantity", min_value=1, value=10, step=1)
        
        with col_input2:
            entry = st.number_input("💰 Entry Price (₹)", min_value=0.0, value=0.0, step=0.5, 
                                   help="Entry price per share")
            sl = st.number_input("🛑 Stop Loss (₹)", min_value=0.0, value=0.0, step=0.5,
                                help="Stop loss price (optional)")
            target = st.number_input("🎯 Target (₹)", min_value=0.0, value=0.0, step=0.5,
                                    help="Target price (optional)")
        
        # Calculate metrics
        if entry > 0:
            sl_actual = sl if sl > 0 else entry * 0.97
            target_actual = target if target > 0 else entry * 1.05
            
            risk = abs(entry - sl_actual)
            reward = abs(target_actual - entry)
            rr_ratio = reward / risk if risk > 0 else 0
            
            st.info(f"💡 Risk: ₹{risk:.2f}/share | Reward: ₹{reward:.2f}/share | R:R = {rr_ratio:.2f}:1")
        
        submitted = st.form_submit_button("✅ Place Order", use_container_width=True, type="primary")
        
        if submitted:
            if symbol and entry > 0:
                execute_trade(symbol.upper(), action, quantity, entry, sl, target)
                st.success(f"✅ {action} order placed: {quantity} x {symbol.upper()} @ ₹{entry:.2f}")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Please enter valid symbol and entry price!")

# ---------------------------
# Display Active Trades
# ---------------------------
def display_paper_trades():
    """Display active trades with live P/L tracking"""
    init_paper_trades()
    
    if not st.session_state.get("trades"):
        st.info("📭 No trades yet. Use the scanner or manual entry to place trades.")
        return
    
    df_trades = pd.DataFrame(st.session_state.trades)
    open_trades_df = df_trades[df_trades["Status"].str.startswith("OPEN")]
    
    if not open_trades_df.empty:
        st.markdown("## 📊 Active Positions")
        
        # Fetch live prices
        live_prices = {}
        progress_placeholder = st.empty()
        
        for i, sym in enumerate(open_trades_df["Symbol"].unique()):
            progress_placeholder.text(f"Fetching prices... {i+1}/{len(open_trades_df['Symbol'].unique())}")
            try:
                data = yf.Ticker(sym + ".NS").history(period="1d", interval="5m")
                live_prices[sym] = float(data["Close"].iloc[-1]) if not data.empty else 0
            except:
                live_prices[sym] = open_trades_df.loc[open_trades_df["Symbol"] == sym, "Entry"].values[0]
        
        progress_placeholder.empty()
        
        # Map current prices
        df_trades["CurrentPrice"] = df_trades["Symbol"].map(live_prices)
        
        # Calculate P/L
        def calculate_pl(row):
            if row["Type"] == "BUY":
                return (row["CurrentPrice"] - row["Entry"]) * row["Qty"]
            else:
                return (row["Entry"] - row["CurrentPrice"]) * row["Qty"]
        
        df_trades["P/L (₹)"] = df_trades.apply(calculate_pl, axis=1)
        df_trades["P/L (%)"] = (df_trades["P/L (₹)"] / (df_trades["Entry"] * df_trades["Qty"])) * 100
        
        # Auto-close logic
        for t in st.session_state.trades:
            if t["Status"].startswith("OPEN"):
                sym = t["Symbol"]
                try:
                    cp = df_trades.loc[df_trades["Symbol"] == sym, "CurrentPrice"].values[0]
                except:
                    continue
                
                if t["Type"] == "BUY":
                    if t["Target"] and cp >= t["Target"]:
                        t["Status"] = "CLOSED (Target Hit)"
                        pl = (cp - t["Entry"]) * t["Qty"]
                        st.success(f"🎯 Target hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f}")
                    elif t["StopLoss"] and cp <= t["StopLoss"]:
                        t["Status"] = "CLOSED (Stop Loss Hit)"
                        pl = (cp - t["Entry"]) * t["Qty"]
                        st.error(f"❌ Stop loss hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f}")
                
                elif t["Type"] == "SELL":
                    if t["Target"] and cp <= t["Target"]:
                        t["Status"] = "CLOSED (Target Hit)"
                        pl = (t["Entry"] - cp) * t["Qty"]
                        st.success(f"🎯 Target hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f}")
                    elif t["StopLoss"] and cp >= t["StopLoss"]:
                        t["Status"] = "CLOSED (Stop Loss Hit)"
                        pl = (t["Entry"] - cp) * t["Qty"]
                        st.error(f"❌ Stop loss hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f}")
        
        save_trades()
        
        # Display trades table
        open_trades_display = df_trades[df_trades["Status"].str.startswith("OPEN")].copy()
        
        if not open_trades_display.empty:
            # Format for display
            display_cols = ["Symbol", "Type", "Entry", "CurrentPrice", "Qty", "StopLoss", "Target", "P/L (₹)", "P/L (%)", "Time"]
            
            for col in ["Entry", "CurrentPrice", "StopLoss", "Target"]:
                open_trades_display[col] = open_trades_display[col].apply(
                    lambda x: f"₹{x:.2f}" if x > 0 else "-"
                )
            
            open_trades_display["P/L (₹)"] = open_trades_display["P/L (₹)"].apply(
                lambda x: f"₹{x:.2f}" if pd.notna(x) else "-"
            )
            open_trades_display["P/L (%)"] = open_trades_display["P/L (%)"].apply(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "-"
            )
            
            st.dataframe(
                open_trades_display[display_cols],
                use_container_width=True,
                height=min(450, len(open_trades_display) * 40 + 50)
            )
            
            # Summary metrics
            st.markdown("### 📈 Portfolio Summary")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            total_pl = df_trades[df_trades["Status"].str.startswith("OPEN")]["P/L (₹)"].sum()
            total_investment = (df_trades[df_trades["Status"].str.startswith("OPEN")]["Entry"] * 
                               df_trades[df_trades["Status"].str.startswith("OPEN")]["Qty"]).sum()
            total_current = (df_trades[df_trades["Status"].str.startswith("OPEN")]["CurrentPrice"] * 
                            df_trades[df_trades["Status"].str.startswith("OPEN")]["Qty"]).sum()
            
            with col_m1:
                st.metric("💰 Total P/L", f"₹{total_pl:.2f}", 
                         delta=f"{total_pl:.2f}", 
                         delta_color="normal")
            
            with col_m2:
                st.metric("💼 Investment", f"₹{total_investment:.2f}")
            
            with col_m3:
                st.metric("📊 Current Value", f"₹{total_current:.2f}")
            
            with col_m4:
                open_count = len(open_trades_display)
                st.metric("🔓 Open Trades", open_count)
        
        else:
            st.info("✅ No open positions. All trades closed.")
    
    else:
        st.info("✅ No open trades currently.")
    
    # Show closed trades
    closed_trades = df_trades[~df_trades["Status"].str.startswith("OPEN")]
    
    if not closed_trades.empty:
        st.markdown("---")
        col_header, col_clear = st.columns([4, 1])
        
        with col_header:
            st.markdown(f"### 📜 Trade History ({len(closed_trades)} closed)")
        
        with col_clear:
            if st.button("🗑️ Clear History", use_container_width=True, help="Remove all closed trades"):
                clear_closed_trades()
                st.success("✅ Trade history cleared!")
                st.rerun()
        
        with st.expander("View Closed Trades", expanded=False):
            display_closed = closed_trades[["Symbol", "Type", "Entry", "Qty", "Status", "Time"]].copy()
            display_closed["Entry"] = display_closed["Entry"].apply(lambda x: f"₹{x:.2f}")
            st.dataframe(display_closed, use_container_width=True)

# ---------------------------
# Manage Open Trades
# ---------------------------
def manage_paper_trades():
    """Enhanced trade management with better UI"""
    init_paper_trades()
    
    open_trades = [t for t in st.session_state.trades if t["Status"].startswith("OPEN")]
    
    if not open_trades:
        return
    
    st.markdown("---")
    st.markdown("## ⚙️ Manage Open Positions")
    
    for i, t in enumerate(st.session_state.trades):
        if t["Status"].startswith("OPEN"):
            # Create card for each trade
            trade_card = f"""
            <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:8px; 
            margin-bottom:10px; border-left:4px solid {"#10b981" if t['Type']=='BUY' else "#ef4444"};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
            <span style="font-size:18px; font-weight:700; color:white;">{t['Symbol']}</span>
            <span style="margin-left:10px; background:{"rgba(16,185,129,0.3)" if t['Type']=='BUY' else "rgba(239,68,68,0.3)"}; 
            color:{"#10b981" if t['Type']=='BUY' else "#ef4444"}; padding:2px 8px; 
            border-radius:12px; font-size:11px; font-weight:600;">{t['Type']}</span>
            </div>
            <div style="text-align:right;">
            <div style="font-size:12px; color:#9ca3af;">Qty: {t['Qty']}</div>
            <div style="font-size:12px; color:#9ca3af;">Entry: ₹{t['Entry']:.2f}</div>
            </div>
            </div>
            <div style="margin-top:8px; font-size:11px; color:#d1d5db;">
            🎯 Target: ₹{t['Target']:.2f} | 🛑 SL: ₹{t['StopLoss']:.2f}
            </div>
            </div>
            """            
            col_card, col_btn = st.columns([5, 1])
            
            with col_card:
                # ⚠️ CRITICAL: Add unsafe_allow_html=True here too
                st.markdown(trade_card, unsafe_allow_html=True)
            
            with col_btn:
                if st.button("❌ Close", key=f"close_trade_{i}", use_container_width=True):
                    st.session_state.trades[i]["Status"] = "CLOSED (Manual)"
                    st.success(f"✅ {t['Symbol']} closed manually")
                    save_trades()
                    st.rerun()


# ---------------------------
# Complete Paper Trading Interface
# ---------------------------
def paper_trading_interface():
    """Complete enhanced paper trading interface"""
    init_paper_trades()
    
    # Check for pending trade from scanner
    if st.session_state.get('pending_trade') and st.session_state['pending_trade'].get('switch_to_paper'):
        trade = st.session_state['pending_trade']
        
        st.markdown("## 🎯 Quick Execute from Scanner")
        
        # Beautiful trade card
        action_color = "#10b981" if trade['action'] == 'BUY' else "#ef4444"
        action_emoji = "🟢" if trade['action'] == 'BUY' else "🔴"
        
        trade_card = f"""
        <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding:24px;border-radius:14px;margin-bottom:20px;box-shadow:0 6px 16px rgba(0,0,0,0.4);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
        <h2 style="color:white;margin:0;font-size:32px;">{action_emoji} {trade['action']} {trade['symbol']}</h2>
        <div style="background:rgba(255,255,255,0.2);padding:8px 16px;border-radius:20px;">
        <span style="color:white;font-size:14px;font-weight:600;">Last: ₹{trade['last_price']:.2f}</span>
        </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;">
        <div style="background:rgba(16,185,129,0.3);padding:14px;border-radius:10px;text-align:center;border:2px solid rgba(16,185,129,0.6);">
        <div style="color:#6ee7b7;font-size:12px;margin-bottom:5px;font-weight:600;">💰 ENTRY</div>
        <div style="color:#10b981;font-size:22px;font-weight:800;">₹{trade['entry']:.2f}</div>
        </div>
        <div style="background:rgba(239,68,68,0.3);padding:14px;border-radius:10px;text-align:center;border:2px solid rgba(239,68,68,0.6);">
        <div style="color:#fca5a5;font-size:12px;margin-bottom:5px;font-weight:600;">🛑 STOP LOSS</div>
        <div style="color:#ef4444;font-size:22px;font-weight:800;">₹{trade['sl']:.2f}</div>
        </div>
        <div style="background:rgba(34,197,94,0.3);padding:14px;border-radius:10px;text-align:center;border:2px solid rgba(34,197,94,0.6);">
        <div style="color:#86efac;font-size:12px;margin-bottom:5px;font-weight:600;">🎯 TARGET</div>
        <div style="color:#22c55e;font-size:22px;font-weight:800;">₹{trade['target']:.2f}</div>
        </div>
        </div>
        </div>
        """

        st.markdown(trade_card, unsafe_allow_html=True)

        
        # Quick execution
        col_qty, col_btn1, col_btn2 = st.columns([2, 1, 1])
        
        with col_qty:
            quantity = st.number_input("📦 Quantity", min_value=1, value=1, step=1, key="quick_qty")
        
        with col_btn1:
            if st.button("✅ Execute", use_container_width=True, type="primary"):
                try:
                    execute_trade(trade['symbol'], trade['action'], quantity, 
                                 trade['entry'], trade['sl'], trade['target'])
                    st.success(f"✅ {trade['action']} {quantity} x {trade['symbol']} @ ₹{trade['entry']:.2f}")
                    st.balloons()
                    st.session_state['pending_trade'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed: {e}")
        
        with col_btn2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state['pending_trade'] = None
                st.rerun()
        
        st.markdown("---")
    
    # Display active trades
    display_paper_trades()
    
    st.markdown("---")
    
    # Manual entry
    paper_trade_manual()
    
    # Manage trades
    manage_paper_trades()
