import { X } from "lucide-react";
import { OptimizeDefenseResult } from "../../../types/simulator";

interface Props {
  result: OptimizeDefenseResult | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

export default function OptimizerModal({ result, loading, error, onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/30 z-30 flex items-center justify-center p-6" onClick={onClose}>
      <div className="bg-surface border border-border rounded-lg shadow-card w-full max-w-md p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-text">Optimize Defense</h2>
          <button onClick={onClose} className="text-subtext hover:text-text"><X size={16} /></button>
        </div>
        <p className="text-xs text-subtext mb-4">
          Ranked by simulated risk reduction for the last-run scenario. Each value comes from
          actually re-running the simulation engine with that control applied.
        </p>

        {loading && <p className="text-sm text-subtext">Running simulations...</p>}
        {error && <p className="text-sm text-danger">{error}</p>}

        {result && (
          <div className="space-y-2">
            <p className="text-xs text-subtext mb-1">Baseline risk: <span className="text-text font-medium">{result.baseline_risk}/100</span></p>
            {result.ranking.map((r, i) => (
              <div key={r.defense_id} className="flex items-center justify-between border border-border rounded-md px-3 py-2">
                <div>
                  <p className="text-sm text-text">{i + 1}. {r.defense_label}</p>
                  <p className="text-xs text-subtext">Estimated impact: {r.estimated_impact}</p>
                </div>
                <p className="text-sm font-semibold text-success">−{r.risk_reduction}</p>
              </div>
            ))}
            <p className="text-[11px] text-subtext pt-1">Simulated project estimates, not guaranteed real-world outcomes.</p>
          </div>
        )}
      </div>
    </div>
  );
}
