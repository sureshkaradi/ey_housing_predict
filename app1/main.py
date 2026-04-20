"""App1: Property Value Estimator API (runs on port 8080)"""
import json
import pickle
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from pathlib import Path
from pydantic import BaseModel, Field

# Model paths (reuse Task 1 model)
BASE_DIR = Path(__file__).parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"
METRICS_PATH = BASE_DIR / "models" / "metrics.json"

# Pydantic schemas
class PropertyFeatures(BaseModel):
    square_footage: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=1, le=10)
    bathrooms: float = Field(..., ge=1, le=10)
    year_built: int = Field(..., ge=1800, le=2025)
    lot_size: float = Field(..., gt=0)
    distance_to_city_center: float = Field(..., ge=0)
    school_rating: float = Field(..., ge=1, le=10)

class PredictionResponse(BaseModel):
    predicted_price: float
    features: PropertyFeatures

class BatchPredictionRequest(BaseModel):
    records: list[PropertyFeatures]

class BatchPredictionResponse(BaseModel):
    predictions: list[float]
    count: int

class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app1")

app = FastAPI(
    title="App1: Property Value Estimator API",
    version="1.0.0",
    description="REST API for property value estimation (App1)",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
scaler = None

@app.on_event("startup")
def load_model():
    global model, scaler
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
        logger.info("Model and scaler loaded.")
    except Exception as e:
        logger.error(f"Failed to load model/scaler: {e}")

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=model is not None and scaler is not None,
    )

@app.post("/predict", response_model=PredictionResponse)
def predict(features: PropertyFeatures):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")
    try:
        X = np.array([
            [
                features.square_footage,
                features.bedrooms,
                features.bathrooms,
                features.year_built,
                features.lot_size,
                features.distance_to_city_center,
                features.school_rating,
            ]
        ])
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)[0]
        return PredictionResponse(predicted_price=float(prediction), features=features)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

@app.post("/predict-batch", response_model=BatchPredictionResponse)
def predict_batch(request: BatchPredictionRequest):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")
    if not request.records:
        raise HTTPException(status_code=400, detail="Empty records list")
    try:
        X = np.array([
            [
                r.square_footage,
                r.bedrooms,
                r.bathrooms,
                r.year_built,
                r.lot_size,
                r.distance_to_city_center,
                r.school_rating,
            ] for r in request.records
        ])
        X_scaled = scaler.transform(X)
        predictions = model.predict(X_scaled)
        return BatchPredictionResponse(predictions=[float(p) for p in predictions], count=len(predictions))
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=400, detail=f"Batch prediction failed: {e}")

@app.get("/")
def root():
    return {"message": "App1: Property Value Estimator API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
