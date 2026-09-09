"""
Database Scenario -> Scenario Adapter -> Existing Simulation Engine.

The deterministic simulation engine (app/simulation_engine/engine.py) is
written against the plain, frozen `Scenario` dataclass defined in
app/scenario_engine/scenarios.py. Rather than rewrite that engine to
know about SQLAlchemy, this module adapts rows from the `scenarios` /
`case_studies` database tables back into that same dataclass shape, so
`run_simulation()` and every other existing consumer keep working
unchanged.

Read path (used by the API routes):

    DB row (ScenarioModel)
         |  _to_dataclass()
         v
    Scenario (frozen dataclass, identical shape to the static catalog)
         |
         v
    app.simulation_engine.engine.run_simulation(..., scenario=<this>)

If the database has not been seeded yet (or a specific id is missing —
e.g. a fresh install before the first startup seed has run), every
function here transparently falls back to the static in-memory catalog
in app.scenario_engine.scenarios, so the simulator never breaks because
of an empty table.
"""
from sqlalchemy.orm import Session

from app.models.models import CaseStudyModel, ScenarioModel
from app.scenario_engine.scenarios import Scenario
from app.scenario_engine.scenarios import get_scenario as _get_static_scenario
from app.scenario_engine.scenarios import list_scenarios as _list_static_scenarios
from app.scenario_engine.scenarios import scenarios_for_entry_point as _static_scenarios_for_entry_point


def _to_dataclass(row: ScenarioModel) -> Scenario:
    return Scenario(
        id=row.id,
        name=row.name,
        category=row.category,
        description=row.description,
        prerequisites=list(row.prerequisites or []),
        entry_point_types=list(row.entry_point_types or []),
        affected_asset_types=list(row.affected_asset_types or []),
        impact=list(row.impact or []),
        risk_level=row.risk_level,
        detection=list(row.detection or []),
        prevention=list(row.prevention or []),
        mitre_technique_ids=list(row.mitre_technique_ids or []),
    )


def get_db_scenario(db: Session, scenario_id: str) -> Scenario | None:
    """Look up one scenario, database first, static catalog as fallback."""
    row = (
        db.query(ScenarioModel)
        .filter(ScenarioModel.id == scenario_id, ScenarioModel.enabled.is_(True))
        .first()
    )
    if row is not None:
        return _to_dataclass(row)
    return _get_static_scenario(scenario_id)


def list_db_scenarios(db: Session, category: str | None = None) -> list[Scenario]:
    q = db.query(ScenarioModel).filter(ScenarioModel.enabled.is_(True))
    if category:
        q = q.filter(ScenarioModel.category == category)
    rows = q.order_by(ScenarioModel.name).all()
    if rows:
        return [_to_dataclass(r) for r in rows]
    # Table not seeded yet — fall back to the static catalog so the
    # simulator still works on a brand-new install before first startup.
    return _list_static_scenarios(category)


def db_scenarios_for_entry_point(db: Session, component_type: str) -> list[Scenario]:
    rows = db.query(ScenarioModel).filter(ScenarioModel.enabled.is_(True)).all()
    if rows:
        return [_to_dataclass(r) for r in rows if component_type in (r.entry_point_types or [])]
    return _static_scenarios_for_entry_point(component_type)


# ---------- Case studies ----------

def list_db_case_studies(db: Session) -> list[CaseStudyModel]:
    rows = db.query(CaseStudyModel).order_by(CaseStudyModel.year.desc()).all()
    return rows


def get_db_case_study(db: Session, case_id: str) -> CaseStudyModel | None:
    return db.query(CaseStudyModel).filter(CaseStudyModel.id == case_id).first()
