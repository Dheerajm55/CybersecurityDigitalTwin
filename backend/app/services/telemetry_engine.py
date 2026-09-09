"""
Telemetry / Security Event Engine.

Generates SYNTHETIC security events against the existing seeded assets so
the application behaves like a continuously monitored organization rather
than a static dashboard. This is explicitly simulated telemetry, not real
network/host monitoring — every event this module produces is labeled
with a `source_type`-equivalent origin and is clearly presented in the UI
as "SIMULATED ENVIRONMENT" (see frontend Dashboard).

This module does not perform any real action against any system. It only
inserts SecurityEvent rows into the application's own database and
recomputes the existing deterministic risk engine's output — the same
risk_engine.py used everywhere else in the app. Nothing here is machine
learning; event selection is weighted-random over a fixed, readable
template catalog, which keeps behavior explainable and reviewable.
"""
import random
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.models import Asset, Criticality, SecurityEvent
from app.services.risk_updater import recompute_asset


@dataclass(frozen=True)
class EventTemplate:
    event_type: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    risk_impact: float
    message: str
    source: str
    destination_is_self: bool = True  # if True, destination = the targeted asset's name


EVENT_TEMPLATES: list[EventTemplate] = [
    EventTemplate("AUTH_SUCCESS", "LOW", 0.0, "Successful authentication", "internal user"),
    EventTemplate("AUTH_FAILURE", "MEDIUM", 4.0, "Authentication failure detected", "unknown client"),
    EventTemplate("REPEATED_LOGIN_FAILURE", "HIGH", 14.0, "Multiple authentication failures detected", "unknown client"),
    EventTemplate("UNUSUAL_LOGIN_LOCATION", "MEDIUM", 8.0, "Login observed from an unusual location", "external network"),
    EventTemplate("PORT_SCAN_DETECTED", "MEDIUM", 6.0, "Port scan activity detected against this asset", "external network"),
    EventTemplate("SUSPICIOUS_OUTBOUND_TRAFFIC", "HIGH", 12.0, "Suspicious outbound traffic detected", "internal process"),
    EventTemplate("ABNORMAL_DNS_REQUEST", "MEDIUM", 5.0, "Abnormal DNS request pattern observed", "internal process"),
    EventTemplate("NEW_PROCESS_DETECTED", "LOW", 2.0, "New process observed on host", "endpoint agent"),
    EventTemplate("MALWARE_LIKE_BEHAVIOR", "CRITICAL", 20.0, "Behavior consistent with malware activity observed", "endpoint agent"),
    EventTemplate("PRIVILEGE_ESCALATION_SIMULATION", "CRITICAL", 18.0, "Simulated privilege escalation attempt observed", "internal process"),
    EventTemplate("VULNERABILITY_DETECTED", "HIGH", 10.0, "New vulnerability detected on asset", "vulnerability scanner"),
]

# Positive/recovery events reduce active risk rather than add to it — they
# mark prior events RESOLVED instead of inserting new active ones.
RECOVERY_EVENT_TYPES = {"SECURITY_CONTROL_ACTIVATED", "FIREWALL_BLOCK", "MFA_ENABLED", "ASSET_ISOLATED"}


def _weighted_asset_choice(assets: list[Asset]) -> Asset:
    """Weight selection toward assets that are already riskier, so the
    simulated environment tends to escalate existing hot spots rather than
    spreading attention uniformly at random — closer to how real telemetry
    clusters around already-weak points."""
    weights = [max(1.0, a.risk_score) for a in assets]
    return random.choices(assets, weights=weights, k=1)[0]


def generate_event(db: Session, asset: Asset | None = None) -> SecurityEvent | None:
    """Insert one simulated security event, tied to a real seeded asset,
    and recompute that asset's risk. Returns the created event, or None if
    there are no assets to generate telemetry against."""
    assets = db.query(Asset).all()
    if not assets:
        return None

    target = asset or _weighted_asset_choice(assets)
    template = random.choice(EVENT_TEMPLATES)

    event = SecurityEvent(
        id=str(uuid.uuid4()),
        asset_id=target.id,
        event_type=template.event_type,
        severity=Criticality(template.severity),
        message=template.message,
        status="ACTIVE",
        risk_impact=template.risk_impact,
        source=template.source,
        destination=target.name if template.destination_is_self else None,
    )
    db.add(event)
    db.flush()

    recompute_asset(db, target)
    db.commit()
    db.refresh(event)
    db.refresh(target)
    return event


def resolve_event(db: Session, event_id: str) -> SecurityEvent | None:
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        return None
    event.status = "RESOLVED"
    db.add(event)
    db.flush()
    if event.asset_id:
        asset = db.query(Asset).filter(Asset.id == event.asset_id).first()
        if asset:
            recompute_asset(db, asset)
    db.commit()
    db.refresh(event)
    return event


def simulate_attack_chain(db: Session, source_asset_id: str | None = None) -> list[SecurityEvent]:
    """Ties the live telemetry engine to the EXISTING deterministic
    attack-path engine (app/services/graph_engine.py) rather than
    duplicating attack logic: finds a real riskiest path from a source
    asset (or the highest-risk asset if none given), and emits one
    escalating CRITICAL-severity event per hop along that path, so the
    Digital Twin and event feed visibly reflect a simulated compromise
    spreading exactly along a path the app's own attack-path engine
    identified — not an arbitrary/random set of assets."""
    from app.services.graph_engine import find_riskiest_path  # local import avoids a circular import at module load

    assets = db.query(Asset).all()
    if not assets:
        return []

    source = None
    if source_asset_id:
        source = db.query(Asset).filter(Asset.id == source_asset_id).first()
    if not source:
        source = max(assets, key=lambda a: a.risk_score)

    result = find_riskiest_path(db, source.id)
    if not result:
        # No reachable path from this source — fall back to a single event on it.
        event = generate_event(db, source)
        return [event] if event else []

    created: list[SecurityEvent] = []
    for i, step in enumerate(result["path"]):
        asset = db.query(Asset).filter(Asset.id == step["asset_id"]).first()
        if not asset:
            continue
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            asset_id=asset.id,
            event_type="ATTACK_SIMULATION_COMPROMISE",
            severity=Criticality.CRITICAL if i > 0 else Criticality.HIGH,
            message=f"Simulated attack compromise — hop {i + 1} of {len(result['path'])} along a "
                    f"{result['risk_class']} risk path",
            status="ACTIVE",
            risk_impact=15.0 if i > 0 else 8.0,
            source="attack simulation" if i == 0 else result["path"][i - 1]["name"],
            destination=asset.name,
        )
        db.add(event)
        db.flush()
        recompute_asset(db, asset)
        created.append(event)

    db.commit()
    for e in created:
        db.refresh(e)
    return created


def reset_environment(db: Session) -> int:
    """Resolve every currently-ACTIVE event and recompute risk for every
    asset, restoring the environment to its baseline (pre-live-telemetry)
    state. Returns the number of events resolved. Seeded vulnerabilities
    and assets are untouched — only live telemetry state is reset."""
    active_events = db.query(SecurityEvent).filter(SecurityEvent.status == "ACTIVE").all()
    count = len(active_events)
    for e in active_events:
        e.status = "RESOLVED"
        db.add(e)
    db.commit()

    for asset in db.query(Asset).all():
        recompute_asset(db, asset)
    db.commit()
    return count
