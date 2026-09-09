import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactFlow, {
  addEdge,
  Background,
  Connection,
  Controls,
  Edge,
  MarkerType,
  Node,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";

import {
  fetchComponentCatalog,
  fetchDefenseControls,
  fetchScenarios,
  optimizeDefense,
  predictPaths,
  runSimulation,
} from "../../services/simulatorApi";
import {
  CaseStudy,
  ComponentTypeDef,
  EnvironmentTemplate,
  OptimizeDefenseResult,
  PredictedPath,
  SimNode,
  SimulationRunResult,
} from "../../types/simulator";

import PageHeader from "../../components/PageHeader";
import Toolbar from "./components/Toolbar";
import SimNodeCard, { SimNodeCardData } from "./components/SimNodeCard";
import NodeDetailsPanel from "./components/NodeDetailsPanel";
import ScenarioPicker from "./components/ScenarioPicker";
import CompromiseDetailsPanel from "./components/CompromiseDetailsPanel";
import StatusBar from "./components/StatusBar";
import TemplatesModal from "./components/TemplatesModal";
import CaseStudiesModal from "./components/CaseStudiesModal";
import OptimizerModal from "./components/OptimizerModal";
import PredictorModal from "./components/PredictorModal";
import { extractErrorMessage } from "../../utils/errors";

type NodeData = SimNodeCardData & {
  componentType: string;
  mfa_enabled: boolean;
  firewall_enabled: boolean;
  monitoring_enabled: boolean;
  segmented: boolean;
  criticality: string;
};

const NODE_TYPES = { simNode: SimNodeCard };
const SAVE_KEY = "cdt_simulator_saves";

let idCounter = 0;
function newId(prefix: string) {
  idCounter += 1;
  return `${prefix.toLowerCase()}_${Date.now().toString(36)}_${idCounter}`;
}

export default function Simulator() {
  const [nodes, setNodes, onNodesChange] = useNodesState<NodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const [lastResult, setLastResult] = useState<SimulationRunResult | null>(null);
  const [riskChain, setRiskChain] = useState<number[]>([]);
  const [appliedDefenseLabels, setAppliedDefenseLabels] = useState<string[]>([]);
  const [appliedDefenseIds, setAppliedDefenseIds] = useState<string[]>([]);
  const [simulating, setSimulating] = useState(false);
  const [applyingDefense, setApplyingDefense] = useState<string | null>(null);

  const [showTemplates, setShowTemplates] = useState(false);
  const [showCaseStudies, setShowCaseStudies] = useState(false);
  const [optimizerOpen, setOptimizerOpen] = useState(false);
  const [optimizerResult, setOptimizerResult] = useState<OptimizeDefenseResult | null>(null);
  const [optimizerLoading, setOptimizerLoading] = useState(false);
  const [optimizerError, setOptimizerError] = useState<string | null>(null);
  const [predictorOpen, setPredictorOpen] = useState(false);
  const [predictorResult, setPredictorResult] = useState<PredictedPath[] | null>(null);
  const [predictorLoading, setPredictorLoading] = useState(false);
  const [predictorError, setPredictorError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const catalogQuery = useQuery({ queryKey: ["sim-catalog"], queryFn: fetchComponentCatalog });
  const defenseControlsQuery = useQuery({ queryKey: ["sim-defense-controls"], queryFn: fetchDefenseControls });

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || null;

  function toSimNode(n: Node<NodeData>): SimNode {
    return {
      id: n.id,
      type: n.data.componentType,
      name: n.data.name,
      x: n.position.x,
      y: n.position.y,
      mfa_enabled: n.data.mfa_enabled,
      firewall_enabled: n.data.firewall_enabled,
      monitoring_enabled: n.data.monitoring_enabled,
      segmented: n.data.segmented,
      criticality: n.data.criticality,
      state: n.data.state,
    };
  }

  const scenarioQuery = useQuery({
    queryKey: ["sim-scenarios", selectedNode?.data.componentType],
    queryFn: () => fetchScenarios({ entry_point_type: selectedNode!.data.componentType }),
    enabled: !!selectedNode && selectedNode.data.side === "ATTACK",
  });

  // ---------- Topology helpers ----------

  function toEngineNodes() {
    return nodes.map((n) => ({
      id: n.id,
      type: n.data.componentType,
      name: n.data.name,
      mfa_enabled: n.data.mfa_enabled,
      firewall_enabled: n.data.firewall_enabled,
      monitoring_enabled: n.data.monitoring_enabled,
      segmented: n.data.segmented,
      criticality: n.data.criticality,
    }));
  }

  function toEngineEdges() {
    return edges.map((e) => ({ source: e.source, target: e.target }));
  }

  const nodeNames = useMemo(() => Object.fromEntries(nodes.map((n) => [n.id, n.data.name])), [nodes]);

  // ---------- Add / edit components ----------

  function addComponent(type: ComponentTypeDef) {
    const sideCount = nodes.filter((n) => n.data.side === type.side).length;
    const x = type.side === "ATTACK" ? 40 : 480;
    const y = 40 + sideCount * 90;

    const node: Node<NodeData> = {
      id: newId(type.id),
      type: "simNode",
      position: { x, y },
      data: {
        name: type.label,
        shortId: newId(type.id.slice(0, 3)).slice(-6),
        icon: type.icon,
        state: "NORMAL",
        side: type.side,
        componentType: type.id,
        mfa_enabled: false,
        firewall_enabled: false,
        monitoring_enabled: false,
        segmented: false,
        criticality: type.default_criticality,
      },
    };
    setNodes((nds) => [...nds, node]);
  }

  function deleteNode(id: string) {
    setNodes((nds) => nds.filter((n) => n.id !== id));
    setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
    if (selectedNodeId === id) setSelectedNodeId(null);
  }

  function renameNode(id: string, name: string) {
    setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, name } } : n)));
  }

  function toggleNodeField(id: string, field: "mfa_enabled" | "firewall_enabled" | "monitoring_enabled" | "segmented") {
    setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, [field]: !n.data[field] } } : n)));
  }

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            id: newId("edge"),
            markerEnd: { type: MarkerType.ArrowClosed, color: "#94A3B8" },
            style: { stroke: "#94A3B8", strokeWidth: 1.25 },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  // ---------- Simulation ----------

  async function handleSimulate(scenarioId: string) {
    if (!selectedNode) return;
    setSimulating(true);
    try {
      const result = await runSimulation({
        scenario_id: scenarioId,
        entry_point_id: selectedNode.id,
        components: toEngineNodes(),
        edges: toEngineEdges(),
        applied_defenses: [],
      });
      applyResultToCanvas(result);
      setLastResult(result);
      setRiskChain([result.risk_after]);
      setAppliedDefenseLabels([]);
      setAppliedDefenseIds([]);
    } catch (err) {
      // Surfaced via lastResult staying null; a toast system is out of scope here.
      console.error(err);
    } finally {
      setSimulating(false);
    }
  }

  function applyResultToCanvas(result: SimulationRunResult) {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...n.data, state: result.node_states[n.id] || n.data.state },
      }))
    );
    setEdges((eds) =>
      eds.map((e) => {
        const idxSource = result.visited_order.indexOf(e.source);
        const idxTarget = result.visited_order.indexOf(e.target);
        const isActive = idxSource !== -1 && idxTarget === idxSource + 1;
        const isBlocked = !!result.blocked_at_edge && result.blocked_at_edge[0] === e.source && result.blocked_at_edge[1] === e.target;
        return {
          ...e,
          animated: isActive,
          style: {
            stroke: isBlocked ? "#16A34A" : isActive ? "#DC2626" : "#94A3B8",
            strokeWidth: isActive || isBlocked ? 2.5 : 1.25,
          },
          markerEnd: { type: MarkerType.ArrowClosed, color: isBlocked ? "#16A34A" : isActive ? "#DC2626" : "#94A3B8" },
        };
      })
    );
  }

  async function handleApplyDefense(defenseId: string, label: string) {
    if (!lastResult) return;
    setApplyingDefense(defenseId);
    try {
      const nextDefenses = [...appliedDefenseIds, defenseId];
      const result = await runSimulation({
        scenario_id: lastResult.scenario_id,
        entry_point_id: lastResult.entry_point_id,
        components: toEngineNodes(),
        edges: toEngineEdges(),
        applied_defenses: nextDefenses,
      });
      applyResultToCanvas(result);
      setLastResult(result);
      setRiskChain((chain) => [...chain, result.risk_after]);
      setAppliedDefenseIds(nextDefenses);
      setAppliedDefenseLabels((labels) => [...labels, label]);
    } catch (err) {
      console.error(err);
    } finally {
      setApplyingDefense(null);
    }
  }

  function resetSimulation() {
    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, state: "NORMAL" } })));
    setEdges((eds) => eds.map((e) => ({ ...e, animated: false, style: { stroke: "#94A3B8", strokeWidth: 1.25 }, markerEnd: { type: MarkerType.ArrowClosed, color: "#94A3B8" } })));
    setLastResult(null);
    setRiskChain([]);
    setAppliedDefenseLabels([]);
    setAppliedDefenseIds([]);
  }

  // ---------- Save / load / export / import ----------

  function serializeWorkspace() {
    return {
      nodes: nodes.map((n) => ({ id: n.id, position: n.position, data: n.data })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
    };
  }

  function loadWorkspace(payload: { nodes: any[]; edges: any[] }) {
    setNodes(
      payload.nodes.map((n) => ({
        id: n.id,
        type: "simNode",
        position: n.position,
        data: n.data,
      }))
    );
    setEdges(
      payload.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        style: { stroke: "#94A3B8", strokeWidth: 1.25 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#94A3B8" },
      }))
    );
    resetSimulation();
    setSelectedNodeId(null);
  }

  function handleSave() {
    const name = window.prompt("Name this simulation:");
    if (!name) return;
    const raw = localStorage.getItem(SAVE_KEY);
    const saves = raw ? JSON.parse(raw) : {};
    saves[name] = serializeWorkspace();
    localStorage.setItem(SAVE_KEY, JSON.stringify(saves));
  }

  function handleLoad() {
    const raw = localStorage.getItem(SAVE_KEY);
    const saves = raw ? JSON.parse(raw) : {};
    const names = Object.keys(saves);
    if (names.length === 0) {
      window.alert("No saved simulations yet. Use Save first.");
      return;
    }
    const name = window.prompt(`Load which simulation?\n\n${names.join("\n")}`);
    if (!name || !saves[name]) return;
    loadWorkspace(saves[name]);
  }

  function handleExport() {
    const blob = new Blob([JSON.stringify(serializeWorkspace(), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "simulator-topology.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleImportClick() {
    fileInputRef.current?.click();
  }

  function handleImportFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const payload = JSON.parse(reader.result as string);
        loadWorkspace(payload);
      } catch {
        window.alert("That file isn't a valid simulator topology export.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  }

  function handleLoadTemplate(template: EnvironmentTemplate) {
    const scale = { x: 170, y: 90 };
    loadWorkspace({
      nodes: template.nodes.map((n) => {
        const type = catalogQuery.data?.find((c) => c.id === n.type);
        return {
          id: n.id,
          position: { x: n.x * scale.x, y: n.y * scale.y },
          data: {
            name: n.name,
            shortId: n.id,
            icon: type?.icon || "monitor",
            state: "NORMAL",
            side: type?.side || (n.type === "ATTACKER" ? "ATTACK" : "DEFENSE"),
            componentType: n.type,
            mfa_enabled: false,
            firewall_enabled: false,
            monitoring_enabled: false,
            segmented: false,
            criticality: n.criticality,
          },
        };
      }),
      edges: template.edges.map((e) => ({ id: newId("edge"), source: e.source, target: e.target })),
    });
    setShowTemplates(false);
  }

  function handleRecreateCase(caseStudy: CaseStudy) {
    // Build a minimal synthetic chain from the mapped scenario's own data —
    // grounded in the scenario library, not invented for the case study.
    (async () => {
      const scenarios = await fetchScenarios();
      const s = scenarios.find((sc) => sc.id === caseStudy.recreate_scenario_id);
      if (!s) return;
      const entryType = s.entry_point_types[0] || "ATTACKER";
      const chainTypes = [entryType, ...s.affected_asset_types.slice(0, 2)];
      const ids = chainTypes.map((t, i) => `case_${i}_${newId(t.slice(0, 3))}`);
      const nodesPayload = chainTypes.map((t, i) => {
        const type = catalogQuery.data?.find((c) => c.id === t);
        return {
          id: ids[i],
          position: { x: i * 200 + 40, y: 120 },
          data: {
            name: type?.label || t.replaceAll("_", " "),
            shortId: ids[i].slice(-6),
            icon: type?.icon || "monitor",
            state: "NORMAL",
            side: type?.side || (i === 0 ? "ATTACK" : "DEFENSE"),
            componentType: t,
            mfa_enabled: false,
            firewall_enabled: false,
            monitoring_enabled: false,
            segmented: false,
            criticality: type?.default_criticality || "MEDIUM",
          },
        };
      });
      const edgesPayload = ids.slice(0, -1).map((id, i) => ({ id: newId("edge"), source: id, target: ids[i + 1] }));
      loadWorkspace({ nodes: nodesPayload, edges: edgesPayload });
      setShowCaseStudies(false);
    })();
  }

  // ---------- Optimizer / predictor ----------

  async function handleOptimize() {
    if (!lastResult) {
      window.alert("Run a simulation first, then Optimize Defense will rank controls for that scenario.");
      return;
    }
    setOptimizerOpen(true);
    setOptimizerLoading(true);
    setOptimizerError(null);
    setOptimizerResult(null);
    try {
      const result = await optimizeDefense({
        scenario_id: lastResult.scenario_id,
        entry_point_id: lastResult.entry_point_id,
        components: toEngineNodes(),
        edges: toEngineEdges(),
      });
      setOptimizerResult(result);
    } catch (err) {
      setOptimizerError(extractErrorMessage(err, "Unable to compute defense ranking."));
    } finally {
      setOptimizerLoading(false);
    }
  }

  async function handleFindPaths() {
    setPredictorOpen(true);
    setPredictorLoading(true);
    setPredictorError(null);
    setPredictorResult(null);
    try {
      const result = await predictPaths({ components: toEngineNodes(), edges: toEngineEdges() });
      setPredictorResult(result.paths);
    } catch (err) {
      setPredictorError(extractErrorMessage(err, "Unable to analyze the topology."));
    } finally {
      setPredictorLoading(false);
    }
  }

  // ---------- Keyboard shortcuts (Section 37) ----------

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      const typing = tag === "INPUT" || tag === "TEXTAREA";
      if ((e.key === "Delete" || e.key === "Backspace") && selectedNodeId && !typing) {
        deleteNode(selectedNodeId);
      } else if (e.key === "Escape") {
        setSelectedNodeId(null);
        setShowTemplates(false);
        setShowCaseStudies(false);
        setOptimizerOpen(false);
        setPredictorOpen(false);
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        handleSave();
      } else if (e.key.toLowerCase() === "r" && !typing) {
        resetSimulation();
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedNodeId, nodes, edges]);

  const isCompromiseView =
    selectedNode &&
    selectedNode.data.side === "DEFENSE" &&
    lastResult &&
    lastResult.node_states[selectedNode.id] &&
    lastResult.node_states[selectedNode.id] !== "NORMAL";

  return (
    <div className="flex flex-col h-screen">
      <PageHeader title="Cyber Attack & Defense Simulator" subtitle="A safe, non-destructive cyber range for exploring attack paths and defenses." />

      <Toolbar
        catalog={catalogQuery.data || []}
        onAddComponent={addComponent}
        onReset={resetSimulation}
        onSave={handleSave}
        onLoad={handleLoad}
        onExport={handleExport}
        onImport={handleImportClick}
        onOpenTemplates={() => setShowTemplates(true)}
        onOpenCaseStudies={() => setShowCaseStudies(true)}
        onFindPaths={handleFindPaths}
        onOptimize={handleOptimize}
      />
      <input ref={fileInputRef} type="file" accept="application/json" className="hidden" onChange={handleImportFile} />

      <div className="flex-1 flex min-h-0">
        <div className="flex-1 relative min-w-0">
          {/* Visual divider between Attack (left) and Defense (right) environments */}
          <div className="absolute inset-0 pointer-events-none z-10">
            <div className="absolute left-6 top-3 text-xs font-semibold text-subtext tracking-wide">ATTACK ENVIRONMENT</div>
            <div className="absolute right-6 top-3 text-xs font-semibold text-subtext tracking-wide">DEFENSE ENVIRONMENT</div>
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border" />
          </div>

          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={NODE_TYPES}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            onPaneClick={() => setSelectedNodeId(null)}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#E2E8F0" gap={20} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        {selectedNode && (
          <div className="w-80 shrink-0 border-l border-border bg-bg overflow-y-auto p-4 space-y-4">
            <NodeDetailsPanel
              node={toSimNode(selectedNode)}
              onClose={() => setSelectedNodeId(null)}
              onDelete={deleteNode}
              onRename={renameNode}
              onToggle={toggleNodeField}
            />

            {selectedNode.data.side === "ATTACK" && !isCompromiseView && (
              <ScenarioPicker
                entryNodeName={selectedNode.data.name}
                scenarios={scenarioQuery.data}
                loading={scenarioQuery.isLoading}
                onSimulate={handleSimulate}
                simulating={simulating}
              />
            )}

            {isCompromiseView && lastResult && (
              <CompromiseDetailsPanel
                node={toSimNode(selectedNode)}
                result={lastResult}
                riskChain={riskChain}
                appliedDefenseLabels={appliedDefenseLabels}
                availableDefenses={defenseControlsQuery.data || []}
                onApplyDefense={(id) => {
                  const label = (defenseControlsQuery.data || []).find((d) => d.id === id)?.label || id;
                  handleApplyDefense(id, label);
                }}
                applyingDefense={applyingDefense}
              />
            )}
          </div>
        )}
      </div>

      <StatusBar selectedNode={selectedNode ? toSimNode(selectedNode) : null} lastResult={lastResult} />

      {showTemplates && <TemplatesModal onClose={() => setShowTemplates(false)} onSelect={handleLoadTemplate} />}
      {showCaseStudies && <CaseStudiesModal onClose={() => setShowCaseStudies(false)} onRecreate={handleRecreateCase} />}
      {optimizerOpen && (
        <OptimizerModal
          result={optimizerResult}
          loading={optimizerLoading}
          error={optimizerError}
          onClose={() => setOptimizerOpen(false)}
        />
      )}
      {predictorOpen && (
        <PredictorModal
          paths={predictorResult}
          loading={predictorLoading}
          error={predictorError}
          onClose={() => setPredictorOpen(false)}
          nodeNames={nodeNames}
        />
      )}
    </div>
  );
}
