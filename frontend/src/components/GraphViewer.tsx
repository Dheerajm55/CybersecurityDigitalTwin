import { useMemo, useCallback, MouseEvent as ReactMouseEvent } from "react";
import ReactFlow, {
  Background,
  Controls,
  Edge,
  MarkerType,
  Node,
  Position,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { DigitalTwinGraph } from "../types";

interface Props {
  graph: DigitalTwinGraph;
  onNodeClick?: (nodeId: string) => void;
  highlightedPath?: string[];
}

const RISK_COLOR: Record<string, string> = {
  CRITICAL: "#DC2626",
  HIGH: "#D97706",
  MEDIUM: "#2563EB",
  LOW: "#16A34A",
};

function layoutNodes(graph: DigitalTwinGraph): Node[] {
  // Simple deterministic layered layout: group by in-degree "depth" so the
  // graph reads left-to-right like the spec's Email -> GitHub -> Cloud -> DB
  // chain, without pulling in a heavy layout library.
  const depth = new Map<string, number>();
  const incoming = new Map<string, number>();
  graph.nodes.forEach((n) => incoming.set(n.id, 0));
  graph.edges.forEach((e) => incoming.set(e.target, (incoming.get(e.target) || 0) + 1));

  const queue = graph.nodes.filter((n) => (incoming.get(n.id) || 0) === 0).map((n) => n.id);
  queue.forEach((id) => depth.set(id, 0));

  const adjacency = new Map<string, string[]>();
  graph.edges.forEach((e) => {
    if (!adjacency.has(e.source)) adjacency.set(e.source, []);
    adjacency.get(e.source)!.push(e.target);
  });

  const visited = new Set<string>(queue);
  let i = 0;
  while (i < queue.length) {
    const current = queue[i++];
    const d = depth.get(current) || 0;
    for (const next of adjacency.get(current) || []) {
      if (!visited.has(next) || (depth.get(next) ?? 0) < d + 1) {
        depth.set(next, Math.max(depth.get(next) ?? 0, d + 1));
      }
      if (!visited.has(next)) {
        visited.add(next);
        queue.push(next);
      }
    }
  }
  graph.nodes.forEach((n) => {
    if (!depth.has(n.id)) depth.set(n.id, 0);
  });

  const columnCounts = new Map<number, number>();

  return graph.nodes.map((n) => {
    const d = depth.get(n.id) || 0;
    const row = columnCounts.get(d) || 0;
    columnCounts.set(d, row + 1);

    return {
      id: n.id,
      position: { x: d * 240, y: row * 110 },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: { label: n.label, node: n },
      type: "default",
      style: {
        border: `1.5px solid ${RISK_COLOR[n.risk_class] || "#E2E8F0"}`,
        borderRadius: 8,
        background: "#FFFFFF",
        padding: 10,
        fontSize: 12,
        width: 190,
        boxShadow: "0 1px 2px rgba(17,24,39,0.06)",
      },
    } as Node;
  });
}

export default function GraphViewer({ graph, onNodeClick, highlightedPath }: Props) {
  const initialNodes = useMemo(() => layoutNodes(graph), [graph]);

  const initialEdges: Edge[] = useMemo(
    () =>
      graph.edges.map((e) => {
        const isHighlighted =
          highlightedPath &&
          highlightedPath.includes(e.source) &&
          highlightedPath.includes(e.target) &&
          highlightedPath.indexOf(e.target) === highlightedPath.indexOf(e.source) + 1;

        return {
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.relationship_type,
          animated: !!isHighlighted,
          style: {
            stroke: isHighlighted ? "#DC2626" : "#94A3B8",
            strokeWidth: isHighlighted ? 2.5 : 1.25,
          },
          labelStyle: { fontSize: 10, fill: "#64748B" },
          markerEnd: { type: MarkerType.ArrowClosed, color: isHighlighted ? "#DC2626" : "#94A3B8" },
        } as Edge;
      }),
    [graph, highlightedPath]
  );

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleNodeClick = useCallback(
    (_: ReactMouseEvent, node: Node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  return (
    <div style={{ height: 560 }} className="border border-border rounded-lg bg-surface overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesDraggable
      >
        <Background color="#E2E8F0" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
