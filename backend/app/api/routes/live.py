"""
Live telemetry: WebSocket stream + simulation controls.

    Backend
       |
       | WebSocket
       v
    React Frontend

Message types broadcast over the WebSocket (see connection_manager.py):
  - security_event   : a newly generated or resolved SecurityEvent
  - risk_update       : an asset's risk score changed, with old/new + reason
  - attack_simulation : a batch marker wrapping a sequence of security_event/
                         risk_update messages produced by one "Simulate Attack" run
  - environment_reset : the live environment was restored to baseline

This module never performs a real action against any system — see the
module docstring in app/services/telemetry_engine.py for the safety
guarantee that applies to everything generated here.
"""
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import decode_access_token
from app.database.session import SessionLocal, get_db
from app.models.models import Asset, SecurityEvent, User
from app.services.connection_manager import manager
from app.services.live_state import live_state
from app.services.telemetry_engine import generate_event, reset_environment, resolve_event, simulate_attack_chain

logger = logging.getLogger("cyber_twin.live")

router = APIRouter(prefix="/api/live", tags=["live"])


def _event_message(event: SecurityEvent, asset_name: str, msg_type: str = "security_event") -> dict:
    return {
        "type": msg_type,
        "event": {
            "event_id": event.id,
            "timestamp": event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
            "asset_id": event.asset_id,
            "asset_name": asset_name,
            "event_type": event.event_type,
            "severity": str(event.severity.value if hasattr(event.severity, "value") else event.severity),
            "description": event.message,
            "source": event.source,
            "destination": event.destination,
            "risk_impact": event.risk_impact,
            "status": event.status,
        },
    }


def _risk_update_message(asset: Asset, old_risk: float, reason: str) -> dict:
    return {
        "type": "risk_update",
        "asset_id": asset.id,
        "asset_name": asset.name,
        "old_risk": old_risk,
        "new_risk": asset.risk_score,
        "risk_class": asset.risk_class,
        "reason": reason,
    }


# ---------- WebSocket stream ----------

@router.websocket("/ws")
async def live_ws(websocket: WebSocket, token: str | None = None):
    if token:
        try:
            decode_access_token(token)
        except Exception:
            await websocket.close(code=1008)  # policy violation
            return
    else:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "connected", "paused": live_state.paused})
        while True:
            # This endpoint is broadcast-only from the server's perspective;
            # we still need to await incoming messages so FastAPI notices a
            # client disconnect rather than leaking the connection.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Live WebSocket connection error")
    finally:
        await manager.disconnect(websocket)


# ---------- REST simulation controls ----------

@router.get("/status")
def live_status(_user: User = Depends(get_current_user)):
    return {
        "paused": live_state.paused,
        "interval_seconds": live_state.interval_seconds,
        "connected_clients": manager.active_count,
    }


@router.post("/pause")
async def pause_live(_user: User = Depends(get_current_user)):
    live_state.paused = True
    await manager.broadcast({"type": "simulation_status", "paused": True})
    return {"paused": True}


@router.post("/resume")
async def resume_live(_user: User = Depends(get_current_user)):
    live_state.paused = False
    await manager.broadcast({"type": "simulation_status", "paused": False})
    return {"paused": False}


@router.post("/generate-event")
async def generate_event_now(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    asset_before_risk: dict[str, float] = {a.id: a.risk_score for a in db.query(Asset).all()}
    event = generate_event(db)
    if not event:
        raise HTTPException(status_code=400, detail="No assets exist to generate telemetry against")

    asset = db.query(Asset).filter(Asset.id == event.asset_id).first()
    old_risk = asset_before_risk.get(asset.id, asset.risk_score)

    await manager.broadcast(_event_message(event, asset.name))
    if asset.risk_score != old_risk:
        await manager.broadcast(_risk_update_message(asset, old_risk, event.message))

    return {"event_id": event.id, "asset_id": asset.id, "message": event.message}


@router.post("/simulate-attack")
async def simulate_attack_now(
    source_asset_id: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    all_assets = {a.id: a for a in db.query(Asset).all()}
    before_risk = {aid: a.risk_score for aid, a in all_assets.items()}

    events = simulate_attack_chain(db, source_asset_id)
    if not events:
        raise HTTPException(status_code=400, detail="No reachable attack path could be simulated from this asset")

    await manager.broadcast({"type": "attack_simulation", "hop_count": len(events)})
    for event in events:
        asset = db.query(Asset).filter(Asset.id == event.asset_id).first()
        if not asset:
            continue
        await manager.broadcast(_event_message(event, asset.name))
        old = before_risk.get(asset.id, asset.risk_score)
        if asset.risk_score != old:
            await manager.broadcast(_risk_update_message(asset, old, event.message))
        await asyncio.sleep(0.4)  # small stagger so the frontend can animate hop-by-hop

    return {"hops": len(events)}


@router.post("/reset")
async def reset_environment_now(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    resolved_count = reset_environment(db)
    await manager.broadcast({"type": "environment_reset", "resolved_events": resolved_count})
    return {"resolved_events": resolved_count}


@router.post("/events/{event_id}/resolve")
async def resolve_event_now(event_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    event = resolve_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    asset = db.query(Asset).filter(Asset.id == event.asset_id).first()
    if asset:
        await manager.broadcast(_event_message(event, asset.name))
    return {"event_id": event.id, "status": event.status}


# ---------- Background telemetry loop ----------

async def telemetry_loop() -> None:
    """Runs for the lifetime of the process, generating one simulated event
    on each tick unless paused. Started from main.py's startup handler."""
    while True:
        try:
            await asyncio.sleep(live_state.interval_seconds)
            if live_state.paused or manager.active_count == 0:
                continue

            db = SessionLocal()
            try:
                before = {a.id: a.risk_score for a in db.query(Asset).all()}
                event = generate_event(db)
                if not event:
                    continue
                asset = db.query(Asset).filter(Asset.id == event.asset_id).first()
                if not asset:
                    continue
                await manager.broadcast(_event_message(event, asset.name))
                old = before.get(asset.id, asset.risk_score)
                if asset.risk_score != old:
                    await manager.broadcast(_risk_update_message(asset, old, event.message))
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Telemetry loop tick failed")
