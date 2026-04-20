"""Lv2 — XGBoost CPI forecaster.

Uses multi-feature macro data (PPI, oil, wages, M2, unemployment)
with lag engineering and TimeSeriesSplit cross-validation.
"""

import logging

import numpy as np
import pandas as pd
from fredapi import Fred
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

from configs.settings import settings

logger = logging.getLogger(__name__)


FEATURE_SERIES = {
    "cpi":   "CPIAUCSL",
    "ppi":   "PPIACO",
    "oil":   "DCOILWTICO",
    "wage":  "CES0500000003",
    "unemp": "UNRATE",
    "m2":    "M2SL",
    "t10y":  "GS10",
}
LAG_FEATURES = ["ppi", "oil", "wage"]
LAGS = [1, 2, 3]


def load_features(start: str = "2010-01-01") -> pd.DataFrame:
    fred = Fred(api_key=settings.fred_api_key)
    raw = {}
    for name, sid in FEATURE_SERIES.items():
        try:
            s = fred.get_series(sid, observation_start=start)
            raw[name] = s.resample("MS").last().pct_change(12) * 100
        except Exception as e:
            logger.warning("Skipping %s: %s", name, e)

    df = pd.DataFrame(raw)

    for col in LAG_FEATURES:
        if col in df.columns:
            for lag in LAGS:
                df[f"{col}_lag{lag}"] = df[col].shift(lag)

    # Target: next month's CPI
    df["target"] = df["cpi"].shift(-1)
    df = df.dropna()
    logger.info("Feature matrix: %d rows × %d cols", *df.shape)
    return df


class XGBoostCPIForecaster:

    def __init__(self, n_estimators: int = 300, max_depth: int = 4, learning_rate: float = 0.05):
        self.params = dict(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        self._model = XGBRegressor(**self.params)
        self.feature_cols: list[str] = []

    def fit(self, df: pd.DataFrame) -> "XGBoostCPIForecaster":
        self.feature_cols = [c for c in df.columns if c not in ("cpi", "target")]
        X, y = df[self.feature_cols], df["target"]
        self._model.fit(X, y)
        logger.info("Fitted on %d samples with %d features", len(X), len(self.feature_cols))
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self._model.predict(df[self.feature_cols])

    def cross_val_mae(self, df: pd.DataFrame, n_splits: int = 5) -> float:
        feature_cols = [c for c in df.columns if c not in ("cpi", "target")]
        X, y = df[feature_cols], df["target"]
        tscv = TimeSeriesSplit(n_splits=n_splits)
        maes = []
        for tr, te in tscv.split(X):
            m = XGBRegressor(**self.params)
            m.fit(X.iloc[tr], y.iloc[tr])
            preds = m.predict(X.iloc[te])
            maes.append(mean_absolute_error(y.iloc[te], preds))
        mean_mae = float(np.mean(maes))
        logger.info("CV MAE (n_splits=%d): %.4f%%p", n_splits, mean_mae)
        return mean_mae

    def feature_importance(self, df: pd.DataFrame) -> pd.Series:
        feature_cols = [c for c in df.columns if c not in ("cpi", "target")]
        return pd.Series(
            self._model.feature_importances_,
            index=feature_cols,
        ).sort_values(ascending=False)


def run() -> None:
    df = load_features()
    model = XGBoostCPIForecaster()
    mae = model.cross_val_mae(df)
    model.fit(df)

    # Predict next month using latest row
    latest = df.iloc[[-1]].copy()
    pred = model.predict(latest)[0]

    print(f"\n=== XGBoost CPI Forecast ===")
    print(f"Next month CPI YoY estimate: {pred:.2f}%")
    print(f"Cross-val MAE: {mae:.4f}%p")
    print("\nTop 10 features:")
    print(model.feature_importance(df).head(10).round(4).to_string())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()
