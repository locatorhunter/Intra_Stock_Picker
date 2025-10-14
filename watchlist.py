from datetime import datetime

def display_watchlist(notify_desktop, notify_telegram, BOT_TOKEN, CHAT_ID):
    import requests
    import streamlit as st
    import pandas as pd
    import yfinance as yf

    # Inject improved CSS styling for watchlist UI
    st.markdown('''
    <style>
    /* Container and general */
    .watchlist-container {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      max-width: 900px;
      margin: 1rem auto;
      padding: 0 12px;
    }

    /* Titles */
    .watchlist-container h1, .watchlist-container h2, .watchlist-container h3 {
      font-weight: 600;
      color: #111;
      margin-bottom: 0.4rem;
      letter-spacing: 0.02em;
    }

    /* Buttons */
    .button-primary {
      background-color: #2563eb;
      border: none;
      color: white;
      padding: 6px 14px;
      border-radius: 4px;
      font-weight: 600;
      cursor: pointer;
      transition: background-color 0.25s ease;
      font-size: 14px;
    }
    .button-primary:hover {
      background-color: #1d4ed8;
    }

    /* Watchlist entries */
    .watchlist-entry {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 15px;
      padding: 10px 12px;
      border-bottom: 1px solid #e5e7eb;
      transition: background-color 0.15s ease;
    }
    .watchlist-entry:hover {
      background-color: #f9fafb;
    }

    /* Left block (symbol and target info) */
    .watchlist-info {
      flex-grow: 1;
      color: #DA70D6;
      font-weight: 600;
    }

    /* Status badges */
    .status-badge {
      padding: 3px 10px;
      border-radius: 9999px;
      font-size: 13px;
      font-weight: 700;
      min-width: 80px;
      text-align: center;
    }
    .status-active {
      background-color: #e0f2fe;
      color: #0284c7;
    }
    .status-target-hit {
      background-color: #dcfce7;
      color: #15803d;
    }
    .status-stop-hit {
      background-color: #fee2e2;
      color: #b91c1c;
    }

    /* Price block */
    .price-info {
      min-width: 120px;
      color: #555;
      font-weight: 500;
      text-align: right;
      font-family: monospace;
    }

    /* Notification message style */
    .toast-msg {
      background-color: #fef3c7;
      border-left: 5px solid #fbbf24;
      padding: 12px 16px;
      margin-bottom: 12px;
      font-weight: 600;
      color: #92400e;
      border-radius: 4px;
      font-size: 14px;
    }
    </style>
    ''', unsafe_allow_html=True)

    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = {}

    now = datetime.now()
    refresh_time_str = now.strftime("%I:%M:%S %p")
    st.markdown(f"⏰ Refreshed at: **{refresh_time_str}**")

    # Inner helper functions
    def get_price_data(symbol, period="1d", interval="5m"):
        df = yf.download(f"{symbol}.NS", period=period, interval=interval, progress=False)
        if df.empty:
            return pd.DataFrame()
        return df

    def notify_stock(symbol, last_price, entry, sl, tgt, msg,
                     desktop_enabled=False, telegram_enabled=False,
                     BOT_TOKEN=None, CHAT_ID=None):
        st.success(f"{msg} [{symbol}] (Price: {last_price}, Entry: {entry}, SL: {sl}, Target: {tgt})")

        if desktop_enabled:
            try:
                from plyer import notification
                notification.notify(
                    title=f"{msg} [{symbol}]",
                    message=f"Price: {last_price}\nEntry: {entry}\nSL: {sl}\nTarget: {tgt}",
                    timeout=6
                )
            except Exception as e:
                st.warning(f"Desktop notification error: {e}")

        if telegram_enabled and BOT_TOKEN and CHAT_ID:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                text = f"{msg} [{symbol}]\nPrice: {last_price}\nEntry: {entry}\nSL: {sl}\nTarget: {tgt}"
                requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=5)
            except Exception as e:
                st.warning(f"Telegram notification error: {e}")

    # Demo picks
    demo_picks = [
        {"Symbol": "RELIANCE", "Entry": 2500, "StopLoss": 2480, "Target": 2550},
        {"Symbol": "TCS", "Entry": 3700, "StopLoss": 3680, "Target": 3750},
    ]

    st.title("Live Stocks Watchlist Demo")
    st.subheader("Scanner/Manual Picks")

    for pick in demo_picks:
        sym = pick["Symbol"]
        entry = pick["Entry"]
        stop = pick["StopLoss"]
        tgt = pick["Target"]
        col1, col2 = st.columns([3,1])

        with col1:
            st.markdown(f"<div class='watchlist-info'><b>{sym}</b> | Entry: {entry} | SL: {stop} | Target: {tgt}</div>", unsafe_allow_html=True)
        with col2:
            if st.button(f"Add {sym} to Watchlist", key=f"add_{sym}"):
                st.session_state.watchlist[sym] = {
                    "entry": entry,
                    "sl": stop,
                    "target": tgt,
                    "status": "Active"
                }
                st.success(f"Added {sym} to watchlist!")

    st.subheader("Live Watchlist & Alerts")

    remove_syms = []

    # Watchlist container start
    st.markdown("<div class='watchlist-container'>", unsafe_allow_html=True)
    for sym, info in st.session_state.watchlist.items():
        df = get_price_data(sym, period="1d", interval="5m")
        curr_price = float(df["Close"].values[-1]) if not df.empty else None

        entry = info["entry"]
        sl = info["sl"]
        tgt = info["target"]
        status = info["status"]
        status_class = {
            "Active": "status-active",
            "Target Hit": "status-target-hit",
            "Stop Hit": "status-stop-hit"
        }.get(status, "status-active")

        # Check alerts and notify
        if curr_price is not None and status == "Active":
            if curr_price >= tgt:
                notify_stock(sym, curr_price, entry, sl, tgt,
                             msg="🎯 Target hit!",
                             desktop_enabled=notify_desktop,
                             telegram_enabled=notify_telegram,
                             BOT_TOKEN=BOT_TOKEN, CHAT_ID=CHAT_ID)
                info["status"] = "Target Hit"
                remove_syms.append(sym)
            elif curr_price <= sl:
                notify_stock(sym, curr_price, entry, sl, tgt,
                             msg="⛔ Stoploss hit!",
                             desktop_enabled=notify_desktop,
                             telegram_enabled=notify_telegram,
                             BOT_TOKEN=BOT_TOKEN, CHAT_ID=CHAT_ID)
                info["status"] = "Stop Hit"
                remove_syms.append(sym)

        st.markdown(f'''
        <div class="watchlist-entry">
            <div class="watchlist-info">{sym} | Entry: {entry} | SL: {sl} | Target: {tgt}</div>
            <div class="price-info">{curr_price if curr_price is not None else "N/A"}</div>
            <div class="status-badge {status_class}">{status}</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # container end

    for sym in remove_syms:
        del st.session_state.watchlist[sym]

    st.info("Page auto-refresh will re-check alerts and prices.")
