"""
Simulation Engine.

Implements the deterministic pipeline described in Section 40/41 of the
spec:

    Simulation Scenario
    -> Validate topology
    -> Identify entry point
    -> Evaluate prerequisites
    -> Traverse logical graph
    -> Evaluate security controls
    -> Determine simulated outcome
    -> Update temporary twin state
    -> Run risk analysis
    -> Generate recommendations

This module NEVER touches the real Digital Twin database (see
app/models/models.py). It operates entirely on a topology the client
submits in the request body — an ephemeral, client-owned "digital twin
simulation branch," exactly as Section 27 requires ("Only modify the
digital twin simulation. Do not modify the real environment.").

Nothing here performs a real action against any system. All outcomes
are computed by evaluating simple, transparent rules (Section 17) over
the submitted topology's declared security-control flags.
"""
from dataclasses import dataclass

from app.scenario_engine.scenarios import Scenario, get_scenario
from app.simulation_engine.components import get_component_type

# ---------- State machine (Section 21 / 41) ----------

NORMAL = "NORMAL"
TARGETED = "TARGETED"
UNDER_ATTACK = "UNDER_ATTACK"
COMPROMISED = "COMPROMISED"
DETECTED = "DETECTED"
BLOCKED = "BLOCKED"
ISOLATED = "ISOLATED"
RECOVERED = "RECOVERED"


@dataclass
class SimComponent:
    id: str
    type: str
    name: str
    # Declared security posture on this specific node — all default to
    # False/off so an unconfigured topology behaves like an undefended one.
    mfa_enabled: bool = False
    firewall_enabled: bool = False
    monitoring_enabled: bool = False
    segmented: bool = False
    criticality: str = "MEDIUM"


@dataclass
class SimEdge:
    source: str
    target: str


@dataclass
class TimelineEvent:
    offset_seconds: int
    message: str


@dataclass
class SimulationOutcome:
    scenario: Scenario
    entry_point_id: str
    visited_order: list[str]
    node_states: dict[str, str]
    blocked_at_edge: tuple[str, str] | None
    detected: bool
    risk_before: float
    risk_after: float
    timeline: list[TimelineEvent]
    explanation: list[str]
    recommended_controls: list[str]


CRITICALITY_BASE = {"LOW": 10, "MEDIUM": 25, "HIGH": 45, "CRITICAL": 65}
RISK_LEVEL_BONUS = {"LOW": 5, "MEDIUM": 12, "HIGH": 22, "CRITICAL": 32}


def _build_adjacency(edges: list[SimEdge]) -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {}
    for e in edges:
        adj.setdefault(e.source, []).append(e.target)
    return adj


def run_simulation(
    scenario_id: str,
    entry_point_id: str,
    components: list[SimComponent],
    edges: list[SimEdge],
    applied_defenses: list[str] | None = None,
    scenario: Scenario | None = None,
) -> SimulationOutcome:
    """Run one deterministic simulation and return a full outcome,
    including a state per visited node and a plain-language timeline.

    `scenario` is optional: callers that already resolved a Scenario
    object themselves (for example the API routes, which now look
    scenarios up from the database via
    app.scenario_engine.db_adapter.get_db_scenario) can pass it directly
    so this function doesn't re-look-up the static in-memory catalog.
    Existing callers that don't pass it keep behaving exactly as before,
    reading from the static catalog via `get_scenario`."""
    if scenario is None:
        scenario = get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    comp_by_id = {c.id: c for c in components}
    if entry_point_id not in comp_by_id:
        raise ValueError(f"Entry point {entry_point_id} not found in topology")

    entry = comp_by_id[entry_point_id]
    entry_type_mismatch = entry.type not in scenario.entry_point_types

    applied_defenses = applied_defenses or []
    adjacency = _build_adjacency(edges)

    node_states: dict[str, str] = {c.id: NORMAL for c in components}
    node_states[entry_point_id] = UNDER_ATTACK
    timeline: list[TimelineEvent] = [TimelineEvent(0, "Simulation started")]
    explanation: list[str] = []
    visited_order: list[str] = [entry_point_id]
    blocked_at_edge: tuple[str, str] | None = None
    detected = False
    t = 1

    if entry_type_mismatch:
        explanation.append(
            f"{entry.name} is not a typical entry point for '{scenario.name}', "
            "but the simulation proceeds since this is a sandbox scenario."
        )

    timeline.append(TimelineEvent(t, f"Entry point identified: {entry.name}"))
    t += 2

    # Global defenses applied via "Apply Defense" (Section 13) act as if
    # every node in the topology had that control turned on.
    global_mfa = "MFA" in applied_defenses
    global_segmentation = "NETWORK_SEGMENTATION" in applied_defenses
    global_firewall = "FIREWALL_RULE" in applied_defenses
    global_monitoring = "MONITORING" in applied_defenses
    global_least_privilege = "LEAST_PRIVILEGE" in applied_defenses

    frontier = list(adjacency.get(entry_point_id, []))
    hop_index = 0
    seen = {entry_point_id}

    while frontier and hop_index < 6:  # hard cap so a cyclic/huge topology can't loop forever
        next_node_id = frontier.pop(0)
        if next_node_id in seen:
            continue
        seen.add(next_node_id)

        node = comp_by_id.get(next_node_id)
        if node is None:
            continue
        node_type = get_component_type(node.type)

        node_states[next_node_id] = TARGETED
        timeline.append(TimelineEvent(t, f"{node.name} targeted"))
        t += 2

        # --- Rule 1: Firewall blocks network/application/malware paths ---
        firewall_here = node.firewall_enabled or global_firewall or (node_type is not None and node_type.id in ("FIREWALL", "SECURITY_FIREWALL"))
        if firewall_here and scenario.category in ("NETWORK", "APPLICATION", "MALWARE"):
            node_states[next_node_id] = BLOCKED
            blocked_at_edge = (entry_point_id, next_node_id)
            timeline.append(TimelineEvent(t, f"Firewall rule blocked the simulated path at {node.name}"))
            explanation.append(f"Firewall control on {node.name} blocked this simulated {scenario.category.lower()} path.")
            break

        # --- Rule 2: MFA blocks/detects identity-category compromise ---
        mfa_here = node.mfa_enabled or global_mfa
        if scenario.category == "IDENTITY" and "No MFA enforced" in scenario.prerequisites and mfa_here:
            node_states[next_node_id] = DETECTED
            detected = True
            timeline.append(TimelineEvent(t, f"MFA challenge stopped the simulated compromise at {node.name}"))
            explanation.append(f"MFA on {node.name} prevented the simulated identity compromise from succeeding.")
            blocked_at_edge = (entry_point_id, next_node_id)
            break

        # --- Rule 3: Network segmentation stops lateral spread beyond first hop ---
        segmented_here = node.segmented or global_segmentation
        if segmented_here and hop_index >= 1:
            node_states[next_node_id] = ISOLATED
            timeline.append(TimelineEvent(t, f"Network segmentation isolated {node.name} from the spreading path"))
            explanation.append(f"Network segmentation prevented the simulated path from reaching {node.name}.")
            blocked_at_edge = (entry_point_id, next_node_id)
            break

        # --- Otherwise: compromise succeeds at this node ---
        monitored_here = node.monitoring_enabled or global_monitoring
        state = DETECTED if monitored_here else COMPROMISED
        if monitored_here:
            detected = True
        node_states[next_node_id] = state
        visited_order.append(next_node_id)
        timeline.append(TimelineEvent(
            t,
            f"{scenario.name} succeeded against {node.name}" + (" (detected by monitoring)" if monitored_here else "")
        ))
        t += 2

        if global_least_privilege:
            explanation.append(f"Least-privilege controls limited the potential blast radius from {node.name}.")

        # Continue traversal from this node
        frontier.extend(adjacency.get(next_node_id, []))
        hop_index += 1

    if not explanation:
        if len(visited_order) > 1:
            explanation.append(
                f"No blocking control was present along the path from {entry.name}, "
                f"so the simulated {scenario.name.lower()} reached {len(visited_order) - 1} additional asset(s)."
            )
        else:
            explanation.append(f"The simulated path from {entry.name} had no reachable connected assets to test.")

    if detected and not blocked_at_edge:
        timeline.append(TimelineEvent(t, "Detection rule triggered"))
        t += 2

    # --- Risk scoring ---
    risk_before = _score_topology(components, node_states={c.id: NORMAL for c in components}, scenario=scenario)
    risk_after = _score_topology(components, node_states=node_states, scenario=scenario)

    if blocked_at_edge:
        timeline.append(TimelineEvent(t, "Simulation resolved: path blocked"))
    else:
        timeline.append(TimelineEvent(t, "Simulation resolved: path succeeded"))

    return SimulationOutcome(
        scenario=scenario,
        entry_point_id=entry_point_id,
        visited_order=visited_order,
        node_states=node_states,
        blocked_at_edge=blocked_at_edge,
        detected=detected,
        risk_before=risk_before,
        risk_after=risk_after,
        timeline=timeline,
        explanation=explanation,
        recommended_controls=scenario.prevention,
    )


def _score_topology(components: list[SimComponent], node_states: dict[str, str], scenario: Scenario) -> float:
    """A simple, transparent 0-100 score: base criticality of affected
    nodes plus a bonus for the scenario's own risk level, capped."""
    compromised_types = (COMPROMISED, DETECTED, UNDER_ATTACK, TARGETED)
    affected = [c for c in components if node_states.get(c.id) in compromised_types]
    if not affected:
        return 0.0
    base = max(CRITICALITY_BASE.get(c.criticality, 25) for c in affected)
    bonus = RISK_LEVEL_BONUS.get(scenario.risk_level, 12)
    spread_bonus = min(20, (len(affected) - 1) * 6)
    return min(100.0, round(base + bonus + spread_bonus, 1))


def classify(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"
