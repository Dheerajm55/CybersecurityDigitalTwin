"""LightGBM risk-prediction model (Phase 4.1).

Purpose: an independent second gradient-boosting model on the same
standardized feature set as XGBoost, used for ensemble comparison in
the risk prediction service (Phase 5) — different boosting strategy
(leaf-wise vs level-wise growth) gives a genuinely different, not
duplicate, second opinion.
"""
from lightgbm import LGBMClassifier

from app.ml.risk.base import BaseRiskModel


class LightGBMRiskModel(BaseRiskModel):
    name = "lightgbm"
    purpose = "risk_prediction"

    def _build_estimator(self):
        return LGBMClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=2,
            verbosity=-1,
            min_child_samples=10,
        )
