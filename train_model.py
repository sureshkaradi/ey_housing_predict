"""Train and save the housing price prediction model."""
import json
import pickle
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from config import MODEL_PATH, SCALER_PATH, METRICS_PATH, DATA_DIR


def load_data() -> Tuple[np.ndarray, np.ndarray, list]:
    """Load housing dataset from CSV file."""
    csv_path = DATA_DIR / "housing_price_data.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Drop id column if exists
    if 'id' in df.columns:
        df = df.drop('id', axis=1)
    
    # Target variable is 'price', features are everything else
    y = df['price'].values
    X = df.drop('price', axis=1).values
    feature_names = df.drop('price', axis=1).columns.tolist()
    
    return X, y, feature_names


def train_model() -> Dict[str, Any]:
    """Train the linear regression model and save artifacts."""
    print("Loading data...")
    X, y, feature_names = load_data()

    print(f"Dataset shape: {X.shape}")
    print(f"Features: {feature_names}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train model
    print("Training model...")
    model = LinearRegression()
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)

    train_mse = mean_squared_error(y_train, y_pred_train)
    test_mse = mean_squared_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)

    metrics = {
        "train_mse": float(train_mse),
        "test_mse": float(test_mse),
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "train_mae": float(train_mae),
        "test_mae": float(test_mae),
        "model_coefficients": model.coef_.tolist(),
        "model_intercept": float(model.intercept_),
        "feature_names": feature_names,
        "training_samples": X_train.shape[0],
        "test_samples": X_test.shape[0],
    }

    # Save model
    print(f"Saving model to {MODEL_PATH}...")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    # Save scaler
    print(f"Saving scaler to {SCALER_PATH}...")
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    # Save metrics
    print(f"Saving metrics to {METRICS_PATH}...")
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nModel Training Complete!")
    print(f"Train R2: {train_r2:.4f}")
    print(f"Test R2: {test_r2:.4f}")
    print(f"Train MAE: {train_mae:.4f}")
    print(f"Test MAE: {test_mae:.4f}")

    return metrics


if __name__ == "__main__":
    train_model()
