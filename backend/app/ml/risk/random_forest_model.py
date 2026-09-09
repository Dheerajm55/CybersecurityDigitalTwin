"""Random Forest risk-prediction model (Phase 4.2).

Purpose: third ensemble member and, per Phase 4.2, the primary source of
real feature-importance values surfaced to the frontend ("Top Risk
Factors") — Random Forest's `feature_importances_` (mean decrease in
impurity across trees) is a stable, well-understood choice for this,
and is exposed unchanged via BaseRiskModel.feature_importance().
"""
from sklearn.ensemble import RandomForestClassifier

from app.ml.risk.base import BaseRiskModel


class RandomForestRiskModel(BaseRiskModel):
    name = "random_forest"
    purpose = "risk_prediction"

    def _build_estimator(self):
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=2,
        )
