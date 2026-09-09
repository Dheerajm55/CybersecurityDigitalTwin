export interface LiveSecurityEvent {
  event_id: string;
  timestamp: string;
  asset_id: string | null;
  asset_name: string;
  event_type: string;
  severity: string;
  description: string;
  source: string | null;
  destination: string | null;
  risk_impact: number;
  status: string;
}

export interface RiskUpdateMessage {
  type: "risk_update";
  asset_id: string;
  asset_name: string;
  old_risk: number;
  new_risk: number;
  risk_class: string;
  reason: string;
}

export interface SecurityEventMessage {
  type: "security_event";
  event: LiveSecurityEvent;
}

export interface ConnectedMessage {
  type: "connected";
  paused: boolean;
}

export interface SimulationStatusMessage {
  type: "simulation_status";
  paused: boolean;
}

export interface AttackSimulationMessage {
  type: "attack_simulation";
  hop_count: number;
}

export interface EnvironmentResetMessage {
  type: "environment_reset";
  resolved_events: number;
}

export type LiveMessage =
  | RiskUpdateMessage
  | SecurityEventMessage
  | ConnectedMessage
  | SimulationStatusMessage
  | AttackSimulationMessage
  | EnvironmentResetMessage;

export interface LiveStatus {
  paused: boolean;
  interval_seconds: number;
  connected_clients: number;
}
