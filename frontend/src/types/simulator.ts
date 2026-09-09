export interface ComponentTypeDef {
  id: string;
  label: string;
  category: string;
  side: "ATTACK" | "DEFENSE";
  icon: string;
  default_criticality: string;
  is_defense_control: boolean;
}

export interface DefenseControlDef {
  id: string;
  label: string;
  category: string;
}

export interface ScenarioDef {
  id: string;
  name: string;
  category: string;
  description: string;
  prerequisites: string[];
  entry_point_types: string[];
  affected_asset_types: string[];
  impact: string[];
  risk_level: string;
  detection: string[];
  prevention: string[];
  mitre_technique_ids: string[];
}

export interface TemplateNodeDef {
  id: string;
  type: string;
  name: string;
  x: number;
  y: number;
  criticality: string;
}

export interface TemplateEdgeDef {
  source: string;
  target: string;
}

export interface EnvironmentTemplate {
  id: string;
  name: string;
  description: string;
  nodes: TemplateNodeDef[];
  edges: TemplateEdgeDef[];
}

export interface CaseStudy {
  id: string;
  title: string;
  year: number;
  attack_category: string;
  affected_sector: string;
  attack_chain_summary: string[];
  impact: string;
  security_lesson: string;
  preventive_controls: string[];
  sources: string[];
  recreate_scenario_id: string;
}

// ---------- Live simulator workspace state ----------

export interface SimNode {
  id: string;
  type: string; // ComponentTypeDef.id
  name: string;
  x: number;
  y: number;
  mfa_enabled: boolean;
  firewall_enabled: boolean;
  monitoring_enabled: boolean;
  segmented: boolean;
  criticality: string;
  state: string; // NORMAL | TARGETED | UNDER_ATTACK | COMPROMISED | DETECTED | BLOCKED | ISOLATED | RECOVERED
}

export interface SimEdgeState {
  id: string;
  source: string;
  target: string;
  blocked?: boolean;
  active?: boolean;
}

export interface TimelineEvent {
  offset_seconds: number;
  message: string;
}

export interface SimulationRunResult {
  scenario_id: string;
  scenario_name: string;
  entry_point_id: string;
  visited_order: string[];
  node_states: Record<string, string>;
  blocked_at_edge: [string, string] | null;
  detected: boolean;
  risk_before: number;
  risk_after: number;
  risk_class_before: string;
  risk_class_after: string;
  timeline: TimelineEvent[];
  explanation: string[];
  recommended_controls: string[];
}

export interface DefenseRankingItem {
  defense_id: string;
  defense_label: string;
  risk_after: number;
  risk_reduction: number;
  estimated_impact: string;
}

export interface OptimizeDefenseResult {
  baseline_risk: number;
  ranking: DefenseRankingItem[];
}

export interface PredictedPath {
  scenario_id: string;
  scenario_name: string;
  entry_point_id: string;
  entry_point_name: string;
  visited_order: string[];
  risk_after: number;
  risk_class: string;
}
