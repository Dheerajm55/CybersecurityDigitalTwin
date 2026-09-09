"""
Core relational data model.

IMPORTANT — privacy/security by design:
No table in this schema stores real passwords, private keys, API secrets,
or session tokens. `User.hashed_password` stores only an Argon2 hash of
the *application login* password. `Asset` has no credential fields at
all — only metadata describing an asset's security posture (MFA status,
exposure, permissions, etc.), which is what the risk engine needs.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Criticality(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AssetType(str, enum.Enum):
    USER = "USER"
    DEVICE = "DEVICE"
    LAPTOP = "LAPTOP"
    SMARTPHONE = "SMARTPHONE"
    SERVER = "SERVER"
    ROUTER = "ROUTER"
    FIREWALL = "FIREWALL"
    EMAIL_ACCOUNT = "EMAIL_ACCOUNT"
    GITHUB_ACCOUNT = "GITHUB_ACCOUNT"
    CLOUD_ACCOUNT = "CLOUD_ACCOUNT"
    DATABASE = "DATABASE"
    WEB_APPLICATION = "WEB_APPLICATION"
    API = "API"
    SAAS_APPLICATION = "SAAS_APPLICATION"
    STORAGE_BUCKET = "STORAGE_BUCKET"
    VPN = "VPN"
    IDENTITY_PROVIDER = "IDENTITY_PROVIDER"


class RelationshipType(str, enum.Enum):
    OWNS = "OWNS"
    ACCESSES = "ACCESSES"
    AUTHENTICATES = "AUTHENTICATES"
    CONNECTS_TO = "CONNECTS_TO"
    DEPENDS_ON = "DEPENDS_ON"
    HAS_PERMISSION = "HAS_PERMISSION"
    RECOVERS = "RECOVERS"
    HOSTS = "HOSTS"
    STORES_DATA = "STORES_DATA"
    TRUSTS = "TRUSTS"
    CAN_REACH = "CAN_REACH"


class User(Base):
    """Application login account (NOT a digital-twin 'asset')."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="analyst")  # analyst | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Asset(Base):
    """A node in the digital twin graph."""

    __tablename__ = "assets"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)
    owner = Column(String, nullable=True)
    criticality = Column(Enum(Criticality), default=Criticality.MEDIUM)

    hostname = Column(String, nullable=True)
    operating_system = Column(String, nullable=True)
    environment = Column(String, default="production")  # production | staging | dev
    internet_exposed = Column(Boolean, default=False)

    mfa_enabled = Column(Boolean, default=False)
    authentication_type = Column(String, default="password")  # password | sso | oauth | key
    permission_level = Column(String, default="standard")  # read-only | standard | write | admin
    permission_count = Column(Integer, default=1)

    tags = Column(String, nullable=True)  # comma-separated
    description = Column(Text, nullable=True)
    source_type = Column(String, default="synthetic")  # synthetic | imported | simulated

    # Denormalized, recomputed by the risk engine — never hand-edited by users.
    risk_score = Column(Float, default=0.0)
    risk_class = Column(String, default="LOW")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vulnerabilities = relationship(
        "Vulnerability", back_populates="asset", cascade="all, delete-orphan"
    )


class AssetRelationship(Base):
    """A directed edge between two assets in the digital twin graph."""

    __tablename__ = "asset_relationships"

    id = Column(String, primary_key=True, default=_uuid)
    source_asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    target_asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    relationship_type = Column(Enum(RelationshipType), nullable=False)
    weight = Column(Float, default=1.0)  # traversal cost used by the attack-path engine
    created_at = Column(DateTime, default=datetime.utcnow)


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id = Column(String, primary_key=True, default=_uuid)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    cve_id = Column(String, nullable=True)  # e.g. CVE-2024-12345, null for internal findings
    title = Column(String, nullable=False)
    severity = Column(Enum(Criticality), default=Criticality.MEDIUM)
    cvss_score = Column(Float, nullable=True)
    status = Column(String, default="open")  # open | patched | accepted_risk
    known_exploited = Column(Boolean, default=False)  # CISA KEV flag
    affected_component = Column(String, nullable=True)
    recommended_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="vulnerabilities")


class SecurityControl(Base):
    __tablename__ = "security_controls"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    current_state = Column(String, default="not_implemented")  # implemented | partial | not_implemented
    risk_reduction_estimate = Column(Float, default=0.0)  # 0-1, project estimate only
    priority = Column(String, default="medium")
    affected_asset_ids = Column(Text, nullable=True)  # comma-separated asset ids
    created_at = Column(DateTime, default=datetime.utcnow)


class Simulation(Base):
    """A single 'what-if' run: one applied control change and its effect."""

    __tablename__ = "simulations"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    target_asset_id = Column(String, ForeignKey("assets.id"), nullable=True)
    action = Column(String, nullable=False)  # e.g. "enable_mfa", "patch_vulnerability"
    risk_before = Column(Float, nullable=False)
    risk_after = Column(Float, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AttackPath(Base):
    """A cached, computed attack path between two assets (Phase 3 groundwork)."""

    __tablename__ = "attack_paths"

    id = Column(String, primary_key=True, default=_uuid)
    source_asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    target_asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    path_asset_ids = Column(Text, nullable=False)  # ordered, comma-separated
    risk_score = Column(Float, nullable=False)
    risk_class = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String, primary_key=True, default=_uuid)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=True)
    event_type = Column(String, nullable=False)
    severity = Column(Enum(Criticality), default=Criticality.LOW)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Added for the live telemetry engine (see app/services/telemetry_engine.py).
    # All nullable/defaulted so this is backward compatible with the existing
    # table shape; older rows simply read back with the defaults below.
    risk_impact = Column(Float, default=0.0)  # how much this event nudged the asset's risk score
    status = Column(String, default="ACTIVE")  # ACTIVE | RESOLVED
    source = Column(String, nullable=True)  # e.g. an IP, account, or asset name the event originated from
    destination = Column(String, nullable=True)  # e.g. the asset/service the event targeted


class ScenarioModel(Base):
    """Database-backed mirror of the simulator's attack scenario catalog
    (see app/scenario_engine/scenarios.py — the static, versioned Python
    catalog remains the seed/bootstrap source of truth and a fallback if
    this table is ever empty, per ARCHITECTURE.md's stated migration
    path: 'promoting it to the database later is a data-migration, not a
    redesign').

    Uses the string `id` from the Python catalog (e.g. "credential_compromise")
    as the primary key so seeding is idempotent and case studies /
    simulator requests can reference scenarios by the same stable id used
    throughout the existing frontend and API.

    List-shaped fields are stored as JSON (works on both SQLite and
    Postgres via SQLAlchemy's generic JSON type) rather than introducing
    a separate join table, since these are small, scenario-owned lists
    that are never queried/filtered element-wise elsewhere in the app.
    """

    __tablename__ = "scenarios"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # IDENTITY | APPLICATION | NETWORK | MALWARE | DATA
    description = Column(Text, nullable=False)
    risk_level = Column(String, nullable=False)  # LOW | MEDIUM | HIGH | CRITICAL

    prerequisites = Column(JSON, default=list)  # list[str]
    entry_point_types = Column(JSON, default=list)  # list[str] — component types this can start from
    affected_asset_types = Column(JSON, default=list)  # list[str] — component types this can spread to
    impact = Column(JSON, default=list)  # list[str]
    attack_chain = Column(JSON, default=list)  # list[str] — high-level conceptual chain summary
    detection = Column(JSON, default=list)  # list[str]
    prevention = Column(JSON, default=list)  # list[str]
    mitre_technique_ids = Column(JSON, default=list)  # list[str]

    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case_studies = relationship("CaseStudyModel", back_populates="scenario")


class CaseStudyModel(Base):
    """Database-backed mirror of the simulator's educational case-study
    library (see app/case_studies/case_studies.py). Same seed/fallback
    relationship to the static Python catalog as ScenarioModel above.

    Field names deliberately match the existing `CaseStudyOut` API schema
    (`affected_sector`, `attack_chain_summary`, `security_lesson`,
    `preventive_controls`, `recreate_scenario_id`) so the already-working
    `/api/simulator/case-studies` contract and frontend types do not need
    to change, while adding the extra descriptive fields requested for
    this phase (`initial_condition`, `affected_assets`,
    `mitre_techniques`, `detection_signals`) as nullable/defaulted
    additions.
    """

    __tablename__ = "case_studies"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    attack_category = Column(String, nullable=False)
    affected_sector = Column(String, nullable=False)

    initial_condition = Column(Text, nullable=True)
    attack_chain_summary = Column(JSON, default=list)  # list[str]
    affected_assets = Column(JSON, default=list)  # list[str]
    impact = Column(Text, nullable=False)
    mitre_techniques = Column(JSON, default=list)  # list[str]
    detection_signals = Column(JSON, default=list)  # list[str]
    security_lesson = Column(Text, nullable=False)
    preventive_controls = Column(JSON, default=list)  # list[str]
    sources = Column(JSON, default=list)  # list[str]

    recreate_scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scenario = relationship("ScenarioModel", back_populates="case_studies")
