"""Market Intelligence REST API.

Run locally:
    uvicorn src.api.main:app --reload --port 8000

Swagger UI: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Market Intelligence API",
    description="Economic forecasting, market indicators, and financial news NLP",
    version="0.1.0",
)


# ── Response schemas ──────────────────────────────────────────────────────────

class CPIForecast(BaseModel):
    model: str
    forecast_yoy: float
    unit: str = "% YoY"
    steps_ahead: int = 1


class FOMCForecast(BaseModel):
    direction: str          # HIKE | HOLD | CUT
    hike_prob: float
    hold_prob: float
    cut_prob: float


class NewsSentiment(BaseModel):
    title: str
    source: str
    sentiment: str
    hawk_score: float
    dove_score: float
    relevance: float


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


# ── Forecast endpoints ────────────────────────────────────────────────────────

@app.get("/predict/cpi", response_model=CPIForecast, tags=["Forecast"])
def predict_cpi(model: str = "arima", steps: int = 1):
    """
    Forecast next month's CPI YoY using the selected model.
    - **model**: arima | xgboost | ensemble
    - **steps**: months ahead (1–3)
    """
    if steps not in range(1, 4):
        raise HTTPException(status_code=422, detail="steps must be 1, 2, or 3")
    if model not in ("arima", "xgboost", "ensemble"):
        raise HTTPException(status_code=422, detail="model must be arima | xgboost | ensemble")

    # TODO Phase 2: load fitted model from disk and return real forecast
    # Placeholder until models are trained
    return CPIForecast(model=model, forecast_yoy=3.2, steps_ahead=steps)


@app.get("/predict/fomc", response_model=FOMCForecast, tags=["Forecast"])
def predict_fomc():
    """Predict next FOMC meeting rate decision direction."""
    # TODO Phase 2: wire up FOMCClassifier.predict_proba()
    return FOMCForecast(direction="HOLD", hike_prob=0.05, hold_prob=0.82, cut_prob=0.13)


# ── Indicators ────────────────────────────────────────────────────────────────

@app.get("/indicators/macro", tags=["Indicators"])
def macro_indicators():
    """Return latest values for key US macro indicators."""
    # TODO Phase 1: pull from DB (collected by FRED pipeline)
    return {
        "cpi_yoy": None,
        "ppi_yoy": None,
        "fed_funds_rate": None,
        "unemployment": None,
        "t10y_yield": None,
        "note": "Connect FRED collector in Phase 1 to populate these.",
    }


@app.get("/indicators/markets", tags=["Indicators"])
def market_indicators():
    """Return latest index levels and key market metrics."""
    # TODO Phase 1: pull from market collector DB
    return {
        "sp500": None,
        "nasdaq100": None,
        "kospi": None,
        "btc_usd": None,
        "vix": None,
        "krw_usd": None,
    }


# ── News ──────────────────────────────────────────────────────────────────────

@app.get("/news/latest", response_model=list[NewsSentiment], tags=["News"])
def latest_news(limit: int = 10):
    """Return the most recent market-relevant news with sentiment scores."""
    # TODO Phase 2: wire up NewsCollector + FinBERTAnalyzer
    return []


@app.get("/news/fomc", tags=["News"])
def fomc_news():
    """Latest FOMC-related news and statement delta score."""
    # TODO Phase 3: wire up FOMCParser
    return {"delta_score": None, "tone": None, "articles": []}
