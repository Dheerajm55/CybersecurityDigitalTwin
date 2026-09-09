"""
Simulator component catalog.

Purely descriptive data for the "+ Add Component" palette (Section 4).
Nothing here is executable — it's metadata the frontend renders into a
dropdown, and that the simulation engine uses to validate topologies
(e.g. "can THREAT_SOURCE be a valid entry point for this scenario?").

THREAT category components are explicitly simulation abstractions —
see the docstring on each one. None of them represent real malware,
exploit code, or attack infrastructure.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ComponentType:
    id: str
    label: str
    category: str  # NETWORK | APPLICATION | CLOUD | ENDPOINT | SECURITY | THREAT
    side: str  # ATTACK | DEFENSE
    icon: str  # lucide-react icon name, resolved client-side
    default_criticality: str = "MEDIUM"
    is_defense_control: bool = False  # true for firewall/MFA/etc. — used by the rules engine


COMPONENT_CATALOG: list[ComponentType] = [
    # ---------- NETWORK ----------
    ComponentType("COMPUTER", "Computer", "NETWORK", "DEFENSE", "monitor"),
    ComponentType("LAPTOP", "Laptop", "NETWORK", "DEFENSE", "laptop"),
    ComponentType("SERVER", "Server", "NETWORK", "DEFENSE", "server", "HIGH"),
    ComponentType("ROUTER", "Router", "NETWORK", "DEFENSE", "router"),
    ComponentType("SWITCH", "Switch", "NETWORK", "DEFENSE", "network"),
    ComponentType("FIREWALL", "Firewall", "NETWORK", "DEFENSE", "shield", "HIGH", is_defense_control=True),
    ComponentType("VPN", "VPN", "NETWORK", "DEFENSE", "lock", is_defense_control=True),
    ComponentType("ACCESS_POINT", "Access Point", "NETWORK", "DEFENSE", "wifi"),

    # ---------- APPLICATION ----------
    ComponentType("WEB_SERVER", "Web Server", "APPLICATION", "DEFENSE", "globe", "HIGH"),
    ComponentType("API_SERVER", "API Server", "APPLICATION", "DEFENSE", "plug", "HIGH"),
    ComponentType("DATABASE", "Database", "APPLICATION", "DEFENSE", "database", "CRITICAL"),
    ComponentType("APPLICATION_SERVER", "Application Server", "APPLICATION", "DEFENSE", "server", "HIGH"),
    ComponentType("DNS_SERVER", "DNS Server", "APPLICATION", "DEFENSE", "globe"),
    ComponentType("MAIL_SERVER", "Mail Server", "APPLICATION", "DEFENSE", "mail", "HIGH"),

    # ---------- CLOUD ----------
    ComponentType("CLOUD_SERVER", "Cloud Server", "CLOUD", "DEFENSE", "cloud", "HIGH"),
    ComponentType("CLOUD_STORAGE", "Cloud Storage", "CLOUD", "DEFENSE", "cloud", "HIGH"),
    ComponentType("CLOUD_DATABASE", "Cloud Database", "CLOUD", "DEFENSE", "database", "CRITICAL"),
    ComponentType("IDENTITY_PROVIDER", "Identity Provider", "CLOUD", "DEFENSE", "key", "CRITICAL"),

    # ---------- ENDPOINT ----------
    ComponentType("DESKTOP", "Desktop", "ENDPOINT", "DEFENSE", "monitor"),
    ComponentType("EMPLOYEE_PC", "Employee PC", "ENDPOINT", "DEFENSE", "monitor"),
    ComponentType("MOBILE", "Mobile", "ENDPOINT", "DEFENSE", "smartphone"),
    ComponentType("IOT_DEVICE", "IoT Device", "ENDPOINT", "DEFENSE", "cpu"),

    # ---------- SECURITY ----------
    ComponentType("SECURITY_FIREWALL", "Firewall", "SECURITY", "DEFENSE", "shield", "HIGH", is_defense_control=True),
    ComponentType("IDS", "IDS", "SECURITY", "DEFENSE", "radar", is_defense_control=True),
    ComponentType("IPS", "IPS", "SECURITY", "DEFENSE", "shield-alert", is_defense_control=True),
    ComponentType("SIEM", "SIEM", "SECURITY", "DEFENSE", "activity", is_defense_control=True),
    ComponentType("AUTHENTICATION_SERVER", "Authentication Server", "SECURITY", "DEFENSE", "key", "HIGH", is_defense_control=True),

    # ---------- THREAT (simulation abstractions only) ----------
    ComponentType("ATTACKER", "Attacker", "THREAT", "ATTACK", "user-x"),
    ComponentType("THREAT_SOURCE", "Threat Source", "THREAT", "ATTACK", "alert-triangle"),
    ComponentType("EXTERNAL_NETWORK", "External Network", "THREAT", "ATTACK", "globe"),
    ComponentType("BOTNET_SIMULATOR", "Botnet Simulator", "THREAT", "ATTACK", "network"),
    ComponentType("MALICIOUS_DOCUMENT_SIMULATOR", "Malicious Document Simulator", "THREAT", "ATTACK", "file-warning"),
    ComponentType("COMPROMISED_ACCOUNT_SIMULATOR", "Compromised Account Simulator", "THREAT", "ATTACK", "user-x"),
]

CATALOG_BY_ID = {c.id: c for c in COMPONENT_CATALOG}


def get_component_type(component_type_id: str) -> ComponentType | None:
    return CATALOG_BY_ID.get(component_type_id)


# Additional standalone defense controls a user can apply via "Apply Defense"
# (Section 13/14) that aren't necessarily placed as their own node.
DEFENSE_CONTROLS = [
    {"id": "MFA", "label": "Enable MFA", "category": "Identity"},
    {"id": "LEAST_PRIVILEGE", "label": "Apply least privilege", "category": "Access Control"},
    {"id": "NETWORK_SEGMENTATION", "label": "Network segmentation", "category": "Network"},
    {"id": "FIREWALL_RULE", "label": "Enable firewall rule", "category": "Network"},
    {"id": "MONITORING", "label": "Improve endpoint monitoring", "category": "Detection"},
    {"id": "SESSION_REVIEW", "label": "Disable unused sessions", "category": "Identity"},
    {"id": "CREDENTIAL_ROTATION", "label": "Rotate affected credentials", "category": "Identity"},
]
