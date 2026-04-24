"""App2: Property Market Analysis API (runs on port 8081)"""
import json
import pickle
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"
DATA_PATH = BASE_DIR / "data" / "housing_price_data.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app2")

app = FastAPI(
    title="App2: Property Market Analysis API",
    version="1.0.0",
    description="REST API for property market analysis with ML-powered what-if analysis",
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


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
    dataset_rows: int


class WhatIfRequest(BaseModel):
    square_footage: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=1, le=10)
    bathrooms: float = Field(..., ge=1, le=10)
    year_built: int = Field(..., ge=1800, le=2025)
    lot_size: float = Field(..., gt=0)
    distance_to_city_center: float = Field(..., ge=0)
    school_rating: float = Field(..., ge=1, le=10)


class WhatIfResponse(BaseModel):
    predicted_price: float
    scenario: WhatIfRequest


class MarketSummaryResponse(BaseModel):
    total_properties: int
    average_price: float
    median_price: float
    min_price: float
    max_price: float
    average_square_footage: float
    average_school_rating: float
    bedrooms_distribution: dict
    bathrooms_distribution: dict


class SegmentFilterResponse(BaseModel):
    segment: str
    count: int
    average_price: float
    average_square_footage: float
    average_school_rating: float


@app.on_event("startup")
def startup_event():
    global model, scaler
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
        logger.info("App2 model and scaler loaded")
    except Exception as exc:
        logger.error(f"Failed to load App2 model or scaler: {exc}")


@lru_cache(maxsize=1)
def load_data():
    df = pd.read_csv(DATA_PATH)
    return df


@lru_cache(maxsize=1)
def market_summary():
    df = load_data()
    return {
        "total_properties": int(len(df)),
        "average_price": float(df["price"].mean()),
        "median_price": float(df["price"].median()),
        "min_price": float(df["price"].min()),
        "max_price": float(df["price"].max()),
        "average_square_footage": float(df["square_footage"].mean()),
        "average_school_rating": float(df["school_rating"].mean()),
        "bedrooms_distribution": df["bedrooms"].value_counts().sort_index().to_dict(),
        "bathrooms_distribution": df["bathrooms"].value_counts().sort_index().to_dict(),
    }


def apply_filters(df, min_price, max_price, min_bedrooms, max_bedrooms, min_school_rating, max_school_rating):
    if min_price is not None:
        df = df[df["price"] >= min_price]
    if max_price is not None:
        df = df[df["price"] <= max_price]
    if min_bedrooms is not None:
        df = df[df["bedrooms"] >= min_bedrooms]
    if max_bedrooms is not None:
        df = df[df["bedrooms"] <= max_bedrooms]
    if min_school_rating is not None:
        df = df[df["school_rating"] >= min_school_rating]
    if max_school_rating is not None:
        df = df[df["school_rating"] <= max_school_rating]
    return df


@app.get("/health", response_model=HealthResponse)
def health():
    df = load_data()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=model is not None and scaler is not None,
        dataset_rows=len(df),
    )


@app.get("/market-summary", response_model=MarketSummaryResponse)
def summary():
    summary_data = market_summary()
    return MarketSummaryResponse(**summary_data)


@app.get("/filter", response_model=list[SegmentFilterResponse])
def filter_data(
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_bedrooms: Optional[int] = Query(None, ge=1),
    max_bedrooms: Optional[int] = Query(None, ge=1),
    min_school_rating: Optional[float] = Query(None, ge=1),
    max_school_rating: Optional[float] = Query(None, ge=10),
):
    df = load_data()
    filtered = apply_filters(df, min_price, max_price, min_bedrooms, max_bedrooms, min_school_rating, max_school_rating)
    if filtered.empty:
        return []
    groups = filtered.groupby("bedrooms").agg(
        count=("price", "size"),
        average_price=("price", "mean"),
        average_square_footage=("square_footage", "mean"),
        average_school_rating=("school_rating", "mean"),
    )
    return [
        SegmentFilterResponse(
            segment=f"{int(index)} bedrooms",
            count=int(row["count"]),
            average_price=float(row["average_price"]),
            average_square_footage=float(row["average_square_footage"]),
            average_school_rating=float(row["average_school_rating"]),
        )
        for index, row in groups.iterrows()
    ]


@app.post("/what-if", response_model=WhatIfResponse)
def what_if(request: WhatIfRequest):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        X = np.array([
            [
                request.square_footage,
                request.bedrooms,
                request.bathrooms,
                request.year_built,
                request.lot_size,
                request.distance_to_city_center,
                request.school_rating,
            ]
        ])
        X_scaled = scaler.transform(X)
        prediction = float(model.predict(X_scaled)[0])
        return WhatIfResponse(predicted_price=prediction, scenario=request)
    except Exception as exc:
        logger.error(f"App2 what-if prediction failed: {exc}")
        raise HTTPException(status_code=400, detail=f"What-if analysis failed: {exc}")


@app.get("/export/csv")
def export_csv(
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    bedrooms: Optional[int] = Query(None, ge=1),
):
    df = load_data()
    if min_price is not None:
        df = df[df["price"] >= min_price]
    if max_price is not None:
        df = df[df["price"] <= max_price]
    if bedrooms is not None:
        df = df[df["bedrooms"] == bedrooms]
    filename = "market-export.csv"
    csv_data = df.to_csv(index=False)
    return {
        "filename": filename,
        "data": csv_data,
    }


@app.get("/")
def root():
    return {"message": "App2: Property Market Analysis API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app2.main:app", host="0.0.0.0", port=8081, reload=True)
