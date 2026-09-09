from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.models import SecurityControl

router = APIRouter(prefix="/api/controls", tags=["controls"])


@router.get("")
def list_controls(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    controls = db.query(SecurityControl).order_by(SecurityControl.risk_reduction_estimate.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "category": c.category,
            "current_state": c.current_state,
            "risk_reduction_estimate": c.risk_reduction_estimate,
            "priority": c.priority,
            "affected_asset_count": len((c.affected_asset_ids or "").split(",")) if c.affected_asset_ids else 0,
        }
        for c in controls
    ]
