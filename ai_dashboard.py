"""
ai_dashboard.py - Complete AI Predictions Dashboard
"""

import streamlit as st
import pandas as pd
from ai_predictor import StockPredictor, PredictionTracker
from ai_ui import render_ai_prediction
from functions import extract_symbol_df, compute_indicators
import os
import json


def render_ai_training_interface():
    """AI Model Training Interface"""
    
    st.markdown("## 🛠️ AI Model Training & Management")
    
    # Check if models exist
    models_exist = os.path.exists("ai_models/rf_model.pkl")
    
    col_info, col_actions = st.columns([2, 1])
    
    with col_info:
        if models_exist:
            st.success("✅ **AI Models Trained & Ready**")
            
            # Show model info
            try:
                if os.path.exists("ai_models/feature_names.json"):
                    with open("ai_models/feature_names.json", 'r') as f:
                        features = json.load(f)
                    
                    st.markdown(f"""
**Model Details:**
- 📊 Features: {len(features)}
- 🤖 Models: Random Forest + Logistic Regression
- 🎯 Task: Direction prediction (UP/DOWN)
- 📈 Training data: Real NSE historical data
""")
            except:
                pass
        else:
            st.warning("⚠️ **AI Models Not Trained**")
            
            st.markdown("""
**Training Process:**
- Downloads 6 months of data from 30 top stocks
- Creates 1000+ training samples
- Trains 2 ML models (RF + LR)
- Time: 3-5 minutes (one-time setup)
""")
    
    with col_actions:
        if models_exist:
            if st.button("🔄 Retrain Models", use_container_width=True, type="secondary"):
                from sidebar import train_ai_models
                with st.spinner("Retraining models..."):
                    success, msg = train_ai_models()
                    if success:
                        st.success("✅ Models retrained!")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            
            if st.button("🗑️ Delete Models", use_container_width=True):
                try:
                    import shutil
                    if os.path.exists("ai_models"):
                        shutil.rmtree("ai_models")
                    st.success("✅ Models deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")
        else:
            if st.button("🚀 Train AI Models Now", use_container_width=True, type="primary"):
                from sidebar import train_ai_models
                success, msg = train_ai_models()
                
                if success:
                    st.success("✅ Training complete!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    
    st.markdown("---")
    
    # Performance tracking
    tracker = st.session_state.tracker
    stats = tracker.get_accuracy_stats()
    
    if stats['total'] > 0:
        st.markdown("## 📊 AI Performance Metrics")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.metric("Overall Accuracy", f"{stats['accuracy']:.1f}%", 
                     delta=f"{stats['correct']}/{stats['total']}")
        
        with col_m2:
            st.metric("Bullish Accuracy", f"{stats['bullish_accuracy']:.1f}%")
        
        with col_m3:
            st.metric("Bearish Accuracy", f"{stats['bearish_accuracy']:.1f}%")
        
        with col_m4:
            st.metric("Last 10 Trades", f"{stats['recent_10']:.1f}%")


def render_ai_dashboard(shortlisted_stocks, df_candidates, df_batch):
    """Main AI predictions dashboard"""
    
    # Training interface at top
    render_ai_training_interface()
    
    # Check if models are trained
    predictor = st.session_state.predictor
    
    if predictor is None or predictor.rf_model is None:
        st.info("👆 Train AI models above to see predictions for qualified stocks")
        return
    
    st.markdown("## 🎯 AI Predictions for Qualified Stocks")
    
    # Filters
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        min_confidence = st.slider("Minimum Confidence", 0, 100, 60, 5,
                                   help="Filter predictions by AI confidence level")
    
    with col_filter2:
        prediction_filter = st.multiselect("Filter by Prediction", 
                                          ["BULLISH", "BEARISH", "NEUTRAL"],
                                          default=["BULLISH", "BEARISH", "NEUTRAL"])
    
    st.markdown("---")
    
    # Render predictions for each stock
    predictions_shown = 0
    
    for stock in shortlisted_stocks:
        candidate_row = df_candidates.loc[stock]
        score = candidate_row.get("Score", 0)
        
        df_stock = extract_symbol_df(df_batch, stock)
        
        if df_stock is None or df_stock.empty:
            continue
        
        df_stock = compute_indicators(df_stock)
        
        if df_stock.empty:
            continue
        
        # Quick prediction check for filtering
        features = predictor.prepare_features(df_stock)
        if features:
            prob_up, confidence, ai_prediction, details = predictor.predict(features)
            
            # Apply filters
            if confidence * 100 < min_confidence:
                continue
            
            if ai_prediction not in prediction_filter:
                continue
            
            predictions_shown += 1
            
            # Determine technical signal
            technical_signal = "BUY" if score >= 6 else "NEUTRAL"
            
            # Show full AI analysis
            with st.expander(f"🤖 {stock} - AI Analysis (Technical Score: {score})", expanded=False):
                # Add anchor for linking from scanner
                st.markdown(f'<div id="ai-tab-{stock}"></div>', unsafe_allow_html=True)
                
                render_ai_prediction(stock, df_stock, technical_signal, min_confidence=min_confidence/100)
    
    if predictions_shown == 0:
        st.info(f"ℹ️ No stocks match your filters (Confidence ≥ {min_confidence}%)")
