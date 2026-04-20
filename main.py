"""Main FastAPI application for housing price prediction."""
import json
import pickle
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from config import APP_TITLE, APP_VERSION, APP_DESCRIPTION, MODEL_PATH, SCALER_PATH, METRICS_PATH
from models import (
    HousingFeatures,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelInfo,
    HealthResponse,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and scaler
model = None
scaler = None
metrics_data = None


def load_model():
    """Load model, scaler, and metrics from disk."""
    global model, scaler, metrics_data

    try:
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            logger.info("Model loaded successfully")
        else:
            logger.warning(f"Model not found at {MODEL_PATH}")

        if SCALER_PATH.exists():
            with open(SCALER_PATH, "rb") as f:
                scaler = pickle.load(f)
            logger.info("Scaler loaded successfully")
        else:
            logger.warning(f"Scaler not found at {SCALER_PATH}")

        if METRICS_PATH.exists():
            with open(METRICS_PATH, "r") as f:
                metrics_data = json.load(f)
            logger.info("Metrics loaded successfully")
        else:
            logger.warning(f"Metrics not found at {METRICS_PATH}")

    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    logger.info("Starting up application...")
    load_model()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        model_loaded=model is not None and scaler is not None,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(features: HousingFeatures):
    """
    Predict housing price for a single record.

    Expected input:
    - square_footage: Property size in square feet
    - bedrooms: Number of bedrooms
    - bathrooms: Number of bathrooms
    - year_built: Year property was built
    - lot_size: Lot size in square feet
    - distance_to_city_center: Distance to city center in miles
    - school_rating: School district rating (1-10)
    """
    if model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train the model first.",
        )

    try:
        # Convert to numpy array with feature order
        X = np.array(
            [
                [
                    features.square_footage,
                    features.bedrooms,
                    features.bathrooms,
                    features.year_built,
                    features.lot_size,
                    features.distance_to_city_center,
                    features.school_rating,
                ]
            ]
        )

        # Scale and predict
        X_scaled = scaler.transform(X)
        prediction = model.predict(X_scaled)[0]

        return PredictionResponse(
            predicted_price=float(prediction),
            features=features,
        )

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")


@app.post("/predict-batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict housing prices for multiple records (batch prediction).

    Accepts a list of housing features and returns predictions for all.
    """
    if model is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train the model first.",
        )

    if not request.records:
        raise HTTPException(status_code=400, detail="Empty records list")

    try:
        # Convert to numpy array
        X = np.array(
            [
                [
                    r.square_footage,
                    r.bedrooms,
                    r.bathrooms,
                    r.year_built,
                    r.lot_size,
                    r.distance_to_city_center,
                    r.school_rating,
                ]
                for r in request.records
            ]
        )

        # Scale and predict
        X_scaled = scaler.transform(X)
        predictions = model.predict(X_scaled)

        return BatchPredictionResponse(
            predictions=[float(p) for p in predictions],
            count=len(predictions),
        )

    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Batch prediction failed: {str(e)}")


@app.get("/model-info", response_model=ModelInfo)
async def model_info():
    """
    Get model information including coefficients and performance metrics.

    Returns:
    - Model type
    - Feature names
    - Model coefficients for each feature
    - Model intercept
    - Training and test metrics
    """
    if metrics_data is None:
        raise HTTPException(
            status_code=503,
            detail="Model metrics not available. Please train the model first.",
        )

    try:
        feature_names = metrics_data.get("feature_names", [])
        coefficients = dict(
            zip(feature_names, metrics_data.get("model_coefficients", []))
        )

        # Extract performance metrics
        perf_metrics = {
            "train_r2": metrics_data.get("train_r2"),
            "test_r2": metrics_data.get("test_r2"),
            "train_mae": metrics_data.get("train_mae"),
            "test_mae": metrics_data.get("test_mae"),
            "train_mse": metrics_data.get("train_mse"),
            "test_mse": metrics_data.get("test_mse"),
            "training_samples": metrics_data.get("training_samples"),
            "test_samples": metrics_data.get("test_samples"),
        }

        return ModelInfo(
            model_type="Linear Regression",
            feature_names=feature_names,
            coefficients=coefficients,
            intercept=metrics_data.get("model_intercept", 0),
            metrics=perf_metrics,
        )

    except Exception as e:
        logger.error(f"Error retrieving model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving model info: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "title": APP_TITLE,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "predict_single": "/predict (POST)",
            "predict_batch": "/predict-batch (POST)",
            "model_info": "/model-info (GET)",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
