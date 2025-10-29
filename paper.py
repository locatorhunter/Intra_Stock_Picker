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
# paper.py - Enhanced display_paper_trades function

def display_paper_trades():
    """Display all active and closed trades with comprehensive details"""
    init_paper_trades()
    
    st.markdown("## 🧾 Active Trades")
    
    if not st.session_state.get("trades"):
        st.info("📭 No trades placed yet. Use the scanner or manual entry to place trades.")
        return
    
    df_trades = pd.DataFrame(st.session_state.trades)
    open_trades = df_trades[df_trades["Status"].str.startswith("OPEN")]
    
    if not open_trades.empty:
        # Fetch live prices
        live_prices = {}
        progress_placeholder = st.empty()
        
        for i, sym in enumerate(open_trades["Symbol"].unique()):
            progress_placeholder.text(f"Fetching prices... {i+1}/{len(open_trades['Symbol'].unique())}")
            try:
                data = yf.Ticker(sym + ".NS").history(period="1d", interval="5m")
                live_prices[sym] = float(data["Close"].iloc[-1]) if not data.empty else 0
            except:
                live_prices[sym] = open_trades.loc[open_trades["Symbol"] == sym, "Entry"].values[0]
        
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
        
        # Calculate additional metrics
        df_trades["Investment"] = df_trades["Entry"] * df_trades["Qty"]
        df_trades["Current Value"] = df_trades["CurrentPrice"] * df_trades["Qty"]
        df_trades["Risk (₹)"] = abs(df_trades["Entry"] - df_trades["StopLoss"]) * df_trades["Qty"]
        df_trades["Potential Gain (₹)"] = abs(df_trades["Target"] - df_trades["Entry"]) * df_trades["Qty"]
        
        # Calculate distance to SL and Target
        def calc_sl_distance(row):
            if row["Type"] == "BUY":
                return ((row["CurrentPrice"] - row["StopLoss"]) / row["CurrentPrice"] * 100) if row["StopLoss"] > 0 else 0
            else:
                return ((row["StopLoss"] - row["CurrentPrice"]) / row["CurrentPrice"] * 100) if row["StopLoss"] > 0 else 0
        
        def calc_target_distance(row):
            if row["Type"] == "BUY":
                return ((row["Target"] - row["CurrentPrice"]) / row["CurrentPrice"] * 100) if row["Target"] > 0 else 0
            else:
                return ((row["CurrentPrice"] - row["Target"]) / row["CurrentPrice"] * 100) if row["Target"] > 0 else 0
        
        df_trades["SL Distance (%)"] = df_trades.apply(calc_sl_distance, axis=1)
        df_trades["Target Distance (%)"] = df_trades.apply(calc_target_distance, axis=1)
        
        # ========== AUTO-CLOSE LOGIC - CORRECTED ==========
        for t in st.session_state.trades:
            if t["Status"].startswith("OPEN"):
                sym = t["Symbol"]
                try:
                    cp = df_trades.loc[df_trades["Symbol"] == sym, "CurrentPrice"].values[0]
                except:
                    continue
                
                if t["Type"] == "BUY":
                    if t["Target"] and cp >= t["Target"]:
                        pl = (cp - t["Entry"]) * t["Qty"]
                        pl_pct = ((cp - t["Entry"]) / t["Entry"] * 100)
                        t["Status"] = "CLOSED (Target Hit)"
                        t["Exit Price"] = float(cp)
                        t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                        t["Final P/L"] = float(pl)
                        t["P/L %"] = float(pl_pct)
                        st.success(f"🎯 Target hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
                    elif t["StopLoss"] and cp <= t["StopLoss"]:
                        pl = (cp - t["Entry"]) * t["Qty"]
                        pl_pct = ((cp - t["Entry"]) / t["Entry"] * 100)
                        t["Status"] = "CLOSED (Stop Loss Hit)"
                        t["Exit Price"] = float(cp)
                        t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                        t["Final P/L"] = float(pl)
                        t["P/L %"] = float(pl_pct)
                        st.error(f"❌ Stop loss hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
                
                elif t["Type"] == "SELL":
                    if t["Target"] and cp <= t["Target"]:
                        pl = (t["Entry"] - cp) * t["Qty"]
                        pl_pct = ((t["Entry"] - cp) / t["Entry"] * 100)
                        t["Status"] = "CLOSED (Target Hit)"
                        t["Exit Price"] = float(cp)
                        t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                        t["Final P/L"] = float(pl)
                        t["P/L %"] = float(pl_pct)
                        st.success(f"🎯 Target hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
                    elif t["StopLoss"] and cp >= t["StopLoss"]:
                        pl = (t["Entry"] - cp) * t["Qty"]
                        pl_pct = ((t["Entry"] - cp) / t["Entry"] * 100)
                        t["Status"] = "CLOSED (Stop Loss Hit)"
                        t["Exit Price"] = float(cp)
                        t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                        t["Final P/L"] = float(pl)
                        t["P/L %"] = float(pl_pct)
                        st.error(f"❌ Stop loss hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
        
        save_trades()
        

        
        # Display active trades with comprehensive details
        open_trades_display = df_trades[df_trades["Status"].str.startswith("OPEN")].copy()
        
        if not open_trades_display.empty:
            # Format for display
            display_cols = [
                "Symbol", "Type", "Entry", "CurrentPrice", "Qty", 
                "StopLoss", "Target", "Investment", "Current Value",
                "P/L (₹)", "P/L (%)", "SL Distance (%)", "Target Distance (%)",
                "Risk (₹)", "Potential Gain (₹)", "Time"
            ]
            
            # Format currency columns
            for col in ["Entry", "CurrentPrice", "StopLoss", "Target", "Investment", "Current Value", "P/L (₹)", "Risk (₹)", "Potential Gain (₹)"]:
                open_trades_display[col] = open_trades_display[col].apply(
                    lambda x: f"₹{x:.2f}" if x > 0 else "-"
                )
            
            # Format percentage columns
            for col in ["P/L (%)", "SL Distance (%)", "Target Distance (%)"]:
                open_trades_display[col] = open_trades_display[col].apply(
                    lambda x: f"{x:.2f}%" if pd.notna(x) else "-"
                )
            
            # Color-coded display with tabs
            tab_table, tab_visual = st.tabs(["📊 Table View", "📈 Visual Dashboard"])
            
            with tab_table:
                st.dataframe(
                    open_trades_display[display_cols],
                    use_container_width=True,
                    height=min(450, len(open_trades_display) * 40 + 50)
                )
            
            with tab_visual:
                # Visual cards for each trade
                for idx, row in open_trades_display.iterrows():
                    pl_value = df_trades.loc[idx, "P/L (₹)"]
                    pl_pct = df_trades.loc[idx, "P/L (%)"]
                    pl_color = "#10b981" if pl_value > 0 else "#ef4444" if pl_value < 0 else "#94a3b8"
                    
                    trade_card = f"""
<div style="background:rgba(255,255,255,0.03);padding:16px;border-radius:10px;margin-bottom:12px;
            border-left:4px solid {pl_color};">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
<div>
<h3 style="color:white;margin:0;font-size:20px;">{row['Symbol']} 
<span style="background:{"rgba(16,185,129,0.3)" if df_trades.loc[idx, "Type"]=="BUY" else "rgba(239,68,68,0.3)"};
             color:{"#10b981" if df_trades.loc[idx, "Type"]=="BUY" else "#ef4444"};
             padding:2px 8px;border-radius:10px;font-size:12px;margin-left:8px;">
{df_trades.loc[idx, "Type"]}
</span>
</h3>
<span style="color:#94a3b8;font-size:11px;">Qty: {df_trades.loc[idx, "Qty"]} | Entry: ₹{df_trades.loc[idx, "Entry"]:.2f}</span>
</div>
<div style="text-align:right;">
<div style="color:{pl_color};font-size:24px;font-weight:700;">₹{pl_value:.2f}</div>
<div style="color:{pl_color};font-size:12px;">{pl_pct:.2f}%</div>
</div>
</div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px;">
<div style="background:rgba(59,130,246,0.1);padding:8px;border-radius:6px;text-align:center;">
<div style="color:#93c5fd;font-size:10px;">Current</div>
<div style="color:white;font-size:14px;font-weight:600;">₹{df_trades.loc[idx, "CurrentPrice"]:.2f}</div>
</div>
<div style="background:rgba(239,68,68,0.1);padding:8px;border-radius:6px;text-align:center;">
<div style="color:#fca5a5;font-size:10px;">Stop Loss</div>
<div style="color:#ef4444;font-size:14px;font-weight:600;">₹{df_trades.loc[idx, "StopLoss"]:.2f}</div>
<div style="color:#f87171;font-size:9px;">{df_trades.loc[idx, "SL Distance (%)"]:.1f}% away</div>
</div>
<div style="background:rgba(34,197,94,0.1);padding:8px;border-radius:6px;text-align:center;">
<div style="color:#86efac;font-size:10px;">Target</div>
<div style="color:#22c55e;font-size:14px;font-weight:600;">₹{df_trades.loc[idx, "Target"]:.2f}</div>
<div style="color:#4ade80;font-size:9px;">{df_trades.loc[idx, "Target Distance (%)"]:.1f}% away</div>
</div>
<div style="background:rgba(245,158,11,0.1);padding:8px;border-radius:6px;text-align:center;">
<div style="color:#fcd34d;font-size:10px;">Risk:Reward</div>
<div style="color:#f59e0b;font-size:14px;font-weight:600;">
{(df_trades.loc[idx, "Potential Gain (₹)"] / df_trades.loc[idx, "Risk (₹)"]):.2f}:1
</div>
</div>
</div>

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
<div style="background:rgba(168,85,247,0.1);padding:6px;border-radius:4px;">
<span style="color:#c4b5fd;font-size:10px;">Investment:</span>
<span style="color:white;font-size:11px;font-weight:600;margin-left:4px;">₹{df_trades.loc[idx, "Investment"]:.2f}</span>
</div>
<div style="background:rgba(99,102,241,0.1);padding:6px;border-radius:4px;">
<span style="color:#c7d2fe;font-size:10px;">Current Value:</span>
<span style="color:white;font-size:11px;font-weight:600;margin-left:4px;">₹{df_trades.loc[idx, "Current Value"]:.2f}</span>
</div>
<div style="background:rgba(59,130,246,0.1);padding:6px;border-radius:4px;">
<span style="color:#93c5fd;font-size:10px;">Time:</span>
<span style="color:white;font-size:11px;font-weight:600;margin-left:4px;">{df_trades.loc[idx, "Time"]}</span>
</div>
</div>
</div>
"""
                    st.markdown(trade_card, unsafe_allow_html=True)
            
            # Enhanced summary metrics
            st.markdown("### 📈 Portfolio Summary")
            # Custom CSS for compact metrics
            st.markdown("""
            <style>
            div[data-testid="stMetricValue"] {
                font-size: 20px;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 12px;
            }
            </style>
            """, unsafe_allow_html=True)
            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
            
            total_pl = df_trades[df_trades["Status"].str.startswith("OPEN")]["P/L (₹)"].sum()
            total_investment = (df_trades[df_trades["Status"].str.startswith("OPEN")]["Entry"] * 
                               df_trades[df_trades["Status"].str.startswith("OPEN")]["Qty"]).sum()
            total_current = (df_trades[df_trades["Status"].str.startswith("OPEN")]["CurrentPrice"] * 
                            df_trades[df_trades["Status"].str.startswith("OPEN")]["Qty"]).sum()
            total_risk = df_trades[df_trades["Status"].str.startswith("OPEN")]["Risk (₹)"].sum()
            total_potential = df_trades[df_trades["Status"].str.startswith("OPEN")]["Potential Gain (₹)"].sum()
            
            with col_m1:
                st.metric("💰 Total P/L", f"₹{total_pl:.2f}", 
                         delta=f"{(total_pl/total_investment*100):.2f}%" if total_investment > 0 else "0%", 
                         delta_color="normal")
            
            with col_m2:
                st.metric("💼 Investment", f"₹{total_investment:.2f}")
            
            with col_m3:
                st.metric("📊 Current Value", f"₹{total_current:.2f}")
            
            with col_m4:
                st.metric("⚠️ Total Risk", f"₹{total_risk:.2f}")
            
            with col_m5:
                st.metric("🎯 Potential Gain", f"₹{total_potential:.2f}")
        
        else:
            st.info("✅ No open positions. All trades closed.")
    
    else:
        st.info("✅ No open trades currently.")
    
    # Enhanced closed trades history (replace the existing section)
    closed_trades = df_trades[~df_trades["Status"].str.startswith("OPEN")]

    if not closed_trades.empty:
        st.markdown("---")
        col_header, col_stats, col_clear = st.columns([2, 2, 1])

        with col_header:
            st.markdown(f"### 📜 Trade History ({len(closed_trades)} closed)")

        with col_stats:
            # Win rate calculation
            if "Final P/L" in closed_trades.columns:
                # Convert to numeric safely
                closed_trades["Final P/L"] = pd.to_numeric(closed_trades["Final P/L"], errors='coerce')
                winning_trades = len(closed_trades[closed_trades["Final P/L"] > 0])
                total_profit = closed_trades[closed_trades["Final P/L"] > 0]["Final P/L"].sum()
                total_loss = closed_trades[closed_trades["Final P/L"] < 0]["Final P/L"].sum()
            else:
                winning_trades = 0
                total_profit = 0
                total_loss = 0

            total_closed = len(closed_trades)
            win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0

            st.metric("🎯 Win Rate", f"{win_rate:.1f}%", 
                     delta=f"{winning_trades}/{total_closed} trades")

        with col_clear:
            if st.button("🗑️ Clear History", use_container_width=True, help="Remove all closed trades"):
                clear_closed_trades()
                st.success("✅ Trade history cleared!")
                st.rerun()

        with st.expander("View Detailed History", expanded=False):
            # Enhanced closed trades display with all details
            base_cols = ["Symbol", "Type", "Qty", "Entry", "Status", "Time"]
            optional_cols = ["Exit Price", "Exit Time", "Final P/L", "P/L %", "StopLoss", "Target"]

            # Build display columns
            display_cols = [col for col in base_cols if col in closed_trades.columns]
            display_cols.extend([col for col in optional_cols if col in closed_trades.columns])

            closed_display = closed_trades[display_cols].copy()

            # Format currency columns
            currency_cols = ["Entry", "StopLoss", "Target", "Exit Price", "Final P/L"]
            for col in currency_cols:
                if col in closed_display.columns:
                    closed_display[col] = closed_display[col].apply(
                        lambda x: f"₹{x:.2f}" if pd.notna(x) and isinstance(x, (int, float)) else "-"
                    )

            # Format percentage column
            if "P/L %" in closed_display.columns:
                closed_display["P/L %"] = closed_display["P/L %"].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) and isinstance(x, (int, float)) else "-"
                )

            # Color-code the dataframe (Streamlit doesn't support this directly, but we can show it in a better way)
            st.dataframe(closed_display, use_container_width=True, height=min(400, len(closed_display) * 35 + 50))

            # Enhanced Performance analytics
            if "Final P/L" in closed_trades.columns:
                st.markdown("#### 📊 Detailed Performance Analytics")

                col_p1, col_p2, col_p3, col_p4 = st.columns(4)

                total_realized_pl = closed_trades["Final P/L"].sum()
                winning_closed = closed_trades[closed_trades["Final P/L"] > 0]
                losing_closed = closed_trades[closed_trades["Final P/L"] < 0]

                avg_win = winning_closed["Final P/L"].mean() if len(winning_closed) > 0 else 0
                avg_loss = losing_closed["Final P/L"].mean() if len(losing_closed) > 0 else 0

                # Profit factor
                profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0

                with col_p1:
                    st.metric("💵 Total Realized P/L", 
                             f"₹{total_realized_pl:.2f}",
                             delta=f"{total_realized_pl:.2f}")

                with col_p2:
                    st.metric("📈 Avg Win", f"₹{avg_win:.2f}")

                with col_p3:
                    st.metric("📉 Avg Loss", f"₹{avg_loss:.2f}")

                with col_p4:
                    st.metric("⚖️ Profit Factor", f"{profit_factor:.2f}",
                             help="Total Profit / Total Loss ratio (>1 is good)")

                # Additional stats
                col_s1, col_s2, col_s3 = st.columns(3)

                with col_s1:
                    st.metric("💰 Total Profit", f"₹{total_profit:.2f}")

                with col_s2:
                    st.metric("💸 Total Loss", f"₹{total_loss:.2f}")

                with col_s3:
                    avg_trade_pl = total_realized_pl / total_closed if total_closed > 0 else 0
                    st.metric("📊 Avg Trade P/L", f"₹{avg_trade_pl:.2f}")

                # Best and Worst trades
                if len(closed_trades) > 0:
                    st.markdown("#### 🏆 Best & Worst Trades")
                    col_best, col_worst = st.columns(2)

                    best_trade = closed_trades.loc[closed_trades["Final P/L"].idxmax()]
                    worst_trade = closed_trades.loc[closed_trades["Final P/L"].idxmin()]

                    with col_best:
                        best_pl = best_trade["Final P/L"]
                        st.success(f"""
                        **🏆 Best Trade**  
                        {best_trade['Symbol']} ({best_trade['Type']})  
                        Profit: ₹{best_pl:.2f}
                        """)

                    with col_worst:
                        worst_pl = worst_trade["Final P/L"]
                        st.error(f"""
                        **💔 Worst Trade**  
                        {worst_trade['Symbol']} ({worst_trade['Type']})  
                        Loss: ₹{worst_pl:.2f}
                        """)



# ---------------------------
# Manage Open Trades
# ---------------------------
# ---------------------------
# Manage Open Trades with Current P/L
# ---------------------------
def manage_paper_trades():
    """Enhanced trade management showing current P/L"""
    init_paper_trades()
    
    open_trades = [t for t in st.session_state.trades if t["Status"].startswith("OPEN")]
    
    if not open_trades:
        return
    
    st.markdown("---")
    st.markdown("## ⚙️ Manage Open Positions")
    
    for i, t in enumerate(st.session_state.trades):
        if t["Status"].startswith("OPEN"):
            # Get current price
            try:
                ticker = yf.Ticker(t["Symbol"] + ".NS")
                data = ticker.history(period="1d", interval="5m")
                current_price = float(data["Close"].iloc[-1]) if not data.empty else t["Entry"]
            except:
                current_price = t["Entry"]
            
            # Calculate current P/L
            if t["Type"] == "BUY":
                current_pl = (current_price - t["Entry"]) * t["Qty"]
                pl_pct = ((current_price - t["Entry"]) / t["Entry"] * 100)
            else:
                current_pl = (t["Entry"] - current_price) * t["Qty"]
                pl_pct = ((t["Entry"] - current_price) / t["Entry"] * 100)
            
            # Color for P/L
            pl_color = "#10b981" if current_pl > 0 else "#ef4444" if current_pl < 0 else "#94a3b8"
            
            # Enhanced trade card with P/L
            trade_card = f"""
<div style="background:rgba(255,255,255,0.05); padding:14px; border-radius:10px; 
margin-bottom:12px; border-left:4px solid {pl_color};">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
<div>
<span style="font-size:18px; font-weight:700; color:white;">{t['Symbol']}</span>
<span style="margin-left:10px; background:{"rgba(16,185,129,0.3)" if t['Type']=='BUY' else "rgba(239,68,68,0.3)"}; 
color:{"#10b981" if t['Type']=='BUY' else "#ef4444"}; padding:2px 8px; 
border-radius:12px; font-size:11px; font-weight:600;">{t['Type']}</span>
</div>
<div style="text-align:right;">
<div style="color:{pl_color};font-size:18px;font-weight:700;">₹{current_pl:.2f}</div>
<div style="color:{pl_color};font-size:11px;">({pl_pct:+.2f}%)</div>
</div>
</div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;">
<div style="text-align:center;">
<div style="color:#94a3b8;font-size:9px;">Qty</div>
<div style="color:white;font-size:13px;font-weight:600;">{t['Qty']}</div>
</div>
<div style="text-align:center;">
<div style="color:#94a3b8;font-size:9px;">Entry</div>
<div style="color:white;font-size:13px;font-weight:600;">₹{t['Entry']:.2f}</div>
</div>
<div style="text-align:center;">
<div style="color:#93c5fd;font-size:9px;">Current</div>
<div style="color:#3b82f6;font-size:13px;font-weight:600;">₹{current_price:.2f}</div>
</div>
<div style="text-align:center;">
<div style="color:#fcd34d;font-size:9px;">Investment</div>
<div style="color:#f59e0b;font-size:13px;font-weight:600;">₹{t['Entry'] * t['Qty']:.2f}</div>
</div>
</div>

<div style="font-size:11px; color:#d1d5db;">
🎯 Target: ₹{t['Target']:.2f} | 🛑 SL: ₹{t['StopLoss']:.2f}
</div>
</div>
"""
            
            col_card, col_btn = st.columns([5, 1])
            
            with col_card:
                st.markdown(trade_card, unsafe_allow_html=True)
            
            with col_btn:
                if st.button("❌ Close", key=f"close_trade_{i}", use_container_width=True):
                    # Close trade and record exit details
                    st.session_state.trades[i]["Status"] = "CLOSED (Manual)"
                    st.session_state.trades[i]["Exit Price"] = float(current_price)
                    st.session_state.trades[i]["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state.trades[i]["Final P/L"] = float(current_pl)
                    st.session_state.trades[i]["P/L %"] = float(pl_pct)
                    
                    st.success(f"✅ {t['Symbol']} closed at ₹{current_price:.2f} | P/L: ₹{current_pl:.2f} ({pl_pct:+.2f}%)")
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
