"""
Standardized feature representation for the ML risk models (Phase 3.1).

Every feature here is computed from data that actually exists in the
CDT2 database — Asset, Vulnerability, SecurityControl, SecurityEvent,
and AssetRelationship (via the existing graph_engine). No field is
invented. Two features from the master spec's suggested list
(`firewall_enabled`, `monitoring_enabled`) are intentionally NOT
included: the current schema has no per-asset firewall/monitoring flag
and no "Firewall"/"Monitoring" SecurityControl category in the seeded
data, and Phase 3.2 forbids inventing database fields to backfill them.
`network_segmentation` is included, but as an org-wide signal (the
"Network Segmentation" control's implementation state), since
segmentation is recorded at the control level, not per asset, in the
current model. `anomaly_count` is intentionally NOT included yet — it
is produced by Isolation Forest, which is out of scope until Phase 6;
`active_security_events` is used as the nearest real substitute
available today.

    Digital Twin (Asset, Vulnerability, SecurityControl, SecurityEvent,
                  AssetRelationship)
                    |
                    v
       build_environment_features(db)      (org-wide, computed once)
                    |
                    v
       build_asset_features(db, asset)      (per-asset)
                    |
                    v
       build_risk_features(db, asset)       (asset + environment, flat
                                              dict -> ordered vector)
                    |
                    v
              ML models (XGBoost / LightGBM / Random Forest)
"""
from dataclasses import dataclass, fields

from sqlalchemy.orm import Session

from app.models.models import (
    Asset,
    Criticality,
    SecurityControl,
    SecurityEvent,
    Vulnerability,
)
from app.services.graph_engine import weighted_graph
import networkx as nx

CRITICALITY_ORDINAL = {
    Criticality.LOW: 1,
    Criticality.MEDIUM: 2,
    Criticality.HIGH: 3,
    Criticality.CRITICAL: 4,
}

PERMISSION_LEVEL_ORDINAL = {
    "read-only": 0,
    "standard": 1,
    "write": 2,
    "admin": 3,
}

CONTROL_STATE_SCORE = {
    "not_implemented": 0.0,
    "partial": 0.5,
    "implemented": 1.0,
}


def _crit_of(value) -> Criticality:
    if isinstance(value, Criticality):
        return value
    try:
        return Criticality(value)
    except Exception:
        return Criticality.MEDIUM


@dataclass
class EnvironmentFeatures:
    """Org-wide features, computed once per request/training run and
    reused for every asset (segmentation and control maturity are
    recorded at the control level in this schema, not per-asset)."""

    network_segmentation: float  # 0 / 0.5 / 1, from the "Network Segmentation" control's current_state
    org_control_maturity: float  # mean implementation state across all recorded controls, 0-1


@dataclass
class AssetFeatures:
    """Per-asset features, all derived from real, queryable columns."""

    asset_criticality: int  # 1-4 ordinal
    internet_exposed: int  # 0/1
    mfa_enabled: int  # 0/1
    permission_level_score: int  # 0-3 ordinal
    permission_count: int
    vulnerability_count: int  # open vulnerabilities
    critical_vulnerability_count: int  # open + CRITICAL severity
    known_exploited: int  # 0/1 — any open vuln flagged CISA KEV
    avg_cvss_score: float  # mean CVSS of open vulns, 0 if none
    attack_path_length: int  # hops from nearest entry point (in-degree 0 node)
    attack_path_cost: float  # cumulative Dijkstra cost from nearest entry point
    historical_security_events: int  # total SecurityEvent rows ever logged for this asset
    active_security_events: int  # currently ACTIVE SecurityEvent rows for this asset


FEATURE_NAMES: list[str] = (
    [f.name for f in fields(AssetFeatures)] + [f.name for f in fields(EnvironmentFeatures)]
)


def build_environment_features(db: Session) -> EnvironmentFeatures:
    controls = db.query(SecurityControl).all()
    if not controls:
        return EnvironmentFeatures(network_segmentation=0.0, org_control_maturity=0.0)

    seg_controls = [c for c in controls if c.category == "Network" and "segmentation" in c.name.lower()]
    segmentation = (
        max(CONTROL_STATE_SCORE.get(c.current_state, 0.0) for c in seg_controls)
        if seg_controls else 0.0
    )
    maturity = sum(CONTROL_STATE_SCORE.get(c.current_state, 0.0) for c in controls) / len(controls)
    return EnvironmentFeatures(network_segmentation=segmentation, org_control_maturity=round(maturity, 3))


def _attack_path_length_and_cost(asset_id: str, g: nx.DiGraph) -> tuple[int, float]:
    if asset_id not in g.nodes:
        return 0, 0.0
    entry_points = [n for n in g.nodes if g.in_degree(n) == 0]
    if not entry_points or asset_id in entry_points:
        return 0, 0.0

    best_len, best_cost = None, None
    for src in entry_points:
        if src == asset_id or not nx.has_path(g, src, asset_id):
            continue
        try:
            path = nx.dijkstra_path(g, src, asset_id, weight="cost")
            cost = nx.dijkstra_path_length(g, src, asset_id, weight="cost")
        except nx.NetworkXNoPath:
            continue
        length = len(path) - 1
        if best_len is None or cost < best_cost:
            best_len, best_cost = length, cost
    if best_len is None:
        return 0, 0.0
    return best_len, round(best_cost, 2)


def build_asset_features(
    db: Session,
    asset: Asset,
    vulnerabilities: list[Vulnerability] | None = None,
    events: list[SecurityEvent] | None = None,
    graph: nx.DiGraph | None = None,
) -> AssetFeatures:
    """Build the per-asset feature set. Accepts pre-fetched
    vulnerabilities/events/graph so callers building features for many
    assets at once (training, batch inference) don't re-query per asset."""
    if vulnerabilities is None:
        vulnerabilities = db.query(Vulnerability).filter(Vulnerability.asset_id == asset.id).all()
    if events is None:
        events = db.query(SecurityEvent).filter(SecurityEvent.asset_id == asset.id).all()
    if graph is None:
        graph = weighted_graph(db)

    open_vulns = [v for v in vulnerabilities if v.status == "open"]
    critical_open = [v for v in open_vulns if _crit_of(v.severity) == Criticality.CRITICAL]
    known_exploited = any(v.known_exploited for v in open_vulns)
    cvss_values = [v.cvss_score for v in open_vulns if v.cvss_score is not None]
    avg_cvss = round(sum(cvss_values) / len(cvss_values), 2) if cvss_values else 0.0

    path_length, path_cost = _attack_path_length_and_cost(asset.id, graph)

    active_events = [e for e in events if (e.status or "ACTIVE") == "ACTIVE"]

    return AssetFeatures(
        asset_criticality=CRITICALITY_ORDINAL[_crit_of(asset.criticality)],
        internet_exposed=int(bool(asset.internet_exposed)),
        mfa_enabled=int(bool(asset.mfa_enabled)),
        permission_level_score=PERMISSION_LEVEL_ORDINAL.get(asset.permission_level, 1),
        permission_count=asset.permission_count or 0,
        vulnerability_count=len(open_vulns),
        critical_vulnerability_count=len(critical_open),
        known_exploited=int(known_exploited),
        avg_cvss_score=avg_cvss,
        attack_path_length=path_length,
        attack_path_cost=path_cost,
        historical_security_events=len(events),
        active_security_events=len(active_events),
    )


def build_risk_features(db: Session, asset: Asset) -> dict[str, float]:
    """Convenience wrapper: full flat feature dict (asset + environment)
    for one asset, in FEATURE_NAMES order. Used by the online inference
    path (app/ml/inference.py) where only one asset is being scored."""
    env = build_environment_features(db)
    af = build_asset_features(db, asset)
    return _flatten(af, env)


def _flatten(af: AssetFeatures, env: EnvironmentFeatures) -> dict[str, float]:
    d = {**af.__dict__, **env.__dict__}
    return {name: d[name] for name in FEATURE_NAMES}


def build_feature_matrix(db: Session) -> tuple[list[str], list[dict[str, float]]]:
    """Build features for every asset currently in the digital twin, for
    batch inference (e.g. the AI Model Observatory / dashboard). Returns
    (asset_ids, feature_dicts) in the same order."""
    assets = db.query(Asset).all()
    vulns_by_asset: dict[str, list[Vulnerability]] = {}
    for v in db.query(Vulnerability).all():
        vulns_by_asset.setdefault(v.asset_id, []).append(v)
    events_by_asset: dict[str, list[SecurityEvent]] = {}
    for e in db.query(SecurityEvent).all():
        events_by_asset.setdefault(e.asset_id, []).append(e)

    env = build_environment_features(db)
    graph = weighted_graph(db)

    asset_ids, rows = [], []
    for a in assets:
        af = build_asset_features(
            db, a,
            vulnerabilities=vulns_by_asset.get(a.id, []),
            events=events_by_asset.get(a.id, []),
            graph=graph,
        )
        asset_ids.append(a.id)
        rows.append(_flatten(af, env))
    return asset_ids, rows
