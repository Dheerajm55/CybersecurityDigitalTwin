from pydantic import BaseModel, Field


# ---------- Catalog ----------

class ComponentTypeOut(BaseModel):
    id: str
    label: str
    category: str
    side: str
    icon: str
    default_criticality: str
    is_defense_control: bool


class DefenseControlOut(BaseModel):
    id: str
    label: str
    category: str


# ---------- Scenario library ----------

class ScenarioOut(BaseModel):
    id: str
    name: str
    category: str
    description: str
    prerequisites: list[str]
    entry_point_types: list[str]
    affected_asset_types: list[str]
    impact: list[str]
    risk_level: str
    detection: list[str]
    prevention: list[str]
    mitre_technique_ids: list[str]
    attack_chain: list[str] = []
    enabled: bool = True


class ScenarioCreate(BaseModel):
    """Input schema for authoring a new database-backed scenario (Phase 2.5).
    Deliberately mirrors ScenarioOut minus `id`/`enabled` bookkeeping. This
    creates a new SAFE, CONCEPTUAL scenario definition only — the same
    kind of data already in app/scenario_engine/scenarios.py — never any
    exploit code, payload, or operational attack instructions."""

    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=2000)
    risk_level: str = Field(pattern=r"^(LOW|MEDIUM|HIGH|CRITICAL)$")
    prerequisites: list[str] = []
    entry_point_types: list[str] = []
    affected_asset_types: list[str] = []
    impact: list[str] = []
    attack_chain: list[str] = []
    detection: list[str] = []
    prevention: list[str] = []
    mitre_technique_ids: list[str] = []


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    category: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=2000)
    risk_level: str | None = Field(default=None, pattern=r"^(LOW|MEDIUM|HIGH|CRITICAL)$")
    prerequisites: list[str] | None = None
    entry_point_types: list[str] | None = None
    affected_asset_types: list[str] | None = None
    impact: list[str] | None = None
    attack_chain: list[str] | None = None
    detection: list[str] | None = None
    prevention: list[str] | None = None
    mitre_technique_ids: list[str] | None = None
    enabled: bool | None = None


# ---------- Environment templates ----------

class TemplateNodeOut(BaseModel):
    id: str
    type: str
    name: str
    x: int
    y: int
    criticality: str


class TemplateEdgeOut(BaseModel):
    source: str
    target: str


class TemplateOut(BaseModel):
    id: str
    name: str
    description: str
    nodes: list[TemplateNodeOut]
    edges: list[TemplateEdgeOut]


# ---------- Case studies ----------

class CaseStudyOut(BaseModel):
    id: str
    title: str
    year: int
    attack_category: str
    affected_sector: str
    attack_chain_summary: list[str]
    impact: str
    security_lesson: str
    preventive_controls: list[str]
    sources: list[str]
    recreate_scenario_id: str
    # Additive fields (Phase 2) — populated from the linked scenario's own
    # data where available; None/[] on any case study not yet backed by
    # the database (e.g. before the first startup seed has run).
    initial_condition: str | None = None
    affected_assets: list[str] = []
    mitre_techniques: list[str] = []
    detection_signals: list[str] = []


# ---------- Simulation run ----------

class SimComponentIn(BaseModel):
    id: str
    type: str
    name: str
    mfa_enabled: bool = False
    firewall_enabled: bool = False
    monitoring_enabled: bool = False
    segmented: bool = False
    criticality: str = "MEDIUM"


class SimEdgeIn(BaseModel):
    source: str
    target: str


class SimulationRunRequest(BaseModel):
    scenario_id: str
    entry_point_id: str
    components: list[SimComponentIn]
    edges: list[SimEdgeIn]
    applied_defenses: list[str] = []


class TimelineEventOut(BaseModel):
    offset_seconds: int
    message: str


class SimulationRunResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    entry_point_id: str
    visited_order: list[str]
    node_states: dict[str, str]
    blocked_at_edge: list[str] | None
    detected: bool
    risk_before: float
    risk_after: float
    risk_class_before: str
    risk_class_after: str
    timeline: list[TimelineEventOut]
    explanation: list[str]
    recommended_controls: list[str]


# ---------- Defense optimizer (Section 29) ----------

class OptimizeDefenseRequest(BaseModel):
    scenario_id: str
    entry_point_id: str
    components: list[SimComponentIn]
    edges: list[SimEdgeIn]


class DefenseRankingItem(BaseModel):
    defense_id: str
    defense_label: str
    risk_after: float
    risk_reduction: float
    estimated_impact: str  # LOW | MEDIUM | HIGH


class OptimizeDefenseResponse(BaseModel):
    baseline_risk: float
    ranking: list[DefenseRankingItem]


# ---------- Attack path predictor (Section 28) ----------

class PredictPathsRequest(BaseModel):
    components: list[SimComponentIn]
    edges: list[SimEdgeIn]


class PredictedPath(BaseModel):
    scenario_id: str
    scenario_name: str
    entry_point_id: str
    entry_point_name: str
    visited_order: list[str]
    risk_after: float
    risk_class: str


class PredictPathsResponse(BaseModel):
    paths: list[PredictedPath]
