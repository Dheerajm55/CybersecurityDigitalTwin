"""
Deterministic synthetic demo data.

Populates the database with a realistic (but entirely fictional) digital
environment so the application is never empty on first run, per Section
23 of the spec. Includes the exact
Email -> GitHub -> Cloud -> Database
chain used in the Section 41 demo walkthrough, plus a broader set of
assets, vulnerabilities and relationships so the dashboard, digital
twin graph, and attack-path engine all have real material to work with.

All identities, hostnames, and CVEs below are synthetic/illustrative.
No real credentials, secrets, or organization data are included or
required anywhere in this file.

SEEDING IS IDEMPOTENT AND RUNS ON EVERY STARTUP. It is split into two
independent, separately-gated steps rather than one all-or-nothing block
keyed on "does any user exist":

  ensure_demo_user(db)  — looked up by normalized email; created only if
                           missing; an EXISTING demo account's password
                           is never touched. This runs unconditionally.

  the synthetic environment (assets/vulns/controls/events below) — gated
  on whether any Asset already exists, since this is a single connected
  graph seeded as one unit (shared foreign keys), not something that
  makes sense to re-seed piecemeal.

Decoupling these two matters: previously, seeding was skipped entirely
if ANY user row existed for ANY reason (e.g. someone had registered a
second, unrelated account), which could permanently prevent the demo
account from ever being created on a database that otherwise looked
"already set up". Gating the demo user separately means it is always
ensured to exist, regardless of what else is in the users table.
"""
import logging
import random

from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email
from app.models.models import (
    Asset,
    AssetRelationship,
    AssetType,
    Criticality,
    RelationshipType,
    SecurityControl,
    SecurityEvent,
    User,
    Vulnerability,
)
from app.services.risk_updater import recompute_all

random.seed(42)

logger = logging.getLogger("cyber_twin")

DEMO_EMAIL = "demo@digitaltwin.local"
DEMO_PASSWORD = "DemoPass123!"


def _asset(db, name, asset_type, **kwargs) -> Asset:
    a = Asset(name=name, asset_type=asset_type, **kwargs)
    db.add(a)
    db.flush()
    return a


def _rel(db, source: Asset, target: Asset, rel_type, weight=1.0):
    db.add(
        AssetRelationship(
            source_asset_id=source.id,
            target_asset_id=target.id,
            relationship_type=rel_type,
            weight=weight,
        )
    )


def ensure_demo_user(db: Session) -> User:
    """Idempotently ensure the demo login account exists, looked up by
    its normalized email. Safe to call on every startup, any number of
    times, against a fresh or pre-existing database:

    - Missing -> create it with the known demo password.
    - Present -> return it as-is. The existing password hash is never
      regenerated or overwritten, so a real operator who has since
      changed the demo account's password won't have that change
      silently reverted on the next restart.
    """
    email = normalize_email(DEMO_EMAIL)
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        logger.info("Demo user already present (user_id=%s); leaving existing password unchanged.", user.id)
        return user

    user = User(
        email=email,
        full_name="Demo Analyst",
        hashed_password=hash_password(DEMO_PASSWORD),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created demo user (user_id=%s).", user.id)
    return user


def seed_database(db: Session) -> None:
    ensure_demo_user(db)

    if db.query(Asset).first() is not None:
        return  # synthetic environment already seeded
    email = _asset(
        db, "Corporate Email Account", AssetType.EMAIL_ACCOUNT,
        owner="J. Rivera", criticality=Criticality.HIGH,
        mfa_enabled=False, authentication_type="password",
        permission_level="standard", permission_count=3,
        internet_exposed=True, environment="production",
        description="Primary corporate email/SSO recovery address.",
        tags="identity,email",
    )
    github = _asset(
        db, "GitHub Organization Account", AssetType.GITHUB_ACCOUNT,
        owner="J. Rivera", criticality=Criticality.HIGH,
        mfa_enabled=False, authentication_type="oauth",
        permission_level="write", permission_count=12,
        internet_exposed=True, environment="production",
        description="Org-level GitHub account with repository write access.",
        tags="identity,saas,code",
    )
    cloud = _asset(
        db, "Primary Cloud Account", AssetType.CLOUD_ACCOUNT,
        owner="Platform Team", criticality=Criticality.CRITICAL,
        mfa_enabled=True, authentication_type="sso",
        permission_level="admin", permission_count=25,
        internet_exposed=False, environment="production",
        description="Cloud provider root/organization account.",
        tags="cloud,infrastructure",
    )
    database = _asset(
        db, "Customer Database", AssetType.DATABASE,
        owner="Platform Team", criticality=Criticality.CRITICAL,
        mfa_enabled=False, authentication_type="password",
        permission_level="admin", permission_count=6,
        internet_exposed=False, environment="production",
        description="Primary PostgreSQL instance holding customer records.",
        tags="database,sensitive-data",
    )

    _rel(db, email, github, RelationshipType.RECOVERS, weight=1.0)
    _rel(db, github, cloud, RelationshipType.AUTHENTICATES, weight=1.0)
    _rel(db, cloud, database, RelationshipType.HOSTS, weight=1.0)

    db.add(Vulnerability(
        asset_id=github.id, cve_id="CVE-2024-30103", title="OAuth token overly broad scope",
        severity=Criticality.HIGH, cvss_score=7.5, status="open", known_exploited=False,
        affected_component="OAuth integration", recommended_action="Rotate token and scope to minimum required permissions.",
    ))
    db.add(Vulnerability(
        asset_id=database.id, cve_id="CVE-2023-44487", title="Unpatched database server vulnerability",
        severity=Criticality.CRITICAL, cvss_score=9.1, status="open", known_exploited=True,
        affected_component="PostgreSQL", recommended_action="Apply vendor security patch immediately.",
    ))

    # --- Additional assets to populate the wider environment ---
    laptop = _asset(db, "J. Rivera - Laptop", AssetType.LAPTOP, owner="J. Rivera",
                     criticality=Criticality.MEDIUM, mfa_enabled=True, authentication_type="sso",
                     permission_level="standard", permission_count=4, operating_system="macOS 15",
                     environment="production", tags="endpoint")
    _rel(db, laptop, email, RelationshipType.ACCESSES, weight=1.0)

    phone = _asset(db, "J. Rivera - Smartphone", AssetType.SMARTPHONE, owner="J. Rivera",
                    criticality=Criticality.LOW, mfa_enabled=True, authentication_type="sso",
                    permission_level="read-only", permission_count=2, operating_system="iOS 18",
                    environment="production", tags="endpoint,mobile")
    _rel(db, phone, email, RelationshipType.ACCESSES, weight=1.0)

    vpn = _asset(db, "Corporate VPN", AssetType.VPN, owner="IT Security",
                 criticality=Criticality.HIGH, mfa_enabled=True, authentication_type="sso",
                 permission_level="standard", permission_count=8, internet_exposed=True,
                 environment="production", tags="network")
    idp = _asset(db, "Identity Provider (SSO)", AssetType.IDENTITY_PROVIDER, owner="IT Security",
                 criticality=Criticality.CRITICAL, mfa_enabled=True, authentication_type="sso",
                 permission_level="admin", permission_count=30, internet_exposed=True,
                 environment="production", tags="identity")
    _rel(db, vpn, idp, RelationshipType.TRUSTS, weight=1.0)
    _rel(db, idp, cloud, RelationshipType.AUTHENTICATES, weight=1.0)
    _rel(db, idp, github, RelationshipType.AUTHENTICATES, weight=1.0)

    api = _asset(db, "Public Customer API", AssetType.API, owner="Platform Team",
                 criticality=Criticality.HIGH, mfa_enabled=False, authentication_type="key",
                 permission_level="write", permission_count=5, internet_exposed=True,
                 environment="production", tags="api,public")
    webapp = _asset(db, "Customer Web Application", AssetType.WEB_APPLICATION, owner="Platform Team",
                     criticality=Criticality.HIGH, mfa_enabled=False, authentication_type="password",
                     permission_level="standard", permission_count=3, internet_exposed=True,
                     environment="production", tags="web,public")
    storage = _asset(db, "Backup Storage Bucket", AssetType.STORAGE_BUCKET, owner="Platform Team",
                      criticality=Criticality.HIGH, mfa_enabled=False, authentication_type="key",
                      permission_level="admin", permission_count=4, internet_exposed=True,
                      environment="production", tags="storage,backup")
    firewall = _asset(db, "Perimeter Firewall", AssetType.FIREWALL, owner="IT Security",
                       criticality=Criticality.HIGH, mfa_enabled=True, authentication_type="sso",
                       permission_level="admin", permission_count=6, environment="production",
                       tags="network,perimeter")
    hr_saas = _asset(db, "HR SaaS Platform", AssetType.SAAS_APPLICATION, owner="People Ops",
                      criticality=Criticality.MEDIUM, mfa_enabled=True, authentication_type="sso",
                      permission_level="standard", permission_count=5, internet_exposed=True,
                      environment="production", tags="saas,hr")
    server1 = _asset(db, "Internal App Server", AssetType.SERVER, owner="Platform Team",
                      criticality=Criticality.MEDIUM, mfa_enabled=True, authentication_type="key",
                      permission_level="standard", permission_count=6, operating_system="Ubuntu 24.04",
                      environment="production", tags="server")
    router = _asset(db, "Core Network Router", AssetType.ROUTER, owner="IT Security",
                     criticality=Criticality.MEDIUM, mfa_enabled=True, authentication_type="password",
                     permission_level="admin", permission_count=3, environment="production", tags="network")

    _rel(db, webapp, api, RelationshipType.DEPENDS_ON, weight=1.0)
    _rel(db, api, database, RelationshipType.STORES_DATA, weight=1.0)
    _rel(db, api, cloud, RelationshipType.HOSTS, weight=1.0)
    _rel(db, cloud, storage, RelationshipType.STORES_DATA, weight=1.0)
    _rel(db, firewall, vpn, RelationshipType.CONNECTS_TO, weight=1.0)
    _rel(db, router, firewall, RelationshipType.CONNECTS_TO, weight=1.0)
    _rel(db, idp, hr_saas, RelationshipType.AUTHENTICATES, weight=1.0)
    _rel(db, server1, database, RelationshipType.CONNECTS_TO, weight=1.0)
    _rel(db, laptop, vpn, RelationshipType.CONNECTS_TO, weight=1.0)
    _rel(db, laptop, server1, RelationshipType.ACCESSES, weight=1.0)

    # --- Extra vulnerabilities across the environment ---
    db.add(Vulnerability(asset_id=api.id, cve_id="CVE-2024-3094", title="Outdated API gateway dependency",
                          severity=Criticality.CRITICAL, cvss_score=9.8, status="open", known_exploited=True,
                          affected_component="API gateway library", recommended_action="Upgrade dependency and redeploy."))
    db.add(Vulnerability(asset_id=webapp.id, cve_id="CVE-2023-4863", title="Web app image library heap overflow",
                          severity=Criticality.HIGH, cvss_score=8.8, status="open", known_exploited=False,
                          affected_component="Image processing library", recommended_action="Patch to latest library version."))
    db.add(Vulnerability(asset_id=storage.id, cve_id=None, title="Publicly readable backup bucket",
                          severity=Criticality.HIGH, cvss_score=7.2, status="open", known_exploited=False,
                          affected_component="Bucket ACL", recommended_action="Restrict bucket policy to internal roles only."))
    db.add(Vulnerability(asset_id=server1.id, cve_id="CVE-2022-0778", title="TLS library infinite loop vulnerability",
                          severity=Criticality.MEDIUM, cvss_score=6.5, status="patched", known_exploited=False,
                          affected_component="OpenSSL", recommended_action="Verify patch deployment across fleet."))
    db.add(Vulnerability(asset_id=router.id, cve_id="CVE-2023-20198", title="Router management interface exposure",
                          severity=Criticality.HIGH, cvss_score=8.1, status="open", known_exploited=True,
                          affected_component="Web management UI", recommended_action="Disable external management access."))

    # --- Security controls ---
    db.add(SecurityControl(name="Multi-Factor Authentication", category="Identity",
                            current_state="partial", risk_reduction_estimate=0.30,
                            priority="high", affected_asset_ids=f"{email.id},{github.id},{database.id},{api.id},{webapp.id}"))
    db.add(SecurityControl(name="Least Privilege Access Review", category="Access Control",
                            current_state="not_implemented", risk_reduction_estimate=0.18,
                            priority="high", affected_asset_ids=f"{github.id},{cloud.id},{database.id}"))
    db.add(SecurityControl(name="Patch Management", category="Vulnerability Management",
                            current_state="partial", risk_reduction_estimate=0.22,
                            priority="critical", affected_asset_ids=f"{database.id},{api.id},{router.id}"))
    db.add(SecurityControl(name="Network Segmentation", category="Network", current_state="partial",
                            risk_reduction_estimate=0.15, priority="medium", affected_asset_ids=f"{server1.id},{database.id}"))
    db.add(SecurityControl(name="Storage Access Policy Hardening", category="Data Protection",
                            current_state="not_implemented", risk_reduction_estimate=0.12,
                            priority="high", affected_asset_ids=storage.id))

    # --- A few recent security events for the dashboard feed ---
    db.add(SecurityEvent(asset_id=github.id, event_type="anomaly", severity=Criticality.MEDIUM,
                          message="Unusual OAuth scope grant detected on GitHub organization account."))
    db.add(SecurityEvent(asset_id=database.id, event_type="vulnerability", severity=Criticality.CRITICAL,
                          message="New critical CVE published affecting Customer Database component."))
    db.add(SecurityEvent(asset_id=api.id, event_type="exposure", severity=Criticality.HIGH,
                          message="Public Customer API flagged for known exploited vulnerability."))
    db.add(SecurityEvent(asset_id=router.id, event_type="configuration", severity=Criticality.HIGH,
                          message="Router management interface reachable from outside the corporate network."))

    db.commit()
    recompute_all(db)
