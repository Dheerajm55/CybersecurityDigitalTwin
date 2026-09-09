from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------- Auth ----------

class UserCreate(BaseModel):
    # Deliberately `str`, not `EmailStr` — see the note on UserLogin below.
    # Registration input for a synthetic/demo-friendly app like this one
    # can legitimately include domains (e.g. "*.local") that the
    # email-validator library treats as reserved and rejects with a 422,
    # even though they're perfectly valid identifiers for this
    # application's purposes. A lightweight shape check below still
    # rejects garbage input; it just doesn't enforce full RFC email
    # syntax or DNS-plausibility.
    email: str = Field(min_length=3, max_length=254)
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def _basic_email_shape(cls, v: str) -> str:
        v = v.strip()
        if "@" not in v or v.startswith("@") or v.endswith("@") or " " in v:
            raise ValueError("Enter a valid email address")
        return v


class UserLogin(BaseModel):
    # Intentionally a plain str, not EmailStr: this field is checked against
    # a stored value, not used to construct a new record, so it doesn't need
    # RFC-format validation here — and strict EmailStr validation (via the
    # email-validator library) can reject synthetic/demo domains like
    # "digitaltwin.local" depending on the installed email-validator version,
    # which previously caused a 422 on every login attempt with the demo
    # account. An unrecognized address should fail as 401 (invalid
    # credentials), not 422 (bad request shape).
    email: str = Field(min_length=3)
    password: str


class UserOut(BaseModel):
    id: str
    # Same reasoning as UserLogin, applied to the RESPONSE side: this value
    # is read back from a row that's already in the database — it isn't
    # being validated as fresh input, so re-validating it as EmailStr on
    # every response only adds a way for a trusted stored value (e.g. the
    # seeded demo account "demo@digitaltwin.local") to fail response
    # serialization for the same reason UserLogin used to fail request
    # validation. A response-serialization failure here raises an
    # uncaught exception inside the route (since UserOut.model_validate()
    # is called explicitly in auth.py), which surfaces to the browser as a
    # generic 500 with a non-JSON body — which the frontend's error
    # handling correctly falls back to a generic "Unable to sign in"
    # message for, since it has no usable `detail` field to read. That
    # masked this as a credential problem when it was actually a response
    # schema problem. Using `str` here removes the failure mode entirely.
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Assets ----------

class AssetBase(BaseModel):
    name: str
    asset_type: str
    owner: Optional[str] = None
    criticality: str = "MEDIUM"
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    environment: str = "production"
    internet_exposed: bool = False
    mfa_enabled: bool = False
    authentication_type: str = "password"
    permission_level: str = "standard"
    permission_count: int = 1
    tags: Optional[str] = None
    description: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    owner: Optional[str] = None
    criticality: Optional[str] = None
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    environment: Optional[str] = None
    internet_exposed: Optional[bool] = None
    mfa_enabled: Optional[bool] = None
    authentication_type: Optional[str] = None
    permission_level: Optional[str] = None
    permission_count: Optional[int] = None
    tags: Optional[str] = None
    description: Optional[str] = None


class AssetOut(AssetBase):
    id: str
    risk_score: float
    risk_class: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetRelationshipCreate(BaseModel):
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    weight: float = 1.0


class AssetRelationshipOut(AssetRelationshipCreate):
    id: str

    model_config = {"from_attributes": True}


# ---------- Vulnerabilities ----------

class VulnerabilityCreate(BaseModel):
    asset_id: str
    cve_id: Optional[str] = None
    title: str
    severity: str = "MEDIUM"
    cvss_score: Optional[float] = None
    status: str = "open"
    known_exploited: bool = False
    affected_component: Optional[str] = None
    recommended_action: Optional[str] = None


class VulnerabilityOut(VulnerabilityCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Digital twin graph ----------

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    criticality: str
    risk_score: float
    risk_class: str
    mfa_enabled: bool
    internet_exposed: bool


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    weight: float


class DigitalTwinGraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ---------- Attack paths ----------

class AttackPathRequest(BaseModel):
    source_asset_id: str
    target_asset_id: Optional[str] = None  # if omitted, find riskiest reachable target


class AttackPathStep(BaseModel):
    asset_id: str
    name: str
    asset_type: str


class AttackPathOut(BaseModel):
    path: list[AttackPathStep]
    risk_score: float
    risk_class: str
    explanation: list[str]


# ---------- Risk ----------

class RiskFactor(BaseModel):
    factor: str
    detail: str
    weight: float


class AssetRiskDetail(BaseModel):
    asset_id: str
    name: str
    risk_score: float
    risk_class: str
    factors: list[RiskFactor]


class DashboardSummary(BaseModel):
    total_assets: int
    high_risk_assets: int
    critical_vulnerabilities: int
    attack_path_count: int
    security_score: int
    risk_distribution: dict[str, int]
    active_threats: int = 0
    events_per_min: float = 0.0


# ---------- What-if simulation ----------

class SimulationRequest(BaseModel):
    asset_id: str
    action: str  # enable_mfa | remove_excess_permissions | patch_vulnerability | disable_public_access


class SimulationOut(BaseModel):
    action: str
    asset_id: str
    risk_before: float
    risk_after: float
    risk_reduction: float
    explanation: str
