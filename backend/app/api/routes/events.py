from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.models import Asset, SecurityEvent

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
def list_events(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    events = db.query(SecurityEvent).order_by(SecurityEvent.created_at.desc()).limit(20).all()
    asset_names = {a.id: a.name for a in db.query(Asset).all()}
    return [
        {
            "id": e.id,
            "asset_id": e.asset_id,
            "asset_name": asset_names.get(e.asset_id, "—"),
            "event_type": e.event_type,
            "severity": str(e.severity.value if hasattr(e.severity, "value") else e.severity),
            "message": e.message,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
