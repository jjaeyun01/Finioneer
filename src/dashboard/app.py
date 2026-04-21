"""Market Intelligence Dashboard — Streamlit app.

Run:
    streamlit run src/dashboard/app.py
"""

import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import os
API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Finioneer",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
    .block-container { padding: 1rem 2rem; }
    .metric-label { font-size: 11px !important; }
    div[data-testid="stMetric"] { background: #f8f9fa; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# ── 데이터 로드 ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_markets():
    try:
        return requests.get(f"{API}/api/markets", timeout=5).json()
    except:
        return {}

@st.cache_data(ttl=60)
def get_macro():
    try:
        return requests.get(f"{API}/api/macro", timeout=5).json()
    except:
        return {}

@st.cache_data(ttl=300)
def get_predict_cpi():
    try:
        return requests.get(f"{API}/api/predict/cpi", timeout=10).json()
    except:
        return {}

@st.cache_data(ttl=60)
def get_chart(ticker, period):
    try:
        return requests.get(f"{API}/api/chart/{ticker}?period={period}", timeout=5).json()
    except:
        return {}

def fmt_chg(val):
    if val is None:
        return "—"
    return f"+{val:.2f}%" if val >= 0 else f"{val:.2f}%"

def chg_color(val):
    if val is None:
        return "normal"
    return "normal" if val >= 0 else "inverse"

# ── 헤더 ─────────────────────────────────────────────────────────────────────

col_logo, col_refresh = st.columns([6, 1])
with col_logo:
    st.markdown("## 📈 Finioneer")
with col_refresh:
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── 탭 ───────────────────────────────────────────────────────────────────────

tab_dash, tab_chart, tab_macro, tab_cpi = st.tabs([
    "🏠 대시보드", "📊 차트", "🌐 거시지표", "🤖 AI 예측"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — 대시보드
# ═══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    markets = get_markets()
    macro   = get_macro()

    # 미국 지수
    st.subheader("🇺🇸 미국 지수")
    c1, c2, c3, c4 = st.columns(4)
    for col, key, label in [
        (c1, "SPY",  "S&P 500"),
        (c2, "QQQ",  "Nasdaq-100"),
        (c3, "DJI",  "Dow Jones"),
        (c4, "BTC",  "Bitcoin"),
    ]:
        d = markets.get(key, {})
        col.metric(
            label,
            f"{d.get('price', '—'):,.2f}" if d.get('price') else "—",
            fmt_chg(d.get('change_pct')),
        )

    # 한국 시장
    st.subheader("🇰🇷 한국 시장")
    c1, c2, c3, c4 = st.columns(4)
    for col, key, label in [
        (c1, "KOSPI",   "KOSPI"),
        (c2, "KOSDAQ",  "KOSDAQ"),
        (c3, "SAMSUNG", "삼성전자"),
        (c4, "SKHYNIX", "SK하이닉스"),
    ]:
        d = markets.get(key, {})
        col.metric(
            label,
            f"{d.get('price', '—'):,.0f}" if d.get('price') else "—",
            fmt_chg(d.get('change_pct')),
        )

    st.divider()

    # 거시지표 요약
    st.subheader("📌 핵심 거시지표")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CPI YoY",       f"{macro.get('cpi_yoy', '—')}%")
    c2.metric("Fed Funds Rate", f"{macro.get('fed_funds', '—')}%")
    c3.metric("10Y 금리",      f"{macro.get('t10y', '—')}%")
    c4.metric("VIX",           f"{macro.get('vix', '—')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PPI YoY",    f"{macro.get('ppi_yoy', '—')}%")
    c2.metric("실업률",      f"{macro.get('unemployment', '—')}%")
    c3.metric("M2 통화량",   f"${macro.get('m2', '—'):,.0f}B" if macro.get('m2') else "—")
    c4.metric("달러 인덱스", f"{macro.get('dxy', '—')}")

    st.divider()

    # Mag7
    st.subheader("🔑 Mag 7")
    cols = st.columns(7)
    for col, key in zip(cols, ["AAPL","NVDA","MSFT","TSLA","META","AMZN","GOOGL"]):
        d = markets.get(key, {})
        col.metric(
            key,
            f"${d.get('price', '—'):,.1f}" if d.get('price') else "—",
            fmt_chg(d.get('change_pct')),
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — 차트
# ═══════════════════════════════════════════════════════════════════════════════
with tab_chart:
    col_t, col_p = st.columns([2, 1])
    with col_t:
        ticker = st.selectbox("티커", ["SPY","QQQ","DJI","KOSPI","KOSDAQ","BTC",
                                       "AAPL","NVDA","MSFT","TSLA","META","AMZN","GOOGL",
                                       "SAMSUNG","SKHYNIX"])
    with col_p:
        period = st.selectbox("기간", ["1w","1mo","3mo","6mo","1y","5y"], index=2)

    data = get_chart(ticker, period)
    if data.get("dates"):
        df = pd.DataFrame({
            "date":   data["dates"],
            "open":   data["open"],
            "high":   data["high"],
            "low":    data["low"],
            "close":  data["close"],
            "volume": data["volume"],
        })
        df["date"] = pd.to_datetime(df["date"])

        # 최신 가격 메트릭
        c1, c2, c3 = st.columns(3)
        c1.metric("현재가",  f"{data['latest']:,.2f}")
        c2.metric("등락",    f"{data['change']:+.2f}")
        c3.metric("등락률",  f"{data['change_pct']:+.3f}%")

        # 캔들스틱 차트
        fig = go.Figure(data=[go.Candlestick(
            x=df["date"],
            open=df["open"], high=df["high"],
            low=df["low"],   close=df["close"],
            increasing_line_color="#16a34a",
            decreasing_line_color="#dc2626",
        )])
        fig.update_layout(
            height=420,
            margin=dict(l=0, r=0, t=24, b=0),
            xaxis_rangeslider_visible=False,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis=dict(gridcolor="#f1f3f5"),
            yaxis=dict(gridcolor="#f1f3f5", side="right"),
        )
        st.plotly_chart(fig, width="stretch")

        # 거래량
        fig2 = go.Figure(go.Bar(
            x=df["date"], y=df["volume"],
            marker_color="#2563eb", opacity=0.6,
        ))
        fig2.update_layout(
            height=100,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            showlegend=False,
            yaxis=dict(side="right"),
        )
        st.plotly_chart(fig2, width="stretch")
    else:
        st.warning("데이터를 불러오는 중입니다. API 서버가 켜져 있는지 확인하세요.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — 거시지표
# ═══════════════════════════════════════════════════════════════════════════════
with tab_macro:
    macro = get_macro()
    st.subheader("미국 거시경제 지표")
    st.markdown("FRED API 기준 최신 데이터")

    rows = [
        ("CPI YoY",        macro.get("cpi_yoy"),      "%",  "소비자물가지수 전년비"),
        ("PPI YoY",        macro.get("ppi_yoy"),      "%",  "생산자물가지수 전년비"),
        ("Fed Funds Rate", macro.get("fed_funds"),    "%",  "연방기금금리"),
        ("실업률",          macro.get("unemployment"), "%",  "Unemployment Rate"),
        ("10Y 금리",        macro.get("t10y"),         "%",  "미국 10년물 국채 수익률"),
        ("VIX",             macro.get("vix"),          "",   "CBOE 변동성 지수"),
        ("M2 통화량",       macro.get("m2"),           "B$", "광의통화 M2"),
        ("달러 인덱스",     macro.get("dxy"),          "",   "DXY Broad"),
    ]
    df_macro = pd.DataFrame(rows, columns=["지표", "값", "단위", "설명"])
    df_macro["값"] = df_macro["값"].apply(lambda x: f"{x:,.3f}" if x else "—")
    st.dataframe(df_macro, width="stretch", hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — AI 예측
# ═══════════════════════════════════════════════════════════════════════════════
with tab_cpi:
    pred = get_predict_cpi()
    st.subheader("🤖 AI CPI 예측")

    if pred.get("forecast"):
        c1, c2, c3 = st.columns(3)
        c1.metric("모델",       pred.get("model", "—"))
        c2.metric("현재 CPI",   f"{pred.get('current_cpi', '—')}%")
        c3.metric("Walk-fwd MAE", f"{pred.get('mae', '—')}%p")

        st.divider()
        st.markdown("#### 향후 3개월 CPI YoY 예측")

        fc = pred["forecast"]
        dates  = [f["date"] for f in fc]
        values = [f["cpi_yoy"] for f in fc]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates, y=values,
            marker_color=["#f59e0b","#f97316","#ef4444"],
            text=[f"{v}%" for v in values],
            textposition="outside",
        ))
        fig.add_hline(y=pred.get("current_cpi", 3.3),
                      line_dash="dot", line_color="#2563eb",
                      annotation_text="현재 CPI")
        fig.add_hline(y=2.0,
                      line_dash="dash", line_color="#16a34a",
                      annotation_text="연준 목표 2%")
        fig.update_layout(
            height=320,
            margin=dict(l=0, r=0, t=24, b=0),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            yaxis=dict(title="CPI YoY (%)", gridcolor="#f1f3f5"),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")

        st.info(f"⚠️ 컨센서스 대비 모델 예측이 약 +0.2%p 높습니다. 관세 영향으로 인플레 재상승 가능성을 반영.")
    else:
        st.warning("API 서버에서 예측 데이터를 불러오는 중입니다.")