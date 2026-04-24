"""App1: Property Value Estimator API (runs on port 8080)"""
import json
import pickle
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Model paths (reuse Task 1 model)
BASE_DIR = Path(__file__).parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"
STORE_FILE = BASE_DIR / "app1_store.json"

# Storage helpers

def load_store():
    if not STORE_FILE.exists():
        return {"estimates": [], "comparisons": []}
    try:
        return json.loads(STORE_FILE.read_text())
    except json.JSONDecodeError:
        return {"estimates": [], "comparisons": []}


def save_store(store_data):
    STORE_FILE.write_text(json.dumps(store_data, indent=2))


def next_id(items):
    return max([item["id"] for item in items], default=0) + 1


# Pydantic schemas
class PropertyFeatures(BaseModel):
    square_footage: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=1, le=10)
    bathrooms: float = Field(..., ge=1, le=10)
    year_built: int = Field(..., ge=1800, le=2025)
    lot_size: float = Field(..., gt=0)
    distance_to_city_center: float = Field(..., ge=0)
    school_rating: float = Field(..., ge=1, le=10)


class EstimateRequest(BaseModel):
    property: PropertyFeatures
    notes: Optional[str] = None
    session_id: Optional[str] = None


class EstimateResponse(BaseModel):
    estimate_id: int
    session_id: str
    features: PropertyFeatures
    predicted_price: float
    created_at: datetime
    notes: Optional[str] = None


class BatchEstimateRequest(BaseModel):
    properties: list[PropertyFeatures]
    session_id: Optional[str] = None


class BatchEstimateResponse(BaseModel):
    estimates: list[EstimateResponse]
    count: int


class HistoryResponse(BaseModel):
    total: int
    estimates: list[EstimateResponse]


class ComparisonRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    estimate_ids: list[int] = Field(..., min_items=2, max_items=10)


class ComparisonProperty(BaseModel):
    estimate_id: int
    features: PropertyFeatures
    predicted_price: float


class ComparisonResponse(BaseModel):
    comparison_id: int
    name: str
    session_id: str
    properties: list[ComparisonProperty]
    analysis: dict
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
    stored_estimates: int


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app1")

app = FastAPI(
    title="App1: Property Value Estimator API",
    version="1.0.0",
    description="FastAPI backend for property value estimation with history and comparison support",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] ,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
scaler = None


@app.on_event("startup")
def startup_event():
    global model, scaler
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
        logger.info("App1 model and scaler loaded")
    except Exception as exc:
        logger.error(f"Failed to load App1 model or scaler: {exc}")


@app.get("/health", response_model=HealthResponse)
def health():
    store = load_store()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model_loaded=model is not None and scaler is not None,
        stored_estimates=len(store["estimates"]),
    )


@app.post("/estimate", response_model=EstimateResponse)
def estimate(req: EstimateRequest):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    try:
        session_id = req.session_id or f"session-{datetime.utcnow().timestamp()}"
        X = np.array([
            [
                req.property.square_footage,
                req.property.bedrooms,
                req.property.bathrooms,
                req.property.year_built,
                req.property.lot_size,
                req.property.distance_to_city_center,
                req.property.school_rating,
            ]
        ])
        X_scaled = scaler.transform(X)
        prediction = float(model.predict(X_scaled)[0])
        store = load_store()
        estimate_id = next_id(store["estimates"])
        record = {
            "id": estimate_id,
            "session_id": session_id,
            "features": req.property.model_dump(),
            "predicted_price": prediction,
            "notes": req.notes,
            "created_at": datetime.utcnow().isoformat(),
        }
        store["estimates"].append(record)
        save_store(store)
        return EstimateResponse(
            estimate_id=estimate_id,
            session_id=session_id,
            features=req.property,
            predicted_price=prediction,
            created_at=datetime.fromisoformat(record["created_at"]),
            notes=req.notes,
        )
    except Exception as exc:
        logger.error(f"App1 estimate error: {exc}")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}")


@app.post("/estimate/batch", response_model=BatchEstimateResponse)
def estimate_batch(req: BatchEstimateRequest):
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if not req.properties:
        raise HTTPException(status_code=400, detail="Empty property list")
    try:
        session_id = req.session_id or f"session-{datetime.utcnow().timestamp()}"
        X = np.array([
            [
                prop.square_footage,
                prop.bedrooms,
                prop.bathrooms,
                prop.year_built,
                prop.lot_size,
                prop.distance_to_city_center,
                prop.school_rating,
            ]
            for prop in req.properties
        ])
        X_scaled = scaler.transform(X)
        predictions = [float(p) for p in model.predict(X_scaled)]
        store = load_store()
        estimates = []
        for prop, price in zip(req.properties, predictions):
            estimate_id = next_id(store["estimates"])
            record = {
                "id": estimate_id,
                "session_id": session_id,
                "features": prop.model_dump(),
                "predicted_price": price,
                "notes": None,
                "created_at": datetime.utcnow().isoformat(),
            }
            store["estimates"].append(record)
            estimates.append(
                EstimateResponse(
                    estimate_id=estimate_id,
                    session_id=session_id,
                    features=prop,
                    predicted_price=price,
                    created_at=datetime.fromisoformat(record["created_at"]),
                )
            )
        save_store(store)
        return BatchEstimateResponse(estimates=estimates, count=len(estimates))
    except Exception as exc:
        logger.error(f"App1 batch estimate error: {exc}")
        raise HTTPException(status_code=400, detail=f"Batch prediction failed: {exc}")


@app.get("/history", response_model=HistoryResponse)
def history(session_id: Optional[str] = Query(None), skip: int = 0, limit: int = 20):
    store = load_store()
    estimates = store["estimates"]
    if session_id:
        estimates = [item for item in estimates if item["session_id"] == session_id]
    total = len(estimates)
    results = []
    for item in estimates[skip : skip + limit]:
        results.append(
            EstimateResponse(
                estimate_id=item["id"],
                session_id=item["session_id"],
                features=PropertyFeatures(**item["features"]),
                predicted_price=item["predicted_price"],
                created_at=datetime.fromisoformat(item["created_at"]),
                notes=item.get("notes"),
            )
        )
    return HistoryResponse(total=total, estimates=results)


@app.get("/estimate/{estimate_id}", response_model=EstimateResponse)
def estimate_detail(estimate_id: int):
    store = load_store()
    estimate = next((item for item in store["estimates"] if item["id"] == estimate_id), None)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return EstimateResponse(
        estimate_id=estimate["id"],
        session_id=estimate["session_id"],
        features=PropertyFeatures(**estimate["features"]),
        predicted_price=estimate["predicted_price"],
        created_at=datetime.fromisoformat(estimate["created_at"]),
        notes=estimate.get("notes"),
    )


@app.post("/compare", response_model=ComparisonResponse)
def compare(req: ComparisonRequest, session_id: Optional[str] = Query(None)):
    store = load_store()
    selected = [item for item in store["estimates"] if item["id"] in req.estimate_ids]
    if len(selected) != len(req.estimate_ids):
        raise HTTPException(status_code=404, detail="One or more estimates not found")
    properties = [
        ComparisonProperty(
            estimate_id=item["id"],
            features=PropertyFeatures(**item["features"]),
            predicted_price=item["predicted_price"],
        )
        for item in selected
    ]
    prices = [item["predicted_price"] for item in selected]
    analysis = {
        "count": len(selected),
        "average_price": sum(prices) / len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
        "price_range": max(prices) - min(prices),
    }
    comparison_id = next_id(store["comparisons"])
    record = {
        "id": comparison_id,
        "name": req.name,
        "session_id": session_id or f"session-{datetime.utcnow().timestamp()}",
        "estimate_ids": req.estimate_ids,
        "analysis": analysis,
        "created_at": datetime.utcnow().isoformat(),
    }
    store["comparisons"].append(record)
    save_store(store)
    return ComparisonResponse(
        comparison_id=comparison_id,
        name=req.name,
        session_id=record["session_id"],
        properties=properties,
        analysis=analysis,
        created_at=datetime.fromisoformat(record["created_at"]),
    )


@app.get("/comparisons")
def comparisons(session_id: Optional[str] = Query(None), skip: int = 0, limit: int = 20):
    store = load_store()
    comparisons = store["comparisons"]
    if session_id:
        comparisons = [item for item in comparisons if item["session_id"] == session_id]
    return {
        "total": len(comparisons),
        "items": comparisons[skip : skip + limit],
    }


@app.get("/")
def root():
    return {"message": "App1: Property Value Estimator API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app1.main:app", host="0.0.0.0", port=8080, reload=True)
