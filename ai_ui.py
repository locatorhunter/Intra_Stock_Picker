"""
ai_ui.py - Enhanced AI prediction UI with detailed diagnostics
"""

import streamlit as st
import pandas as pd 
from ai_predictor import StockPredictor, PredictionTracker
import plotly.graph_objects as go

# Initialize global instances
if 'predictor' not in st.session_state:
    st.session_state.predictor = StockPredictor()

if 'tracker' not in st.session_state:
    st.session_state.tracker = PredictionTracker()


def render_ai_confidence_gauge(prob_up, confidence):
    """Render circular confidence gauge"""
    
    if prob_up > 0.55:
        color = "#10b981"
        label = "BULLISH"
    elif prob_up < 0.45:
        color = "#ef4444"
        label = "BEARISH"
    else:
        color = "#94a3b8"
        label = "NEUTRAL"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=prob_up * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"AI Prediction: {label}", 'font': {'size': 16}},
        delta={'reference': 50, 'suffix': '%'},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': "rgba(255,255,255,0.1)",
            'borderwidth': 2,
            'bordercolor': color,
            'steps': [
                {'range': [0, 45], 'color': 'rgba(239,68,68,0.2)'},
                {'range': [45, 55], 'color': 'rgba(148,163,184,0.2)'},
                {'range': [55, 100], 'color': 'rgba(16,185,129,0.2)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': prob_up * 100
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"}
    )
    
    return fig


def render_ai_prediction(symbol, df, technical_signal=None, min_confidence=0.6):
    """
    Enhanced AI prediction with detailed diagnostics even for low confidence
    
    Args:
        symbol: Stock symbol
        df: Price dataframe with indicators
        technical_signal: Technical analysis signal
        min_confidence: Minimum confidence to show prediction (0-1)
    """
    
    # Access from session state (already initialized in main.py)
    predictor = st.session_state.predictor
    tracker = st.session_state.tracker
    
    if predictor is None:
        st.error("❌ AI Predictor failed to initialize. Check console for errors.")
        return
    features = predictor.prepare_features(df)
    
    if features is None:
        st.warning("⚠️ Insufficient data for AI prediction (need at least 50 candles)")
        return
    
    # Check if models are trained
    models_trained = predictor.rf_model is not None and predictor.lr_model is not None
    
    if not models_trained:
        st.error("❌ **AI Models Not Trained Yet**")
        
        st.markdown("""
<div style="padding:16px;background:rgba(239,68,68,0.1);border-radius:10px;border-left:4px solid #ef4444;margin:16px 0;">
<h4 style="color:#ef4444;margin-top:0;">🤖 Why Am I Seeing This?</h4>

<p style="color:#fca5a5;font-size:13px;line-height:1.6;">
The AI prediction models haven't been trained yet. This is normal for a first-time setup.
</p>

<h5 style="color:#ef4444;margin-bottom:8px;">📋 What the AI Needs:</h5>
<ul style="color:#fca5a5;font-size:12px;line-height:1.8;margin:0;">
<li>Historical stock data (100+ samples)</li>
<li>Price movements, volume patterns, and technical indicators</li>
<li>Training time: 2-5 minutes (one-time setup)</li>
</ul>

<h5 style="color:#ef4444;margin:12px 0 8px 0;">🚀 How to Train:</h5>
<ol style="color:#fca5a5;font-size:12px;line-height:1.8;margin:0;">
<li>Go to <strong>Sidebar → 🤖 AI Settings</strong></li>
<li>Click <strong>"Train AI Models"</strong> button</li>
<li>Wait for training to complete</li>
<li>Refresh this page</li>
</ol>
</div>
""", unsafe_allow_html=True)
        
        # Show extracted features for debugging
        with st.expander("🔍 View Extracted Features (Debug Info)", expanded=False):
            st.markdown("**Features extracted from current stock data:**")
            
            features_df = pd.DataFrame([features]).T
            features_df.columns = ['Value']
            features_df['Value'] = features_df['Value'].apply(lambda x: f"{x:.4f}" if isinstance(x, float) else str(x))
            
            st.dataframe(features_df, use_container_width=True)
            
            st.info("""
            💡 These features are ready for the AI model. Once you train the models, 
            they will use these values to make predictions.
            """)
        
        return
    
    # Get prediction
    prob_up, confidence, ai_prediction, details = predictor.predict(features)
    
    # Always show basic prediction info
    st.markdown("### 🤖 AI Prediction Results")
    
    # Main prediction display
    col_gauge, col_details = st.columns([1, 1])
    
    with col_gauge:
        fig = render_ai_confidence_gauge(prob_up, confidence)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_details:
        confidence_color = "#10b981" if confidence > 0.75 else "#f59e0b" if confidence > 0.6 else "#ef4444"
        
        st.markdown(f"""
<div style="background:rgba(255,255,255,0.05);padding:16px;border-radius:10px;height:100%;">
<h4 style="margin-top:0;color:#3b82f6;">📊 Prediction Details</h4>

<div style="margin:12px 0;">
<span style="color:#94a3b8;">Probability UP:</span>
<span style="color:#10b981;font-size:18px;font-weight:700;margin-left:8px;">{prob_up*100:.1f}%</span>
</div>

<div style="margin:12px 0;">
<span style="color:#94a3b8;">Probability DOWN:</span>
<span style="color:#ef4444;font-size:18px;font-weight:700;margin-left:8px;">{(1-prob_up)*100:.1f}%</span>
</div>

<div style="margin:12px 0;">
<span style="color:#94a3b8;">AI Confidence:</span>
<span style="color:{confidence_color};font-size:18px;font-weight:700;margin-left:8px;">{confidence*100:.0f}%</span>
</div>

<div style="margin-top:16px;padding:10px;background:rgba(59,130,246,0.1);border-radius:6px;border-left:3px solid #3b82f6;">
<span style="color:#93c5fd;font-size:11px;">
💡 Confidence >75%: Strong | 60-75%: Moderate | <60%: Weak
</span>
</div>
</div>
""", unsafe_allow_html=True)
    
    # Low confidence warning (but still show data)
    if confidence < min_confidence:
        st.markdown(f"""
<div style="padding:14px;background:rgba(245,158,11,0.15);border-radius:10px;border-left:4px solid #f59e0b;margin:16px 0;">
<h4 style="color:#f59e0b;margin-top:0;">⚠️ Low Confidence Warning</h4>
<p style="color:#fcd34d;font-size:13px;margin:0;">
AI confidence ({confidence*100:.0f}%) is below your minimum threshold ({min_confidence*100:.0f}%). 
The prediction is shown below for your analysis, but use with extra caution.
</p>

<details style="margin-top:12px;">
<summary style="color:#fcd34d;cursor:pointer;font-size:12px;font-weight:600;">
📋 Click to see why confidence is low
</summary>
<div style="margin-top:8px;padding:10px;background:rgba(0,0,0,0.2);border-radius:6px;">
<p style="color:#fcd34d;font-size:11px;margin:0;line-height:1.6;">
<strong>Possible reasons for low confidence:</strong><br>
• Mixed signals from technical indicators<br>
• Stock showing unusual/unpredictable behavior<br>
• Recent market volatility or news impact<br>
• Limited historical patterns matching current setup<br>
• Consolidation phase (direction unclear)
</p>
</div>
</details>
</div>
""", unsafe_allow_html=True)
    
    # Model Details
    with st.expander("🔬 Model Internals (Advanced)", expanded=False):
        st.markdown("**Individual Model Predictions:**")
        
        col_rf, col_lr = st.columns(2)
        
        with col_rf:
            rf_pred = details.get('rf_prediction', 0.5) * 100
            st.markdown(f"""
<div style="background:rgba(34,197,94,0.1);padding:12px;border-radius:8px;text-align:center;">
<div style="color:#86efac;font-size:11px;">RANDOM FOREST</div>
<div style="color:#22c55e;font-size:24px;font-weight:700;">{rf_pred:.1f}%</div>
<div style="color:#6ee7b7;font-size:10px;">Probability UP</div>
</div>
""", unsafe_allow_html=True)
        
        with col_lr:
            lr_pred = details.get('lr_prediction', 0.5) * 100
            st.markdown(f"""
<div style="background:rgba(59,130,246,0.1);padding:12px;border-radius:8px;text-align:center;">
<div style="color:#93c5fd;font-size:11px;">LOGISTIC REGRESSION</div>
<div style="color:#3b82f6;font-size:24px;font-weight:700;">{lr_pred:.1f}%</div>
<div style="color:#93c5fd;font-size:10px;">Probability UP</div>
</div>
""", unsafe_allow_html=True)
        
        st.info(f"""
        **Ensemble Method:** Averaging both models  
        **Final Prediction:** {prob_up*100:.1f}% UP  
        **Agreement Score:** {(1 - abs(rf_pred - lr_pred)/100):.1%}
        """)
    
    # Consensus Analysis
    if technical_signal:
        st.markdown("---")
        st.markdown("#### 🎯 Technical vs AI Consensus")
        
        tech_direction = "BULLISH" if technical_signal in ["BUY", "LONG"] else "BEARISH" if technical_signal in ["SELL", "SHORT"] else "NEUTRAL"
        agreement = (tech_direction == ai_prediction)
        
        col_tech, col_ai, col_consensus = st.columns(3)
        
        with col_tech:
            tech_color = "#10b981" if tech_direction == "BULLISH" else "#ef4444" if tech_direction == "BEARISH" else "#94a3b8"
            st.markdown(f"""
<div style="text-align:center;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;border:2px solid {tech_color};">
<div style="color:#94a3b8;font-size:11px;">TECHNICAL</div>
<div style="color:{tech_color};font-size:20px;font-weight:700;">{tech_direction}</div>
</div>
""", unsafe_allow_html=True)
        
        with col_ai:
            ai_color = "#10b981" if ai_prediction == "BULLISH" else "#ef4444" if ai_prediction == "BEARISH" else "#94a3b8"
            st.markdown(f"""
<div style="text-align:center;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;border:2px solid {ai_color};">
<div style="color:#94a3b8;font-size:11px;">AI PREDICTION</div>
<div style="color:{ai_color};font-size:20px;font-weight:700;">{ai_prediction}</div>
</div>
""", unsafe_allow_html=True)
        
        with col_consensus:
            if agreement and tech_direction != "NEUTRAL":
                consensus_html = f"""
<div style="text-align:center;padding:12px;background:linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius:8px;border:2px solid #10b981;box-shadow:0 4px 8px rgba(16,185,129,0.3);">
<div style="color:white;font-size:11px;">CONSENSUS</div>
<div style="color:white;font-size:18px;font-weight:700;">✅ STRONG {tech_direction}</div>
<div style="color:rgba(255,255,255,0.8);font-size:10px;margin-top:4px;">Both agree!</div>
</div>
"""
            else:
                consensus_html = f"""
<div style="text-align:center;padding:12px;background:rgba(245,158,11,0.2);border-radius:8px;border:2px solid #f59e0b;">
<div style="color:#fcd34d;font-size:11px;">CONSENSUS</div>
<div style="color:#f59e0b;font-size:18px;font-weight:700;">⚠️ MIXED</div>
<div style="color:#fcd34d;font-size:10px;margin-top:4px;">Signals differ</div>
</div>
"""
            st.markdown(consensus_html, unsafe_allow_html=True)
    
    # Feature Importance
    with st.expander("📌 What's Driving This Prediction?", expanded=False):
        st.markdown("**Top Contributing Factors:**")
        
        for idx, (feature, importance) in enumerate(details['top_features'], 1):
            feature_name = feature.replace('_', ' ').title()
            
            st.markdown(f"""
<div style="margin:8px 0;padding:8px;background:rgba(255,255,255,0.03);border-radius:6px;">
<div style="display:flex;justify-content:space-between;margin-bottom:4px;">
<span style="color:#94a3b8;font-size:13px;">{idx}. {feature_name}</span>
<span style="color:white;font-size:13px;font-weight:600;">{importance*100:.1f}%</span>
</div>
<div style="background:#1e293b;border-radius:4px;height:6px;">
<div style="background:#3b82f6;width:{importance*100}%;height:100%;border-radius:4px;"></div>
</div>
</div>
""", unsafe_allow_html=True)
        
        st.markdown("""
<div style="padding:10px;background:rgba(59,130,246,0.1);border-radius:6px;margin-top:12px;">
<span style="color:#93c5fd;font-size:11px;">
💡 <strong>How to interpret:</strong> Higher percentage = more influence on the prediction. 
The top 2-3 factors usually account for 60-70% of the decision.
</span>
</div>
""", unsafe_allow_html=True)
    
    # Show extracted features
    with st.expander("📊 Raw Features Used", expanded=False):
         st.markdown("**All features extracted for this prediction:**")
         
         # Don't re-import pd here - use the one from top of file
         features_df = pd.DataFrame([features]).T
         features_df.columns = ['Value']
         features_df.index.name = 'Feature'
         
         # Format values
         features_df['Value'] = features_df['Value'].apply(
             lambda x: f"{x:.4f}" if isinstance(x, float) else str(x)
         )
         
         st.dataframe(features_df, use_container_width=True, height=400)
    
    # Track prediction
    tracker = st.session_state.tracker
    current_price = float(df['Close'].iloc[-1])
    
    if st.button("📝 Save This Prediction for Tracking", key=f"save_pred_{symbol}"):
        tracker.save_prediction(symbol, ai_prediction, prob_up, confidence, current_price)
        st.success(f"✅ Prediction saved! We'll verify its accuracy later.")
    
    # Show accuracy stats
    stats = tracker.get_accuracy_stats()
    if stats['total'] > 0:
        st.markdown("---")
        st.markdown("#### 📊 AI Model Performance")
        
        col_acc1, col_acc2, col_acc3, col_acc4 = st.columns(4)
        
        with col_acc1:
            acc_color = "#10b981" if stats['accuracy'] > 60 else "#f59e0b" if stats['accuracy'] > 50 else "#ef4444"
            st.metric("Overall Accuracy", f"{stats['accuracy']:.1f}%", 
                     delta=f"{stats['correct']}/{stats['total']}")
        
        with col_acc2:
            st.metric("Bullish Accuracy", f"{stats['bullish_accuracy']:.1f}%")
        
        with col_acc3:
            st.metric("Bearish Accuracy", f"{stats['bearish_accuracy']:.1f}%")
        
        with col_acc4:
            st.metric("Last 10 Predictions", f"{stats['recent_10']:.1f}%")
