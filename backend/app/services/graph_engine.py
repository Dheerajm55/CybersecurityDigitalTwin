"""
Deterministic attack-path analysis using NetworkX.

This is a MATHEMATICAL SIMULATION over the digital twin graph. It never
performs real network requests, exploitation, credential use, or any
action against real systems — it only reasons over asset/relationship
records already stored in the application database (synthetic, imported,
or explicitly entered by the user).

Edge weight = traversal cost. Lower weight = easier for an attacker to
move across that relationship. We derive weight from the target asset's
security posture (MFA, exposure, permissions) so that "weakest path"
falls out of Dijkstra's algorithm naturally, then convert path cost into
a 0-100 risk score for display.
"""
import networkx as nx
from sqlalchemy.orm import Session

from app.models.models import Asset, AssetRelationship, Vulnerability
from app.services.risk_engine import compute_asset_risk


def build_graph(db: Session) -> nx.DiGraph:
    g = nx.DiGraph()
    assets = db.query(Asset).all()
    for a in assets:
        g.add_node(a.id, asset=a)

    edges = db.query(AssetRelationship).all()
    for e in edges:
        if e.source_asset_id in g.nodes and e.target_asset_id in g.nodes:
            g.add_edge(e.source_asset_id, e.target_asset_id, weight=e.weight, rel_type=e.relationship_type)
    return g


def _traversal_cost(asset: Asset, vulns: list[Vulnerability]) -> float:
    """Lower cost = easier next hop for an attacker. Base cost 10,
    reduced by weak controls, so a weakly-defended asset is 'cheaper'
    to move through."""
    cost = 10.0
    if not asset.mfa_enabled:
        cost -= 3
    if asset.internet_exposed:
        cost -= 2
    if asset.permission_level in ("write", "admin"):
        cost -= 2
    open_critical = [v for v in vulns if v.status == "open" and str(v.severity) in ("Criticality.CRITICAL", "CRITICAL")]
    if open_critical:
        cost -= 3
    return max(1.0, cost)


def weighted_graph(db: Session) -> nx.DiGraph:
    g = build_graph(db)
    vulns_by_asset: dict[str, list[Vulnerability]] = {}
    for v in db.query(Vulnerability).all():
        vulns_by_asset.setdefault(v.asset_id, []).append(v)

    for u, v, data in g.edges(data=True):
        target_asset: Asset = g.nodes[v]["asset"]
        cost = _traversal_cost(target_asset, vulns_by_asset.get(v, []))
        data["cost"] = cost
    return g


def find_riskiest_path(db: Session, source_id: str, target_id: str | None = None):
    """Find the attack path from source_id that reaches either the given
    target_id, or (if none given) the highest-risk asset reachable from
    source_id. Uses Dijkstra shortest-cost path as the deterministic
    baseline algorithm (Section 9 of the spec)."""
    g = weighted_graph(db)
    if source_id not in g.nodes:
        return None

    if target_id:
        if target_id not in g.nodes or not nx.has_path(g, source_id, target_id):
            return None
        node_path = nx.dijkstra_path(g, source_id, target_id, weight="cost")
    else:
        reachable = nx.descendants(g, source_id)
        if not reachable:
            return None
        # riskiest reachable target = highest stored risk_score
        best_target = max(reachable, key=lambda n: g.nodes[n]["asset"].risk_score)
        node_path = nx.dijkstra_path(g, source_id, best_target, weight="cost")

    return score_path(db, g, node_path)


def score_path(db: Session, g: nx.DiGraph, node_path: list[str]):
    explanation: list[str] = []
    total = 0.0
    steps = []

    for i, node_id in enumerate(node_path):
        asset: Asset = g.nodes[node_id]["asset"]
        steps.append({"asset_id": asset.id, "name": asset.name, "asset_type": str(asset.asset_type).replace("AssetType.", "")})
        total += asset.risk_score
        if not asset.mfa_enabled:
            explanation.append(f"{asset.name}: MFA disabled")
        if asset.internet_exposed:
            explanation.append(f"{asset.name}: internet exposed")
        if asset.permission_level in ("write", "admin"):
            explanation.append(f"{asset.name}: elevated permissions ({asset.permission_level})")

    avg = total / len(node_path)
    length_penalty = max(0, (4 - len(node_path))) * 3  # shorter paths are more dangerous
    risk_score = min(100.0, round(avg + length_penalty, 1))

    from app.services.risk_engine import classify
    risk_class = classify(risk_score)

    if not explanation:
        explanation.append("Path exists but no single high-risk control gap dominates; risk driven by cumulative asset criticality.")

    return {
        "path": steps,
        "risk_score": risk_score,
        "risk_class": risk_class,
        "explanation": explanation,
    }


def all_critical_paths(db: Session, limit: int = 10):
    """Enumerate attack paths from every entry-point-like asset (accounts
    with no incoming edges) to every high-value asset (databases, cloud,
    storage), ranked by risk score, for the dashboard's 'Critical Attack
    Paths' widget."""
    g = weighted_graph(db)
    entry_points = [n for n in g.nodes if g.in_degree(n) == 0]
    high_value = [
        n for n in g.nodes
        if str(g.nodes[n]["asset"].asset_type) in (
            "AssetType.DATABASE", "DATABASE",
            "AssetType.CLOUD_ACCOUNT", "CLOUD_ACCOUNT",
            "AssetType.STORAGE_BUCKET", "STORAGE_BUCKET",
        )
    ]

    results = []
    for src in entry_points:
        for tgt in high_value:
            if src == tgt or not nx.has_path(g, src, tgt):
                continue
            node_path = nx.dijkstra_path(g, src, tgt, weight="cost")
            results.append(score_path(db, g, node_path))

    results.sort(key=lambda r: r["risk_score"], reverse=True)
    return results[:limit]
