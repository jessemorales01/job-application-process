"""
Lead Win Probability Model Training Script

This script generates synthetic lead data and trains a logistic regression model
to predict the probability of winning/converting a lead.

Features used:
- estimated_value: Dollar amount of the deal
- status_score: Numeric representation of lead status (new=1 to converted=5)
- has_phone: Whether lead has phone number (0/1)
- has_company: Whether lead has company name (0/1)

Run this script to generate the trained model file.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Ensures that the same random data is generated each run for reproducibility
np.random.seed(33)

n_samples = 1000

print("Generating synthetic lead data...")

data = {
    # Exponential distribution because most real deals are smaller values
    'estimated_value': np.random.exponential(5000, n_samples),
    
    # Maps to Lead model status: new=1, contacted=2, qualified=3, converted=4, lost=0
    'status_score': np.random.choice([0, 1, 2, 3, 4], n_samples, p=[0.1, 0.3, 0.25, 0.2, 0.15]),
    
    'has_phone': np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),
    
    'has_company': np.random.choice([0, 1], n_samples, p=[0.2, 0.8]),
}

df = pd.DataFrame(data)

# Higher value + higher status + contact info = more likely to win
win_probability = (
    0.25 * np.clip(df['estimated_value'] / 20000, 0, 1) +
    0.35 * (df['status_score'] / 4) +
    0.20 * df['has_phone'] +
    0.20 * df['has_company'] +
    np.random.normal(0, 0.15, n_samples)  # Random noise for realistic variance
)

df['won'] = (win_probability > 0.5).astype(int)

print(f"Generated {n_samples} samples")
print(f"Win rate: {df['won'].mean():.1%}")

X = df[['estimated_value', 'status_score', 'has_phone', 'has_company']]
y = df['won']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scaling normalizes features so larger values like estimated_value dont dominate
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\nTraining logistic regression model...")

model = LogisticRegression(random_state=42)
model.fit(X_train_scaled, y_train)

train_accuracy = model.score(X_train_scaled, y_train)
test_accuracy = model.score(X_test_scaled, y_test)

print(f"Training accuracy: {train_accuracy:.1%}")
print(f"Test accuracy: {test_accuracy:.1%}")

print("\nFeature importance (coefficients):")
for feature, coef in zip(X.columns, model.coef_[0]):
    print(f"  {feature}: {coef:.3f}")

model_path = os.path.join(os.path.dirname(__file__), 'lead_win_model.joblib')
scaler_path = os.path.join(os.path.dirname(__file__), 'lead_scaler.joblib')

joblib.dump(model, model_path)
joblib.dump(scaler, scaler_path)

print(f"\nModel saved to: {model_path}")
print(f"Scaler saved to: {scaler_path}")
print("\nTraining complete!")

