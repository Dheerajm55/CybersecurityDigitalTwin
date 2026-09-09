import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { X, Zap } from "lucide-react";
import PageHeader from "../components/PageHeader";
import GraphViewer from "../components/GraphViewer";
import RiskBadge from "../components/RiskBadge";
import { LoadingState, ErrorState } from "../components/StateViews";
import { fetchDigitalTwin, simulateAttackPath } from "../services/api";
import { AttackPath, DigitalTwinGraph, GraphNode } from "../types";
import { extractErrorMessage } from "../utils/errors";

const FILTERS = ["All", "Critical", "High Risk", "Medium", "Low", "Devices", "Accounts", "Cloud", "Applications", "Databases"];

const DEVICE_TYPES = ["DEVICE", "LAPTOP", "SMARTPHONE", "SERVER", "ROUTER", "FIREWALL", "VPN"];
const ACCOUNT_TYPES = ["USER", "EMAIL_ACCOUNT", "GITHUB_ACCOUNT", "IDENTITY_PROVIDER"];
const CLOUD_TYPES = ["CLOUD_ACCOUNT", "STORAGE_BUCKET"];
const APP_TYPES = ["WEB_APPLICATION", "API", "SAAS_APPLICATION"];
const DB_TYPES = ["DATABASE"];

function applyFilter(graph: DigitalTwinGraph, filter: string): DigitalTwinGraph {
  if (filter === "All") return graph;

  let keep: (n: GraphNode) => boolean;
  if (filter === "Critical") keep = (n) => n.risk_class === "CRITICAL";
  else if (filter === "High Risk") keep = (n) => n.risk_class === "HIGH" || n.risk_class === "CRITICAL";
  else if (filter === "Medium") keep = (n) => n.risk_class === "MEDIUM";
  else if (filter === "Low") keep = (n) => n.risk_class === "LOW";
  else if (filter === "Devices") keep = (n) => DEVICE_TYPES.includes(n.type);
  else if (filter === "Accounts") keep = (n) => ACCOUNT_TYPES.includes(n.type);
  else if (filter === "Cloud") keep = (n) => CLOUD_TYPES.includes(n.type);
  else if (filter === "Applications") keep = (n) => APP_TYPES.includes(n.type);
  else if (filter === "Databases") keep = (n) => DB_TYPES.includes(n.type);
  else keep = () => true;

  const nodeIds = new Set(graph.nodes.filter(keep).map((n) => n.id));
  return {
    nodes: graph.nodes.filter((n) => nodeIds.has(n.id)),
    edges: graph.edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target)),
  };
}

export default function DigitalTwin() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["twin"], queryFn: fetchDigitalTwin });
  const [filter, setFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [simResult, setSimResult] = useState<AttackPath | null>(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);

  const filteredGraph = useMemo(() => {
    if (!data) return { nodes: [], edges: [] } as DigitalTwinGraph;
    let g = applyFilter(data, filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      const ids = new Set(g.nodes.filter((n) => n.label.toLowerCase().includes(q)).map((n) => n.id));
      g = { nodes: g.nodes.filter((n) => ids.has(n.id)), edges: g.edges.filter((e) => ids.has(e.source) && ids.has(e.target)) };
    }
    return g;
  }, [data, filter, search]);

  const selectedNode = data?.nodes.find((n) => n.id === selectedNodeId) || null;
  const connectedCount = data
    ? data.edges.filter((e) => e.source === selectedNodeId || e.target === selectedNodeId).length
    : 0;

  async function handleSimulateCompromise() {
    if (!selectedNodeId) return;
    setSimLoading(true);
    setSimError(null);
    setSimResult(null);
    try {
      const result = await simulateAttackPath(selectedNodeId);
      setSimResult(result);
    } catch (err: any) {
      setSimError(extractErrorMessage(err, "No attack path could be computed from this asset."));
    } finally {
      setSimLoading(false);
    }
  }

  if (isLoading) return <LoadingState label="Loading digital twin..." />;
  if (isError || !data) return <ErrorState message="Unable to load the digital twin graph." />;

  return (
    <div>
      <PageHeader title="Digital Twin" subtitle="A live graph representation of your digital environment." />

      <div className="p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <input
            placeholder="Search assets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-md border border-border px-3 py-1.5 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent"
          />
          <div className="flex flex-wrap gap-1.5">
            {FILTERS.map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                  filter === f
                    ? "bg-accent text-white border-accent"
                    : "bg-surface text-subtext border-border hover:bg-bg"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-4">
          <div className="flex-1 min-w-0">
            <GraphViewer
              graph={filteredGraph}
              onNodeClick={(id) => {
                setSelectedNodeId(id);
                setSimResult(null);
                setSimError(null);
              }}
              highlightedPath={simResult?.path.map((s) => s.asset_id)}
            />
          </div>

          {selectedNode && (
            <div className="w-80 shrink-0 bg-surface border border-border rounded-lg shadow-card p-5 h-fit">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-xs text-subtext">Asset</p>
                  <p className="text-sm font-semibold text-text">{selectedNode.label}</p>
                </div>
                <button onClick={() => { setSelectedNodeId(null); setSimResult(null); }} className="text-subtext hover:text-text">
                  <X size={16} />
                </button>
              </div>

              <dl className="space-y-2.5 text-sm">
                <Row label="Type" value={selectedNode.type.replaceAll("_", " ")} />
                <Row label="Criticality" value={selectedNode.criticality} />
                <Row label="MFA" value={selectedNode.mfa_enabled ? "Enabled" : "Disabled"} />
                <Row label="Exposure" value={selectedNode.internet_exposed ? "Public" : "Internal"} />
                <Row label="Connected Assets" value={String(connectedCount)} />
                <div className="flex items-center justify-between">
                  <span className="text-subtext">Risk Score</span>
                  <span className="flex items-center gap-2">
                    <RiskBadge level={selectedNode.risk_class} size="sm" />
                    <span className="text-text font-medium">{selectedNode.risk_score}/100</span>
                  </span>
                </div>
              </dl>

              <button
                onClick={handleSimulateCompromise}
                disabled={simLoading}
                className="mt-5 w-full flex items-center justify-center gap-1.5 bg-accent text-white text-sm font-medium py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-60"
              >
                <Zap size={14} />
                {simLoading ? "Simulating..." : "Simulate Compromise"}
              </button>

              {simError && <p className="text-xs text-danger mt-2">{simError}</p>}

              {simResult && (
                <div className="mt-4 border-t border-border pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-text">Highest Risk Path</p>
                    <RiskBadge level={simResult.risk_class} size="sm" />
                  </div>
                  <p className="text-xs text-subtext mb-2">
                    {simResult.path.map((s) => s.name).join(" → ")}
                  </p>
                  <p className="text-xs text-text font-medium mb-1">Risk: {simResult.risk_score}/100</p>
                  <p className="text-xs font-semibold text-text mt-3 mb-1">Why?</p>
                  <ul className="text-xs text-subtext list-disc list-inside space-y-0.5">
                    {simResult.explanation.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-subtext">{label}</span>
      <span className="text-text font-medium">{value}</span>
    </div>
  );
}
