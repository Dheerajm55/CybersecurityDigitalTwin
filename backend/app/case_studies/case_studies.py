"""
Real-World Security Cases.

Educational, high-level case studies only. No exploit instructions,
payloads, or operational attack detail — each entry is a summary of
publicly reported incidents plus the general security lesson learned,
with a source pointer for further reading. This module is static
reference data, not fetched or scraped at runtime.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseStudy:
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
    # Which synthetic simulator scenario this case maps to for "Recreate as Safe Simulation"
    recreate_scenario_id: str


CASE_STUDIES: dict[str, CaseStudy] = {}


def _register(c: CaseStudy) -> None:
    CASE_STUDIES[c.id] = c


_register(CaseStudy(
    id="case_phishing_credential_compromise",
    title="Enterprise Credential Compromise via Phishing",
    year=2023,
    attack_category="Identity / Phishing",
    affected_sector="General enterprise",
    attack_chain_summary=[
        "Employee received a deceptive message impersonating a trusted service.",
        "Employee entered credentials on a fraudulent page.",
        "Attacker used the credential to access cloud and email services.",
        "Lack of MFA allowed the session to proceed without a second factor.",
    ],
    impact="Unauthorized access to email and cloud resources; potential exposure of internal data.",
    security_lesson="Multi-factor authentication and conditional access substantially reduce the "
                     "blast radius of a single compromised password, and security-awareness training "
                     "reduces the odds of the initial click.",
    preventive_controls=["MFA", "Conditional access", "Security awareness training", "Email filtering"],
    sources=["CISA — Phishing guidance: https://www.cisa.gov/topics/cyber-threats-and-advisories/phishing"],
    recreate_scenario_id="credential_compromise",
))

_register(CaseStudy(
    id="case_ransomware_availability_impact",
    title="Ransomware-Driven Operational Disruption",
    year=2021,
    attack_category="Malware / Ransomware",
    affected_sector="Critical infrastructure",
    attack_chain_summary=[
        "Initial access gained through a compromised credential on a remote-access system.",
        "Attacker moved laterally due to flat network architecture.",
        "Ransomware-style impact disrupted operational systems.",
        "Organization proactively took systems offline to contain the impact.",
    ],
    impact="Multi-day operational disruption and significant recovery cost.",
    security_lesson="Network segmentation, immutable backups, and strong remote-access controls "
                     "(including MFA) are consistently cited as the highest-leverage mitigations "
                     "against this attack pattern.",
    preventive_controls=["MFA on remote access", "Network segmentation", "Immutable backups", "Incident response plan"],
    sources=["CISA — Ransomware guidance: https://www.cisa.gov/stopransomware"],
    recreate_scenario_id="ransomware_impact",
))

_register(CaseStudy(
    id="case_cloud_misconfiguration_exposure",
    title="Cloud Storage Misconfiguration Data Exposure",
    year=2022,
    attack_category="Application / Misconfiguration",
    affected_sector="Technology / SaaS",
    attack_chain_summary=[
        "A cloud storage resource was configured with overly permissive access.",
        "The exposure was identified through routine or external security research rather than exploitation.",
        "Sensitive records were reachable without authentication.",
    ],
    impact="Potential exposure of customer or internal data; regulatory and reputational impact.",
    security_lesson="Automated cloud security posture management and configuration baselines catch "
                     "this class of issue before it becomes exploitable.",
    preventive_controls=["Cloud security posture management", "Configuration baselines", "Least privilege access policies"],
    sources=["OWASP — Cloud security guidance: https://owasp.org/www-project-cloud-security/"],
    recreate_scenario_id="misconfiguration_abuse",
))

_register(CaseStudy(
    id="case_api_broken_access_control",
    title="API Broken Access Control Data Exposure",
    year=2023,
    attack_category="Application / API",
    affected_sector="Technology",
    attack_chain_summary=[
        "An API endpoint failed to properly verify that the requester was authorized for the requested record.",
        "Sequential or predictable identifiers allowed enumeration of records belonging to other users.",
        "No anomaly detection flagged the high-volume access pattern in time.",
    ],
    impact="Exposure of records beyond what any single user should have been able to access.",
    security_lesson="Broken access control remains one of the most common root causes in public "
                     "API incidents; explicit authorization checks per-object, not just per-endpoint, "
                     "are essential.",
    preventive_controls=["Per-object authorization checks", "Rate limiting", "API access monitoring"],
    sources=["OWASP API Security Top 10: https://owasp.org/www-project-api-security/"],
    recreate_scenario_id="api_authorization_failure",
))


_register(CaseStudy(
    id="case_password_spraying_identity_provider",
    title="Password Spraying Against a Cloud Identity Provider",
    year=2023,
    attack_category="Identity / Credential Guessing",
    affected_sector="General enterprise",
    attack_chain_summary=[
        "Attacker attempted a small number of common passwords against many accounts, staying below "
        "per-account lockout thresholds.",
        "No MFA was enforced on the targeted accounts.",
        "A small number of accounts using weak or reused passwords were accessed.",
    ],
    impact="Unauthorized access to a handful of accounts; no confirmed downstream compromise after "
           "the activity was detected.",
    security_lesson="Password spraying is designed to evade traditional lockout policies; MFA and "
                     "risk-based/conditional access catch what lockout policy alone misses.",
    preventive_controls=["MFA", "Conditional access", "Account lockout policy", "Login velocity monitoring"],
    sources=["CISA — Identity guidance: https://www.cisa.gov/topics/cyber-threats-and-advisories"],
    recreate_scenario_id="password_spraying",
))

_register(CaseStudy(
    id="case_mfa_fatigue_push_bombing",
    title="MFA Fatigue via Repeated Push Notifications",
    year=2022,
    attack_category="Identity / MFA Bypass",
    affected_sector="Technology",
    attack_chain_summary=[
        "Attacker already held a valid password for a target account.",
        "Attacker triggered a high volume of push-based MFA prompts in a short window.",
        "The targeted user approved a prompt out of fatigue or confusion.",
    ],
    impact="Authenticated access to an account despite MFA being enabled.",
    security_lesson="Push-based MFA without number matching or rate limiting can be worn down; "
                     "number-matching MFA and prompt throttling close this gap.",
    preventive_controls=["Number-matching MFA", "Prompt rate limiting", "Security awareness training"],
    sources=["CISA — Phishing-resistant MFA: https://www.cisa.gov/resources-tools/resources/phishing-resistant-mfa"],
    recreate_scenario_id="mfa_fatigue",
))

_register(CaseStudy(
    id="case_session_hijacking_token_theft",
    title="Session Hijacking via Long-Lived Token Reuse",
    year=2023,
    attack_category="Identity / Session Management",
    affected_sector="Technology / SaaS",
    attack_chain_summary=[
        "A long-lived session token was exposed through an insecure storage or logging pathway.",
        "No device binding or session anomaly detection was in place.",
        "The token was reused from a different device/location without triggering re-authentication.",
    ],
    impact="Unauthorized session use, allowing continued access without needing the original password.",
    security_lesson="Short session lifetimes, device binding, and session anomaly detection reduce the "
                     "value of a stolen token to an attacker.",
    preventive_controls=["Short session lifetimes", "Session monitoring", "Device binding"],
    sources=["OWASP — Session Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html"],
    recreate_scenario_id="session_compromise",
))

_register(CaseStudy(
    id="case_privilege_escalation_admin_takeover",
    title="Privilege Escalation via Misconfigured Role Assignment",
    year=2023,
    attack_category="Identity / Privilege Escalation",
    affected_sector="Technology",
    attack_chain_summary=[
        "A standard account was inadvertently assigned an overly broad administrative role.",
        "No periodic access review caught the excess privilege.",
        "The account's elevated access was used to reach sensitive systems.",
    ],
    impact="Administrative-level access obtained without a corresponding administrative need.",
    security_lesson="Least-privilege role design and periodic access reviews are the most direct "
                     "mitigations against silent privilege creep.",
    preventive_controls=["Least privilege", "Periodic access reviews", "Just-in-time elevation"],
    sources=["NIST — Access Control guidance: https://csrc.nist.gov/topics/security-and-privacy/access-control"],
    recreate_scenario_id="privilege_escalation",
))

_register(CaseStudy(
    id="case_web_app_vulnerability_exploitation",
    title="Unpatched Web Application Vulnerability Exploitation",
    year=2023,
    attack_category="Application / Web Vulnerability",
    affected_sector="Technology",
    attack_chain_summary=[
        "A publicly known vulnerability in a web application component remained unpatched.",
        "The internet-facing service was reachable without a compensating control such as a WAF rule.",
        "The vulnerability's logical consequence resulted in service disruption or data exposure risk.",
    ],
    impact="Service disruption and elevated risk of further pivot into connected systems.",
    security_lesson="Timely patch management combined with a web application firewall provides layered "
                     "protection while a permanent fix is rolled out.",
    preventive_controls=["Patch management", "Web application firewall", "Input validation"],
    sources=["OWASP Top 10: https://owasp.org/www-project-top-ten/"],
    recreate_scenario_id="web_app_vulnerability",
))

_register(CaseStudy(
    id="case_supply_chain_compromise",
    title="Compromise via a Trusted Third-Party Dependency",
    year=2024,
    attack_category="Application / Supply Chain",
    affected_sector="Technology",
    attack_chain_summary=[
        "A widely used third-party software dependency was compromised upstream of the organization.",
        "The dependency was pulled into a build without pinning or integrity verification.",
        "The compromised code executed with the trust level of the application it was bundled into.",
    ],
    impact="Potential widespread downstream compromise across every deployment using the affected build.",
    security_lesson="A software bill of materials, dependency pinning, and build-integrity verification "
                     "reduce blind trust in upstream software.",
    preventive_controls=["Software bill of materials", "Dependency pinning and verification", "Vendor risk review"],
    sources=["CISA — Software supply chain guidance: https://www.cisa.gov/supply-chain"],
    recreate_scenario_id="supply_chain_compromise",
))

_register(CaseStudy(
    id="case_lateral_movement_flat_network",
    title="Lateral Movement Across a Flat Network",
    year=2022,
    attack_category="Network / Lateral Movement",
    affected_sector="Critical infrastructure",
    attack_chain_summary=[
        "An initial foothold was established on a single endpoint.",
        "A flat network with shared local credentials allowed movement to adjacent systems.",
        "The attacker reached progressively higher-value assets without crossing a segmentation boundary.",
    ],
    impact="Expanded access well beyond the original point of compromise.",
    security_lesson="Network segmentation and least-privilege credential scoping are the highest-leverage "
                     "controls against lateral spread once a single host is compromised.",
    preventive_controls=["Network segmentation", "Least privilege", "Micro-segmentation"],
    sources=["CISA — Network segmentation guidance: https://www.cisa.gov/resources-tools/resources/layering-network-security-segmentation"],
    recreate_scenario_id="lateral_movement",
))

_register(CaseStudy(
    id="case_network_intrusion_unsegmented_perimeter",
    title="Network Intrusion via an Exposed Internal Path",
    year=2023,
    attack_category="Network / Intrusion",
    affected_sector="General enterprise",
    attack_chain_summary=[
        "An internal system was reachable from the internet with no network segmentation in place.",
        "The exposed path allowed reconnaissance of internal network structure.",
        "Further access attempts followed the identified path toward internal servers.",
    ],
    impact="Internal network reconnaissance and a foothold for further compromise attempts.",
    security_lesson="Zero-trust network access and firewall rules that deny-by-default significantly "
                     "shrink the exposed attack surface.",
    preventive_controls=["Network segmentation", "Firewall rules", "Zero trust access"],
    sources=["CISA — Zero trust maturity model: https://www.cisa.gov/zero-trust-maturity-model"],
    recreate_scenario_id="unauthorized_access",
))

_register(CaseStudy(
    id="case_remote_access_compromise_vpn",
    title="Remote-Access System Compromise via Weak Credentials",
    year=2021,
    attack_category="Network / Remote Access",
    affected_sector="Critical infrastructure",
    attack_chain_summary=[
        "A remote-access system was reachable from the internet without MFA enforced.",
        "A weak or reused credential allowed a successful remote logon.",
        "The resulting access served as a foothold for further internal movement.",
    ],
    impact="Unauthorized internal network access originating from a remote-access entry point.",
    security_lesson="MFA on every remote-access path, combined with conditional access policies, "
                     "closes one of the most consistently abused entry points.",
    preventive_controls=["MFA on remote access", "Conditional access", "Least privilege VPN scoping"],
    sources=["CISA — Remote access security: https://www.cisa.gov/resources-tools/resources/remote-access-security"],
    recreate_scenario_id="remote_access_compromise",
))

_register(CaseStudy(
    id="case_trojan_persistent_foothold",
    title="Persistent Endpoint Foothold via Trojanized Software",
    year=2022,
    attack_category="Malware / Endpoint",
    affected_sector="General enterprise",
    attack_chain_summary=[
        "A malicious document or trojanized installer was opened on an endpoint.",
        "No endpoint detection and response was in place to flag the resulting process behavior.",
        "The foothold persisted, creating an ongoing data exfiltration and lateral movement risk.",
    ],
    impact="Persistent unauthorized access risk on the affected endpoint.",
    security_lesson="Endpoint detection and response plus application allowlisting are the most direct "
                     "controls against a persistent endpoint foothold.",
    preventive_controls=["Endpoint detection and response", "Application allowlisting"],
    sources=["CISA — Malware guidance: https://www.cisa.gov/topics/cyber-threats-and-advisories/malware-phishing-and-ransomware"],
    recreate_scenario_id="trojan_behavior",
))

_register(CaseStudy(
    id="case_public_storage_exposure",
    title="Publicly Reachable Cloud Storage Exposure",
    year=2022,
    attack_category="Cloud / Data Exposure",
    affected_sector="Technology / SaaS",
    attack_chain_summary=[
        "A cloud storage resource was configured to allow public or overly broad access.",
        "No data classification control flagged the sensitivity of the stored records.",
        "The resource remained reachable without authentication until the exposure was found.",
    ],
    impact="Potential exposure of records to anyone with the resource's address.",
    security_lesson="Data classification combined with automated cloud security posture management "
                     "catches this class of issue before it becomes exploitable.",
    preventive_controls=["Data classification", "Encryption at rest", "Cloud security posture management"],
    sources=["OWASP — Cloud security guidance: https://owasp.org/www-project-cloud-security/"],
    recreate_scenario_id="data_exposure",
))

_register(CaseStudy(
    id="case_data_exfiltration_excessive_permissions",
    title="Data Exfiltration Enabled by Excessive Database Permissions",
    year=2023,
    attack_category="Cloud / Data Exfiltration",
    affected_sector="Technology",
    attack_chain_summary=[
        "A service account held far broader database permissions than its function required.",
        "No query monitoring flagged an unusual, high-volume read pattern.",
        "The excess access was used to read and exfiltrate more data than any legitimate use required.",
    ],
    impact="Data exposure beyond what any single legitimate workload should have been able to access.",
    security_lesson="Least-privilege database roles and query/activity monitoring limit both the "
                     "likelihood and the blast radius of this pattern.",
    preventive_controls=["Least privilege database roles", "Query monitoring", "Encryption"],
    sources=["OWASP — Data protection guidance: https://owasp.org/www-project-top-ten/"],
    recreate_scenario_id="unauthorized_db_access",
))


def list_case_studies() -> list[CaseStudy]:
    return list(CASE_STUDIES.values())


def get_case_study(case_id: str) -> CaseStudy | None:
    return CASE_STUDIES.get(case_id)
