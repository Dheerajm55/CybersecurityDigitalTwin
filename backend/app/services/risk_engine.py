"""
Deterministic "Project Risk Score" engine.

This is intentionally NOT machine learning — it is a transparent, rule
based baseline that the application never depends on AI to produce, per
the project's reliability requirement (Section 14 / 40 of the spec):
"The system should never depend entirely on AI."

Score is 0-100. Higher = riskier. Weights are configurable constants
below rather than hidden magic numbers, and every score comes with a
human-readable list of contributing factors so it can be explained in
the UI ("Why is this asset high risk?").

Later phases may blend this with an ML-predicted probability (XGBoost)
and a graph-derived score (GraphSAGE) into a combined posture score —
see Section 14 of the master spec. That blending step is not yet wired
up; only the deterministic component is implemented in this build.
"""
from dataclasses import dataclass

from app.models.models import Asset, Criticality, SecurityEvent, Vulnerability

CRITICALITY_WEIGHT = {
    Criticality.LOW: 5,
    Criticality.MEDIUM: 15,
    Criticality.HIGH: 25,
    Criticality.CRITICAL: 35,
}

SEVERITY_WEIGHT = {
    Criticality.LOW: 3,
    Criticality.MEDIUM: 8,
    Criticality.HIGH: 15,
    Criticality.CRITICAL: 22,
}

MAX_SCORE = 100.0
MAX_EVENT_CONTRIBUTION = 25.0  # cap so a burst of live events can't alone blow the score to 100


@dataclass
class RiskFactor:
    factor: str
    detail: str
    weight: float


def _crit_of(value) -> Criticality:
    if isinstance(value, Criticality):
        return value
    try:
        return Criticality(value)
    except Exception:
        return Criticality.MEDIUM


def compute_asset_risk(
    asset: Asset,
    vulnerabilities: list[Vulnerability],
    recent_events: list[SecurityEvent] | None = None,
) -> tuple[float, str, list[RiskFactor]]:
    """Compute a 0-100 project risk score for a single asset plus an
    ordered, explainable list of contributing factors.

    `recent_events` is optional and backward compatible: existing callers
    that only pass (asset, vulnerabilities) are unaffected. When provided
    (by the live telemetry engine — see app/services/telemetry_engine.py),
    unresolved ACTIVE security events contribute to the score too, so risk
    visibly moves as events occur rather than only when an asset's static
    fields change."""
    factors: list[RiskFactor] = []
    score = 0.0

    crit = _crit_of(asset.criticality)
    crit_w = CRITICALITY_WEIGHT[crit]
    score += crit_w
    factors.append(RiskFactor("Asset criticality", f"{crit.value} value asset", crit_w))

    if asset.internet_exposed:
        score += 15
        factors.append(RiskFactor("Internet exposure", "Asset is reachable from the public internet", 15))

    if not asset.mfa_enabled and asset.authentication_type in ("password", "oauth"):
        score += 15
        factors.append(RiskFactor("MFA disabled", "Multi-factor authentication is not enforced", 15))

    if asset.permission_level in ("write", "admin"):
        bump = 10 if asset.permission_level == "write" else 16
        score += bump
        factors.append(RiskFactor("Elevated permissions", f"Permission level: {asset.permission_level}", bump))

    if asset.permission_count and asset.permission_count > 10:
        bump = min(12, (asset.permission_count - 10) * 0.8)
        score += bump
        factors.append(RiskFactor("Excessive permission count", f"{asset.permission_count} permissions granted", round(bump, 1)))

    open_vulns = [v for v in vulnerabilities if v.status == "open"]
    for v in open_vulns:
        sev = _crit_of(v.severity)
        w = SEVERITY_WEIGHT[sev]
        if v.known_exploited:
            w += 8
        score += w
        label = f"{v.cve_id} ({sev.value})" if v.cve_id else f"{v.title} ({sev.value})"
        detail = "Known exploited vulnerability, unpatched" if v.known_exploited else "Unpatched vulnerability"
        factors.append(RiskFactor(f"Vulnerability: {label}", detail, w))

    if asset.authentication_type == "key" and not asset.mfa_enabled:
        score += 5
        factors.append(RiskFactor("Key-based auth without rotation policy", "No MFA fallback on key compromise", 5))

    if recent_events:
        active_events = [e for e in recent_events if (e.status or "ACTIVE") == "ACTIVE"]
        if active_events:
            event_contribution = min(MAX_EVENT_CONTRIBUTION, sum(e.risk_impact or 0.0 for e in active_events))
            if event_contribution > 0:
                score += event_contribution
                worst = max(active_events, key=lambda e: e.risk_impact or 0.0)
                detail = f"{len(active_events)} active event(s); most recent: {worst.message}"
                factors.append(RiskFactor("Live security events", detail, round(event_contribution, 1)))

    score = max(0.0, min(MAX_SCORE, score))
    risk_class = classify(score)

    factors.sort(key=lambda f: f.weight, reverse=True)
    return round(score, 1), risk_class, factors


def classify(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def security_score_from_assets(risk_scores: list[float]) -> int:
    """Overall org 'Security Score' out of 100 — inverse of mean asset risk,
    weighted slightly toward the worst offenders so a few critical assets
    pull the score down meaningfully."""
    if not risk_scores:
        return 100
    avg = sum(risk_scores) / len(risk_scores)
    worst = max(risk_scores)
    blended_risk = 0.7 * avg + 0.3 * worst
    return max(0, round(100 - blended_risk))
