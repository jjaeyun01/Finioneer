"""Unit tests for the ARIMA forecaster (no API calls — uses synthetic data)."""

import numpy as np
import pandas as pd
import pytest

from src.models.arima import ARIMAForecaster


@pytest.fixture
def synthetic_cpi() -> pd.Series:
    """Stationary-ish series that mimics CPI YoY behaviour."""
    rng = np.random.default_rng(42)
    idx = pd.date_range("2015-01-01", periods=100, freq="MS")
    values = 2.5 + np.cumsum(rng.normal(0, 0.1, 100))
    return pd.Series(values, index=idx, name="cpi_yoy")


def test_fit_and_forecast(synthetic_cpi):
    model = ARIMAForecaster(order=(1, 1, 1))
    model.fit(synthetic_cpi)
    fc = model.forecast(steps=3)
    assert len(fc) == 3
    assert fc.notna().all()


def test_mae_is_positive(synthetic_cpi):
    model = ARIMAForecaster(order=(1, 1, 1))
    mae = model.mae(synthetic_cpi, n_test=6)
    assert mae >= 0
