"""Pydantic models for API request/response validation."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HousingFeatures(BaseModel):
    """Single housing feature input."""
    square_footage: float = Field(..., description="Square footage of the house")
    bedrooms: float = Field(..., description="Number of bedrooms")
    bathrooms: float = Field(..., description="Number of bathrooms")
    year_built: float = Field(..., description="Year the house was built")
    lot_size: float = Field(..., description="Size of the lot")
    distance_to_city_center: float = Field(..., description="Distance to city center in miles")
    school_rating: float = Field(..., description="School rating score")


class PredictionResponse(BaseModel):
    """Single prediction response."""
    predicted_price: float = Field(..., description="Predicted house price in USD")
    features: HousingFeatures = Field(..., description="Input features used")


class BatchPredictionRequest(BaseModel):
    """Batch prediction request."""
    records: List[HousingFeatures] = Field(..., description="List of housing features")


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""
    predictions: List[float] = Field(..., description="List of predicted prices in Rupees")
    count: int = Field(..., description="Number of predictions")


class ModelInfo(BaseModel):
    """Model information and metrics."""
    model_type: str = Field(default="Linear Regression", description="Type of ML model")
    feature_names: List[str] = Field(..., description="Feature names")
    coefficients: Dict[str, float] = Field(..., description="Model coefficients")
    intercept: float = Field(..., description="Model intercept")
    metrics: Dict[str, float] = Field(..., description="Performance metrics")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(..., description="API version")
    model_loaded: bool = Field(..., description="Whether model is loaded")
