"""
ML risk-prediction API (Phase 5.2).

Follows the same conventions as every other route module in this app:
FastAPI APIRouter, get_current_user auth dependency, get_db session
dependency, Pydantic response_models. Every endpoint here runs real
inference against real digital-twin data — no static/demo predictions.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.ml.inference import predict_asset_risk
from app.ml.model_registry import describe_all, get_model
from app.models.models import Asset, SecurityEvent, Vulnerability
from app.schemas.ml_schemas import (
    AssetRiskPredictionOut,
    FeatureImportanceOut,
    MLModelMeta,
    MLPredictionOut,
)
from app.services.risk_engine import compute_asset_risk

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.get("/models", response_model=list[MLModelMeta])
def list_models(_user=Depends(get_current_user)):
    """Real metadata for every registered model — status, when it was
    last trained, and its actual last-evaluation metrics (or None if it
    has never been trained). Nothing here is hardcoded."""
    return [MLModelMeta(**m) for m in describe_all()]


@router.get("/models/{model_name}", response_model=MLModelMeta)
def get_model_meta(model_name: str, _user=Depends(get_current_user)):
    try:
        model = get_model(model_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")
    return MLModelMeta(**model.metadata())


@router.get("/models/{model_name}/feature-importance", response_model=FeatureImportanceOut)
def get_feature_importance(model_name: str, _user=Depends(get_current_user)):
    """Real feature_importances_ from the trained estimator (Random
    Forest and XGBoost expose this; LightGBM does too). Returns None,
    not a fabricated distribution, if the model isn't trained."""
    try:
        model = get_model(model_name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")
    return FeatureImportanceOut(model=model_name, feature_importance=model.feature_importance())


@router.post("/risk/predict/{asset_id}", response_model=AssetRiskPredictionOut)
def predict_risk_for_asset(asset_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Run every registered ML model against ONE real asset's current
    digital-twin data, alongside the (unchanged, authoritative)
    deterministic risk engine score, per Phase 5.1's 'do not replace the
    deterministic engine' rule."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    vulns = db.query(Vulnerability).filter(Vulnerability.asset_id == asset_id).all()
    events = db.query(SecurityEvent).filter(SecurityEvent.asset_id == asset_id).all()
    det_score, det_class, _ = compute_asset_risk(asset, vulns, events)

    result = predict_asset_risk(db, asset, det_score, det_class)

    return AssetRiskPredictionOut(
        asset_id=result.asset_id,
        asset_name=asset.name,
        deterministic_risk=result.deterministic_risk,
        deterministic_risk_class=result.deterministic_risk_class,
        ml_predictions={k: MLPredictionOut(**v) for k, v in result.ml_predictions.items()},
        ensemble_probability=result.ensemble_probability,
        ensemble_risk_level=result.ensemble_risk_level,
        model_agreement=result.model_agreement,
        dataset_label=result.dataset_label,
        ml_status=result.ml_status,
    )


@router.get("/evaluation", response_model=list[MLModelMeta])
def get_evaluation(_user=Depends(get_current_user)):
    """Alias over /models focused on evaluation metrics — kept as a
    separate documented endpoint since Phase 5.2 explicitly calls for
    GET /api/ml/evaluation, even though the data is the same metadata
    payload as /models (no duplicate computation, just a named route for
    frontend/API clarity)."""
    return [MLModelMeta(**m) for m in describe_all()]
