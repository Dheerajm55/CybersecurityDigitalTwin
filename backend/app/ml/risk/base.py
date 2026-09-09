"""
Common interface for the three risk-prediction models (Phase 3.3 / 4).

XGBoost, LightGBM, and Random Forest are all scikit-learn-API compatible
classifiers, so this base class implements train/evaluate/save/load once
and each concrete model subclass only has to provide its estimator and a
name/artifact path. This is what "consistent interface... do not
duplicate unnecessary code" (Phase 4.1) means in practice.

Every model:
  - trains only when explicitly asked (train()), never implicitly on a
    request path (Phase 38 performance rule: training != inference)
  - persists to backend/models/<name>.joblib (Phase 4.4)
  - fails soft: if the artifact is missing/incompatible, predict()/
    predict_proba() raise a clear, typed error the API layer can catch
    and turn into "model not trained" rather than a 500 (Phase 37)
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np

from app.ml.evaluation import EvaluationResult, evaluate_classifier, stratified_split
from app.ml.feature_engineering import FEATURE_NAMES
from app.ml.synthetic_data import DATASET_LABEL, dataset_metadata, generate_synthetic_dataset

logger = logging.getLogger("cyber_twin.ml")

MODEL_DIR = Path(__file__).resolve().parents[3] / "models"  # backend/models/
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class ModelNotTrainedError(RuntimeError):
    """Raised by predict()/predict_proba() when no trained artifact
    exists yet. Callers (the risk prediction service / API routes) catch
    this specifically so one untrained/missing model degrades gracefully
    instead of crashing the whole risk endpoint (Phase 37)."""


class BaseRiskModel:
    name: str = "base"
    purpose: str = "risk_prediction"

    def __init__(self):
        self._estimator = None
        self._trained_at: str | None = None
        self._evaluation: EvaluationResult | None = None
        self._dataset_meta: dict | None = None
        self._feature_names: list[str] = FEATURE_NAMES

    # ---- subclasses provide this ----
    def _build_estimator(self):
        raise NotImplementedError

    # ---- shared behavior ----
    @property
    def artifact_path(self) -> Path:
        return MODEL_DIR / f"{self.name}.joblib"

    def is_trained(self) -> bool:
        return self._estimator is not None

    def train(self, n_samples: int = 2000, seed: int = 42) -> EvaluationResult:
        """Generate the synthetic dataset, fit the estimator on a
        stratified train split, and evaluate on the held-out test split.
        Returns the real EvaluationResult — never fabricated."""
        df = generate_synthetic_dataset(n_samples=n_samples, seed=seed)
        X = df[self._feature_names].values
        y = df["is_high_risk"].values

        X_train, X_test, y_train, y_test = stratified_split(X, y, seed=seed)

        estimator = self._build_estimator()
        estimator.fit(X_train, y_train)

        y_pred = estimator.predict(X_test)
        y_proba = estimator.predict_proba(X_test)[:, 1]
        result = evaluate_classifier(y_test, y_pred, y_proba, n_train=len(X_train))

        self._estimator = estimator
        self._evaluation = result
        self._dataset_meta = dataset_metadata(n_samples, seed)
        import datetime
        self._trained_at = datetime.datetime.utcnow().isoformat() + "Z"

        logger.info("%s trained: accuracy=%.3f f1=%.3f roc_auc=%s", self.name, result.accuracy, result.f1, result.roc_auc)
        return result

    def save(self) -> Path:
        if not self.is_trained():
            raise ModelNotTrainedError(f"{self.name} has not been trained yet; nothing to save.")
        payload = {
            "estimator": self._estimator,
            "trained_at": self._trained_at,
            "evaluation": self._evaluation.to_dict(),
            "dataset_meta": self._dataset_meta,
            "feature_names": self._feature_names,
        }
        joblib.dump(payload, self.artifact_path)
        return self.artifact_path

    def load(self) -> bool:
        """Returns True if a compatible artifact was loaded, False if no
        artifact exists yet. Never raises for a simply-missing file —
        only for a file that exists but is unreadable/incompatible,
        which is surfaced as a clear log warning and treated the same as
        'not trained' by callers."""
        if not self.artifact_path.exists():
            return False
        try:
            payload = joblib.load(self.artifact_path)
            if payload.get("feature_names") != self._feature_names:
                logger.warning(
                    "%s artifact feature schema mismatch (expected %s, got %s); "
                    "ignoring stale artifact — retrain required.",
                    self.name, self._feature_names, payload.get("feature_names"),
                )
                return False
            self._estimator = payload["estimator"]
            self._trained_at = payload.get("trained_at")
            eval_dict = payload.get("evaluation") or {}
            self._evaluation = EvaluationResult(**eval_dict) if eval_dict else None
            self._dataset_meta = payload.get("dataset_meta")
            return True
        except Exception as e:  # corrupt file, incompatible pickle, etc.
            logger.warning("%s artifact at %s could not be loaded (%s); treating as not trained.", self.name, self.artifact_path, e)
            return False

    def predict_proba(self, feature_row: dict[str, float]) -> float:
        if not self.is_trained():
            raise ModelNotTrainedError(f"{self.name} is not trained/loaded.")
        x = np.array([[feature_row[f] for f in self._feature_names]])
        return float(self._estimator.predict_proba(x)[0, 1])

    def predict(self, feature_row: dict[str, float]) -> dict:
        proba = self.predict_proba(feature_row)
        risk_level = self._risk_level(proba)
        return {"model": self.name, "risk_probability": round(proba, 4), "risk_level": risk_level}

    @staticmethod
    def _risk_level(proba: float) -> str:
        if proba >= 0.75:
            return "CRITICAL"
        if proba >= 0.5:
            return "HIGH"
        if proba >= 0.25:
            return "MEDIUM"
        return "LOW"

    def feature_importance(self) -> dict[str, float] | None:
        """Returns real per-feature importance if the underlying
        estimator exposes it, else None (not every model type does)."""
        if not self.is_trained():
            return None
        importances = getattr(self._estimator, "feature_importances_", None)
        if importances is None:
            return None
        total = float(sum(importances)) or 1.0
        return {
            name: round(float(val) / total, 4)
            for name, val in sorted(zip(self._feature_names, importances), key=lambda t: t[1], reverse=True)
        }

    def metadata(self) -> dict:
        return {
            "model_name": self.name,
            "model_type": type(self._estimator).__name__ if self._estimator else None,
            "purpose": self.purpose,
            "status": "trained" if self.is_trained() else "not_trained",
            "trained_at": self._trained_at,
            "dataset": self._dataset_meta.get("dataset") if self._dataset_meta else None,
            "input_features": self._feature_names,
            "output_type": "risk_probability (0-1) + risk_level (LOW/MEDIUM/HIGH/CRITICAL)",
            "evaluation": self._evaluation.to_dict() if self._evaluation else None,
        }
