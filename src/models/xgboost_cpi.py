"""Lv2 — XGBoost CPI forecaster (Component-based, MoM target).

Cleveland Fed 방식 참고:
- Core CPI + Energy CPI 분리 예측 후 가중합산
- MoM을 타겟으로
- EIA 휘발유 가격을 핵심 입력으로 사용
"""

import logging
import time
import numpy as np
import pandas as pd
from fredapi import Fred
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor
from configs.settings import settings

logger = logging.getLogger(__name__)

SERIES = {
    "cpi":        "CPIAUCSL",
    "core_cpi":   "CPILFESL",
    "energy_cpi": "CPIENGSL",
    "ppi":        "PPIACO",
    "core_ppi":   "PPIFES",
    "oil":        "DCOILWTICO",
    "gasoline":   "GASREGCOVW",
    "wage":       "CES0500000003",
    "unemp":      "UNRATE",
    "t10y":       "GS10",
}

WEIGHTS = {
    "core":   0.793,
    "energy": 0.068,
    "food":   0.139,
}


def load_data(start: str = "2012-01-01") -> pd.DataFrame:
    fred = Fred(api_key=settings.fred_api_key)
    raw = {}
    for name, sid in SERIES.items():
        for attempt in range(3):
            try:
                s = fred.get_series(sid, observation_start=start)
                raw[name] = s.resample("MS").mean()
                logger.info("Loaded %s: %d obs", name, len(raw[name]))
                break
            except Exception as e:
                if attempt == 2:
                    logger.warning("Skipping %s (%s): %s", name, sid, e)
                else:
                    time.sleep(1)
    return pd.DataFrame(raw)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    # 필수 컬럼 없으면 재시도
    fred = Fred(api_key=settings.fred_api_key)
    for name, sid in [("cpi", "CPIAUCSL"), ("core_cpi", "CPILFESL"), ("energy_cpi", "CPIENGSL")]:
        if name not in df.columns:
            logger.warning("Re-fetching %s...", name)
            try:
                s = fred.get_series(sid, observation_start="2012-01-01")
                df[name] = s.resample("MS").mean()
            except Exception as e:
                logger.error("Failed to fetch %s: %s", name, e)

    out = pd.DataFrame(index=df.index)

    # ── 타겟 (MoM %) ──────────────────────────────────────────────────────────
    if "core_cpi" in df.columns:
        out["target_core"]   = df["core_cpi"].pct_change(1) * 100
    if "energy_cpi" in df.columns:
        out["target_energy"] = df["energy_cpi"].pct_change(1) * 100
    if "cpi" in df.columns:
        out["target_cpi"]    = df["cpi"].pct_change(1) * 100

    # ── 선행 지표 MoM ─────────────────────────────────────────────────────────
    for col in ["ppi", "core_ppi", "oil", "gasoline", "wage"]:
        if col in df.columns:
            out[f"{col}_mom"] = df[col].pct_change(1) * 100

    # YoY (추세)
    for col in ["ppi", "oil", "wage"]:
        if col in df.columns:
            out[f"{col}_yoy"] = df[col].pct_change(12) * 100

    # 레벨 지표
    for col in ["unemp", "t10y"]:
        if col in df.columns:
            out[col] = df[col]
            out[f"{col}_diff"] = df[col].diff()

    # ── 자기회귀 피처 (AR) ────────────────────────────────────────────────────
    if "target_core" in out.columns:
        for lag in [1, 2, 3, 6]:
            out[f"core_lag{lag}"] = out["target_core"].shift(lag)
        out["core_ma3"] = out["target_core"].shift(1).rolling(3).mean()
        out["core_ma6"] = out["target_core"].shift(1).rolling(6).mean()

    if "target_energy" in out.columns:
        for lag in [1, 2, 3]:
            out[f"energy_lag{lag}"] = out["target_energy"].shift(lag)

    # ── 유가 시차 (1~2개월 선행) ──────────────────────────────────────────────
    if "oil_mom" in out.columns:
        for lag in [1, 2]:
            out[f"oil_mom_lag{lag}"] = out["oil_mom"].shift(lag)
    if "gasoline_mom" in out.columns:
        for lag in [1, 2]:
            out[f"gas_mom_lag{lag}"] = out["gasoline_mom"].shift(lag)

    # ── PPI → CPI 전가 시차 (2~3개월) ────────────────────────────────────────
    if "ppi_mom" in out.columns:
        for lag in [2, 3]:
            out[f"ppi_mom_lag{lag}"] = out["ppi_mom"].shift(lag)

    # ── 계절성 ────────────────────────────────────────────────────────────────
    out["month"] = out.index.month
    out["q1"] = (out.index.month.isin([1, 2, 3])).astype(int)
    out["q2"] = (out.index.month.isin([4, 5, 6])).astype(int)
    out["q3"] = (out.index.month.isin([7, 8, 9])).astype(int)

    out = out.dropna()
    logger.info("Feature matrix: %d rows × %d cols", *out.shape)
    return out


EXCLUDE = {"target_core", "target_energy", "target_cpi"}

XGB_PARAMS = dict(
    n_estimators=300,
    max_depth=3,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.7,
    reg_alpha=0.05,
    reg_lambda=1.0,
    random_state=42,
)


class ComponentCPIForecaster:
    """Core CPI MoM + Energy CPI MoM 분리 예측 후 가중합산."""

    def __init__(self):
        self.core_model   = XGBRegressor(**XGB_PARAMS)
        self.energy_model = XGBRegressor(**XGB_PARAMS)
        self.feature_cols: list[str] = []

    def _feature_cols(self, df: pd.DataFrame) -> list[str]:
        return [c for c in df.columns if c not in EXCLUDE]

    def fit(self, df: pd.DataFrame) -> "ComponentCPIForecaster":
        self.feature_cols = self._feature_cols(df)
        X = df[self.feature_cols]
        if "target_core" in df.columns:
            self.core_model.fit(X, df["target_core"])
        if "target_energy" in df.columns:
            self.energy_model.fit(X, df["target_energy"])
        logger.info("Fitted: %d samples, %d features", len(X), len(self.feature_cols))
        return self

    def predict_components(self, df: pd.DataFrame) -> dict:
        X = df[self.feature_cols]
        core_pred   = float(self.core_model.predict(X)[0])
        energy_pred = float(self.energy_model.predict(X)[0])
        headline    = (core_pred * (WEIGHTS["core"] + WEIGHTS["food"])
                       + energy_pred * WEIGHTS["energy"])
        return {
            "core_mom":     round(core_pred, 4),
            "energy_mom":   round(energy_pred, 4),
            "headline_mom": round(headline, 4),
        }

    def cross_val(self, df: pd.DataFrame, n_splits: int = 5) -> dict:
        feature_cols = self._feature_cols(df)
        X = df[feature_cols]
        tscv = TimeSeriesSplit(n_splits=n_splits)
        core_maes, energy_maes, headline_maes = [], [], []

        for tr, te in tscv.split(X):
            cm = XGBRegressor(**XGB_PARAMS)
            em = XGBRegressor(**XGB_PARAMS)

            if "target_core" in df.columns:
                cm.fit(X.iloc[tr], df["target_core"].iloc[tr])
                cp = cm.predict(X.iloc[te])
                core_maes.append(mean_absolute_error(df["target_core"].iloc[te], cp))
            else:
                cp = np.zeros(len(te))

            if "target_energy" in df.columns:
                em.fit(X.iloc[tr], df["target_energy"].iloc[tr])
                ep = em.predict(X.iloc[te])
                energy_maes.append(mean_absolute_error(df["target_energy"].iloc[te], ep))
            else:
                ep = np.zeros(len(te))

            if "target_cpi" in df.columns:
                hp = (cp * (WEIGHTS["core"] + WEIGHTS["food"])
                      + ep * WEIGHTS["energy"])
                headline_maes.append(mean_absolute_error(df["target_cpi"].iloc[te], hp))

        result = {
            "core_mae":     round(float(np.mean(core_maes)), 4) if core_maes else None,
            "energy_mae":   round(float(np.mean(energy_maes)), 4) if energy_maes else None,
            "headline_mae": round(float(np.mean(headline_maes)), 4) if headline_maes else None,
        }
        logger.info("CV — Core: %.4f | Energy: %.4f | Headline: %.4f",
                    result["core_mae"] or 0,
                    result["energy_mae"] or 0,
                    result["headline_mae"] or 0)
        return result

    def feature_importance(self) -> pd.DataFrame:
        return pd.DataFrame({
            "core":   self.core_model.feature_importances_,
            "energy": self.energy_model.feature_importances_,
        }, index=self.feature_cols).sort_values("core", ascending=False)


def run() -> None:
    logger.info("=== Component-based CPI Forecaster ===")
    raw = load_data()
    df  = build_features(raw)

    model = ComponentCPIForecaster()
    logger.info("Running cross-validation...")
    cv = model.cross_val(df)
    model.fit(df)
    pred = model.predict_components(df.iloc[[-1]])

    current_yoy = raw["cpi"].pct_change(12).iloc[-1] * 100 if "cpi" in raw.columns else float("nan")

    print("\n" + "="*52)
    print("   Component-based CPI Forecast (MoM)")
    print("="*52)
    print(f"  현재 CPI YoY:          {current_yoy:.2f}%")
    print(f"\n  [예측 — 다음 달 MoM]")
    print(f"  Core CPI MoM:          {pred['core_mom']:+.3f}%")
    print(f"  Energy CPI MoM:        {pred['energy_mom']:+.3f}%")
    print(f"  Headline CPI MoM:      {pred['headline_mom']:+.3f}%")
    print(f"\n  [교차검증 MAE — MoM 기준]")
    print(f"  Core MAE:              {cv['core_mae']}%p")
    print(f"  Energy MAE:            {cv['energy_mae']}%p")
    print(f"  Headline MAE:          {cv['headline_mae']}%p")
    print(f"\n  [참고]")
    print(f"  Cleveland Fed 목표:    ~0.05%p MoM")
    print(f"  ARIMA YoY MAE:         0.2188%p (다른 기준)")
    print(f"\n  Top Core features:")
    fi = model.feature_importance()
    print(fi["core"].head(8).round(4).to_string())
    print(f"\n  Top Energy features:")
    print(fi["energy"].head(5).round(4).to_string())
    print("="*52)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()