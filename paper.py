# ---------------------------
# paper.py - Enhanced Paper Trading Module (Improved)
# ---------------------------

import os
import tempfile
from datetime import datetime
import pytz
from functools import lru_cache

import streamlit as st
import pandas as pd
import yfinance as yf

IST = pytz.timezone("Asia/Kolkata")
# Save CSV next to this file so it's not dependent on current working dir
TRADES_FILE = os.path.join(os.path.dirname(__file__), "paper_trades.csv")
DEFAULT_COLUMNS = ["Symbol", "Qty", "Type", "Entry", "StopLoss", "Target", "Status", "Time"]

# ---------------------------
# File utilities
# ---------------------------
def ensure_csv_exists():
    """Ensure CSV file exists with proper headers"""
    if not os.path.exists(TRADES_FILE):
        df = pd.DataFrame(columns=DEFAULT_COLUMNS)
        df.to_csv(TRADES_FILE, index=False)


def safe_rerun():
    """Safe Streamlit rerun helper.

    Uses `st.experimental_rerun()` when available; otherwise toggles a
    session-state value to force Streamlit to rerun and calls `st.stop()` to
    end the current run. This provides a backward-compatible fallback for
    Streamlit builds that don't expose `experimental_rerun`.
    """
    try:
        # Try the newer / preferred APIs first. Some Streamlit builds provide
        # `experimental_rerun`, others expose `rerun`. Try both for maximum
        # compatibility.
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
            return
        if hasattr(st, "rerun"):
            # Stable API in newer Streamlit versions
            st.rerun()
            return
    except Exception:
        # If direct rerun calls fail for any reason, fall back to a session
        # state toggle which causes Streamlit to re-run on change.
        pass

    # Toggle a session-state flag to trigger a rerun on interaction
    key = "_rerun_trigger"
    st.session_state[key] = not st.session_state.get(key, False)
    # Stop execution now; Streamlit will re-run due to session state change
    try:
        st.stop()
    except Exception:
        # As a final fallback, do nothing (script will finish)
        return


def atomic_save_df(df: pd.DataFrame, path: str):
    """Write DataFrame atomically to avoid file corruption"""
    dirpath = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath, prefix=".tmp_trades_", suffix=".csv")
    os.close(fd)
    try:
        df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ---------------------------
# Load/Save trades
# ---------------------------
def init_paper_trades():
    """Initialize trade session & load from CSV with error handling"""
    if "trades" in st.session_state:
        return

    ensure_csv_exists()
    try:
        df = pd.read_csv(TRADES_FILE)
        if df.empty or len(df.columns) == 0:
            st.session_state.trades = []
        else:
            # Normalize columns and types
            df.columns = [c if c in df.columns else c for c in df.columns]
            # Ensure Symbol uppercase
            if "Symbol" in df.columns:
                df["Symbol"] = df["Symbol"].astype(str).str.upper()
            st.session_state.trades = df.to_dict("records")
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        # corrupted file -> recreate
        print(f"Warning: Trade history file corrupted. Starting fresh. Error: {e}")
        try:
            os.remove(TRADES_FILE)
        except Exception:
            pass
        ensure_csv_exists()
        st.session_state.trades = []
    except Exception as e:
        print(f"Error loading trades: {e}")
        st.session_state.trades = []


def save_trades():
    """Save trades to CSV persistently with error handling (atomic)"""
    try:
        init_paper_trades()
        trades = st.session_state.get("trades", [])
        if trades:
            df = pd.DataFrame(trades)
            # Ensure basic columns exist
            for c in DEFAULT_COLUMNS:
                if c not in df.columns:
                    df[c] = pd.NA
            atomic_save_df(df[sorted(df.columns)], TRADES_FILE)
        else:
            df = pd.DataFrame(columns=DEFAULT_COLUMNS)
            atomic_save_df(df, TRADES_FILE)
    except Exception as e:
        print(f"Error saving trades: {e}")
        st.error(f"Failed to save trades: {e}")


# ---------------------------
# Price fetching
# ---------------------------
@lru_cache(maxsize=256)
def _get_ticker_price(sym_ns: str):
    """Fetch last close for single ticker, cached"""
    try:
        t = yf.Ticker(sym_ns)
        data = t.history(period="1d", interval="5m")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception:
        pass
    return None


def fetch_live_prices(symbols):
    """
    Fetch live prices for a list of symbols (NSE tickers without .NS suffix).
    Returns a dict {SYM: price_or_None}
    """
    prices = {}
    unique = [s.upper() for s in dict.fromkeys(symbols)]
    for s in unique:
        price = _get_ticker_price(f"{s}.NS")
        prices[s] = price
    return prices


# ---------------------------
# Execute Trade Function
# ---------------------------
def execute_trade(symbol, action, quantity, price, sl=0.0, target=0.0):
    """Execute a trade from the scanner or manual entry"""
    init_paper_trades()

    sym = symbol.upper().strip()
    entry = float(price)
    sl_val = float(sl) if sl and float(sl) > 0 else round(entry * 0.97, 4)
    target_val = float(target) if target and float(target) > 0 else round(entry * 1.05, 4)

    trade = {
        "Symbol": sym,
        "Qty": int(quantity),
        "Type": action.upper(),
        "Entry": float(entry),
        "StopLoss": float(sl_val),
        "Target": float(target_val),
        "Status": "OPEN",
        "Time": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    }

    st.session_state.trades.append(trade)
    save_trades()

    # Notify but don't break on failure
    try:
        from functions import notify_trade_execution  # optional
        notify_trade_execution(symbol, action, quantity, price, trade_type="paper")
    except Exception:
        pass

    return True


# ---------------------------
# Delete Closed Trades
# ---------------------------
def clear_closed_trades():
    """Remove all closed trades from history"""
    init_paper_trades()
    st.session_state.trades = [t for t in st.session_state.trades if str(t.get("Status", "")).upper().startswith("OPEN")]
    save_trades()


# ---------------------------
# Manual Trade Entry Form
# ---------------------------
def paper_trade_manual():
    """Enhanced manual trade entry with better UI"""
    st.markdown("### 📝 Quick Trade Entry")

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
                execute_trade(symbol, action, quantity, entry, sl, target)
                st.success(f"✅ {action} order placed: {quantity} x {symbol.upper()} @ ₹{entry:.2f}")
                st.balloons()
                safe_rerun()
            else:
                st.error("❌ Please enter valid symbol and entry price!")


# ---------------------------
# Display Active Trades
# ---------------------------
def display_paper_trades():
    """Display all active and closed trades with comprehensive details"""
    init_paper_trades()
    st.markdown("## 🧾 Active Trades")

    trades = st.session_state.get("trades", [])
    if not trades:
        st.info("📭 No trades placed yet. Use the scanner or manual entry to place trades.")
        return

    # Load into DataFrame and ensure numeric types
    df_trades = pd.DataFrame(trades).copy()
    if df_trades.empty:
        st.info("📭 No trades placed yet.")
        return

    # Normalize symbol and ensure numeric columns
    df_trades["Symbol"] = df_trades["Symbol"].astype(str).str.upper()
    for col in ["Entry", "StopLoss", "Target", "Qty"]:
        if col in df_trades.columns:
            df_trades[col] = pd.to_numeric(df_trades[col], errors="coerce")

    open_mask = df_trades["Status"].astype(str).str.upper().str.startswith("OPEN")
    open_trades = df_trades[open_mask]

    if not open_trades.empty:
        # Fetch live prices for unique symbols among open trades
        unique_syms = open_trades["Symbol"].unique().tolist()
        progress_placeholder = st.empty()
        live_prices = {}
        try:
            # fetch prices with progress
            for i, sym in enumerate(unique_syms):
                progress_placeholder.text(f"Fetching prices... {i+1}/{len(unique_syms)}")
                price = _get_ticker_price(f"{sym}.NS")
                if price is None:
                    # fallback to entry for that symbol's first occurrence
                    price = float(open_trades[open_trades["Symbol"] == sym]["Entry"].iloc[0])
                live_prices[sym] = float(price)
        finally:
            progress_placeholder.empty()

        # Map current prices (for all rows)
        df_trades["CurrentPrice"] = df_trades["Symbol"].map(live_prices).fillna(df_trades.get("Entry", pd.Series([0] * len(df_trades))))

        # Calculate P/L safely
        def calculate_pl(row):
            try:
                cp = float(row["CurrentPrice"])
                entry = float(row["Entry"])
                qty = float(row["Qty"])
                if row["Type"].upper() == "BUY":
                    return (cp - entry) * qty
                else:
                    return (entry - cp) * qty
            except Exception:
                return 0.0

        df_trades["P/L (₹)"] = df_trades.apply(calculate_pl, axis=1)
        df_trades["P/L (%)"] = (df_trades["P/L (₹)"] / (df_trades["Entry"] * df_trades["Qty"])) * 100

        # Additional metrics
        df_trades["Investment"] = df_trades["Entry"] * df_trades["Qty"]
        df_trades["Current Value"] = df_trades["CurrentPrice"] * df_trades["Qty"]
        df_trades["Risk (₹)"] = (df_trades["Entry"] - df_trades["StopLoss"]).abs() * df_trades["Qty"]
        df_trades["Potential Gain (₹)"] = (df_trades["Target"] - df_trades["Entry"]).abs() * df_trades["Qty"]

        # Distance calculations
        def calc_sl_distance(row):
            try:
                cp = float(row["CurrentPrice"])
                sl = float(row["StopLoss"])
                if sl <= 0:
                    return 0.0
                if row["Type"].upper() == "BUY":
                    return ((cp - sl) / cp * 100)
                else:
                    return ((sl - cp) / cp * 100)
            except Exception:
                return 0.0

        def calc_target_distance(row):
            try:
                cp = float(row["CurrentPrice"])
                tgt = float(row["Target"])
                if tgt <= 0:
                    return 0.0
                if row["Type"].upper() == "BUY":
                    return ((tgt - cp) / cp * 100)
                else:
                    return ((cp - tgt) / cp * 100)
            except Exception:
                return 0.0

        df_trades["SL Distance (%)"] = df_trades.apply(calc_sl_distance, axis=1)
        df_trades["Target Distance (%)"] = df_trades.apply(calc_target_distance, axis=1)

        # Auto-close logic (updates session_state in place)
        changed = False
        for t in st.session_state.trades:
            if not str(t.get("Status", "")).upper().startswith("OPEN"):
                continue
            sym = t.get("Symbol", "").upper()
            # get current price safely
            cp_vals = df_trades.loc[df_trades["Symbol"] == sym, "CurrentPrice"].values
            if len(cp_vals) == 0:
                continue
            cp = float(cp_vals[0])
            typ = str(t.get("Type", "")).upper()
            entry = float(t.get("Entry", 0.0))
            qty = float(t.get("Qty", 0))
            sl_val = float(t.get("StopLoss") or 0)
            tgt_val = float(t.get("Target") or 0)

            if typ == "BUY":
                if tgt_val and cp >= tgt_val:
                    pl = (cp - entry) * qty
                    pl_pct = ((cp - entry) / entry * 100) if entry else 0
                    t["Status"] = "CLOSED (Target Hit)"
                    t["Exit Price"] = float(cp)
                    t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                    t["Final P/L"] = float(pl)
                    t["P/L %"] = float(pl_pct)
                    st.success(f"🎯 Target hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
                    changed = True
                elif sl_val and cp <= sl_val:
                    pl = (cp - entry) * qty
                    pl_pct = ((cp - entry) / entry * 100) if entry else 0
                    t["Status"] = "CLOSED (Stop Loss Hit)"
                    t["Exit Price"] = float(cp)
                    t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                    t["Final P/L"] = float(pl)
                    t["P/L %"] = float(pl_pct)
                    st.error(f"❌ Stop loss hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
                    changed = True

            elif typ == "SELL":
                if tgt_val and cp <= tgt_val:
                    pl = (entry - cp) * qty
                    pl_pct = ((entry - cp) / entry * 100) if entry else 0
                    t["Status"] = "CLOSED (Target Hit)"
                    t["Exit Price"] = float(cp)
                    t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                    t["Final P/L"] = float(pl)
                    t["P/L %"] = float(pl_pct)
                    st.success(f"🎯 Target hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
                    changed = True
                elif sl_val and cp >= sl_val:
                    pl = (entry - cp) * qty
                    pl_pct = ((entry - cp) / entry * 100) if entry else 0
                    t["Status"] = "CLOSED (Stop Loss Hit)"
                    t["Exit Price"] = float(cp)
                    t["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                    t["Final P/L"] = float(pl)
                    t["P/L %"] = float(pl_pct)
                    st.error(f"❌ Stop loss hit! {t['Symbol']} closed @ ₹{cp:.2f} | P/L: ₹{pl:.2f} ({pl_pct:+.2f}%)")
                    changed = True

        if changed:
            save_trades()

        # Prepare display for open trades only
        open_display = df_trades[open_mask].copy()
        if not open_display.empty:
            display_cols = [
                "Symbol", "Type", "Entry", "CurrentPrice", "Qty",
                "StopLoss", "Target", "Investment", "Current Value",
                "P/L (₹)", "P/L (%)", "SL Distance (%)", "Target Distance (%)",
                "Risk (₹)", "Potential Gain (₹)", "Time"
            ]
            # Safe formatting function
            def fmt_currency(x):
                try:
                    return f"₹{float(x):,.2f}"
                except Exception:
                    return "-"

            for col in ["Entry", "CurrentPrice", "StopLoss", "Target", "Investment", "Current Value", "P/L (₹)", "Risk (₹)", "Potential Gain (₹)"]:
                if col in open_display.columns:
                    open_display[col] = open_display[col].apply(fmt_currency)

            for col in ["P/L (%)", "SL Distance (%)", "Target Distance (%)"]:
                if col in open_display.columns:
                    open_display[col] = open_display[col].apply(lambda x: f"{float(x):.2f}%" if pd.notna(x) else "-")

            tab_table, tab_visual = st.tabs(["📊 Table View", "📈 Visual Dashboard"])
            with tab_table:
                st.dataframe(open_display[[c for c in display_cols if c in open_display.columns]],
                             use_container_width=True,
                             height=min(450, len(open_display) * 40 + 50))

            with tab_visual:
                # Visual cards for each open trade
                for idx, row in open_display.reset_index().iterrows():
                    base_idx = row["index"]
                    pl_value = df_trades.loc[base_idx, "P/L (₹)"]
                    pl_pct = df_trades.loc[base_idx, "P/L (%)"]
                    pl_color = "#10b981" if pl_value > 0 else "#ef4444" if pl_value < 0 else "#94a3b8"
                    type_is_buy = df_trades.loc[base_idx, "Type"].upper() == "BUY"
                    current_price = df_trades.loc[base_idx, "CurrentPrice"]
                    stop_loss = df_trades.loc[base_idx, "StopLoss"]
                    target_price = df_trades.loc[base_idx, "Target"]
                    investment = df_trades.loc[base_idx, "Investment"]
                    risk_val = df_trades.loc[base_idx, "Risk (₹)"]
                    potential = df_trades.loc[base_idx, "Potential Gain (₹)"]
                    # Simplified HTML card
                    card = f"""
<div style="background:rgba(255,255,255,0.03);padding:12px;border-radius:10px;margin-bottom:12px;border-left:4px solid {pl_color};">
<div style="display:flex;justify-content:space-between;align-items:center;">
<div>
<strong style="font-size:18px;color:white;">{row['Symbol']}</strong>
<span style="margin-left:8px;padding:2px 8px;border-radius:8px;
background:{'rgba(16,185,129,0.12)' if type_is_buy else 'rgba(239,68,68,0.12)'}; color:{'#10b981' if type_is_buy else '#ef4444'};">
{df_trades.loc[base_idx, 'Type']}</span>
<div style="color:#94a3b8;font-size:12px;margin-top:4px;">Qty: {df_trades.loc[base_idx, 'Qty']} | Entry: ₹{df_trades.loc[base_idx, 'Entry']:.2f}</div>
</div>
<div style="text-align:right;">
<div style="color:{pl_color};font-size:20px;font-weight:700;">₹{pl_value:.2f}</div>
<div style="color:{pl_color};font-size:12px;">{pl_pct:.2f}%</div>
</div>
</div>
</div>
"""
                    st.markdown(card, unsafe_allow_html=True)

            # Portfolio summary
            st.markdown("### 📈 Portfolio Summary")
            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

            total_pl = df_trades.loc[open_mask, "P/L (₹)"].sum()
            total_investment = df_trades.loc[open_mask, "Investment"].sum()
            total_current = df_trades.loc[open_mask, "Current Value"].sum()
            total_risk = df_trades.loc[open_mask, "Risk (₹)"].sum()
            total_potential = df_trades.loc[open_mask, "Potential Gain (₹)"].sum()

            with col_m1:
                delta = f"{(total_pl / total_investment * 100):.2f}%" if total_investment else "0%"
                st.metric("💰 Total P/L", f"₹{total_pl:.2f}", delta=delta, delta_color="normal")
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

    # Closed trades
    closed_trades = df_trades[~open_mask]
    if not closed_trades.empty:
        st.markdown("---")
        col_header, col_stats, col_clear = st.columns([2, 2, 1])
        with col_header:
            st.markdown(f"### 📜 Trade History ({len(closed_trades)} closed)")
        with col_stats:
            if "Final P/L" in closed_trades.columns:
                closed_trades["Final P/L"] = pd.to_numeric(closed_trades["Final P/L"], errors="coerce").fillna(0)
                winning_trades = len(closed_trades[closed_trades["Final P/L"] > 0])
                total_profit = closed_trades[closed_trades["Final P/L"] > 0]["Final P/L"].sum()
                total_loss = closed_trades[closed_trades["Final P/L"] < 0]["Final P/L"].sum()
            else:
                winning_trades = total_profit = total_loss = 0
            total_closed = len(closed_trades)
            win_rate = (winning_trades / total_closed * 100) if total_closed else 0
            st.metric("🎯 Win Rate", f"{win_rate:.1f}%", delta=f"{winning_trades}/{total_closed} trades")
        with col_clear:
            if st.button("🗑️ Clear History", use_container_width=True, help="Remove all closed trades"):
                clear_closed_trades()
                st.success("✅ Trade history cleared!")
                safe_rerun()
        with st.expander("View Detailed History", expanded=False):
            base_cols = ["Symbol", "Type", "Qty", "Entry", "Status", "Time"]
            optional_cols = ["Exit Price", "Exit Time", "Final P/L", "P/L %", "StopLoss", "Target"]
            display_cols = [c for c in base_cols if c in closed_trades.columns] + [c for c in optional_cols if c in closed_trades.columns]
            closed_display = closed_trades[display_cols].copy()
            currency_cols = ["Entry", "StopLoss", "Target", "Exit Price", "Final P/L"]
            for col in currency_cols:
                if col in closed_display.columns:
                    closed_display[col] = closed_display[col].apply(lambda x: f"₹{float(x):.2f}" if pd.notna(x) and _is_number(x := x) else "-")
            if "P/L %" in closed_display.columns:
                closed_display["P/L %"] = closed_display["P/L %"].apply(lambda x: f"{float(x):+.2f}%" if pd.notna(x) and _is_number(x := x) else "-")
            st.dataframe(closed_display, use_container_width=True, height=min(400, len(closed_display) * 35 + 50))

            # Performance analytics
            if "Final P/L" in closed_trades.columns:
                st.markdown("#### 📊 Detailed Performance Analytics")
                col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                total_realized_pl = closed_trades["Final P/L"].sum()
                winning_closed = closed_trades[closed_trades["Final P/L"] > 0]
                losing_closed = closed_trades[closed_trades["Final P/L"] < 0]
                avg_win = winning_closed["Final P/L"].mean() if len(winning_closed) else 0
                avg_loss = losing_closed["Final P/L"].mean() if len(losing_closed) else 0
                profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0
                with col_p1:
                    st.metric("💵 Total Realized P/L", f"₹{total_realized_pl:.2f}", delta=f"{total_realized_pl:.2f}")
                with col_p2:
                    st.metric("📈 Avg Win", f"₹{avg_win:.2f}")
                with col_p3:
                    st.metric("📉 Avg Loss", f"₹{avg_loss:.2f}")
                with col_p4:
                    st.metric("⚖️ Profit Factor", f"{profit_factor:.2f}", help="Total Profit / Total Loss ratio (>1 is good)")

# utility used in closed_display formatting
def _is_number(x):
    try:
        float(x)
        return True
    except Exception:
        return False


# ---------------------------
# Manage Open Trades
# ---------------------------
def manage_paper_trades():
    """Enhanced trade management showing current P/L"""
    init_paper_trades()
    open_trades = [t for t in st.session_state.trades if str(t.get("Status", "")).upper().startswith("OPEN")]
    if not open_trades:
        return

    st.markdown("---")
    st.markdown("## ⚙️ Manage Open Positions")

    for i, t in enumerate(st.session_state.trades):
        if not str(t.get("Status", "")).upper().startswith("OPEN"):
            continue
        try:
            current_price = _get_ticker_price(f"{t['Symbol']}.NS") or float(t.get("Entry", 0.0))
        except Exception:
            current_price = float(t.get("Entry", 0.0))

        if str(t.get("Type", "")).upper() == "BUY":
            current_pl = (current_price - float(t.get("Entry", 0.0))) * float(t.get("Qty", 0))
            pl_pct = ((current_price - float(t.get("Entry", 0.0))) / float(t.get("Entry", 0.0)) * 100) if float(t.get("Entry", 0.0)) else 0
        else:
            current_pl = (float(t.get("Entry", 0.0)) - current_price) * float(t.get("Qty", 0))
            pl_pct = ((float(t.get("Entry", 0.0)) - current_price) / float(t.get("Entry", 0.0)) * 100) if float(t.get("Entry", 0.0)) else 0

        pl_color = "#10b981" if current_pl > 0 else "#ef4444" if current_pl < 0 else "#94a3b8"

        trade_card = f"""
<div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:10px; margin-bottom:12px; border-left:4px solid {pl_color};">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<span style="font-size:16px; font-weight:700; color:white;">{t['Symbol']}</span>
<span style="margin-left:8px; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; background:{'rgba(16,185,129,0.12)' if t['Type']=='BUY' else 'rgba(239,68,68,0.12)'}; color:{'#10b981' if t['Type']=='BUY' else '#ef4444'};">{t['Type']}</span>
</div>
<div style="text-align:right;">
<div style="color:{pl_color};font-size:18px;font-weight:700;">₹{current_pl:.2f}</div>
<div style="color:{pl_color};font-size:11px;">({pl_pct:+.2f}%)</div>
</div>
</div>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px;">
<div style="text-align:center;"><div style="color:#94a3b8;font-size:9px;">Qty</div><div style="color:white;font-size:13px;font-weight:600;">{t['Qty']}</div></div>
<div style="text-align:center;"><div style="color:#94a3b8;font-size:9px;">Entry</div><div style="color:white;font-size:13px;font-weight:600;">₹{float(t['Entry']):.2f}</div></div>
<div style="text-align:center;"><div style="color:#93c5fd;font-size:9px;">Current</div><div style="color:#3b82f6;font-size:13px;font-weight:600;">₹{current_price:.2f}</div></div>
<div style="text-align:center;"><div style="color:#fcd34d;font-size:9px;">Investment</div><div style="color:#f59e0b;font-size:13px;font-weight:600;">₹{float(t['Entry'])*float(t['Qty']):.2f}</div></div>
</div>
<div style="font-size:11px; color:#d1d5db; margin-top:6px;">🎯 Target: ₹{t.get('Target', 0):.2f} | 🛑 SL: ₹{t.get('StopLoss', 0):.2f}</div>
</div>
"""
        col_card, col_btn = st.columns([5, 1])
        with col_card:
            st.markdown(trade_card, unsafe_allow_html=True)
        with col_btn:
            if st.button("❌ Close", key=f"close_trade_{i}", use_container_width=True):
                st.session_state.trades[i]["Status"] = "CLOSED (Manual)"
                st.session_state.trades[i]["Exit Price"] = float(current_price)
                st.session_state.trades[i]["Exit Time"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.trades[i]["Final P/L"] = float(current_pl)
                st.session_state.trades[i]["P/L %"] = float(pl_pct)
                st.success(f"✅ {t['Symbol']} closed at ₹{current_price:.2f} | P/L: ₹{current_pl:.2f} ({pl_pct:+.2f}%)")
                save_trades()
                safe_rerun()


# ---------------------------
# Complete Paper Trading Interface
# ---------------------------
def paper_trading_interface():
    """Complete enhanced paper trading interface"""
    init_paper_trades()

    pending = st.session_state.get("pending_trade") or {}
    if pending.get("switch_to_paper"):
        trade = pending
        st.markdown("## 🎯 Quick Execute from Scanner")
        action_color = "#10b981" if trade.get("action", "").upper() == "BUY" else "#ef4444"
        action_emoji = "🟢" if trade.get("action", "").upper() == "BUY" else "🔴"
        trade_card = f"""
        <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:18px;border-radius:12px;margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
        <h2 style="color:white;margin:0;font-size:28px;">{action_emoji} {trade.get('action','')} {trade.get('symbol','')}</h2>
        <div style="background:rgba(255,255,255,0.12);padding:6px 12px;border-radius:16px;">
        <span style="color:white;font-size:13px;font-weight:600;">Last: ₹{trade.get('last_price',0):.2f}</span>
        </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:12px;">
        <div style="background:rgba(16,185,129,0.12);padding:12px;border-radius:10px;text-align:center;">
        <div style="color:#6ee7b7;font-size:11px;">💰 ENTRY</div><div style="color:#10b981;font-size:20px;font-weight:800;">₹{trade.get('entry',0):.2f}</div></div>
        <div style="background:rgba(239,68,68,0.12);padding:12px;border-radius:10px;text-align:center;">
        <div style="color:#fca5a5;font-size:11px;">🛑 STOP LOSS</div><div style="color:#ef4444;font-size:20px;font-weight:800;">₹{trade.get('sl',0):.2f}</div></div>
        <div style="background:rgba(34,197,94,0.12);padding:12px;border-radius:10px;text-align:center;">
        <div style="color:#86efac;font-size:11px;">🎯 TARGET</div><div style="color:#22c55e;font-size:20px;font-weight:800;">₹{trade.get('target',0):.2f}</div></div>
        </div></div>
        """
        st.markdown(trade_card, unsafe_allow_html=True)

        col_qty, col_btn1, col_btn2 = st.columns([2, 1, 1])
        with col_qty:
            quantity = st.number_input("📦 Quantity", min_value=1, value=1, step=1, key="quick_qty")
        with col_btn1:
            if st.button("✅ Execute", use_container_width=True, type="primary"):
                try:
                    execute_trade(trade["symbol"], trade["action"], quantity, trade["entry"], trade["sl"], trade["target"])
                    st.success(f"✅ {trade['action']} {quantity} x {trade['symbol']} @ ₹{trade['entry']:.2f}")
                    st.balloons()
                    st.session_state["pending_trade"] = None
                    safe_rerun()
                except Exception as e:
                    st.error(f"❌ Failed: {e}")
        with col_btn2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state["pending_trade"] = None
                safe_rerun()
        st.markdown("---")

    # Main UI
    display_paper_trades()
    st.markdown("---")
    paper_trade_manual()
    manage_paper_trades()
