import axios from "axios";
import type {
  Asset,
  AssetMLRiskPrediction,
  AssetRiskDetail,
  AttackPath,
  DashboardSummary,
  DigitalTwinGraph,
  SecurityControlSummary,
  SecurityEventItem,
  SimulationResult,
  User,
  Vulnerability,
} from "../types";

export const AUTH_TOKEN_KEY = "cdt_token";
export const AUTH_USER_KEY = "cdt_user";

/** Dispatched whenever a request comes back 401, so the single
 * AuthContext (not this module) decides what to do — clear state, wipe
 * cached queries, and navigate. Keeping that decision out of the axios
 * interceptor avoids the interceptor reaching into React state directly
 * and avoids redirect loops from multiple places independently trying
 * to navigate to /login. */
export const AUTH_UNAUTHORIZED_EVENT = "cdt:unauthorized";

const client = axios.create({ baseURL: "/api" });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      window.dispatchEvent(new CustomEvent(AUTH_UNAUTHORIZED_EVENT));
    }
    return Promise.reject(err);
  }
);

// ---------- Auth ----------

export async function login(email: string, password: string) {
  const { data } = await client.post("/auth/login", { email, password });
  localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
  return data.user as User;
}

export async function register(email: string, full_name: string, password: string) {
  const { data } = await client.post("/auth/register", { email, full_name, password });
  localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
  return data.user as User;
}

/** The backend source of truth for "is this token still valid, and who
 * does it belong to". Session restoration on app load, and nothing
 * else, should ever trust a stored user object without this call
 * confirming it first. */
export async function fetchCurrentUser(): Promise<User> {
  const { data } = await client.get("/auth/me");
  return data as User;
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

/** @deprecated kept for any lingering direct callers — prefer
 * useAuth().logout(), which also clears React Query's cache and
 * navigates. This function only clears storage. */
export function logout() {
  clearStoredAuth();
}

export function getStoredUser(): User | null {
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function getStoredToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem(AUTH_TOKEN_KEY);
}

// ---------- Dashboard ----------

export async function fetchDashboard(): Promise<DashboardSummary> {
  const { data } = await client.get("/dashboard");
  return data;
}

export async function fetchEvents(): Promise<SecurityEventItem[]> {
  const { data } = await client.get("/events");
  return data;
}

// ---------- Assets ----------

export async function fetchAssets(params?: Record<string, string>): Promise<Asset[]> {
  const { data } = await client.get("/assets", { params });
  return data;
}

export async function fetchAsset(id: string): Promise<Asset> {
  const { data } = await client.get(`/assets/${id}`);
  return data;
}

export async function createAsset(payload: Partial<Asset>): Promise<Asset> {
  const { data } = await client.post("/assets", payload);
  return data;
}

export async function updateAsset(id: string, payload: Partial<Asset>): Promise<Asset> {
  const { data } = await client.put(`/assets/${id}`, payload);
  return data;
}

export async function deleteAsset(id: string): Promise<void> {
  await client.delete(`/assets/${id}`);
}

export async function fetchAssetRisk(id: string): Promise<AssetRiskDetail> {
  const { data } = await client.get(`/risk/assets/${id}`);
  return data;
}

// ---------- ML risk analysis (Phase 5) ----------

export async function fetchAssetMLRisk(id: string): Promise<AssetMLRiskPrediction> {
  const { data } = await client.post(`/ml/risk/predict/${id}`);
  return data;
}

// ---------- Digital Twin ----------

export async function fetchDigitalTwin(): Promise<DigitalTwinGraph> {
  const { data } = await client.get("/twin");
  return data;
}

// ---------- Attack paths ----------

export async function fetchCriticalAttackPaths(): Promise<AttackPath[]> {
  const { data } = await client.get("/attack-paths");
  return data;
}

export async function simulateAttackPath(sourceAssetId: string, targetAssetId?: string): Promise<AttackPath> {
  const { data } = await client.post("/attack-paths/simulate", {
    source_asset_id: sourceAssetId,
    target_asset_id: targetAssetId || null,
  });
  return data;
}

// ---------- Vulnerabilities ----------

export async function fetchVulnerabilities(params?: Record<string, string>): Promise<Vulnerability[]> {
  const { data } = await client.get("/vulnerabilities", { params });
  return data;
}

// ---------- Security controls ----------

export async function fetchControls(): Promise<SecurityControlSummary[]> {
  const { data } = await client.get("/controls");
  return data;
}

// ---------- What-if simulator ----------

export async function runWhatIf(assetId: string, action: string): Promise<SimulationResult> {
  const { data } = await client.post("/simulations/what-if", { asset_id: assetId, action });
  return data;
}

// ---------- Live telemetry controls ----------

export async function fetchLiveStatus() {
  const { data } = await client.get("/live/status");
  return data as { paused: boolean; interval_seconds: number; connected_clients: number };
}

export async function pauseLive() {
  const { data } = await client.post("/live/pause");
  return data;
}

export async function resumeLive() {
  const { data } = await client.post("/live/resume");
  return data;
}

export async function generateLiveEvent() {
  const { data } = await client.post("/live/generate-event");
  return data;
}

export async function simulateLiveAttack(sourceAssetId?: string) {
  const { data } = await client.post("/live/simulate-attack", null, {
    params: sourceAssetId ? { source_asset_id: sourceAssetId } : undefined,
  });
  return data;
}

export async function resetLiveEnvironment() {
  const { data } = await client.post("/live/reset");
  return data;
}

export default client;
