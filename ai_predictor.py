"""
ai_predictor.py - ML-based price prediction module
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime
import json

# Constants
MODEL_DIR = "ai_models"
PREDICTIONS_FILE = "predictions_history.json"

class StockPredictor:
    """ML-based stock direction predictor"""
    
    def __init__(self):
        self.rf_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        
        # Create model directory
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)
        
        # Load existing models if available
        self.load_models()
    
    def prepare_features(self, df):
        """Extract ML features from price data"""
        features = {}
        
        if len(df) < 50:
            return None
        
        # Price-based features
        features['price_change_1'] = df['Close'].pct_change(1).iloc[-1]
        features['price_change_5'] = df['Close'].pct_change(5).iloc[-1]
        features['price_change_10'] = df['Close'].pct_change(10).iloc[-1]
        features['price_change_20'] = df['Close'].pct_change(20).iloc[-1]
        
        # Position relative to moving averages
        features['price_to_sma20'] = (df['Close'].iloc[-1] / df['Close'].rolling(20).mean().iloc[-1]) - 1
        features['price_to_sma50'] = (df['Close'].iloc[-1] / df['Close'].rolling(50).mean().iloc[-1]) - 1 if len(df) >= 50 else 0
        
        # Volatility features
        features['volatility_20'] = df['Close'].pct_change().rolling(20).std().iloc[-1]
        features['high_low_range'] = (df['High'].iloc[-1] - df['Low'].iloc[-1]) / df['Close'].iloc[-1]
        
        # Volume features
        features['volume_ratio'] = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1] if df['Volume'].rolling(20).mean().iloc[-1] > 0 else 1
        features['volume_change'] = df['Volume'].pct_change(1).iloc[-1]
        
        # Technical indicators (assuming they exist)
        if 'RSI7' in df.columns:
            features['rsi7'] = df['RSI7'].iloc[-1] / 100  # Normalize to 0-1
        else:
            features['rsi7'] = 0.5
        
        if 'MACD' in df.columns and 'MACD_signal' in df.columns:
            features['macd_diff'] = df['MACD'].iloc[-1] - df['MACD_signal'].iloc[-1]
        else:
            features['macd_diff'] = 0
        
        if 'ADX' in df.columns:
            features['adx'] = df['ADX'].iloc[-1] / 100  # Normalize
        else:
            features['adx'] = 0.2
        
        # Momentum features
        features['momentum_5'] = df['Close'].iloc[-1] / df['Close'].iloc[-6] - 1 if len(df) > 5 else 0
        features['momentum_10'] = df['Close'].iloc[-1] / df['Close'].iloc[-11] - 1 if len(df) > 10 else 0
        
        # Trend features
        features['higher_highs'] = 1 if df['High'].iloc[-1] > df['High'].iloc[-2] and df['High'].iloc[-2] > df['High'].iloc[-3] else 0
        features['higher_lows'] = 1 if df['Low'].iloc[-1] > df['Low'].iloc[-2] and df['Low'].iloc[-2] > df['Low'].iloc[-3] else 0
        
        return features
    
    def train_models(self, training_data):
        """
        Train ML models on historical data
        training_data: List of (features_dict, label) tuples
        label: 1 for UP, 0 for DOWN
        """
        if len(training_data) < 100:
            return False, "Need at least 100 samples to train"
        
        # Prepare data
        X = pd.DataFrame([item[0] for item in training_data])
        y = np.array([item[1] for item in training_data])
        
        self.feature_names = X.columns.tolist()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=20,
            random_state=42
        )
        self.rf_model.fit(X_scaled, y)
        
        # Train Logistic Regression
        self.lr_model = LogisticRegression(
            max_iter=1000,
            random_state=42
        )
        self.lr_model.fit(X_scaled, y)
        
        # Save models
        self.save_models()
        
        return True, "Models trained successfully"
    
    def predict(self, features_dict):
        """
        Predict direction for given features
        Returns: (probability_up, confidence, prediction, details)
        """
        if self.rf_model is None or self.lr_model is None:
            return 0.5, 0, "NEUTRAL", {"error": "Models not trained"}
        
        # Prepare features
        X = pd.DataFrame([features_dict])[self.feature_names]
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from both models
        rf_proba = self.rf_model.predict_proba(X_scaled)[0]
        lr_proba = self.lr_model.predict_proba(X_scaled)[0]
        
        # Ensemble: Average probabilities
        prob_up = (rf_proba[1] + lr_proba[1]) / 2
        prob_down = 1 - prob_up
        
        # Confidence: How far from 50-50?
        confidence = abs(prob_up - 0.5) * 2  # Scale 0-1
        
        # Prediction
        if prob_up > 0.55:
            prediction = "BULLISH"
        elif prob_up < 0.45:
            prediction = "BEARISH"
        else:
            prediction = "NEUTRAL"
        
        # Feature importance (from Random Forest)
        feature_importance = dict(zip(
            self.feature_names,
            self.rf_model.feature_importances_
        ))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        
        details = {
            "prob_up": float(prob_up),
            "prob_down": float(prob_down),
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
            
            return True
        except Exception as e:
            print(f"Error saving models: {e}")
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
                
                print("[✓] AI models loaded successfully")
                return True
        except Exception as e:
            print(f"[✗] Error loading models: {e}")
        
        return False


class PredictionTracker:
    """Track and evaluate prediction accuracy"""
    
    def __init__(self):
        self.predictions = []
        self.load_history()
    
    def save_prediction(self, symbol, prediction, prob_up, confidence, actual_price):
        """Save a prediction for later verification"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "prediction": prediction,
            "prob_up": prob_up,
            "confidence": confidence,
            "price_at_prediction": actual_price,
            "verified": False
        }
        
        self.predictions.append(record)
        self.save_history()
    
    def verify_prediction(self, symbol, current_price):
        """Verify if prediction was correct"""
        unverified = [p for p in self.predictions if not p['verified'] and p['symbol'] == symbol]
        
        for pred in unverified:
            price_change = (current_price - pred['price_at_prediction']) / pred['price_at_prediction']
            
            actual_direction = "BULLISH" if price_change > 0.01 else "BEARISH" if price_change < -0.01 else "NEUTRAL"
            
            pred['price_change'] = price_change
            pred['actual_direction'] = actual_direction
            pred['correct'] = (pred['prediction'] == actual_direction) or (pred['prediction'] == "NEUTRAL" and abs(price_change) < 0.02)
            pred['verified'] = True
        
        self.save_history()
    
    def get_accuracy_stats(self):
        """Calculate prediction accuracy"""
        verified = [p for p in self.predictions if p['verified']]
        
        if not verified:
            return {"accuracy": 0, "total": 0, "correct": 0}
        
        correct = sum(1 for p in verified if p['correct'])
        total = len(verified)
        accuracy = (correct / total) * 100
        
        # By prediction type
        bullish_preds = [p for p in verified if p['prediction'] == 'BULLISH']
        bearish_preds = [p for p in verified if p['prediction'] == 'BEARISH']
        
        return {
            "accuracy": accuracy,
            "total": total,
            "correct": correct,
            "bullish_accuracy": (sum(1 for p in bullish_preds if p['correct']) / len(bullish_preds) * 100) if bullish_preds else 0,
            "bearish_accuracy": (sum(1 for p in bearish_preds if p['correct']) / len(bearish_preds) * 100) if bearish_preds else 0,
            "recent_10": self.get_recent_accuracy(10)
        }
    
    def get_recent_accuracy(self, n=10):
        """Get accuracy of last N predictions"""
        verified = [p for p in self.predictions if p['verified']][-n:]
        
        if not verified:
            return 0
        
        correct = sum(1 for p in verified if p['correct'])
        return (correct / len(verified)) * 100
    
    def save_history(self):
        """Save prediction history to file"""
        try:
            with open(PREDICTIONS_FILE, 'w') as f:
                json.dump(self.predictions, f, indent=2)
        except Exception as e:
            print(f"Error saving predictions: {e}")
    
    def load_history(self):
        """Load prediction history from file"""
        try:
            if os.path.exists(PREDICTIONS_FILE):
                with open(PREDICTIONS_FILE, 'r') as f:
                    self.predictions = json.load(f)
        except Exception as e:
            print(f"Error loading predictions: {e}")
            self.predictions = []
