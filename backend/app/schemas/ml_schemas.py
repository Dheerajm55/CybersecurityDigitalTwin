from pydantic import BaseModel, ConfigDict


class MLModelMeta(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_type: str | None
    purpose: str
    status: str  # "trained" | "not_trained"
    trained_at: str | None
    dataset: str | None
    input_features: list[str]
    output_type: str
    evaluation: dict | None


class MLPredictionOut(BaseModel):
    model: str
    risk_probability: float | None = None
    risk_level: str | None = None
    error: str | None = None


class AssetRiskPredictionOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    asset_id: str
    asset_name: str
    deterministic_risk: float
    deterministic_risk_class: str
    ml_predictions: dict[str, MLPredictionOut]
    ensemble_probability: float | None
    ensemble_risk_level: str | None
    model_agreement: str  # HIGH | MEDIUM | LOW | UNAVAILABLE
    dataset_label: str | None
    ml_status: str  # available | partially_available | unavailable


class FeatureImportanceOut(BaseModel):
    model: str
    feature_importance: dict[str, float] | None
