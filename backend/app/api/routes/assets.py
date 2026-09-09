from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.models import Asset, AssetRelationship
from app.schemas.schemas import (
    AssetCreate,
    AssetOut,
    AssetRelationshipCreate,
    AssetRelationshipOut,
    AssetUpdate,
)
from app.services.risk_updater import recompute_asset

router = APIRouter(prefix="/api/assets", tags=["assets"])


@router.get("", response_model=list[AssetOut])
def list_assets(
    search: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    risk_class: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Asset)
    if search:
        q = q.filter(Asset.name.ilike(f"%{search}%"))
    if asset_type:
        q = q.filter(Asset.asset_type == asset_type)
    if criticality:
        q = q.filter(Asset.criticality == criticality)
    if risk_class:
        q = q.filter(Asset.risk_class == risk_class)
    return q.order_by(Asset.risk_score.desc()).all()


@router.post("", response_model=AssetOut, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.flush()
    recompute_asset(db, asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetOut)
def update_asset(asset_id: str, payload: AssetUpdate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    db.flush()
    recompute_asset(db, asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=204)
def delete_asset(asset_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.query(AssetRelationship).filter(
        (AssetRelationship.source_asset_id == asset_id) | (AssetRelationship.target_asset_id == asset_id)
    ).delete()
    db.delete(asset)
    db.commit()
    return None


@router.post("/relationships", response_model=AssetRelationshipOut, status_code=201)
def create_relationship(payload: AssetRelationshipCreate, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    for aid in (payload.source_asset_id, payload.target_asset_id):
        if not db.query(Asset).filter(Asset.id == aid).first():
            raise HTTPException(status_code=404, detail=f"Asset {aid} not found")
    rel = AssetRelationship(**payload.model_dump())
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


@router.delete("/relationships/{relationship_id}", status_code=204)
def delete_relationship(relationship_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    rel = db.query(AssetRelationship).filter(AssetRelationship.id == relationship_id).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    db.delete(rel)
    db.commit()
    return None
