from pathlib import Path
import streamlit as st
import pandas as pd
from ai_predictor import StockPredictor, PredictionTracker
from ai_ui import render_ai_prediction
from functions import extract_symbol_df, compute_indicators
from paper import safe_rerun
import json
import shutil

MODELS_DIR = Path("ai_models")


def render_ai_training_interface():
    """AI Model Training Interface"""
    st.markdown("## 🛠️ AI Model Training & Management")

    models_exist = MODELS_DIR.is_dir() and (MODELS_DIR / "rf_model.pkl").exists()
    col_info, col_actions = st.columns([2, 1])

    with col_info:
        if models_exist:
            st.success("✅ **AI Models Trained & Ready**")
            try:
                feature_file = MODELS_DIR / "feature_names.json"
                if feature_file.exists():
                    with feature_file.open("r") as f:
                        features = json.load(f)
                    st.markdown(
                        f"""**Model Details:**
- 📊 Features: {len(features)}
- 🤖 Models: Random Forest + Logistic Regression
- 🎯 Task: Direction prediction (UP/DOWN)
- 📈 Training data: Real NSE historical data
"""
                    )
            except (json.JSONDecodeError, OSError) as e:
                st.warning(f"⚠️ Could not load model metadata: {e}")
        else:
            st.warning("⚠️ **AI Models Not Trained**")
            st.markdown(
                """**Training Process:**
- Downloads 6 months of data from 30 top stocks
- Creates 1000+ training samples
- Trains 2 ML models (RF + LR)
- Time: 3-5 minutes (one-time setup)
"""
            )

    with col_actions:
        from sidebar import train_ai_models  # local import kept as original

        if models_exist:
            if st.button("🔄 Retrain Models", use_container_width=True):
                with st.spinner("Retraining models..."):
                    success, msg = train_ai_models()
                    if success:
                        st.success("✅ Models retrained!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            if st.button("🗑️ Delete Models", use_container_width=True):
                try:
                    if MODELS_DIR.exists():
                        shutil.rmtree(MODELS_DIR)
                    st.success("✅ Models deleted")
                    st.rerun()
                except OSError as e:
                    st.error(f"❌ {e}")
        else:
            if st.button("🚀 Train AI Models Now", use_container_width=True):
                with st.spinner("Training models..."):
                    success, msg = train_ai_models()
                    if success:
                        st.success("✅ Training complete!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    st.markdown("---")

    # Performance tracking (use safe access)
    tracker = st.session_state.get("tracker")
    if tracker is None:
        # keep tracker optional — no crash if not set
        st.info("No performance tracker initialized yet.")
        return

    try:
        stats = tracker.get_accuracy_stats()
    except Exception as e:
        st.warning(f"Could not read tracker stats: {e}")
        return

    total = stats.get("total", 0)
    if total > 0:
        st.markdown("## 📊 AI Performance Metrics")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

        with col_m1:
            st.metric(
                "Overall Accuracy",
                f"{stats.get('accuracy', 0):.1f}%",
                delta=f"{stats.get('correct', 0)}/{total}",
            )
        with col_m2:
            st.metric("Bullish Accuracy", f"{stats.get('bullish_accuracy', 0):.1f}%")
        with col_m3:
            st.metric("Bearish Accuracy", f"{stats.get('bearish_accuracy', 0):.1f}%")
        with col_m4:
            st.metric("Last 10 Trades", f"{stats.get('recent_10', 0):.1f}%")


def render_ai_dashboard(shortlisted_stocks, df_candidates, df_batch):
    """Main AI predictions dashboard"""
    render_ai_training_interface()

    predictor: StockPredictor = st.session_state.get("predictor")
    if predictor is None or getattr(predictor, "rf_model", None) is None:
        st.info("👆 Train AI models above to see predictions for qualified stocks")
        return
        
    # Initialize instance counter
    instance_counter = 0

    st.markdown("## 🎯 AI Predictions for Qualified Stocks")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        min_confidence = st.slider(
            "Minimum Confidence (%)", 0, 100, 60, 5, help="Filter predictions by AI confidence level"
        )
    with col_filter2:
        prediction_filter = st.multiselect(
            "Filter by Prediction",
            ["BULLISH", "BEARISH", "NEUTRAL"],
            default=["BULLISH", "BEARISH", "NEUTRAL"],
        )

    st.markdown("---")

    predictions_shown = 0
    for stock in shortlisted_stocks:
        # safe access to candidate row
        try:
            candidate_row = df_candidates.loc[stock]
        except KeyError:
            continue
        score = candidate_row.get("Score", 0)

        df_stock = extract_symbol_df(df_batch, stock)
        if df_stock is None or df_stock.empty:
            continue

        df_stock = compute_indicators(df_stock)
        if df_stock is None or df_stock.empty:
            continue

        # Prepare features (treat None as no-features)
        try:
            features = predictor.prepare_features(df_stock)
        except Exception as e:
            st.warning(f"Skipping {stock}: feature preparation error: {e}")
            continue

        if features is None:
            continue

        try:
            prob_up, confidence, ai_prediction, details = predictor.predict(features)
        except Exception as e:
            st.warning(f"Skipping {stock}: prediction error: {e}")
            continue

        # Normalize confidence to percentage for comparisons
        conf_pct = None
        try:
            if isinstance(confidence, (int, float)):
                if confidence <= 1:
                    conf_pct = float(confidence) * 100.0
                else:
                    conf_pct = float(confidence)
            else:
                conf_pct = float(confidence)
        except Exception:
            conf_pct = 0.0

        if conf_pct < min_confidence:
            continue

        # Normalize prediction label and apply filter
        if ai_prediction is None:
            continue
        if ai_prediction.upper() not in prediction_filter:
            continue

        predictions_shown += 1
        instance_counter += 1
        technical_signal = "BUY" if score >= 6 else "NEUTRAL"

        with st.expander(f"🤖 {stock} - AI Analysis (Technical Score: {score})", expanded=False):
            st.markdown(f'<div id="ai-tab-{stock}_{instance_counter}"></div>', unsafe_allow_html=True)
            # Pass normalized min_confidence (0..1) to rendering helper
            render_ai_prediction(stock, df_stock, technical_signal, min_confidence=min_confidence / 100.0, instance=instance_counter)

    if predictions_shown == 0:
        st.info(f"ℹ️ No stocks match your filters (Confidence ≥ {min_confidence}%)")
        if st.button("Loosen Filters"):
            # simple client-side suggestion: reset to a lower threshold
            st.session_state["min_confidence"] = max(0, min_confidence - 20)
            safe_rerun()
