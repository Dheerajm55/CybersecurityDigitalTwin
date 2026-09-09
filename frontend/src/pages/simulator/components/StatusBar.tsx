import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { SimNode, SimulationRunResult } from "../../../types/simulator";
import TimelinePanel from "./TimelinePanel";

interface Props {
  selectedNode: SimNode | null;
  lastResult: SimulationRunResult | null;
}

export default function StatusBar({ selectedNode, lastResult }: Props) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="border-t border-border bg-surface">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs font-medium text-subtext hover:text-text"
      >
        <div className="flex items-center gap-6">
          <span>
            <span className="text-subtext">Simulation Status: </span>
            <span className="text-text font-medium">{lastResult ? (lastResult.blocked_at_edge ? "Blocked" : "Path succeeded") : "Idle"}</span>
          </span>
          <span>
            <span className="text-subtext">Selected Asset: </span>
            <span className="text-text font-medium">{selectedNode?.name || "None"}</span>
          </span>
          {lastResult && (
            <span>
              <span className="text-subtext">Risk: </span>
              <span className="text-text font-medium">{lastResult.risk_after}/100 ({lastResult.risk_class_after})</span>
            </span>
          )}
          <span className="text-subtext">
            AI Recommendations: <span className="italic">coming later (Phase 11)</span>
          </span>
        </div>
        {expanded ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>

      {expanded && (
        <div className="px-4 pb-3 pt-1">
          <p className="text-[11px] font-semibold text-subtext uppercase tracking-wide mb-1.5">Simulation Timeline</p>
          <TimelinePanel events={lastResult?.timeline || []} />
        </div>
      )}
    </div>
  );
}
