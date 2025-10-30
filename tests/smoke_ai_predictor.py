"""
Smoke test for ai_predictor.StockPredictor
Generates synthetic feature vectors, trains models, and runs a prediction.
"""
import random
import json
import sys
from pathlib import Path

# Ensure project root is on sys.path when running this script directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai_predictor import StockPredictor

def generate_feature(i):
    # Generate a feature dict consistent with prepare_features output
    return {
        'price_change_1': random.uniform(-0.05, 0.05),
        'price_change_5': random.uniform(-0.2, 0.2),
        'price_change_10': random.uniform(-0.3, 0.3),
        'price_change_20': random.uniform(-0.5, 0.5),
        'price_to_sma20': random.uniform(-0.2, 0.2),
        'price_to_sma50': random.uniform(-0.3, 0.3),
        'volatility_20': random.uniform(0.0, 0.1),
        'high_low_range': random.uniform(0.0, 0.1),
        'volume_ratio': random.uniform(0.5, 2.0),
        'volume_change': random.uniform(-0.5, 0.5),
        'rsi7': random.uniform(0.0, 1.0),
        'macd_diff': random.uniform(-1.0, 1.0),
        'adx': random.uniform(0.0, 1.0),
        'momentum_5': random.uniform(-0.2, 0.2),
        'momentum_10': random.uniform(-0.4, 0.4),
        'higher_highs': int(random.choice([0,1])),
        'higher_lows': int(random.choice([0,1])),
    }


def main():
    print("Starting Smoke Test: ai_predictor")
    predictor = StockPredictor()

    # Create synthetic training data
    training_data = []
    for i in range(200):
        features = generate_feature(i)
        # Simple label: 1 if short-term price_change_1 > 0.01 else 0
        label = 1 if features['price_change_1'] > 0.01 else 0
        training_data.append((features, label))

    print(f"Generated {len(training_data)} synthetic training samples")

    success, msg = predictor.train_models(training_data)
    print(f"Training result: success={success}, msg={msg}")

    if not success:
        print("Training failed in smoke test — aborting prediction check.")
        return

    # Run a single prediction
    sample = generate_feature(999)
    prob_up, confidence, prediction, details = predictor.predict(sample)
    print("Prediction output:")
    print(json.dumps({
        'prob_up': prob_up,
        'confidence': confidence,
        'prediction': prediction,
        'details': details
    }, indent=2, default=str))

if __name__ == '__main__':
    main()
