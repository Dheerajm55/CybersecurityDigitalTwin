import client from "./api";
import {
  CaseStudy,
  ComponentTypeDef,
  DefenseControlDef,
  EnvironmentTemplate,
  OptimizeDefenseResult,
  PredictedPath,
  ScenarioDef,
  SimulationRunResult,
} from "../types/simulator";

export async function fetchComponentCatalog(): Promise<ComponentTypeDef[]> {
  const { data } = await client.get("/simulator/components");
  return data;
}

export async function fetchDefenseControls(): Promise<DefenseControlDef[]> {
  const { data } = await client.get("/simulator/defense-controls");
  return data;
}

export async function fetchScenarios(params?: { category?: string; entry_point_type?: string }): Promise<ScenarioDef[]> {
  const { data } = await client.get("/simulator/scenarios", { params });
  return data;
}

export async function fetchTemplates(): Promise<EnvironmentTemplate[]> {
  const { data } = await client.get("/simulator/templates");
  return data;
}

export async function fetchTemplate(id: string): Promise<EnvironmentTemplate> {
  const { data } = await client.get(`/simulator/templates/${id}`);
  return data;
}

export async function fetchCaseStudies(): Promise<CaseStudy[]> {
  const { data } = await client.get("/simulator/case-studies");
  return data;
}

interface RunSimulationInput {
  scenario_id: string;
  entry_point_id: string;
  components: { id: string; type: string; name: string; mfa_enabled: boolean; firewall_enabled: boolean; monitoring_enabled: boolean; segmented: boolean; criticality: string }[];
  edges: { source: string; target: string }[];
  applied_defenses?: string[];
}

export async function runSimulation(input: RunSimulationInput): Promise<SimulationRunResult> {
  const { data } = await client.post("/simulator/run", input);
  return data;
}

export async function optimizeDefense(input: Omit<RunSimulationInput, "applied_defenses">): Promise<OptimizeDefenseResult> {
  const { data } = await client.post("/simulator/optimize-defense", input);
  return data;
}

export async function predictPaths(input: { components: RunSimulationInput["components"]; edges: RunSimulationInput["edges"] }): Promise<{ paths: PredictedPath[] }> {
  const { data } = await client.post("/simulator/predict-paths", input);
  return data;
}
