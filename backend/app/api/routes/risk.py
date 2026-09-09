from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.models import Asset, SecurityEvent, Vulnerability
from app.schemas.schemas import (
    AssetRiskDetail,
    AttackPathOut,
    AttackPathRequest,
    DashboardSummary,
    RiskFactor as RiskFactorSchema,
    SimulationOut,
    SimulationRequest,
)
from app.services.graph_engine import all_critical_paths, find_riskiest_path
from app.services.risk_engine import compute_asset_risk, security_score_from_assets
from app.services.risk_updater import recent_active_events

router = APIRouter(prefix="/api", tags=["risk"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    assets = db.query(Asset).all()
    total = len(assets)
    high_risk = len([a for a in assets if a.risk_class in ("HIGH", "CRITICAL")])
    critical_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == "CRITICAL", Vulnerability.status == "open"
    ).count()
    paths = all_critical_paths(db, limit=50)

    distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for a in assets:
        distribution[a.risk_class] = distribution.get(a.risk_class, 0) + 1

    score = security_score_from_assets([a.risk_score for a in assets])

    active_threats = db.query(SecurityEvent).filter(
        SecurityEvent.status == "ACTIVE",
        SecurityEvent.severity.in_(["HIGH", "CRITICAL"]),
    ).count()

    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    events_last_minute = db.query(SecurityEvent).filter(SecurityEvent.created_at >= one_minute_ago).count()

    return DashboardSummary(
        total_assets=total,
        high_risk_assets=high_risk,
        critical_vulnerabilities=critical_vulns,
        attack_path_count=len(paths),
        security_score=score,
        risk_distribution=distribution,
        active_threats=active_threats,
        events_per_min=float(events_last_minute),
    )


@router.get("/risk/assets/{asset_id}", response_model=AssetRiskDetail)
def asset_risk_detail(asset_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    vulns = db.query(Vulnerability).filter(Vulnerability.asset_id == asset_id).all()
    events = recent_active_events(db, asset_id)
    score, risk_class, factors = compute_asset_risk(asset, vulns, events)
    return AssetRiskDetail(
        asset_id=asset.id,
        name=asset.name,
        risk_score=score,
        risk_class=risk_class,
        factors=[RiskFactorSchema(factor=f.factor, detail=f.detail, weight=f.weight) for f in factors],
    )


@router.get("/attack-paths", response_model=list[dict])
def critical_attack_paths(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return all_critical_paths(db, limit=10)


@router.post("/attack-paths/simulate", response_model=AttackPathOut)
def simulate_attack_path(payload: AttackPathRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    result = find_riskiest_path(db, payload.source_asset_id, payload.target_asset_id)
    if not result:
        raise HTTPException(status_code=404, detail="No reachable attack path found from this asset")
    return AttackPathOut(**result)


@router.post("/simulations/what-if", response_model=SimulationOut)
def what_if(payload: SimulationRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    vulns = db.query(Vulnerability).filter(Vulnerability.asset_id == asset.id).all()
    risk_before, _, _ = compute_asset_risk(asset, vulns)

    # Apply the hypothetical change to an in-memory copy only — nothing is persisted.
    explanation = ""
    if payload.action == "enable_mfa":
        asset.mfa_enabled = True
        explanation = "Simulated enabling multi-factor authentication on this asset."
    elif payload.action == "remove_excess_permissions":
        asset.permission_level = "standard"
        asset.permission_count = min(asset.permission_count, 8)
        explanation = "Simulated reducing permissions to least-privilege standard level."
    elif payload.action == "patch_vulnerability":
        for v in vulns:
            v.status = "patched"
        explanation = "Simulated patching all open vulnerabilities on this asset."
    elif payload.action == "disable_public_access":
        asset.internet_exposed = False
        explanation = "Simulated removing public internet exposure for this asset."
    else:
        raise HTTPException(status_code=400, detail=f"Unknown simulation action: {payload.action}")

    risk_after, _, _ = compute_asset_risk(asset, vulns)

    # Roll back the in-memory mutation so the simulation never persists.
    db.rollback()

    return SimulationOut(
        action=payload.action,
        asset_id=asset.id,
        risk_before=risk_before,
        risk_after=risk_after,
        risk_reduction=round(risk_before - risk_after, 1),
        explanation=explanation,
    )
