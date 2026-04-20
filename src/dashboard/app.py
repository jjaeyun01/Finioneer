"""Market Intelligence Dashboard — Streamlit app.

Run:
    streamlit run src/dashboard/app.py
"""

import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("Market Intelligence")
st.sidebar.markdown("US · Korea · Bitcoin")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "🔮 Forecasts", "📰 News", "⚙️ Settings"],
)

# ── Overview ──────────────────────────────────────────────────────────────────

if page == "📊 Overview":
    st.title("Market Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("S&P 500",    "—", "—")
    col2.metric("Nasdaq-100", "—", "—")
    col3.metric("KOSPI",      "—", "—")
    col4.metric("Bitcoin",    "—", "—")

    st.divider()
    st.subheader("Macro Indicators")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("CPI YoY",         "—", help="US Consumer Price Index")
    col_b.metric("Fed Funds Rate",   "—", help="Current federal funds target rate")
    col_c.metric("10Y Treasury",     "—", help="US 10-year Treasury yield")

    col_d, col_e, col_f = st.columns(3)
    col_d.metric("VIX",             "—", help="CBOE Volatility Index")
    col_e.metric("Unemployment",     "—", help="US Unemployment Rate")
    col_f.metric("KRW/USD",          "—", help="Korean Won / US Dollar rate")

    st.divider()
    st.info("Connect data collectors (Phase 1) to populate live values.")


# ── Forecasts ─────────────────────────────────────────────────────────────────

elif page == "🔮 Forecasts":
    st.title("Economic Forecasts")

    tab_cpi, tab_fomc = st.tabs(["CPI Forecast", "FOMC Direction"])

    with tab_cpi:
        st.subheader("CPI YoY — Next 3 Months")
        model_choice = st.selectbox("Model", ["ARIMA (Lv1)", "XGBoost (Lv2)", "Ensemble (Lv3)"])
        st.info(f"Selected: {model_choice}. Train models in Phase 2 to see predictions.")

        # Placeholder chart
        fig = go.Figure()
        fig.add_annotation(
            text="Forecast will appear here after Phase 2",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab_fomc:
        st.subheader("Next FOMC — Rate Decision")
        col1, col2, col3 = st.columns(3)
        col1.metric("HIKE probability",  "—")
        col2.metric("HOLD probability",  "—")
        col3.metric("CUT probability",   "—")
        st.info("Wire up FOMCClassifier in Phase 2 to see live probabilities.")


# ── News ──────────────────────────────────────────────────────────────────────

elif page == "📰 News":
    st.title("Financial News")
    st.subheader("Market-Relevant Headlines")
    st.info("Connect NewsCollector + FinBERT in Phase 2 to see live news with sentiment tags.")

    # Placeholder table
    sample_cols = ["title", "source", "sentiment", "hawk_score", "published"]
    st.dataframe(pd.DataFrame(columns=sample_cols), use_container_width=True)


# ── Settings ──────────────────────────────────────────────────────────────────

elif page == "⚙️ Settings":
    st.title("Settings")
    st.markdown("Edit `configs/.env` to configure API keys and database connection.")

    st.subheader("API Keys Status")
    try:
        from configs.settings import settings
        fred_ok = bool(settings.fred_api_key and settings.fred_api_key != "your_fred_api_key_here")
        news_ok = bool(settings.news_api_key)
        st.markdown(f"- FRED API: {'✅ set' if fred_ok else '❌ missing'}")
        st.markdown(f"- NewsAPI:  {'✅ set' if news_ok else '⚠️ not set (RSS still works)'}")
    except Exception as e:
        st.error(f"Could not load settings: {e}")
