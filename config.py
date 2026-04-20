import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [MODEL_DIR, DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "housing_model.pkl"
SCALER_PATH = MODEL_DIR / "housing_scaler.pkl"
METRICS_PATH = MODEL_DIR / "metrics.json"

APP_TITLE = "Housing Price Prediction API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "ML API for predicting housing prices based on features"
