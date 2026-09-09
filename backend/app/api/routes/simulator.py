import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.database.session import get_db
from app.models.models import ScenarioModel
from app.scenario_engine.db_adapter import (
    db_scenarios_for_entry_point,
    get_db_case_study,
    get_db_scenario,
    list_db_case_studies,
    list_db_scenarios,
)
from app.schemas.simulator_schemas import (
    CaseStudyOut,
    ComponentTypeOut,
    DefenseControlOut,
    DefenseRankingItem,
    OptimizeDefenseRequest,
    OptimizeDefenseResponse,
    PredictedPath,
    PredictPathsRequest,
    PredictPathsResponse,
    ScenarioCreate,
    ScenarioOut,
    ScenarioUpdate,
    SimulationRunRequest,
    SimulationRunResponse,
    TemplateOut,
)
from app.simulation_engine.components import COMPONENT_CATALOG, DEFENSE_CONTROLS
from app.simulation_engine.engine import SimComponent, SimEdge, classify, run_simulation
from app.simulation_engine.templates import get_template, list_templates

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


# ---------- Component catalog ----------

@router.get("/components", response_model=list[ComponentTypeOut])
def get_component_catalog(_user=Depends(get_current_user)):
    return [
        ComponentTypeOut(
            id=c.id, label=c.label, category=c.category, side=c.side,
            icon=c.icon, default_criticality=c.default_criticality,
            is_defense_control=c.is_defense_control,
        )
        for c in COMPONENT_CATALOG
    ]


@router.get("/defense-controls", response_model=list[DefenseControlOut])
def get_defense_controls(_user=Depends(get_current_user)):
    return [DefenseControlOut(**d) for d in DEFENSE_CONTROLS]


# ---------- Scenario library (database-backed, Phase 2) ----------

@router.get("/scenarios", response_model=list[ScenarioOut])
def get_scenarios(
    category: str | None = None,
    entry_point_type: str | None = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    if entry_point_type:
        scenarios = db_scenarios_for_entry_point(db, entry_point_type)
    else:
        scenarios = list_db_scenarios(db, category)
    return [
        ScenarioOut(
            id=s.id, name=s.name, category=s.category, description=s.description,
            prerequisites=s.prerequisites, entry_point_types=s.entry_point_types,
            affected_asset_types=s.affected_asset_types, impact=s.impact,
            risk_level=s.risk_level, detection=s.detection, prevention=s.prevention,
            mitre_technique_ids=s.mitre_technique_ids,
        )
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}", response_model=ScenarioOut)
def get_scenario_by_id(scenario_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    s = get_db_scenario(db, scenario_id)
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ScenarioOut(
        id=s.id, name=s.name, category=s.category, description=s.description,
        prerequisites=s.prerequisites, entry_point_types=s.entry_point_types,
        affected_asset_types=s.affected_asset_types, impact=s.impact,
        risk_level=s.risk_level, detection=s.detection, prevention=s.prevention,
        mitre_technique_ids=s.mitre_technique_ids,
    )


@router.post("/scenarios", response_model=ScenarioOut, status_code=201)
def create_scenario(payload: ScenarioCreate, db: Session = Depends(get_db), _user=Depends(require_admin)):
    """Create a new SAFE, CONCEPTUAL scenario definition in the database —
    the same kind of data already in the static catalog. Admin-only since
    this mutates a shared, applicationwide scenario library. Never accepts
    or stores exploit code/payloads; every field here is descriptive text
    and small label lists, validated by ScenarioCreate."""
    if db.query(ScenarioModel).filter(ScenarioModel.id == payload.id).first():
        raise HTTPException(status_code=400, detail=f"Scenario id '{payload.id}' already exists")
    row = ScenarioModel(**payload.model_dump(), enabled=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return ScenarioOut(
        id=row.id, name=row.name, category=row.category, description=row.description,
        prerequisites=row.prerequisites, entry_point_types=row.entry_point_types,
        affected_asset_types=row.affected_asset_types, impact=row.impact,
        risk_level=row.risk_level, detection=row.detection, prevention=row.prevention,
        mitre_technique_ids=row.mitre_technique_ids, attack_chain=row.attack_chain, enabled=row.enabled,
    )


@router.put("/scenarios/{scenario_id}", response_model=ScenarioOut)
def update_scenario(scenario_id: str, payload: ScenarioUpdate, db: Session = Depends(get_db), _user=Depends(require_admin)):
    row = db.query(ScenarioModel).filter(ScenarioModel.id == scenario_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return ScenarioOut(
        id=row.id, name=row.name, category=row.category, description=row.description,
        prerequisites=row.prerequisites, entry_point_types=row.entry_point_types,
        affected_asset_types=row.affected_asset_types, impact=row.impact,
        risk_level=row.risk_level, detection=row.detection, prevention=row.prevention,
        mitre_technique_ids=row.mitre_technique_ids, attack_chain=row.attack_chain, enabled=row.enabled,
    )


@router.delete("/scenarios/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: str, db: Session = Depends(get_db), _user=Depends(require_admin)):
    row = db.query(ScenarioModel).filter(ScenarioModel.id == scenario_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(row)
    db.commit()
    return None


# ---------- Environment templates ----------

@router.get("/templates", response_model=list[TemplateOut])
def get_templates(_user=Depends(get_current_user)):
    return [
        TemplateOut(
            id=t.id, name=t.name, description=t.description,
            nodes=[n.__dict__ for n in t.nodes],
            edges=[e.__dict__ for e in t.edges],
        )
        for t in list_templates()
    ]


@router.get("/templates/{template_id}", response_model=TemplateOut)
def get_template_by_id(template_id: str, _user=Depends(get_current_user)):
    t = get_template(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateOut(
        id=t.id, name=t.name, description=t.description,
        nodes=[n.__dict__ for n in t.nodes],
        edges=[e.__dict__ for e in t.edges],
    )


# ---------- Case studies (database-backed, Phase 2) ----------

def _case_study_out(c) -> CaseStudyOut:
    return CaseStudyOut(
        id=c.id, title=c.title, year=c.year, attack_category=c.attack_category,
        affected_sector=c.affected_sector, attack_chain_summary=c.attack_chain_summary or [],
        impact=c.impact, security_lesson=c.security_lesson,
        preventive_controls=c.preventive_controls or [], sources=c.sources or [],
        recreate_scenario_id=c.recreate_scenario_id,
        initial_condition=c.initial_condition,
        affected_assets=c.affected_assets or [],
        mitre_techniques=c.mitre_techniques or [],
        detection_signals=c.detection_signals or [],
    )


@router.get("/case-studies", response_model=list[CaseStudyOut])
def get_case_studies(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    rows = list_db_case_studies(db)
    if rows:
        return [_case_study_out(c) for c in rows]
    # Table not seeded yet — fall back to the static catalog.
    from app.case_studies.case_studies import list_case_studies as _list_static
    return [
        CaseStudyOut(
            id=c.id, title=c.title, year=c.year, attack_category=c.attack_category,
            affected_sector=c.affected_sector, attack_chain_summary=c.attack_chain_summary,
            impact=c.impact, security_lesson=c.security_lesson,
            preventive_controls=c.preventive_controls, sources=c.sources,
            recreate_scenario_id=c.recreate_scenario_id,
        )
        for c in _list_static()
    ]


@router.get("/case-studies/{case_id}", response_model=CaseStudyOut)
def get_case_study_by_id(case_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    c = get_db_case_study(db, case_id)
    if c:
        return _case_study_out(c)
    from app.case_studies.case_studies import get_case_study as _get_static
    static = _get_static(case_id)
    if not static:
        raise HTTPException(status_code=404, detail="Case study not found")
    return CaseStudyOut(
        id=static.id, title=static.title, year=static.year, attack_category=static.attack_category,
        affected_sector=static.affected_sector, attack_chain_summary=static.attack_chain_summary,
        impact=static.impact, security_lesson=static.security_lesson,
        preventive_controls=static.preventive_controls, sources=static.sources,
        recreate_scenario_id=static.recreate_scenario_id,
    )


# ---------- Run simulation ----------

@router.post("/run", response_model=SimulationRunResponse)
def run(payload: SimulationRunRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    scenario = get_db_scenario(db, payload.scenario_id)
    try:
        outcome = run_simulation(
            scenario_id=payload.scenario_id,
            entry_point_id=payload.entry_point_id,
            components=[SimComponent(**c.model_dump()) for c in payload.components],
            edges=[SimEdge(**e.model_dump()) for e in payload.edges],
            applied_defenses=payload.applied_defenses,
            scenario=scenario,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SimulationRunResponse(
        scenario_id=outcome.scenario.id,
        scenario_name=outcome.scenario.name,
        entry_point_id=outcome.entry_point_id,
        visited_order=outcome.visited_order,
        node_states=outcome.node_states,
        blocked_at_edge=list(outcome.blocked_at_edge) if outcome.blocked_at_edge else None,
        detected=outcome.detected,
        risk_before=outcome.risk_before,
        risk_after=outcome.risk_after,
        risk_class_before=classify(outcome.risk_before),
        risk_class_after=classify(outcome.risk_after),
        timeline=[{"offset_seconds": e.offset_seconds, "message": e.message} for e in outcome.timeline],
        explanation=outcome.explanation,
        recommended_controls=outcome.recommended_controls,
    )


# ---------- Defense optimizer (Section 29) ----------

@router.post("/optimize-defense", response_model=OptimizeDefenseResponse)
def optimize_defense(payload: OptimizeDefenseRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Runs the same deterministic engine once per candidate defense control
    and ranks them by simulated risk reduction. Real computation, not a
    lookup table — every number comes from an actual engine run."""
    components = [SimComponent(**c.model_dump()) for c in payload.components]
    edges = [SimEdge(**e.model_dump()) for e in payload.edges]
    scenario = get_db_scenario(db, payload.scenario_id)

    try:
        baseline = run_simulation(payload.scenario_id, payload.entry_point_id, components, edges, applied_defenses=[], scenario=scenario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ranking: list[DefenseRankingItem] = []
    for control in DEFENSE_CONTROLS:
        outcome = run_simulation(
            payload.scenario_id, payload.entry_point_id, components, edges,
            applied_defenses=[control["id"]], scenario=scenario,
        )
        reduction = round(baseline.risk_after - outcome.risk_after, 1)
        if reduction >= 30:
            impact = "HIGH"
        elif reduction >= 10:
            impact = "MEDIUM"
        else:
            impact = "LOW"
        ranking.append(DefenseRankingItem(
            defense_id=control["id"],
            defense_label=control["label"],
            risk_after=outcome.risk_after,
            risk_reduction=reduction,
            estimated_impact=impact,
        ))

    ranking.sort(key=lambda r: r.risk_reduction, reverse=True)
    return OptimizeDefenseResponse(baseline_risk=baseline.risk_after, ranking=ranking)


# ---------- Attack path predictor (Section 28) ----------

@router.post("/predict-paths", response_model=PredictPathsResponse)
def predict_paths(payload: PredictPathsRequest, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """For every ATTACK-side component in the topology, runs every scenario
    that could plausibly start there, and returns the results ranked by
    simulated risk — a real graph/rule analysis, not invented output."""
    components = [SimComponent(**c.model_dump()) for c in payload.components]
    edges = [SimEdge(**e.model_dump()) for e in payload.edges]
    comp_by_id = {c.id: c for c in components}

    results: list[PredictedPath] = []
    for comp in components:
        candidate_scenarios = db_scenarios_for_entry_point(db, comp.type)
        for scenario in candidate_scenarios:
            try:
                outcome = run_simulation(scenario.id, comp.id, components, edges, applied_defenses=[], scenario=scenario)
            except ValueError:
                continue
            if len(outcome.visited_order) <= 1:
                continue  # no reachable path from this entry point
            results.append(PredictedPath(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                entry_point_id=comp.id,
                entry_point_name=comp.name,
                visited_order=outcome.visited_order,
                risk_after=outcome.risk_after,
                risk_class=classify(outcome.risk_after),
            ))

    results.sort(key=lambda r: r.risk_after, reverse=True)
    return PredictPathsResponse(paths=results[:10])
