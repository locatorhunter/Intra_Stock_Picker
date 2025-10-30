"""
ai_predictor.py - ML-based price prediction module (improved)
"""

import os
import json
import pickle
import logging
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Constants
MODEL_DIR = "ai_models"
PREDICTIONS_FILE = "predictions_history.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockPredictor:
    """ML-based stock direction predictor"""

    def __init__(self):
        self.rf_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.feature_names = []

        os.makedirs(MODEL_DIR, exist_ok=True)
        self.load_models()

    def prepare_features(self, df: pd.DataFrame, min_length: int = 20):
        """
        Extract ML features from price data.
        Returns dict or None if insufficient data.
        """
        if df is None or len(df) < min_length:
            return None

        # Ensure numeric columns exist and are valid
        required_cols = ['Close', 'High', 'Low', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                logger.debug("Missing column %s in df, aborting feature prep", col)
                return None
            # Validate numeric data
            if not pd.to_numeric(df[col], errors='coerce').notna().all():
                logger.warning("Invalid numeric data in column %s", col)
                return None
            # Check for zeros in price columns that could cause division issues
            if col != 'Volume' and (df[col] <= 0).any():
                logger.warning("Found zero or negative values in price column %s", col)
                return None

        # Use rolling with min_periods to avoid NaNs where possible
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        features = {}

        # Price-based features: safe pct_change calls with try/except
        def safe_pct_change(series, periods):
            try:
                return float(series.pct_change(periods).iloc[-1])
            except Exception:
                return 0.0

        features['price_change_1'] = safe_pct_change(close, 1)
        features['price_change_5'] = safe_pct_change(close, 5)
        features['price_change_10'] = safe_pct_change(close, 10)
        features['price_change_20'] = safe_pct_change(close, 20)

        # Moving averages with fallbacks
        sma20 = close.rolling(20, min_periods=1).mean().iloc[-1]
        sma50 = close.rolling(50, min_periods=1).mean().iloc[-1]
        features['price_to_sma20'] = float(close.iloc[-1] / sma20 - 1) if sma20 and sma20 > 0 else 0.0
        features['price_to_sma50'] = float(close.iloc[-1] / sma50 - 1) if sma50 and sma50 > 0 else 0.0

        # Volatility features
        try:
            features['volatility_20'] = float(close.pct_change().rolling(20, min_periods=1).std().iloc[-1])
        except Exception:
            features['volatility_20'] = 0.0

        features['high_low_range'] = float((high.iloc[-1] - low.iloc[-1]) / close.iloc[-1]) if close.iloc[-1] != 0 else 0.0

        # Volume features
        vol_ma20 = volume.rolling(20, min_periods=1).mean().iloc[-1]
        features['volume_ratio'] = float(volume.iloc[-1] / vol_ma20) if vol_ma20 and vol_ma20 > 0 else 1.0
        try:
            features['volume_change'] = float(volume.pct_change(1).iloc[-1])
        except Exception:
            features['volume_change'] = 0.0

        # Technical indicators (optional)
        try:
            # RSI should be between 0-100
            if 'RSI7' in df.columns:
                rsi_val = df['RSI7'].iloc[-1]
                if pd.notna(rsi_val) and 0 <= rsi_val <= 100:
                    features['rsi7'] = float(rsi_val / 100)
                else:
                    features['rsi7'] = 0.5
            else:
                features['rsi7'] = 0.5

            # MACD diff (protect against infinity)
            if 'MACD' in df.columns and 'MACD_signal' in df.columns:
                macd = df['MACD'].iloc[-1]
                macd_signal = df['MACD_signal'].iloc[-1]
                if pd.notna(macd) and pd.notna(macd_signal):
                    diff = float(macd - macd_signal)
                    # Clip to reasonable range
                    features['macd_diff'] = max(min(diff, 10), -10)
                else:
                    features['macd_diff'] = 0.0
            else:
                features['macd_diff'] = 0.0

            # ADX should be between 0-100
            if 'ADX' in df.columns:
                adx_val = df['ADX'].iloc[-1]
                if pd.notna(adx_val) and 0 <= adx_val <= 100:
                    features['adx'] = float(adx_val / 100)
                else:
                    features['adx'] = 0.2
            else:
                features['adx'] = 0.2
        except Exception as e:
            logger.warning("Error processing technical indicators: %s", e)
            features['rsi7'] = 0.5
            features['macd_diff'] = 0.0
            features['adx'] = 0.2

        # Momentum features with safe indexing
        def safe_momentum(series, lookback):
            if len(series) > lookback:
                try:
                    return float(series.iloc[-1] / series.iloc[-1 - lookback] - 1)
                except Exception:
                    return 0.0
            return 0.0

        features['momentum_5'] = safe_momentum(close, 5)
        features['momentum_10'] = safe_momentum(close, 10)

        # Trend features (safe checks)
        try:
            features['higher_highs'] = int(high.iloc[-1] > high.iloc[-2] > high.iloc[-3])
            features['higher_lows'] = int(low.iloc[-1] > low.iloc[-2] > low.iloc[-3])
        except Exception:
            features['higher_highs'] = 0
            features['higher_lows'] = 0

        return features

    def train_models(self, training_data):
        """
        Train ML models on historical data
        training_data: List of (features_dict, label) tuples
        label: 1 for UP, 0 for DOWN
        Returns: (success: bool, message: str)
        """
        try:
            if len(training_data) < 100:
                return False, "Need at least 100 samples to train"

            X = pd.DataFrame([item[0] for item in training_data])
            y = np.array([int(item[1]) for item in training_data])

            if X.empty:
                return False, "No feature columns to train on"
                
            # Clean and validate input data
            # Replace inf/-inf with NaN then fill with 0
            X = X.replace([np.inf, -np.inf], np.nan)
            
            # Check for remaining invalid values
            if X.isna().any().any():
                logger.warning("Found NaN values in features, filling with 0")
                X = X.fillna(0)
                
            # Clip extreme values to reasonable ranges
            # Most financial ratios/changes shouldn't exceed these bounds
            X = X.clip(lower=-10, upper=10)
            
            # Verify no remaining invalid values
            if not np.isfinite(X).all().all():
                return False, "Invalid values remain after cleaning"

            self.feature_names = X.columns.tolist()

            X_scaled = self.scaler.fit_transform(X)

            self.rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=20, random_state=42)
            self.rf_model.fit(X_scaled, y)

            self.lr_model = LogisticRegression(max_iter=1000, random_state=42)
            self.lr_model.fit(X_scaled, y)

            saved = self.save_models()
            if not saved:
                logger.warning("Models trained but failed to save to disk.")

            return True, "Models trained successfully"
        except Exception as e:
            logger.exception("Error training models: %s", e)
            return False, f"Training failed: {e}"

    def predict(self, features_dict):
        """
        Predict direction for given features
        Returns: (probability_up, confidence, prediction, details)
        """
        if self.rf_model is None or self.lr_model is None or not self.feature_names:
            return 0.5, 0.0, "NEUTRAL", {"error": "Models not trained or feature names unavailable"}

        # Build DataFrame and align to training features; fill missing with 0
        X = pd.DataFrame([features_dict]).reindex(columns=self.feature_names, fill_value=0)
        try:
            X_scaled = self.scaler.transform(X)
        except Exception as e:
            logger.exception("Scaler transform failed: %s", e)
            return 0.5, 0.0, "NEUTRAL", {"error": "Scaler transform failed"}

        # Predict probabilities
        try:
            rf_proba = self.rf_model.predict_proba(X_scaled)[0]
            lr_proba = self.lr_model.predict_proba(X_scaled)[0]
        except Exception as e:
            logger.exception("Model predict_proba failed: %s", e)
            return 0.5, 0.0, "NEUTRAL", {"error": "Prediction failed"}

        # Ensemble: simple average (could be weighted by OOB / CV scores)
        prob_up = float((rf_proba[1] + lr_proba[1]) / 2.0)
        prob_down = float(1.0 - prob_up)
        confidence = float(abs(prob_up - 0.5) * 2.0)  # scale 0..1

        if prob_up > 0.55:
            prediction = "BULLISH"
        elif prob_up < 0.45:
            prediction = "BEARISH"
        else:
            prediction = "NEUTRAL"

        feature_importance = {}
        try:
            feature_importance = dict(zip(self.feature_names, self.rf_model.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        except Exception:
            top_features = []

        details = {
            "prob_up": prob_up,
            "prob_down": prob_down,
            "rf_prediction": float(rf_proba[1]),
            "lr_prediction": float(lr_proba[1]),
            "top_features": top_features
        }

        return prob_up, confidence, prediction, details

    def save_models(self):
        """Save trained models to disk"""
        try:
            with open(os.path.join(MODEL_DIR, "rf_model.pkl"), 'wb') as f:
                pickle.dump(self.rf_model, f)

            with open(os.path.join(MODEL_DIR, "lr_model.pkl"), 'wb') as f:
                pickle.dump(self.lr_model, f)

            with open(os.path.join(MODEL_DIR, "scaler.pkl"), 'wb') as f:
                pickle.dump(self.scaler, f)

            with open(os.path.join(MODEL_DIR, "feature_names.json"), 'w') as f:
                json.dump(self.feature_names, f)
            logger.info("Models saved to %s", MODEL_DIR)
            return True
        except Exception as e:
            logger.exception("Error saving models: %s", e)
            return False

    def load_models(self):
        """Load trained models from disk"""
        try:
            rf_path = os.path.join(MODEL_DIR, "rf_model.pkl")
            lr_path = os.path.join(MODEL_DIR, "lr_model.pkl")
            scaler_path = os.path.join(MODEL_DIR, "scaler.pkl")
            features_path = os.path.join(MODEL_DIR, "feature_names.json")

            if all(os.path.exists(p) for p in [rf_path, lr_path, scaler_path, features_path]):
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)

                with open(lr_path, 'rb') as f:
                    self.lr_model = pickle.load(f)

                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)

                with open(features_path, 'r') as f:
                    self.feature_names = json.load(f)

                logger.info("[✓] AI models loaded successfully")
                return True
        except Exception as e:
            logger.exception("[✗] Error loading models: %s", e)

        return False


class PredictionTracker:
    """Track and evaluate prediction accuracy"""

    def __init__(self, neutral_threshold: float = 0.01):
        self.predictions = []
        self.neutral_threshold = float(neutral_threshold)  # price change threshold for 'NEUTRAL'
        self.load_history()

    def _to_serializable(self, value):
        # Convert numpy / pandas types to native Python types for JSON
        if isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        if isinstance(value, (pd.Timestamp, datetime)):
            return str(value)
        return value

    def _serialize_record(self, record: dict):
        return {k: self._to_serializable(v) for k, v in record.items()}

    def save_prediction(self, symbol, prediction, prob_up, confidence, price_at_prediction):
        """Save a prediction for later verification"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "prediction": prediction,
            "prob_up": float(prob_up),
            "confidence": float(confidence),
            "price_at_prediction": float(price_at_prediction),
            "verified": False
        }

        self.predictions.append(record)
        self.save_history()

    def verify_prediction(self, symbol, current_price):
        """Verify unverified predictions for a symbol"""
        unverified = [p for p in self.predictions if not p.get('verified') and p.get('symbol') == symbol]

        for pred in unverified:
            try:
                base_price = float(pred.get('price_at_prediction', 0.0))
                if base_price == 0:
                    pred['price_change'] = None
                    pred['actual_direction'] = "UNKNOWN"
                    pred['correct'] = False
                else:
                    price_change = (float(current_price) - base_price) / base_price
                    pred['price_change'] = float(price_change)

                    # Determine actual direction based on unified threshold
                    if price_change > self.neutral_threshold:
                        actual_direction = "BULLISH"
                    elif price_change < -self.neutral_threshold:
                        actual_direction = "BEARISH"
                    else:
                        actual_direction = "NEUTRAL"

                    pred['actual_direction'] = actual_direction

                    # Correctness rules
                    if pred['prediction'] == "NEUTRAL":
                        pred['correct'] = abs(price_change) <= self.neutral_threshold
                    else:
                        pred['correct'] = (pred['prediction'] == actual_direction)

                pred['verified'] = True
            except Exception as e:
                logger.exception("Error verifying prediction: %s", e)
                pred['verified'] = True
                pred['correct'] = False

        self.save_history()

    def get_accuracy_stats(self):
        """Calculate prediction accuracy"""
        verified = [p for p in self.predictions if p.get('verified')]
        if not verified:
            return {"accuracy": 0.0, "total": 0, "correct": 0}

        correct = sum(1 for p in verified if p.get('correct'))
        total = len(verified)
        accuracy = (correct / total) * 100.0

        bullish_preds = [p for p in verified if p.get('prediction') == 'BULLISH']
        bearish_preds = [p for p in verified if p.get('prediction') == 'BEARISH']

        bullish_accuracy = (sum(1 for p in bullish_preds if p.get('correct')) / len(bullish_preds) * 100.0) if bullish_preds else 0.0
        bearish_accuracy = (sum(1 for p in bearish_preds if p.get('correct')) / len(bearish_preds) * 100.0) if bearish_preds else 0.0

        return {
            "accuracy": accuracy,
            "total": total,
            "correct": correct,
            "bullish_accuracy": bullish_accuracy,
            "bearish_accuracy": bearish_accuracy,
            "recent_10": self.get_recent_accuracy(10)
        }

    def get_recent_accuracy(self, n=10):
        """Get accuracy of last N verified predictions"""
        verified = [p for p in self.predictions if p.get('verified')][-n:]
        if not verified:
            return 0.0
        correct = sum(1 for p in verified if p.get('correct'))
        return (correct / len(verified)) * 100.0

    def save_history(self):
        """Save prediction history to file (ensure JSON serializable)"""
        try:
            serializable = [self._serialize_record(p) for p in self.predictions]
            with open(PREDICTIONS_FILE, 'w') as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logger.exception("Error saving predictions: %s", e)

    def load_history(self):
        """Load prediction history from file"""
        try:
            if os.path.exists(PREDICTIONS_FILE):
                with open(PREDICTIONS_FILE, 'r') as f:
                    self.predictions = json.load(f)
            else:
                self.predictions = []
        except Exception as e:
            logger.exception("Error loading predictions: %s", e)
            self.predictions = []
