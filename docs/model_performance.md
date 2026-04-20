# Model Performance Log

매 Phase 완료 후 업데이트.

---

## CPI Forecasting

| Date | Model | MAE (CV) | MAE (holdout) | vs Consensus | Notes |
|------|-------|----------|---------------|-------------|-------|
| — | ARIMA(2,1,2) | — | — | — | Lv1 baseline |
| — | XGBoost | — | — | — | Lv2 |
| — | Ensemble | — | — | — | Lv3 |

*MAE unit: %p (percentage points YoY)*

---

## FOMC Direction Classification

| Date | Model | Accuracy (CV) | F1-Hold | F1-Hike | F1-Cut | Notes |
|------|-------|--------------|---------|---------|--------|-------|
| — | GradientBoosting | — | — | — | — | Lv2 baseline |
| — | + FinBERT signal | — | — | — | — | Lv3 |

---

## News Sentiment

| Date | Model | Accuracy | F1-Positive | F1-Negative | Notes |
|------|-------|----------|-------------|-------------|-------|
| — | FinBERT (zero-shot) | — | — | — | No fine-tuning |

---

## Backtesting Summary

| Strategy | Period | Total Return | Sharpe | Max Drawdown | Notes |
|----------|--------|-------------|--------|--------------|-------|
| CPI surprise long/short | — | — | — | — | Phase 2 |
| FOMC signal | — | — | — | — | Phase 3 |
