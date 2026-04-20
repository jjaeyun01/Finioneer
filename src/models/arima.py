"""Lv1 — ARIMA CPI forecaster."""

import logging
import warnings

import numpy as np
import pandas as pd
from fredapi import Fred
from statsmodels.tsa.arima.model import ARIMA

from configs.settings import settings

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


def load_cpi(start: str = "2010-01-01") -> pd.Series:
    fred = Fred(api_key=settings.fred_api_key)
    cpi_raw = fred.get_series("CPIAUCSL", observation_start=start)
    cpi_yoy = cpi_raw.pct_change(12) * 100
    cpi_yoy = cpi_yoy.dropna().resample("MS").last()
    cpi_yoy.name = "cpi_yoy"
    logger.info("Loaded CPI YoY: %d observations (latest: %.2f%%)", len(cpi_yoy), cpi_yoy.iloc[-1])
    return cpi_yoy


class ARIMAForecaster:

    def __init__(self, order: tuple = (2, 1, 2)):
        self.order = order
        self._result = None

    def fit(self, series: pd.Series) -> "ARIMAForecaster":
        logger.info("Fitting ARIMA%s on %d observations", self.order, len(series))
        self._result = ARIMA(series, order=self.order).fit()
        logger.info("AIC: %.2f | BIC: %.2f", self._result.aic, self._result.bic)
        return self

    def forecast(self, steps: int = 3) -> pd.Series:
        if self._result is None:
            raise RuntimeError("Call .fit() first")
        fc = self._result.forecast(steps=steps)
        logger.info("Forecast (%d months ahead):", steps)
        return fc

    def mae(self, series: pd.Series, n_test: int = 12) -> float:
        errors = []
        for i in range(n_test):
            train_end = len(series) - n_test + i
            train = series.iloc[:train_end]
            actual = float(series.iloc[train_end])
            try:
                result = ARIMA(train, order=self.order).fit()
                pred = float(result.forecast(steps=1).iloc[0])
                errors.append(abs(pred - actual))
            except Exception as e:
                logger.warning("MAE step %d failed: %s", i, e)
        if not errors:
            return float("nan")
        mae_val = float(np.nanmean(errors))
        logger.info("Walk-forward MAE (n=%d): %.4f%%p", n_test, mae_val)
        return mae_val


def run(steps: int = 3) -> pd.Series:
    cpi = load_cpi()
    model = ARIMAForecaster(order=(2, 1, 2))
    model.fit(cpi)
    fc = model.forecast(steps=steps)
    mae = model.mae(cpi)
    print("=== ARIMA CPI Forecast ===")
    print(fc.round(3).to_string())
    print(f"Walk-forward MAE (last 12m): {mae:.4f}%p")
    return fc


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()