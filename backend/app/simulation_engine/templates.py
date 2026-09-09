"""
Environment Templates (Section 33/34).

Predefined, entirely synthetic starting topologies the user can load
into the simulator workspace. Positions are simple grid coordinates the
frontend can lay out immediately without needing a layout algorithm.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TemplateNode:
    id: str
    type: str
    name: str
    x: int
    y: int
    criticality: str = "MEDIUM"


@dataclass(frozen=True)
class TemplateEdge:
    source: str
    target: str


@dataclass(frozen=True)
class EnvironmentTemplate:
    id: str
    name: str
    description: str
    nodes: list[TemplateNode]
    edges: list[TemplateEdge]


def _t(id_, type_, name, x, y, crit="MEDIUM"):
    return TemplateNode(id_, type_, name, x, y, crit)


TEMPLATES: dict[str, EnvironmentTemplate] = {}


def _register(t: EnvironmentTemplate) -> None:
    TEMPLATES[t.id] = t


_register(EnvironmentTemplate(
    id="college_network",
    name="College Network",
    description="A typical campus network: internet-facing perimeter, student and "
                 "faculty endpoints, and a central database.",
    nodes=[
        _t("attacker", "ATTACKER", "External Attacker", 0, 2),
        _t("firewall", "FIREWALL", "Perimeter Firewall", 1, 2, "HIGH"),
        _t("router", "ROUTER", "Core Router", 2, 2),
        _t("student_pc", "DESKTOP", "Student Device", 3, 1),
        _t("faculty_pc", "LAPTOP", "Faculty System", 3, 3, "HIGH"),
        _t("db", "DATABASE", "Student Records Database", 4, 2, "CRITICAL"),
    ],
    edges=[
        TemplateEdge("attacker", "firewall"),
        TemplateEdge("firewall", "router"),
        TemplateEdge("router", "student_pc"),
        TemplateEdge("router", "faculty_pc"),
        TemplateEdge("faculty_pc", "db"),
    ],
))

_register(EnvironmentTemplate(
    id="cloud_environment",
    name="Cloud Environment",
    description="A cloud-hosted web application: load-balanced web tier, API layer, "
                 "and managed database.",
    nodes=[
        _t("attacker", "ATTACKER", "External Attacker", 0, 2),
        _t("firewall", "FIREWALL", "Cloud Firewall", 1, 2, "HIGH"),
        _t("web", "WEB_SERVER", "Web Server", 2, 2, "HIGH"),
        _t("api", "API_SERVER", "API Server", 3, 2, "HIGH"),
        _t("db", "CLOUD_DATABASE", "Cloud Database", 4, 2, "CRITICAL"),
    ],
    edges=[
        TemplateEdge("attacker", "firewall"),
        TemplateEdge("firewall", "web"),
        TemplateEdge("web", "api"),
        TemplateEdge("api", "db"),
    ],
))

_register(EnvironmentTemplate(
    id="iot_environment",
    name="IoT Environment",
    description="A connected-device environment: gateway, IoT devices, and a cloud "
                 "controller.",
    nodes=[
        _t("attacker", "ATTACKER", "External Attacker", 0, 2),
        _t("gateway", "ROUTER", "IoT Gateway", 1, 2),
        _t("iot1", "IOT_DEVICE", "Sensor Device A", 2, 1),
        _t("iot2", "IOT_DEVICE", "Sensor Device B", 2, 3),
        _t("controller", "APPLICATION_SERVER", "Controller", 3, 2, "HIGH"),
        _t("cloud", "CLOUD_SERVER", "Cloud Platform", 4, 2, "HIGH"),
    ],
    edges=[
        TemplateEdge("attacker", "gateway"),
        TemplateEdge("gateway", "iot1"),
        TemplateEdge("gateway", "iot2"),
        TemplateEdge("iot1", "controller"),
        TemplateEdge("iot2", "controller"),
        TemplateEdge("controller", "cloud"),
    ],
))

_register(EnvironmentTemplate(
    id="personal_network",
    name="Personal Network",
    description="A home network: router, personal devices, and a home cloud backup.",
    nodes=[
        _t("attacker", "ATTACKER", "External Attacker", 0, 2),
        _t("router", "ROUTER", "Home Router", 1, 2),
        _t("laptop", "LAPTOP", "Personal Laptop", 2, 1),
        _t("mobile", "MOBILE", "Mobile Phone", 2, 3),
        _t("cloud", "CLOUD_STORAGE", "Cloud Backup", 3, 2, "HIGH"),
    ],
    edges=[
        TemplateEdge("attacker", "router"),
        TemplateEdge("router", "laptop"),
        TemplateEdge("router", "mobile"),
        TemplateEdge("laptop", "cloud"),
    ],
))

_register(EnvironmentTemplate(
    id="enterprise_network",
    name="Enterprise Network",
    description="A layered enterprise network: perimeter, employee endpoints, "
                 "identity provider, and internal database.",
    nodes=[
        _t("attacker", "ATTACKER", "External Attacker", 0, 2),
        _t("firewall", "FIREWALL", "Perimeter Firewall", 1, 2, "HIGH"),
        _t("employee_pc", "EMPLOYEE_PC", "Employee PC", 2, 1),
        _t("idp", "IDENTITY_PROVIDER", "Identity Provider", 2, 3, "CRITICAL"),
        _t("app_server", "APPLICATION_SERVER", "Application Server", 3, 2, "HIGH"),
        _t("db", "DATABASE", "Customer Database", 4, 2, "CRITICAL"),
    ],
    edges=[
        TemplateEdge("attacker", "firewall"),
        TemplateEdge("firewall", "employee_pc"),
        TemplateEdge("employee_pc", "idp"),
        TemplateEdge("idp", "app_server"),
        TemplateEdge("app_server", "db"),
    ],
))

_register(EnvironmentTemplate(
    id="healthcare_environment",
    name="Healthcare Environment",
    description="A clinical network: workstation, records system, and a patient "
                 "database subject to strict confidentiality requirements.",
    nodes=[
        _t("attacker", "ATTACKER", "External Attacker", 0, 2),
        _t("firewall", "FIREWALL", "Perimeter Firewall", 1, 2, "HIGH"),
        _t("workstation", "DESKTOP", "Clinical Workstation", 2, 2),
        _t("records", "APPLICATION_SERVER", "Records System", 3, 2, "HIGH"),
        _t("db", "DATABASE", "Patient Database", 4, 2, "CRITICAL"),
    ],
    edges=[
        TemplateEdge("attacker", "firewall"),
        TemplateEdge("firewall", "workstation"),
        TemplateEdge("workstation", "records"),
        TemplateEdge("records", "db"),
    ],
))

_register(EnvironmentTemplate(
    id="banking_environment",
    name="Banking Environment",
    description="A financial services network: hardened perimeter, teller "
                 "workstation, core banking application, and transaction database.",
    nodes=[
        _t("attacker", "ATTACKER", "External Attacker", 0, 2),
        _t("firewall", "FIREWALL", "Hardened Perimeter Firewall", 1, 2, "HIGH"),
        _t("workstation", "DESKTOP", "Teller Workstation", 2, 2),
        _t("core_app", "APPLICATION_SERVER", "Core Banking Application", 3, 2, "CRITICAL"),
        _t("db", "DATABASE", "Transaction Database", 4, 2, "CRITICAL"),
    ],
    edges=[
        TemplateEdge("attacker", "firewall"),
        TemplateEdge("firewall", "workstation"),
        TemplateEdge("workstation", "core_app"),
        TemplateEdge("core_app", "db"),
    ],
))


def list_templates() -> list[EnvironmentTemplate]:
    return list(TEMPLATES.values())


def get_template(template_id: str) -> EnvironmentTemplate | None:
    return TEMPLATES.get(template_id)
