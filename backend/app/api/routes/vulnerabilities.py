from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.models import Asset, Vulnerability
from app.schemas.schemas import VulnerabilityCreate, VulnerabilityOut
from app.services.risk_updater import recompute_asset

router = APIRouter(prefix="/api/vulnerabilities", tags=["vulnerabilities"])


@router.get("", response_model=list[VulnerabilityOut])
def list_vulnerabilities(
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    known_exploited: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Vulnerability)
    if severity:
        q = q.filter(Vulnerability.severity == severity)
    if status:
        q = q.filter(Vulnerability.status == status)
    if known_exploited is not None:
        q = q.filter(Vulnerability.known_exploited == known_exploited)
    return q.order_by(Vulnerability.created_at.desc()).all()


@router.post("", response_model=VulnerabilityOut, status_code=201)
def create_vulnerability(payload: VulnerabilityCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    vuln = Vulnerability(**payload.model_dump())
    db.add(vuln)
    db.flush()
    recompute_asset(db, asset)
    db.commit()
    db.refresh(vuln)
    return vuln


@router.put("/{vulnerability_id}/status", response_model=VulnerabilityOut)
def update_status(vulnerability_id: str, status: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    vuln.status = status
    db.flush()
    asset = db.query(Asset).filter(Asset.id == vuln.asset_id).first()
    if asset:
        recompute_asset(db, asset)
    db.commit()
    db.refresh(vuln)
    return vuln
