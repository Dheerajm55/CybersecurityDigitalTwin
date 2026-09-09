from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.models import Asset, AssetRelationship
from app.schemas.schemas import DigitalTwinGraph, GraphEdge, GraphNode

router = APIRouter(prefix="/api/twin", tags=["digital-twin"])


@router.get("", response_model=DigitalTwinGraph)
def get_digital_twin(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    assets = db.query(Asset).all()
    relationships = db.query(AssetRelationship).all()

    nodes = [
        GraphNode(
            id=a.id,
            label=a.name,
            type=str(a.asset_type.value if hasattr(a.asset_type, "value") else a.asset_type),
            criticality=str(a.criticality.value if hasattr(a.criticality, "value") else a.criticality),
            risk_score=a.risk_score,
            risk_class=a.risk_class,
            mfa_enabled=a.mfa_enabled,
            internet_exposed=a.internet_exposed,
        )
        for a in assets
    ]

    edges = [
        GraphEdge(
            id=r.id,
            source=r.source_asset_id,
            target=r.target_asset_id,
            relationship_type=str(r.relationship_type.value if hasattr(r.relationship_type, "value") else r.relationship_type),
            weight=r.weight,
        )
        for r in relationships
    ]

    return DigitalTwinGraph(nodes=nodes, edges=edges)
