"""
ai_ui.py - Enhanced AI prediction UI with detailed diagnostics (robustified)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import traceback
import logging
from numbers import Real
from ai_predictor import StockPredictor, PredictionTracker

logger = logging.getLogger(__name__)

# Initialize global instances
if 'predictor' not in st.session_state:
    st.session_state.predictor = StockPredictor()

if 'tracker' not in st.session_state:
    st.session_state.tracker = PredictionTracker()


def _fmt_val(x):
    if isinstance(x, Real):
        return f"{x:.4f}"
    try:
        # fall back to string
        return str(x)
    except Exception:
        return "<unserializable>"


def render_ai_confidence_gauge(prob_up, confidence):
    """Render circular confidence gauge"""
    # Defensive clamping
    try:
        prob_up = max(0.0, min(1.0, float(prob_up)))
    except Exception:
        prob_up = 0.5

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
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 45], 'color': 'rgba(239,68,68,0.18)'},
                {'range': [45, 55], 'color': 'rgba(148,163,184,0.12)'},
                {'range': [55, 100], 'color': 'rgba(16,185,129,0.12)'}
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


def _safe_features_df(features):
    # Try common structures (dict, Series, list, array...)
    try:
        if isinstance(features, dict):
            df = pd.DataFrame.from_dict(features, orient='index', columns=['Value'])
        else:
            df = pd.DataFrame([features]).T
            df.columns = ['Value']
        df.index.name = 'Feature'
        df['Value'] = df['Value'].apply(_fmt_val)
        return df
    except Exception:
        # fallback
        return pd.DataFrame({'Value': [str(features)]})


def render_ai_prediction(symbol, df, technical_signal=None, min_confidence=0.6, instance=None):
    """
    Enhanced AI prediction with detailed diagnostics even for low confidence
    
    Args:
        symbol: Stock symbol
        df: DataFrame with price data
        technical_signal: Technical analysis signal (optional)
        min_confidence: Minimum confidence threshold (0-1)
        instance: Unique instance number for this rendering (optional)
    """
    predictor = st.session_state.get('predictor')
    tracker = st.session_state.get('tracker')
    
    # Use instance number as key suffix if provided
    key_suffix = f"_{instance}" if instance is not None else ""

    if predictor is None:
        st.error("❌ AI Predictor failed to initialize. Check console for errors.")
        return

    features = None
    try:
        features = predictor.prepare_features(df)
    except Exception:
        logger.exception("Error preparing features")
        st.error("❌ Error preparing features for prediction. See console/logs.")
        return

    if features is None:
        st.warning("⚠️ Insufficient data for AI prediction (need at least 50 candles)")
        return

    # Check if models are trained
    models_trained = getattr(predictor, 'rf_model', None) is not None and getattr(predictor, 'lr_model', None) is not None

    if not models_trained:
        st.error("❌ **AI Models Not Trained Yet**")
        st.markdown("""
<div style="padding:16px;background:rgba(239,68,68,0.1);border-radius:10px;border-left:4px solid #ef4444;margin:16px 0;">
<h4 style="color:#ef4444;margin-top:0;">🤖 Why Am I Seeing This?</h4>
<p style="color:#fca5a5;font-size:13px;line-height:1.6;">The AI prediction models haven't been trained yet. This is normal for a first-time setup.</p>
</div>
""", unsafe_allow_html=True)

        with st.expander("🔍 View Extracted Features (Debug Info)", expanded=False):
            st.markdown("**Features extracted from current stock data:**")
            features_df = _safe_features_df(features)
            st.dataframe(features_df, use_container_width=True)
            st.info("💡 These features will be used to train the models.")
        return

    # Predict with spinner and error handling
    try:
        with st.spinner("Running AI prediction..."):
            prob_up, confidence, ai_prediction, details = predictor.predict(features)
    except Exception:
        logger.exception("Prediction failed")
        st.error("❌ Prediction failed. See logs for details.")
        return

    # Ensure safe types & defaults
    try:
        prob_up = float(prob_up)
    except Exception:
        prob_up = 0.5
    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.0

    details = details or {}
    top_features = details.get('top_features', [])

    st.markdown("### 🤖 AI Prediction Results")

    col_gauge, col_details = st.columns([1, 1])
    with col_gauge:
        fig = render_ai_confidence_gauge(prob_up, confidence)
        st.plotly_chart(fig, use_container_width=True, key=f"gauge_{symbol}{key_suffix}")

    with col_details:
        confidence_color = "#10b981" if confidence > 0.75 else "#f59e0b" if confidence > 0.6 else "#ef4444"
        st.markdown(f"""
<div style="background:rgba(255,255,255,0.05);padding:16px;border-radius:10px;height:100%;">
<h4 style="margin-top:0;color:#3b82f6;">📊 Prediction Details</h4>
<div style="margin:12px 0;"><span style="color:#94a3b8;">Probability UP:</span>
<span style="color:#10b981;font-size:18px;font-weight:700;margin-left:8px;">{prob_up*100:.1f}%</span></div>
<div style="margin:12px 0;"><span style="color:#94a3b8;">Probability DOWN:</span>
<span style="color:#ef4444;font-size:18px;font-weight:700;margin-left:8px;">{(1-prob_up)*100:.1f}%</span></div>
<div style="margin:12px 0;"><span style="color:#94a3b8;">AI Confidence:</span>
<span style="color:{confidence_color};font-size:18px;font-weight:700;margin-left:8px;">{confidence*100:.0f}%</span></div>
</div>
""", unsafe_allow_html=True)

    if confidence < min_confidence:
        st.markdown(f"""
<div style="padding:14px;background:rgba(245,158,11,0.15);border-radius:10px;border-left:4px solid #f59e0b;margin:16px 0;">
<h4 style="color:#f59e0b;margin-top:0;">⚠️ Low Confidence Warning</h4>
<p style="color:#fcd34d;font-size:13px;margin:0;">
AI confidence ({confidence*100:.0f}%) is below your minimum threshold ({min_confidence*100:.0f}%). Exercise caution.
</p>
</div>
""", unsafe_allow_html=True)

    # Model Internals
    with st.expander("🔬 Model Internals (Advanced)", expanded=False):
        st.markdown("**Individual Model Predictions:**")
        col_rf, col_lr = st.columns(2)
        rf_prob = float(details.get('rf_prediction', 0.5))
        lr_prob = float(details.get('lr_prediction', 0.5))

        with col_rf:
            st.markdown(f"""
<div style="background:rgba(34,197,94,0.08);padding:12px;border-radius:8px;text-align:center;">
<div style="color:#86efac;font-size:11px;">RANDOM FOREST</div>
<div style="color:#22c55e;font-size:24px;font-weight:700;">{rf_prob*100:.1f}%</div>
<div style="color:#6ee7b7;font-size:10px;">Probability UP</div>
</div>
""", unsafe_allow_html=True)

        with col_lr:
            st.markdown(f"""
<div style="background:rgba(59,130,246,0.08);padding:12px;border-radius:8px;text-align:center;">
<div style="color:#93c5fd;font-size:11px;">LOGISTIC REGRESSION</div>
<div style="color:#3b82f6;font-size:24px;font-weight:700;">{lr_prob*100:.1f}%</div>
<div style="color:#93c5fd;font-size:10px;">Probability UP</div>
</div>
""", unsafe_allow_html=True)

        # Agreement percent (0-100)
        agreement_pct = max(0.0, min(100.0, (1.0 - abs(rf_prob - lr_prob)) * 100.0))
        st.info(f"**Ensemble:** Averaging | **Final Prediction:** {prob_up*100:.1f}% UP | **Agreement:** {agreement_pct:.1f}%")

    # Consensus Analysis (safe)
    if technical_signal:
        st.markdown("---")
        st.markdown("#### 🎯 Technical vs AI Consensus")
        tech_direction = "BULLISH" if technical_signal in ["BUY", "LONG"] else "BEARISH" if technical_signal in ["SELL", "SHORT"] else "NEUTRAL"
        agreement = (tech_direction == (ai_prediction or "").upper())
        col_tech, col_ai, col_consensus = st.columns(3)

        with col_tech:
            tech_color = "#10b981" if tech_direction == "BULLISH" else "#ef4444" if tech_direction == "BEARISH" else "#94a3b8"
            st.markdown(f"<div style='text-align:center;padding:12px;border-radius:8px;border:2px solid {tech_color};'><div style='color:#94a3b8;font-size:11px;'>TECHNICAL</div><div style='color:{tech_color};font-size:20px;font-weight:700;'>{tech_direction}</div></div>", unsafe_allow_html=True)

        with col_ai:
            ai_dir = (ai_prediction or "NEUTRAL").upper()
            ai_color = "#10b981" if ai_dir == "BULLISH" else "#ef4444" if ai_dir == "BEARISH" else "#94a3b8"
            st.markdown(f"<div style='text-align:center;padding:12px;border-radius:8px;border:2px solid {ai_color};'><div style='color:#94a3b8;font-size:11px;'>AI PREDICTION</div><div style='color:{ai_color};font-size:20px;font-weight:700;'>{ai_dir}</div></div>", unsafe_allow_html=True)

        with col_consensus:
            if agreement and tech_direction != "NEUTRAL":
                st.markdown("<div style='text-align:center;padding:12px;border-radius:8px;background:linear-gradient(135deg,#10b981 0%,#059669 100%);color:white;'>✅ STRONG</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center;padding:12px;border-radius:8px;border:2px solid #f59e0b;color:#f59e0b;'>⚠️ MIXED</div>", unsafe_allow_html=True)

    # Feature Importance
    with st.expander("📌 What's Driving This Prediction?", expanded=False):
        st.markdown("**Top Contributing Factors:**")
        if top_features:
            for idx, item in enumerate(top_features, 1):
                # expect tuple (feature_name, importance)
                try:
                    feature, importance = item
                    importance = float(importance)
                except Exception:
                    feature, importance = str(item), 0.0
                feature_name = str(feature).replace('_', ' ').title()
                pct = max(0.0, min(100.0, importance * 100.0))
                st.markdown(f"<div style='margin:8px 0;padding:8px;border-radius:6px;'><div style='display:flex;justify-content:space-between;margin-bottom:4px;'><span style='color:#94a3b8;font-size:13px;'>{idx}. {feature_name}</span><span style='color:white;font-size:13px;font-weight:600;'>{pct:.1f}%</span></div><div style='background:#1e293b;border-radius:4px;height:6px;'><div style='background:#3b82f6;width:{pct}%;height:100%;border-radius:4px;'></div></div></div>", unsafe_allow_html=True)
        else:
            st.info("No feature importance available for this model run.")

    # Show extracted features
    with st.expander("📊 Raw Features Used", expanded=False):
        st.markdown("**All features extracted for this prediction:**")
        features_df = _safe_features_df(features)
        st.dataframe(features_df, use_container_width=True, height=400, key=f"features_df_{symbol}{key_suffix}")

    # Track prediction
    current_price = None
    try:
        current_price = float(df['Close'].iloc[-1])
    except Exception:
        current_price = None

    if st.button("📝 Save This Prediction for Tracking", key=f"save_pred_{symbol}{key_suffix}"):
        try:
            tracker.save_prediction(symbol, ai_prediction, prob_up, confidence, current_price)
            st.success("✅ Prediction saved! We'll verify its accuracy later.")
        except Exception:
            logger.exception("Failed to save prediction")
            st.error("Failed to save prediction. See logs.")

    # Show accuracy stats
    stats = tracker.get_accuracy_stats() if tracker else {}
    if stats and stats.get('total', 0) > 0:
        st.markdown("---")
        st.markdown("#### 📊 AI Model Performance")
        col_acc1, col_acc2, col_acc3, col_acc4 = st.columns(4)

        with col_acc1:
            st.metric("Overall Accuracy", f"{stats.get('accuracy', 0.0):.1f}%", delta=f"{stats.get('correct',0)}/{stats.get('total',0)}")

        with col_acc2:
            st.metric("Bullish Accuracy", f"{stats.get('bullish_accuracy', 0.0):.1f}%")

        with col_acc3:
            st.metric("Bearish Accuracy", f"{stats.get('bearish_accuracy', 0.0):.1f}%")

        with col_acc4:
            st.metric("Last 10 Predictions", f"{stats.get('recent_10', 0.0):.1f}%")
