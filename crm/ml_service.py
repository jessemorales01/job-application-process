"""
ML Prediction Service for Lead Win Probability

This module loads the trained model and provides a function to predict
the win probability for any lead.
"""

import os
import joblib

ML_DIR = os.path.join(os.path.dirname(__file__), '..', 'ml')
MODEL_PATH = os.path.join(ML_DIR, 'lead_win_model.joblib')
SCALER_PATH = os.path.join(ML_DIR, 'lead_scaler.joblib')

# Cached globally to avoid reloading from disk on every prediction
_model = None
_scaler = None


def load_model():
    """Load the trained model and scaler from disk."""
    global _model, _scaler
    
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
            _scaler = joblib.load(SCALER_PATH)
        except FileNotFoundError:
            print(f"Warning: Model files not found at {MODEL_PATH}")
            return None, None
    
    return _model, _scaler


def predict_win_score(lead):
    """Predict win probability (0-1) for a lead, or None if prediction fails."""
    model, scaler = load_model()
    
    if model is None or scaler is None:
        return None
    
    # Must match the mapping used in train_model.py
    status_map = {
        'new': 1,
        'contacted': 2,
        'qualified': 3,
        'converted': 4,
        'lost': 0
    }
    
    # Features must be in same order as training: [estimated_value, status_score, has_phone, has_company]
    features = [[
        float(lead.estimated_value or 0),
        status_map.get(lead.status, 1),
        1 if lead.phone else 0,
        1 if lead.company else 0,
    ]]
    
    try:
        features_scaled = scaler.transform(features)
        probability = model.predict_proba(features_scaled)[0][1]
        return round(probability, 2)
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

