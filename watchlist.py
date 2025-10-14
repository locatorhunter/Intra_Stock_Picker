from datetime import datetime
def display_watchlist(notify_desktop, notify_telegram, BOT_TOKEN, CHAT_ID):
    import requests
    import streamlit as st
    import pandas as pd
    import yfinance as yf
    import streamlit as st
    
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = {}

    now = datetime.now()
    refresh_time_str = now.strftime("%I:%M:%S %p")
    
    st.markdown(f"⏰ Refreshed at: **{refresh_time_str}**")

    for sym, info in list(st.session_state.watchlist.items()):
        df = get_price_data(sym, period="1d", interval="5m")
        if df.empty:
            curr_price = None
        else:
            curr_price = float(df["Close"].values[-1])

        entry = info["entry"]
        sl = info["sl"]
        tgt = info["target"]
        status = info["status"]

        if curr_price is not None and status == "Active":
            if curr_price >= tgt:
                notify_stock(sym, curr_price, entry, sl, tgt, 
                             desktop_enabled=notify_desktop, 
                             telegram_enabled=notify_telegram)
                st.success(f"🎯 {sym} target hit at {curr_price}!")
                info["status"] = "TargetHit"
                del st.session_state.watchlist[sym]  # Optional: auto-remove after alert
            elif curr_price <= sl:
                notify_stock(sym, curr_price, entry, sl, tgt, 
                             desktop_enabled=notify_desktop, 
                             telegram_enabled=notify_telegram)
                st.error(f"⛔ {sym} stop loss hit at {curr_price}!")
                info["status"] = "StopHit"
                del st.session_state.watchlist[sym]
        # Show each watched symbol info etc here

    
    # Optionally send desktop notification or Telegram about refresh
    if st.session_state.get("last_refresh") != refresh_time_str:
        st.session_state["last_refresh"] = refresh_time_str
        # notification example: 
        if notify_desktop:
            try:
                from plyer import notification
                notification.notify(
                    title="NSE Picker Refreshed",
                    message=f"Refreshed at {refresh_time_str}",
                    timeout=3
                )
            except Exception as e:
                st.warning(f"Notification error: {e}")
        if notify_telegram and BOT_TOKEN and CHAT_ID:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                requests.get(url, params={"chat_id": CHAT_ID, "text": f"Refreshed NSE Picker at {refresh_time_str}"}, timeout=5)
            except Exception as e:
                st.warning(f"Telegram notification error: {e}")

    # --------- INIT STATE ------------ #
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = {}  # symbol: {entry, sl, target, status}

    def get_price_data(symbol, period="1d", interval="5m"):
        # simple fetch function using yfinance
        df = yf.download(f"{symbol}.NS", period=period, interval=interval, progress=False)
        if df.empty:
            return pd.DataFrame()
        return df

    def notify_stock(symbol, last_price, entry, sl, tgt, msg,
                     desktop_enabled=False, telegram_enabled=False,
                     BOT_TOKEN=None, CHAT_ID=None):
        import streamlit as st
        import requests

        st.success(f"{msg} [{symbol}] (Price: {last_price}, Entry: {entry}, SL: {sl}, Target: {tgt})")

        # Desktop notification
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

        # Telegram notification
        if telegram_enabled and BOT_TOKEN and CHAT_ID:
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                text = f"{msg} [{symbol}]\nPrice: {last_price}\nEntry: {entry}\nSL: {sl}\nTarget: {tgt}"
                requests.get(url, params={"chat_id": CHAT_ID, "text": text}, timeout=5)
            except Exception as e:
                st.warning(f"Telegram notification error: {e}")

    # --------- DEMO PICKER RESULTS ------------ #
    # Manually define some "scanner" picks for demo
    demo_picks = [
        {"Symbol": "RELIANCE", "Entry": 2500, "StopLoss": 2480, "Target": 2550},
        {"Symbol": "TCS", "Entry": 3700, "StopLoss": 3680, "Target": 3750},
    ]

    st.title("Live Stocks Watchlist Demo")

    # --- Show Demo Picks and Add to Watchlist ---
    st.subheader("Scanner/Manual Picks")
    for pick in demo_picks:
        sym = pick["Symbol"]
        entry = pick["Entry"]
        stop = pick["StopLoss"]
        tgt = pick["Target"]

        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**{sym}**  | Entry: {entry} | SL: {stop} | Target: {tgt}")
        with col2:
            if st.button(f"Add {sym} to Watchlist", key=f"add_{sym}"):
                st.session_state.watchlist[sym] = {
                    "entry": entry,
                    "sl": stop,
                    "target": tgt,
                    "status": "Active"
                }
                st.success(f"Added {sym} to watchlist!")

    # --- Monitor Watchlist ---
    st.subheader("Live Watchlist & Alerts")

    remove_syms = []
    for sym, info in st.session_state.watchlist.items():
        df = get_price_data(sym, period="1d", interval="5m")
        if df.empty:
            curr_price = None
        else:
            curr_price = float(df["Close"].values[-1])

        entry = info["entry"]
        sl = info["sl"]
        tgt = info["target"]
        status = info["status"]
        color = "white"

        # Check hit/alert
        if curr_price is not None and status == "Active":
            if curr_price >= tgt:
                color = "green"
                notify_stock(
                    sym, curr_price, entry, sl, tgt, msg="🎯 Target hit!",
                    desktop_enabled=notify_desktop, telegram_enabled=notify_telegram,
                    BOT_TOKEN=BOT_TOKEN, CHAT_ID=CHAT_ID
                )

                info["status"] = "Target Hit"
                remove_syms.append(sym)
            elif curr_price <= sl:
                color = "red"
                notify_stock(
                    sym, curr_price, entry, sl, tgt, msg="⛔ Stoploss hit!",
                    desktop_enabled=notify_desktop, telegram_enabled=notify_telegram,
                    BOT_TOKEN=BOT_TOKEN, CHAT_ID=CHAT_ID
                )

                info["status"] = "Stop Hit"
                remove_syms.append(sym)
            else:
                color = "lightblue"

        st.markdown(
            f"<div style='color:{color};font-weight:bold;'>"
            f"{sym} | Last: {curr_price} | Entry: {entry} | SL: {sl} | Target: {tgt} | Status: {info['status']}</div>",
            unsafe_allow_html=True,
        )

    # Remove hit stocks from watchlist
    for sym in remove_syms:
        del st.session_state.watchlist[sym]

    st.info("Page auto-refresh will re-check alerts and prices.")
