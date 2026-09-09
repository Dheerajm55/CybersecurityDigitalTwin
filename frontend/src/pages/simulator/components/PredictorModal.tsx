import { X } from "lucide-react";
import { PredictedPath } from "../../../types/simulator";
import RiskBadge from "../../../components/RiskBadge";

interface Props {
  paths: PredictedPath[] | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  nodeNames: Record<string, string>;
}

export default function PredictorModal({ paths, loading, error, onClose, nodeNames }: Props) {
  return (
    <div className="fixed inset-0 bg-black/30 z-30 flex items-center justify-center p-6" onClick={onClose}>
      <div className="bg-surface border border-border rounded-lg shadow-card w-full max-w-lg max-h-[80vh] overflow-y-auto p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-text">Likely Attack Paths</h2>
          <button onClick={onClose} className="text-subtext hover:text-text"><X size={16} /></button>
        </div>
        <p className="text-xs text-subtext mb-4">
          Every threat-side component paired with every compatible scenario, ranked by simulated risk.
        </p>

        {loading && <p className="text-sm text-subtext">Analyzing topology...</p>}
        {error && <p className="text-sm text-danger">{error}</p>}

        {paths && paths.length === 0 && <p className="text-sm text-subtext">No reachable paths found in the current topology.</p>}

        {paths && paths.length > 0 && (
          <div className="space-y-2">
            {paths.map((p, i) => (
              <div key={i} className="border border-border rounded-md px-3 py-2">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-medium text-text">{p.scenario_name}</p>
                  <RiskBadge level={p.risk_class} size="sm" />
                </div>
                <p className="text-xs text-subtext">
                  {p.visited_order.map((id) => nodeNames[id] || id).join(" → ")}
                </p>
                <p className="text-xs text-text mt-1">Risk: {p.risk_after}/100</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
