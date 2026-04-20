# Study Roadmap

Phase별로 무엇을 공부해야 하는지 우선순위 순으로 정리.

---

## Phase 0 — 기반 (Apr 19 ~ May 4, 학기 중)

하루 1~2시간. 코드보다 개념 이해 우선.

### 필수
| 주제 | 리소스 | 예상 시간 |
|------|--------|----------|
| pandas time series 기초 | [공식 docs — Time series / date](https://pandas.pydata.org/docs/user_guide/timeseries.html) | 3h |
| ARIMA 개념 | StatQuest "ARIMA" YouTube 시리즈 (3개) | 2h |
| statsmodels ARIMA | statsmodels 공식 예제 | 2h |
| FRED API | [fred.stlouisfed.org/docs/api/fred/](https://fred.stlouisfed.org/docs/api/fred/) | 1h |

### 목표
- CPI 데이터를 받아서 ARIMA 예측값이 화면에 출력되면 Phase 0 완료

---

## Phase 1 — 파이프라인 (May 5 ~ May 25)

종강 직후 집중. 하루 6~8시간.

### 필수
| 주제 | 리소스 | 예상 시간 |
|------|--------|----------|
| FastAPI 기초 | [FastAPI 공식 튜토리얼](https://fastapi.tiangolo.com/tutorial/) | 4h |
| Streamlit | [streamlit.io/gallery](https://streamlit.io/gallery) | 3h |
| SQLAlchemy 2.0 | 공식 ORM quickstart | 3h |
| APScheduler | 공식 docs | 2h |
| Plotly 시각화 | Plotly Express 기초 + go.Figure | 3h |
| yfinance | PyPI README + 예제 | 1h |

### 목표
- 로컬에서 `streamlit run src/dashboard/app.py` → 지표 대시보드 렌더링

---

## Phase 2 — ML + NLP (May 26 ~ Jun 29)

하루 8시간. 가장 밀도 높은 기간.

### 필수
| 주제 | 리소스 | 예상 시간 |
|------|--------|----------|
| scikit-learn pipeline | [User Guide — Pipelines](https://scikit-learn.org/stable/modules/pipeline.html) | 3h |
| XGBoost 파라미터 튜닝 | XGBoost docs + Kaggle notebooks | 4h |
| TimeSeriesSplit (시계열 CV) | sklearn docs | 2h |
| Feature engineering (lag, rolling) | Towards Data Science 시계열 피처 글 | 3h |
| HuggingFace Transformers 입문 | [huggingface.co/course](https://huggingface.co/course) Ch1-4 | 6h |
| FinBERT 사용법 | `yiyanghkust/finbert-tone` 모델 카드 | 2h |
| backtesting.py | [공식 docs](https://kernc.github.io/backtesting.py/) | 3h |

### 목표
- XGBoost CPI MAE < ARIMA MAE
- FinBERT가 뉴스 기사를 Positive/Negative/Neutral로 분류

---

## Phase 3 — 고급 (Jun 30 ~ Jul 27)

| 주제 | 리소스 | 예상 시간 |
|------|--------|----------|
| PyTorch 기초 | [pytorch.org/tutorials](https://pytorch.org/tutorials/) (60분 블리츠) | 4h |
| LSTM for time series | PyTorch Lightning LSTM 튜토리얼 | 6h |
| Ensemble methods | scikit-learn Ensemble 챕터 | 3h |
| Docker + Docker Compose | [docs.docker.com/get-started](https://docs.docker.com/get-started/) | 4h |
| FastAPI 심화 (Background Tasks, WebSocket) | FastAPI 고급 튜토리얼 | 3h |
| Telegram Bot API | python-telegram-bot 라이브러리 | 2h |

### 목표
- `/predict/cpi` API 엔드포인트가 실제 앙상블 예측값을 반환
- 컨센서스 괴리 시 텔레그램 알림 발송

---

## Phase 4 — 배포 (Jul 28 ~ Aug 10)

| 주제 | 리소스 | 예상 시간 |
|------|--------|----------|
| GitHub Actions | [docs.github.com/actions](https://docs.github.com/en/actions) | 3h |
| Railway 배포 | [railway.app/docs](https://docs.railway.app/) | 2h |
| Next.js 기초 (선택) | [nextjs.org/learn](https://nextjs.org/learn) | 6h |
| Swagger / OpenAPI 문서화 | FastAPI 자동 생성 활용 | 1h |

---

## 참고 서적 (선택)

- *Python for Finance* — Yves Hilpisch (금융 데이터 분석 전반)
- *Advances in Financial Machine Learning* — Marcos López de Prado (고급, Phase 3+)
- *Natural Language Processing with Transformers* — Lewis Tunstall et al. (NLP)

---

## 유용한 커뮤니티 / 레퍼런스

- [QuantLib](https://www.quantlib.org/) — 금융 수학 라이브러리
- [OpenBB Terminal](https://github.com/OpenBB-finance/OpenBBTerminal) — 오픈소스 금융 분석 플랫폼 (코드 참고)
- [Awesome Quant](https://github.com/wilsonfreitas/awesome-quant) — 금융 ML 리소스 큐레이션
- r/algotrading, r/MachineLearning
