from sqlalchemy.orm import Session

from app.models.models import Asset, SecurityEvent, Vulnerability
from app.services.risk_engine import compute_asset_risk


def recent_active_events(db: Session, asset_id: str, limit: int = 20) -> list[SecurityEvent]:
    return (
        db.query(SecurityEvent)
        .filter(SecurityEvent.asset_id == asset_id, SecurityEvent.status == "ACTIVE")
        .order_by(SecurityEvent.created_at.desc())
        .limit(limit)
        .all()
    )


def recompute_asset(db: Session, asset: Asset) -> Asset:
    vulns = db.query(Vulnerability).filter(Vulnerability.asset_id == asset.id).all()
    events = recent_active_events(db, asset.id)
    score, risk_class, _factors = compute_asset_risk(asset, vulns, events)
    asset.risk_score = score
    asset.risk_class = risk_class
    db.add(asset)
    return asset


def recompute_all(db: Session) -> None:
    assets = db.query(Asset).all()
    vulns_by_asset: dict[str, list[Vulnerability]] = {}
    for v in db.query(Vulnerability).all():
        vulns_by_asset.setdefault(v.asset_id, []).append(v)

    events_by_asset: dict[str, list[SecurityEvent]] = {}
    for e in db.query(SecurityEvent).filter(SecurityEvent.status == "ACTIVE").all():
        if e.asset_id:
            events_by_asset.setdefault(e.asset_id, []).append(e)

    for asset in assets:
        score, risk_class, _factors = compute_asset_risk(
            asset, vulns_by_asset.get(asset.id, []), events_by_asset.get(asset.id, [])
        )
        asset.risk_score = score
        asset.risk_class = risk_class
        db.add(asset)
    db.commit()
