"""
Seeds the database-backed Scenario / CaseStudy tables from the existing
static Python catalogs (app/scenario_engine/scenarios.py and
app/case_studies/case_studies.py).

This is intentionally a one-way, idempotent sync FROM the static catalog
INTO the database, run on every startup:

    Python catalog (source of truth / version-controlled definitions)
                    |
                    v
       seed_scenarios_and_case_studies()   (idempotent upsert)
                    |
                    v
        scenarios / case_studies tables    (what the API actually reads)

Idempotency: each row is looked up by its stable string id (the same id
already used throughout the API/frontend, e.g. "credential_compromise").
If the row exists, its fields are refreshed to match the catalog (so
editing a scenario's description in the .py file and restarting picks up
the change); if it doesn't exist, it's inserted. Running this any number
of times never creates duplicate rows.
"""
import logging

from sqlalchemy.orm import Session

from app.case_studies.case_studies import list_case_studies
from app.models.models import CaseStudyModel, ScenarioModel
from app.scenario_engine.scenarios import list_scenarios

logger = logging.getLogger("cyber_twin")


def _derive_attack_chain(scenario) -> list[str]:
    """Build a short, conceptual attack-chain summary from the scenario's
    own declared fields (entry points -> prerequisites -> affected
    assets). This is a derived restatement of data the scenario already
    declares, not invented incident detail, matching this module's own
    'no exploit steps, only conceptual description' rule."""
    entry = scenario.entry_point_types[0].replace("_", " ").title() if scenario.entry_point_types else "an entry point"
    target = scenario.affected_asset_types[0].replace("_", " ").title() if scenario.affected_asset_types else "a connected asset"
    chain = [f"Simulated entry via {entry}"]
    if scenario.prerequisites:
        chain.append(f"Conditions present: {', '.join(scenario.prerequisites)}")
    chain.append(f"Simulated impact reaches {target}")
    return chain


def seed_scenarios_and_case_studies(db: Session) -> tuple[int, int]:
    """Upsert every scenario/case-study from the static catalogs into the
    database. Returns (scenarios_written, case_studies_written)."""
    scenario_count = 0
    for s in list_scenarios():
        row = db.query(ScenarioModel).filter(ScenarioModel.id == s.id).first()
        if row is None:
            row = ScenarioModel(id=s.id)
            db.add(row)
        row.name = s.name
        row.category = s.category
        row.description = s.description
        row.risk_level = s.risk_level
        row.prerequisites = list(s.prerequisites)
        row.entry_point_types = list(s.entry_point_types)
        row.affected_asset_types = list(s.affected_asset_types)
        row.impact = list(s.impact)
        row.attack_chain = _derive_attack_chain(s)
        row.detection = list(s.detection)
        row.prevention = list(s.prevention)
        row.mitre_technique_ids = list(s.mitre_technique_ids)
        row.enabled = True
        scenario_count += 1
    db.flush()

    case_study_count = 0
    for c in list_case_studies():
        row = db.query(CaseStudyModel).filter(CaseStudyModel.id == c.id).first()
        if row is None:
            row = CaseStudyModel(id=c.id)
            db.add(row)
        row.title = c.title
        row.year = c.year
        row.attack_category = c.attack_category
        row.affected_sector = c.affected_sector
        row.attack_chain_summary = list(c.attack_chain_summary)
        row.impact = c.impact
        row.security_lesson = c.security_lesson
        row.preventive_controls = list(c.preventive_controls)
        row.sources = list(c.sources)
        row.recreate_scenario_id = c.recreate_scenario_id

        # Derive the additional descriptive fields from the linked
        # scenario's own real data, rather than hand-authoring 15 more
        # paragraphs of unverifiable detail.
        linked = db.query(ScenarioModel).filter(ScenarioModel.id == c.recreate_scenario_id).first()
        if linked is not None:
            row.initial_condition = (
                f"Conditions present prior to the simulated event: {', '.join(linked.prerequisites)}."
                if linked.prerequisites else None
            )
            row.affected_assets = list(linked.affected_asset_types)
            row.mitre_techniques = list(linked.mitre_technique_ids)
            row.detection_signals = list(linked.detection)

        case_study_count += 1
    db.commit()

    logger.info(
        "Seeded/refreshed %d scenario(s) and %d case stud(y/ies) into the database.",
        scenario_count, case_study_count,
    )
    return scenario_count, case_study_count
