"""Lv3 — Weighted ensemble of ARIMA + XGBoost + NLP signal.

Combines multiple model outputs into a single CPI forecast.
Weights are set by inverse-MAE from cross-validation.
"""

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelOutput:
    name: str
    prediction: float
    mae: float                  # cross-val MAE — lower = higher weight
    metadata: dict = field(default_factory=dict)


class WeightedEnsemble:
    """Inverse-MAE weighted ensemble for CPI point forecasts."""

    def __init__(self, outputs: list[ModelOutput]):
        self.outputs = outputs
        self._weights = self._compute_weights()

    def _compute_weights(self) -> np.ndarray:
        maes = np.array([o.mae for o in self.outputs])
        if np.all(maes == 0):
            return np.ones(len(maes)) / len(maes)
        inv = 1.0 / np.where(maes == 0, 1e-6, maes)
        return inv / inv.sum()

    @property
    def weights(self) -> dict[str, float]:
        return {o.name: round(float(w), 4) for o, w in zip(self.outputs, self._weights)}

    def predict(self) -> float:
        preds = np.array([o.prediction for o in self.outputs])
        return float(np.dot(self._weights, preds))

    def summary(self) -> dict:
        ensemble_pred = self.predict()
        return {
            "ensemble_forecast": round(ensemble_pred, 4),
            "model_weights": self.weights,
            "individual_forecasts": {o.name: round(o.prediction, 4) for o in self.outputs},
        }


def build_ensemble(
    arima_pred: float,
    arima_mae: float,
    xgb_pred: float,
    xgb_mae: float,
    nlp_hawk_score: float | None = None,
    nlp_weight: float = 0.15,
) -> WeightedEnsemble:
    """
    Convenience builder.

    If nlp_hawk_score is provided, adjusts XGBoost prediction slightly
    upward (hawkish → higher inflation) and adds it as a third signal.
    """
    outputs = [
        ModelOutput(name="arima",   prediction=arima_pred, mae=arima_mae),
        ModelOutput(name="xgboost", prediction=xgb_pred,   mae=xgb_mae),
    ]

    if nlp_hawk_score is not None:
        # Hawkish NLP signal: shift prediction proportionally
        nlp_adjustment = (nlp_hawk_score - 0.5) * 0.3  # ±0.15%p max effect
        nlp_pred = xgb_pred + nlp_adjustment
        nlp_mae = (arima_mae + xgb_mae) / 2  # conservative estimate
        outputs.append(ModelOutput(
            name="nlp_signal",
            prediction=nlp_pred,
            mae=nlp_mae,
            metadata={"hawk_score": nlp_hawk_score, "adjustment": nlp_adjustment},
        ))

    return WeightedEnsemble(outputs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    ensemble = build_ensemble(
        arima_pred=3.2,  arima_mae=0.28,
        xgb_pred=3.45,   xgb_mae=0.19,
        nlp_hawk_score=0.62,
    )

    summary = ensemble.summary()
    print("\n=== Ensemble Forecast ===")
    print(f"Final CPI forecast: {summary['ensemble_forecast']:.2f}%")
    print("\nModel weights:")
    for name, w in summary["model_weights"].items():
        pred = summary["individual_forecasts"][name]
        print(f"  {name:<14} weight={w:.3f}  forecast={pred:.2f}%")
