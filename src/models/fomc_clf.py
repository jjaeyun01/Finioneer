"""Lv2 — FOMC rate-direction classifier.

Predicts whether the Fed will hike (+1), hold (0), or cut (-1)
using macro features + optional FinBERT hawkish/dovish signal.
"""

import logging

import numpy as np
import pandas as pd
from fredapi import Fred
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import TimeSeriesSplit

from configs.settings import settings

logger = logging.getLogger(__name__)

FEATURE_SERIES = {
    "cpi":    "CPIAUCSL",
    "ppi":    "PPIACO",
    "unemp":  "UNRATE",
    "t10y":   "GS10",
    "fed":    "FEDFUNDS",
    "gdp":    "GDP",
}


def load_data(start: str = "2000-01-01") -> pd.DataFrame:
    fred = Fred(api_key=settings.fred_api_key)
    raw = {}
    for name, sid in FEATURE_SERIES.items():
        try:
            s = fred.get_series(sid, observation_start=start)
            raw[name] = s.resample("MS").last()
        except Exception as e:
            logger.warning("Skipping %s: %s", name, e)

    df = pd.DataFrame(raw)
    df["cpi_yoy"]   = df["cpi"].pct_change(12) * 100
    df["ppi_yoy"]   = df["ppi"].pct_change(12) * 100
    df["gdp_qoq"]   = df["gdp"].pct_change(3) * 100
    df["t10y_diff"] = df["t10y"].diff()
    df["fed_diff"]  = df["fed"].diff()

    # Lag features
    for col in ["cpi_yoy", "ppi_yoy", "unemp", "t10y"]:
        if col in df.columns:
            df[f"{col}_lag1"] = df[col].shift(1)
            df[f"{col}_lag2"] = df[col].shift(2)

    # Target: FOMC direction (sign of monthly fed funds rate change)
    df["direction"] = df["fed_diff"].apply(
        lambda x: 1 if x > 0.01 else (-1 if x < -0.01 else 0)
    )

    drop_cols = ["cpi", "ppi", "gdp", "fed", "fed_diff"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    df = df.dropna()

    logger.info("FOMC dataset: %d rows | class distribution:\n%s",
                len(df), df["direction"].value_counts().to_string())
    return df


class FOMCClassifier:

    def __init__(self):
        self.params = dict(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )
        self._model = GradientBoostingClassifier(**self.params)
        self.feature_cols: list[str] = []

    def fit(self, df: pd.DataFrame) -> "FOMCClassifier":
        self.feature_cols = [c for c in df.columns if c != "direction"]
        X, y = df[self.feature_cols], df["direction"]
        self._model.fit(X, y)
        logger.info("Fitted FOMC classifier on %d samples", len(X))
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self._model.predict(df[self.feature_cols])

    def predict_proba(self, df: pd.DataFrame) -> pd.DataFrame:
        proba = self._model.predict_proba(df[self.feature_cols])
        return pd.DataFrame(proba, columns=self._model.classes_, index=df.index)

    def evaluate(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        feature_cols = [c for c in df.columns if c != "direction"]
        X, y = df[feature_cols], df["direction"]
        tscv = TimeSeriesSplit(n_splits=n_splits)
        all_preds, all_true = [], []
        for tr, te in tscv.split(X):
            m = GradientBoostingClassifier(**self.params)
            m.fit(X.iloc[tr], y.iloc[tr])
            all_preds.extend(m.predict(X.iloc[te]))
            all_true.extend(y.iloc[te])

        report = classification_report(all_true, all_preds,
                                       target_names=["cut", "hold", "hike"],
                                       output_dict=True)
        logger.info("FOMC CV classification report:\n%s",
                    classification_report(all_true, all_preds,
                                          target_names=["cut", "hold", "hike"]))
        return report


DIRECTION_LABEL = {1: "HIKE", 0: "HOLD", -1: "CUT"}


def run() -> None:
    df = load_data()
    clf = FOMCClassifier()
    clf.evaluate(df)
    clf.fit(df)

    latest = df.iloc[[-1]].copy()
    pred = clf.predict(latest)[0]
    proba = clf.predict_proba(latest)

    print(f"\n=== FOMC Direction Forecast ===")
    print(f"Predicted next move: {DIRECTION_LABEL[pred]}")
    print("\nProbabilities:")
    for cls, label in [(-1, "CUT"), (0, "HOLD"), (1, "HIKE")]:
        if cls in proba.columns:
            print(f"  {label}: {proba[cls].iloc[0]:.1%}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()
