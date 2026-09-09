"""
Risk prediction service (Phase 5).

    Digital Twin (one Asset)
         |
         v
    Feature Engineering (app/ml/feature_engineering.py)
         |
         v
    XGBoost | LightGBM | Random Forest    (app/ml/risk/*)
         |
         v
    Risk Predictions + simple ensemble

This module does NOT replace or modify the deterministic risk engine
(app/services/risk_engine.py) — both are computed independently and
returned side by side. Nothing here changes `Asset.risk_score` in the
database; that value continues to be produced solely by the
deterministic engine, exactly as before this phase (Phase 5.1).

Ensemble methodology: simple, documented, and intentionally not
"blindly averaging everything" — each model contributes equally
(1/3 weight) IF it is trained; if a model failed to train/load, its
weight is redistributed across the remaining trained models rather than
silently treating a missing model as 0. If ALL three models are
untrained, ensemble_probability is None and model_agreement is
"UNAVAILABLE" rather than fabricating a number.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ml.feature_engineering import build_risk_features
from app.ml.model_registry import all_models
from app.ml.risk.base import ModelNotTrainedError
from app.models.models import Asset


@dataclass
class RiskPredictionResult:
    asset_id: str
    deterministic_risk: float
    deterministic_risk_class: str
    ml_predictions: dict[str, dict]  # model_name -> {risk_probability, risk_level} or {"error": ...}
    ensemble_probability: float | None
    ensemble_risk_level: str | None
    model_agreement: str  # HIGH | MEDIUM | LOW | UNAVAILABLE
    dataset_label: str | None
    ml_status: str  # "available" | "partially_available" | "unavailable"


def _agreement_label(probs: list[float]) -> str:
    if len(probs) < 2:
        return "HIGH"  # nothing to disagree with
    spread = max(probs) - min(probs)
    if spread <= 0.10:
        return "HIGH"
    if spread <= 0.25:
        return "MEDIUM"
    return "LOW"


def predict_asset_risk(db: Session, asset: Asset, deterministic_risk: float, deterministic_risk_class: str) -> RiskPredictionResult:
    """Run every registered ML model against one asset's real,
    freshly-computed features. Never returns static/demo predictions —
    every number here comes from an actual model.predict() call."""
    features = build_risk_features(db, asset)

    ml_predictions: dict[str, dict] = {}
    trained_probs: list[float] = []
    dataset_label = None

    for name, model in all_models().items():
        try:
            result = model.predict(features)
            ml_predictions[name] = result
            trained_probs.append(result["risk_probability"])
            meta = model.metadata()
            if meta.get("dataset"):
                dataset_label = meta["dataset"]
        except ModelNotTrainedError:
            ml_predictions[name] = {"model": name, "error": "Model available but not trained"}
        except Exception as e:  # any other model-specific failure (Phase 37: never crash the endpoint)
            ml_predictions[name] = {"model": name, "error": f"Prediction failed: {e}"}

    if trained_probs:
        ensemble_probability = round(sum(trained_probs) / len(trained_probs), 4)
        ensemble_risk_level = _risk_level(ensemble_probability)
        agreement = _agreement_label(trained_probs)
        ml_status = "available" if len(trained_probs) == len(ml_predictions) else "partially_available"
    else:
        ensemble_probability = None
        ensemble_risk_level = None
        agreement = "UNAVAILABLE"
        ml_status = "unavailable"

    return RiskPredictionResult(
        asset_id=asset.id,
        deterministic_risk=deterministic_risk,
        deterministic_risk_class=deterministic_risk_class,
        ml_predictions=ml_predictions,
        ensemble_probability=ensemble_probability,
        ensemble_risk_level=ensemble_risk_level,
        model_agreement=agreement,
        dataset_label=dataset_label,
        ml_status=ml_status,
    )


def _risk_level(proba: float) -> str:
    if proba >= 0.75:
        return "CRITICAL"
    if proba >= 0.5:
        return "HIGH"
    if proba >= 0.25:
        return "MEDIUM"
    return "LOW"
