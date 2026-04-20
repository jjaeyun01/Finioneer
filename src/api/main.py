from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
from configs.settings import settings

app = FastAPI(title="Finioneer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MARKET_DIR = settings.data_dir / "raw" / "market"
FRED_DIR   = settings.data_dir / "raw" / "fred"

TICKER_MAP = {
    "SPY": "GSPC", "QQQ": "NDX", "DJI": "DJI",
    "KOSPI": "KS11", "KOSDAQ": "KQ11",
    "BTC": "BTC_USD",
    "AAPL": "AAPL", "NVDA": "NVDA", "MSFT": "MSFT",
    "TSLA": "TSLA", "META": "META", "AMZN": "AMZN", "GOOGL": "GOOGL",
    "SAMSUNG": "005930_KS", "SKHYNIX": "000660_KS",
}

PERIODS = {"1w": 7, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "5y": 1825}


def load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Data not found: {path.name}")
    return pd.read_parquet(path)


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


@app.get("/api/chart/{ticker}")
def get_chart(ticker: str, period: str = "1mo"):
    key = TICKER_MAP.get(ticker.upper())
    if not key:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    df = load_parquet(MARKET_DIR / f"{key}.parquet")
    df.index = pd.to_datetime(df.index)
    df = df.tail(PERIODS.get(period, 30))
    return {
        "ticker": ticker.upper(),
        "period": period,
        "dates":  df.index.strftime("%Y-%m-%d").tolist(),
        "open":   df["open"].round(2).tolist(),
        "high":   df["high"].round(2).tolist(),
        "low":    df["low"].round(2).tolist(),
        "close":  df["close"].round(2).tolist(),
        "volume": df["volume"].fillna(0).astype(int).tolist(),
        "latest": float(df["close"].iloc[-1].round(2)),
        "change": float((df["close"].iloc[-1] - df["close"].iloc[-2]).round(2)),
        "change_pct": float(((df["close"].iloc[-1] / df["close"].iloc[-2] - 1) * 100).round(3)),
    }


@app.get("/api/markets")
def get_markets():
    result = {}
    for label, key in TICKER_MAP.items():
        path = MARKET_DIR / f"{key}.parquet"
        try:
            df = load_parquet(path)
            latest = float(df["close"].iloc[-1].round(2))
            prev   = float(df["close"].iloc[-2].round(2))
            result[label] = {
                "price":      latest,
                "change":     round(latest - prev, 2),
                "change_pct": round((latest / prev - 1) * 100, 3),
                "date":       str(df.index[-1].date()),
            }
        except Exception as e:
            result[label] = {"error": str(e)}
    return result


@app.get("/api/macro")
def get_macro():
    df = load_parquet(FRED_DIR / "macro.parquet").dropna(how="all")
    
    def latest_yoy(col):
        s = df[col].dropna()
        if len(s) < 13:
            return None
        yoy = (s.iloc[-1] / s.iloc[-13] - 1) * 100
        return round(float(yoy), 3)
    
    def latest(col):
        s = df[col].dropna()
        return round(float(s.iloc[-1]), 4) if len(s) else None

    return {
        "cpi_yoy":      latest_yoy("cpi"),
        "ppi_yoy":      latest_yoy("ppi"),
        "fed_funds":    latest("fed"),
        "unemployment": latest("unemp"),
        "t10y":         latest("t10y"),
        "vix":          latest("vix"),
        "m2":           latest("m2"),
        "dxy":          latest("dxy"),
    }

@app.get("/api/predict/cpi")
def predict_cpi():
    from src.models.arima import load_cpi, ARIMAForecaster
    cpi = load_cpi()
    model = ARIMAForecaster()
    model.fit(cpi)
    fc = model.forecast(steps=3)
    return {
        "model": "ARIMA(2,1,2)",
        "mae": 0.2188,
        "current_cpi": round(float(cpi.iloc[-1]), 3),
        "forecast": [
            {"date": str(d.date()), "cpi_yoy": round(float(v), 3)}
            for d, v in zip(fc.index, fc.values)
        ],
    }
