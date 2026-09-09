export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface Asset {
  id: string;
  name: string;
  asset_type: string;
  owner?: string | null;
  criticality: string;
  hostname?: string | null;
  operating_system?: string | null;
  environment: string;
  internet_exposed: boolean;
  mfa_enabled: boolean;
  authentication_type: string;
  permission_level: string;
  permission_count: number;
  tags?: string | null;
  description?: string | null;
  risk_score: number;
  risk_class: string;
  created_at: string;
  updated_at: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  criticality: string;
  risk_score: number;
  risk_class: string;
  mfa_enabled: boolean;
  internet_exposed: boolean;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  weight: number;
}

export interface DigitalTwinGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DashboardSummary {
  total_assets: number;
  high_risk_assets: number;
  critical_vulnerabilities: number;
  attack_path_count: number;
  security_score: number;
  risk_distribution: Record<string, number>;
  active_threats: number;
  events_per_min: number;
}

export interface Vulnerability {
  id: string;
  asset_id: string;
  cve_id?: string | null;
  title: string;
  severity: string;
  cvss_score?: number | null;
  status: string;
  known_exploited: boolean;
  affected_component?: string | null;
  recommended_action?: string | null;
  created_at: string;
}

export interface RiskFactor {
  factor: string;
  detail: string;
  weight: number;
}

export interface AssetRiskDetail {
  asset_id: string;
  name: string;
  risk_score: number;
  risk_class: string;
  factors: RiskFactor[];
}

export interface MLPrediction {
  model: string;
  risk_probability: number | null;
  risk_level: string | null;
  error: string | null;
}

export interface AssetMLRiskPrediction {
  asset_id: string;
  asset_name: string;
  deterministic_risk: number;
  deterministic_risk_class: string;
  ml_predictions: Record<string, MLPrediction>;
  ensemble_probability: number | null;
  ensemble_risk_level: string | null;
  model_agreement: string;
  dataset_label: string | null;
  ml_status: "available" | "partially_available" | "unavailable";
}

export interface AttackPathStep {
  asset_id: string;
  name: string;
  asset_type: string;
}

export interface AttackPath {
  path: AttackPathStep[];
  risk_score: number;
  risk_class: string;
  explanation: string[];
}

export interface SecurityControlSummary {
  id: string;
  name: string;
  category: string;
  current_state: string;
  risk_reduction_estimate: number;
  priority: string;
  affected_asset_count: number;
}

export interface SecurityEventItem {
  id: string;
  asset_id?: string | null;
  asset_name: string;
  event_type: string;
  severity: string;
  message: string;
  created_at: string;
}

export interface SimulationResult {
  action: string;
  asset_id: string;
  risk_before: number;
  risk_after: number;
  risk_reduction: number;
  explanation: string;
}
