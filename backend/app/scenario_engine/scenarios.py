"""
Attack Scenario Library.

Per Section 42 of the simulator spec: scenario definitions must be
data, not logic embedded in UI components. Every scenario here is a
plain dataclass describing a SAFE, CONCEPTUAL simulation — no exploit
code, payloads, or operational attack steps are stored or produced
anywhere in this module.

This is intentionally NOT a database table yet (see ARCHITECTURE.md /
"Suggested next steps") — it is a static, versioned catalog that the
simulation engine reads the same way it would read a `scenarios` table,
so promoting it to the database later is a data-migration, not a
redesign.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    category: str  # IDENTITY | APPLICATION | NETWORK | MALWARE | DATA
    description: str
    prerequisites: list[str]
    entry_point_types: list[str]  # asset types this scenario can start from
    affected_asset_types: list[str]  # asset types this scenario can spread to
    impact: list[str]
    risk_level: str  # LOW | MEDIUM | HIGH | CRITICAL
    detection: list[str]
    prevention: list[str]
    mitre_technique_ids: list[str] = field(default_factory=list)


SCENARIOS: dict[str, Scenario] = {}


def _register(s: Scenario) -> None:
    SCENARIOS[s.id] = s


# ---------- IDENTITY ----------

_register(Scenario(
    id="credential_compromise",
    name="Credential Compromise Simulation",
    category="IDENTITY",
    description="Simulates an attacker obtaining a valid credential through a "
                 "conceptual phishing or password-reuse scenario, without any "
                 "real message, payload, or credential involved.",
    prerequisites=["No MFA enforced", "Weak or reused password policy"],
    entry_point_types=["ATTACKER", "THREAT_SOURCE"],
    affected_asset_types=["DESKTOP", "LAPTOP", "EMPLOYEE_PC", "MOBILE"],
    impact=["Account access", "Possible lateral movement", "Cloud exposure"],
    risk_level="HIGH",
    detection=["Authentication anomaly", "Impossible travel", "Unusual login pattern"],
    prevention=["MFA", "Conditional access", "Security awareness training"],
    mitre_technique_ids=["T1078", "T1566"],
))

_register(Scenario(
    id="password_spraying",
    name="Password Spraying Simulation",
    category="IDENTITY",
    description="Simulates a low-and-slow guessing pattern against many accounts, "
                 "represented only as an abstract probability shift — no real "
                 "authentication attempts occur.",
    prerequisites=["No account lockout policy", "No MFA enforced"],
    entry_point_types=["ATTACKER", "THREAT_SOURCE", "BOTNET_SIMULATOR"],
    affected_asset_types=["IDENTITY_PROVIDER", "AUTHENTICATION_SERVER"],
    impact=["Account access", "Credential exposure"],
    risk_level="MEDIUM",
    detection=["Multiple failed logins across accounts", "Login velocity anomaly"],
    prevention=["MFA", "Account lockout policy", "Rate limiting"],
    mitre_technique_ids=["T1110.003"],
))

_register(Scenario(
    id="session_compromise",
    name="Session Compromise Simulation",
    category="IDENTITY",
    description="Simulates the conceptual reuse of a stolen session token, "
                 "represented abstractly with no real token generation or theft.",
    prerequisites=["Long-lived sessions", "No session monitoring"],
    entry_point_types=["ATTACKER", "COMPROMISED_ACCOUNT_SIMULATOR"],
    affected_asset_types=["WEB_SERVER", "API_SERVER", "CLOUD_SERVER"],
    impact=["Unauthorized session use", "Data access"],
    risk_level="MEDIUM",
    detection=["Session anomaly detection", "Device fingerprint mismatch"],
    prevention=["Short session lifetimes", "Session monitoring", "Device binding"],
    mitre_technique_ids=["T1539"],
))

_register(Scenario(
    id="mfa_fatigue",
    name="MFA Fatigue (Push Bombing) Simulation",
    category="IDENTITY",
    description="Simulates the conceptual effect of an attacker repeatedly sending push-based MFA "
                 "prompts until a user approves one out of fatigue, represented only as a state and "
                 "risk change — no real push notifications or authentication attempts occur.",
    prerequisites=["Push-based MFA without number matching", "No prompt rate limiting"],
    entry_point_types=["ATTACKER", "COMPROMISED_ACCOUNT_SIMULATOR"],
    affected_asset_types=["IDENTITY_PROVIDER", "AUTHENTICATION_SERVER", "CLOUD_SERVER"],
    impact=["Account access despite MFA being enabled", "Further lateral movement risk"],
    risk_level="HIGH",
    detection=["Abnormal MFA prompt volume", "Approval after many rapid denials"],
    prevention=["Number-matching MFA", "Prompt rate limiting", "Security awareness training"],
    mitre_technique_ids=["T1621"],
))

_register(Scenario(
    id="privilege_escalation",
    name="Privilege Escalation Simulation",
    category="IDENTITY",
    description="Simulates the conceptual consequence of a standard account reaching admin-level "
                 "permissions through a misconfigured role assignment, without any real permission "
                 "change or exploit code.",
    prerequisites=["Overly permissive role assignment", "No periodic access review"],
    entry_point_types=["COMPROMISED_ACCOUNT_SIMULATOR", "ATTACKER"],
    affected_asset_types=["CLOUD_SERVER", "IDENTITY_PROVIDER", "DATABASE"],
    impact=["Administrative access", "Expanded blast radius", "Potential data exposure"],
    risk_level="CRITICAL",
    detection=["Privilege change audit alert", "New admin role anomaly"],
    prevention=["Least privilege", "Periodic access reviews", "Just-in-time elevation"],
    mitre_technique_ids=["T1078.004", "T1068"],
))

# ---------- APPLICATION ----------

_register(Scenario(
    id="web_app_vulnerability",
    name="Web Application Vulnerability Simulation",
    category="APPLICATION",
    description="Simulates the logical consequence of an unpatched web "
                 "application weakness being present, without any real "
                 "exploit code or payload.",
    prerequisites=["Unpatched vulnerability", "Internet-facing service"],
    entry_point_types=["ATTACKER", "THREAT_SOURCE"],
    affected_asset_types=["WEB_SERVER", "APPLICATION_SERVER", "API_SERVER"],
    impact=["Service disruption", "Data exposure", "Further pivot into network"],
    risk_level="HIGH",
    detection=["WAF alert", "Anomalous request pattern"],
    prevention=["Patch management", "Web application firewall", "Input validation"],
    mitre_technique_ids=["T1190"],
))

_register(Scenario(
    id="api_authorization_failure",
    name="API Authorization Failure Simulation",
    category="APPLICATION",
    description="Simulates the conceptual impact of a broken access-control "
                 "check on an API, without performing any real request.",
    prerequisites=["Missing authorization check", "Excessive API permissions"],
    entry_point_types=["ATTACKER", "COMPROMISED_ACCOUNT_SIMULATOR"],
    affected_asset_types=["API_SERVER", "DATABASE"],
    impact=["Unauthorized data access", "Data exposure"],
    risk_level="HIGH",
    detection=["Unusual API access pattern", "Authorization failure logs"],
    prevention=["Least privilege API scopes", "Authorization testing", "API gateway policy"],
    mitre_technique_ids=["T1190"],
))

_register(Scenario(
    id="misconfiguration_abuse",
    name="Misconfiguration Abuse Simulation",
    category="APPLICATION",
    description="Simulates the effect of a security misconfiguration (e.g. an "
                 "overly permissive setting) being present on an asset.",
    prerequisites=["Default or overly permissive configuration"],
    entry_point_types=["ATTACKER", "THREAT_SOURCE"],
    affected_asset_types=["CLOUD_SERVER", "CLOUD_STORAGE", "DATABASE"],
    impact=["Data exposure", "Unauthorized access"],
    risk_level="MEDIUM",
    detection=["Configuration drift alert", "Cloud posture scan"],
    prevention=["Configuration baselines", "Automated posture management"],
    mitre_technique_ids=["T1078.004"],
))

_register(Scenario(
    id="supply_chain_compromise",
    name="Supply-Chain Compromise Simulation",
    category="APPLICATION",
    description="Simulates the conceptual consequence of a trusted third-party package or vendor "
                 "integration being compromised upstream, without any real dependency, package, or "
                 "vendor system being touched.",
    prerequisites=["Unpinned/unverified third-party dependency", "No software bill of materials review"],
    entry_point_types=["THREAT_SOURCE", "ATTACKER"],
    affected_asset_types=["WEB_SERVER", "APPLICATION_SERVER", "API_SERVER", "CLOUD_SERVER"],
    impact=["Widespread downstream compromise", "Loss of build/deploy integrity"],
    risk_level="CRITICAL",
    detection=["Unexpected dependency change", "Build integrity/signature mismatch"],
    prevention=["Software bill of materials", "Dependency pinning and verification", "Vendor risk review"],
    mitre_technique_ids=["T1195"],
))

# ---------- NETWORK ----------

_register(Scenario(
    id="unauthorized_access",
    name="Unauthorized Access Simulation",
    category="NETWORK",
    description="Simulates an attacker conceptually reaching an internal "
                 "asset through an exposed network path.",
    prerequisites=["Internet-exposed asset", "No network segmentation"],
    entry_point_types=["ATTACKER", "EXTERNAL_NETWORK", "THREAT_SOURCE"],
    affected_asset_types=["ROUTER", "SERVER", "DATABASE"],
    impact=["Network reconnaissance", "Further access"],
    risk_level="MEDIUM",
    detection=["Firewall deny logs", "Network flow anomaly"],
    prevention=["Network segmentation", "Firewall rules", "Zero trust access"],
    mitre_technique_ids=["T1133"],
))

_register(Scenario(
    id="lateral_movement",
    name="Lateral Movement Simulation",
    category="NETWORK",
    description="Simulates an attacker moving conceptually from one "
                 "compromised asset to another via a trusted connection.",
    prerequisites=["Flat network", "Shared credentials across assets"],
    entry_point_types=["COMPROMISED_ACCOUNT_SIMULATOR", "ATTACKER"],
    affected_asset_types=["SERVER", "DATABASE", "CLOUD_SERVER"],
    impact=["Expanded access", "Increased blast radius"],
    risk_level="HIGH",
    detection=["Internal traffic anomaly", "Unusual east-west connections"],
    prevention=["Network segmentation", "Least privilege", "Micro-segmentation"],
    mitre_technique_ids=["T1021"],
))

_register(Scenario(
    id="remote_access_compromise",
    name="Remote Access Compromise Simulation",
    category="NETWORK",
    description="Simulates the conceptual consequence of a remote-access system (VPN or similar) "
                 "being reached with a weak or reused credential, without any real remote connection "
                 "being established.",
    prerequisites=["No MFA on remote access", "Internet-exposed remote access system"],
    entry_point_types=["ATTACKER", "EXTERNAL_NETWORK", "THREAT_SOURCE"],
    affected_asset_types=["ROUTER", "SERVER", "CLOUD_SERVER"],
    impact=["Internal network access", "Foothold for lateral movement"],
    risk_level="HIGH",
    detection=["Remote access login anomaly", "Impossible travel on VPN login"],
    prevention=["MFA on remote access", "Conditional access", "Least privilege VPN scoping"],
    mitre_technique_ids=["T1133", "T1078"],
))

# ---------- MALWARE ----------

_register(Scenario(
    id="malware_delivery",
    name="Malware Delivery Simulation",
    category="MALWARE",
    description="Simulates the logical consequence of a malicious attachment "
                 "being opened. No real file, script, or payload of any kind "
                 "is created or transmitted at any point.",
    prerequisites=["No email filtering", "No endpoint protection"],
    entry_point_types=["ATTACKER", "MALICIOUS_DOCUMENT_SIMULATOR"],
    affected_asset_types=["DESKTOP", "LAPTOP", "EMPLOYEE_PC"],
    impact=["Endpoint compromise", "Potential lateral movement"],
    risk_level="HIGH",
    detection=["EDR alert", "Unusual process behavior"],
    prevention=["Email filtering", "Endpoint detection and response", "User training"],
    mitre_technique_ids=["T1566.001"],
))

_register(Scenario(
    id="ransomware_impact",
    name="Ransomware Impact Simulation",
    category="MALWARE",
    description="Simulates the conceptual availability impact of a "
                 "ransomware-style event on connected assets — a state "
                 "change only, never real file encryption of any kind.",
    prerequisites=["Malware delivery succeeded", "No backup isolation"],
    entry_point_types=["MALICIOUS_DOCUMENT_SIMULATOR", "COMPROMISED_ACCOUNT_SIMULATOR"],
    affected_asset_types=["SERVER", "DATABASE", "DESKTOP", "LAPTOP"],
    impact=["Availability loss", "Data integrity concern", "Operational disruption"],
    risk_level="CRITICAL",
    detection=["Mass file-state change alert", "Backup anomaly"],
    prevention=["Immutable backups", "Network segmentation", "Endpoint protection"],
    mitre_technique_ids=["T1486"],
))

_register(Scenario(
    id="trojan_behavior",
    name="Trojan Behavior Simulation",
    category="MALWARE",
    description="Simulates a conceptual persistent foothold on an endpoint, "
                 "represented only as a state and risk change.",
    prerequisites=["Malware delivery succeeded", "No endpoint monitoring"],
    entry_point_types=["MALICIOUS_DOCUMENT_SIMULATOR"],
    affected_asset_types=["DESKTOP", "LAPTOP", "SERVER"],
    impact=["Persistent access risk", "Data exfiltration risk"],
    risk_level="HIGH",
    detection=["Endpoint behavioral analytics", "Unusual outbound connections"],
    prevention=["Endpoint detection and response", "Application allowlisting"],
    mitre_technique_ids=["T1204"],
))

# ---------- DATA ----------

_register(Scenario(
    id="data_exposure",
    name="Data Exposure Simulation",
    category="DATA",
    description="Simulates the conceptual consequence of sensitive data "
                 "becoming reachable due to an upstream compromise.",
    prerequisites=["Upstream asset compromised", "No data classification controls"],
    entry_point_types=["COMPROMISED_ACCOUNT_SIMULATOR", "ATTACKER"],
    affected_asset_types=["DATABASE", "CLOUD_STORAGE"],
    impact=["Sensitive data exposure", "Compliance risk"],
    risk_level="CRITICAL",
    detection=["Data loss prevention alert", "Unusual data access volume"],
    prevention=["Data classification", "Encryption at rest", "Access reviews"],
    mitre_technique_ids=["T1530"],
))

_register(Scenario(
    id="unauthorized_db_access",
    name="Unauthorized Database Access Simulation",
    category="DATA",
    description="Simulates the conceptual consequence of a database being "
                 "reachable without adequate access controls.",
    prerequisites=["Excessive database permissions", "No query monitoring"],
    entry_point_types=["ATTACKER", "COMPROMISED_ACCOUNT_SIMULATOR"],
    affected_asset_types=["DATABASE"],
    impact=["Data exposure", "Data integrity concern"],
    risk_level="CRITICAL",
    detection=["Database activity monitoring", "Anomalous query pattern"],
    prevention=["Least privilege database roles", "Query monitoring", "Encryption"],
    mitre_technique_ids=["T1530"],
))


def list_scenarios(category: str | None = None) -> list[Scenario]:
    values = list(SCENARIOS.values())
    if category:
        values = [s for s in values if s.category == category]
    return values


def get_scenario(scenario_id: str) -> Scenario | None:
    return SCENARIOS.get(scenario_id)


def scenarios_for_entry_point(component_type: str) -> list[Scenario]:
    return [s for s in SCENARIOS.values() if component_type in s.entry_point_types]
