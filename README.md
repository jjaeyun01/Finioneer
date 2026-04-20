# Market Intelligence Platform

> AI-powered economic indicator forecasting, stock market dashboard, and financial news analysis for US markets (NYSE/Nasdaq), Korean markets (KOSPI/KOSDAQ), and Bitcoin.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

This project builds a full-stack market intelligence system that:

- **Tracks** key indicators across US, Korean, and crypto markets in real time
- **Forecasts** macro indicators (CPI, Fed rate direction) using statistical and ML models
- **Analyzes** financial news with NLP to classify market impact and sentiment
- **Alerts** when model predictions diverge significantly from consensus estimates
- **Backtests** prediction signals against historical market performance

---

## Architecture

```
Data Sources (FRED, yfinance, NewsAPI)
        ↓
Collectors (automated daily pipeline)
        ↓
Storage (PostgreSQL + Redis cache)
        ↓
┌─────────────┬──────────────┬───────────────┐
│ ML Models   │  NLP Engine  │  Dashboard    │
│ CPI / FOMC  │  FinBERT     │  Streamlit/   │
│ ARIMA/XGB/  │  News filter │  Next.js      │
│ LSTM        │  Sentiment   │               │
└─────────────┴──────────────┴───────────────┘
        ↓
REST API (FastAPI) → Alerts (Telegram/Slack)
```

---

## Features by Phase

| Phase | Period | Key Features |
|-------|--------|-------------|
| 0 — Foundation | Apr–May 4 | Repo setup, FRED API, ARIMA Lv1 CPI model |
| 1 — Pipeline + Dashboard | May 5–25 | Auto data collection, market indicator dashboard, economic calendar |
| 2 — ML + NLP | May 26–Jun 29 | XGBoost forecaster, FinBERT news classifier, backtesting engine |
| 3 — Advanced + API | Jun 30–Jul 27 | FOMC text analysis, LSTM, ensemble model, REST API, alert bot |
| 4 — Deploy | Jul 28–Aug 10 | Docker, CI/CD, cloud deployment, full documentation |

---

## Tracked Markets & Indicators

**US Markets**
- Nasdaq-100, S&P 500, VIX, US 10Y Treasury yield
- CPI, PPI, NFP, PCE, FOMC rate decisions
- Mag7 earnings schedule

**Korean Markets**
- KOSPI, KOSDAQ
- KRW/USD exchange rate, foreign investor net buying
- Samsung Electronics, SK Hynix flows

**Crypto**
- Bitcoin price, dominance, funding rate
- BTC ETF flows (BlackRock IBIT, Fidelity FBTC)
- Fear & Greed Index, MVRV Ratio

---

## Prediction Models

### Lv 1 — Statistical
- ARIMA on CPI monthly time series
- OLS regression: PPI (lag 2) → CPI

### Lv 2 — Machine Learning
- XGBoost regressor with macro feature engineering
- GradientBoosting classifier for FOMC direction
- TimeSeriesSplit cross-validation

### Lv 3 — NLP + Deep Learning
- FinBERT sentiment on FOMC statements and financial news
- LSTM for multi-step time series forecasting
- Weighted ensemble of all model outputs

### Lv 4 — Production
- Nowcasting pipeline with daily auto-update
- Consensus divergence alerts
- Full backtesting with simulated P&L

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/YOUR_USERNAME/market-intelligence.git
cd market-intelligence

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp configs/.env.example configs/.env
# Edit configs/.env and add your API keys

# 5. Run first data collection
python scripts/collect_data.py

# 6. Launch dashboard
streamlit run src/dashboard/app.py
```

---

## Project Structure

```
market-intelligence/
├── data/
│   ├── raw/              # Raw API responses (never committed)
│   ├── processed/        # Cleaned, feature-engineered datasets
│   └── cache/            # Short-lived cache files
├── src/
│   ├── collectors/       # Data ingestion modules
│   │   ├── fred.py       # FRED API client
│   │   ├── market.py     # yfinance / stock data
│   │   └── news.py       # NewsAPI + RSS scrapers
│   ├── models/           # Forecasting models
│   │   ├── arima.py      # Lv1: ARIMA baseline
│   │   ├── xgboost_cpi.py# Lv2: XGBoost CPI forecaster
│   │   ├── fomc_clf.py   # Lv2: FOMC direction classifier
│   │   ├── lstm.py       # Lv3: LSTM time series
│   │   └── ensemble.py   # Lv3: Weighted ensemble
│   ├── nlp/              # NLP & text analysis
│   │   ├── finbert.py    # FinBERT sentiment pipeline
│   │   ├── fomc_parser.py# FOMC statement change detection
│   │   └── news_filter.py# Market-relevant news classifier
│   ├── dashboard/        # Visualization layer
│   │   ├── app.py        # Streamlit main app
│   │   └── components/   # Chart components
│   ├── api/              # FastAPI REST server
│   │   ├── main.py       # App entrypoint
│   │   └── routes/       # /predict, /news, /indicators
│   └── utils/            # Shared helpers
│       ├── db.py         # Database connection
│       ├── logger.py     # Logging config
│       └── scheduler.py  # APScheduler jobs
├── notebooks/
│   ├── 01_exploration/   # EDA and data analysis
│   ├── 02_modeling/      # Model experiments
│   └── 03_backtesting/   # Strategy backtests
├── tests/
│   ├── unit/             # Unit tests per module
│   └── integration/      # End-to-end pipeline tests
├── scripts/
│   ├── collect_data.py   # One-shot data collection
│   └── train_models.py   # Model training script
├── configs/
│   ├── .env.example      # Environment variable template
│   └── settings.py       # App configuration (pydantic)
├── docs/
│   └── model_performance.md  # MAE / accuracy reports
├── .github/
│   └── workflows/
│       ├── ci.yml         # Test on PR
│       └── daily_collect.yml # Cron data collection
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Environment Variables

```bash
# configs/.env.example

# Data APIs
FRED_API_KEY=your_fred_api_key_here        # fred.stlouisfed.org (free)
NEWS_API_KEY=your_newsapi_key_here         # newsapi.org (free tier)

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/market_intel

# Alerts
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional
REDIS_URL=redis://localhost:6379
```

---

## Model Performance (updated monthly)

| Model | Target | MAE | vs Consensus |
|-------|--------|-----|-------------|
| ARIMA | CPI MoM | — | — |
| XGBoost | CPI MoM | — | — |
| Ensemble | CPI MoM | — | — |
| FOMC Classifier | Rate direction | — | — |

*Performance table updated after each major release.*

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data collection | `fredapi`, `yfinance`, `requests`, `feedparser` |
| Statistical models | `statsmodels`, `pmdarima` |
| ML models | `xgboost`, `lightgbm`, `scikit-learn` |
| Deep learning | `pytorch`, `pytorch-lightning` |
| NLP | `transformers` (FinBERT), `difflib` |
| API server | `fastapi`, `uvicorn` |
| Dashboard | `streamlit`, `plotly` |
| Database | `postgresql`, `sqlalchemy`, `alembic` |
| Scheduling | `apscheduler` |
| DevOps | `docker`, `github-actions` |

---

## Roadmap

- [x] Phase 0: Repository setup and Lv1 ARIMA model
- [ ] Phase 1: Automated data pipeline and indicator dashboard
- [ ] Phase 2: XGBoost forecaster and FinBERT news classifier
- [ ] Phase 3: LSTM, ensemble model, REST API
- [ ] Phase 4: Cloud deployment and CI/CD

---

## License

MIT — see [LICENSE](LICENSE) for details.
