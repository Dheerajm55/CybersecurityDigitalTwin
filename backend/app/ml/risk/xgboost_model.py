"""XGBoost risk-prediction model (Phase 4).

Purpose: predicts probability that an asset's environment represents
high cybersecurity risk, using the standardized feature set from
app/ml/feature_engineering.py. Gradient-boosted trees handle the
nonlinear interactions in the synthetic target (see
app/ml/synthetic_data.py's interaction term) well while staying fast
enough for local/CPU inference.
"""
from xgboost import XGBClassifier

from app.ml.risk.base import BaseRiskModel


class XGBoostRiskModel(BaseRiskModel):
    name = "xgboost"
    purpose = "risk_prediction"

    def _build_estimator(self):
        return XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
            n_jobs=2,
        )
