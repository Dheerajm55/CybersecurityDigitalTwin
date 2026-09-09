"""
Common evaluation for the supervised risk models (Phase 4.3).

All metrics here are computed from an actual held-out test split — never
hardcoded. `evaluate_classifier` is shared by XGBoost, LightGBM, and
Random Forest so their reported numbers are directly comparable (same
metrics, same split logic).
"""
from dataclasses import asdict, dataclass

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


@dataclass
class EvaluationResult:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    confusion_matrix: list[list[int]]
    n_train: int
    n_test: int

    def to_dict(self) -> dict:
        return asdict(self)


def stratified_split(X, y, test_size: float = 0.2, seed: int = 42):
    """Stratified train/test split with a fixed seed, so evaluation is
    reproducible across runs and consistent across all three models."""
    return train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)


def evaluate_classifier(y_true, y_pred, y_proba=None, n_train: int = 0) -> EvaluationResult:
    """Compute real classification metrics on true/predicted labels from
    an actual held-out test set. Never called with fabricated inputs."""
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_proba) if y_proba is not None else None
    except ValueError:
        # roc_auc_score raises if y_true has only one class in this split
        auc = None
    cm = confusion_matrix(y_true, y_pred).tolist()

    return EvaluationResult(
        accuracy=round(float(acc), 4),
        precision=round(float(prec), 4),
        recall=round(float(rec), 4),
        f1=round(float(f1), 4),
        roc_auc=round(float(auc), 4) if auc is not None else None,
        confusion_matrix=cm,
        n_train=n_train,
        n_test=len(y_true),
    )
