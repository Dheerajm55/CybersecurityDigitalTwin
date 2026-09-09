"""
Model registry (Phase 3.3 / 20).

Tracks the set of ML models the application knows about and gives a
single place to fetch a live instance and its metadata. Only the three
Phase 4 models are registered here; Isolation Forest, Autoencoder, the
GNNs, and the NLP models are intentionally NOT added yet (Phase 6+).

No evaluation metrics are hardcoded here — `describe_all()` always calls
into each model's own `metadata()`, which reports real numbers from the
last training run (or "not_trained" if none has happened yet).
"""
from functools import lru_cache

from app.ml.risk.base import BaseRiskModel
from app.ml.risk.lightgbm_model import LightGBMRiskModel
from app.ml.risk.random_forest_model import RandomForestRiskModel
from app.ml.risk.xgboost_model import XGBoostRiskModel

_MODEL_CLASSES: dict[str, type[BaseRiskModel]] = {
    "xgboost": XGBoostRiskModel,
    "lightgbm": LightGBMRiskModel,
    "random_forest": RandomForestRiskModel,
}


@lru_cache(maxsize=1)
def _instances() -> dict[str, BaseRiskModel]:
    """One process-wide instance per model, created once and reused —
    per Phase 38, we don't want to reconstruct/reload a model from disk
    on every request. Each instance attempts to load its saved artifact
    immediately; if none exists yet, it simply stays untrained until
    someone calls train()."""
    instances = {}
    for key, cls in _MODEL_CLASSES.items():
        model = cls()
        model.load()
        instances[key] = model
    return instances


def get_model(name: str) -> BaseRiskModel:
    instances = _instances()
    if name not in instances:
        raise KeyError(f"Unknown model: {name}. Registered models: {list(instances.keys())}")
    return instances[name]


def model_classes() -> dict[str, type[BaseRiskModel]]:
    """Exposed for the training script, which needs to construct fresh,
    untrained instances (not the shared cached singletons above)."""
    return dict(_MODEL_CLASSES)


def all_models() -> dict[str, BaseRiskModel]:
    return _instances()


def reload_all() -> None:
    """Force every registered model to re-read its artifact from disk
    (e.g. after a training run in a different process)."""
    for model in _instances().values():
        model.load()


def describe_all() -> list[dict]:
    return [model.metadata() for model in _instances().values()]
