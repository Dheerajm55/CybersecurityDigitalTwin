import { ShieldCheck } from "lucide-react";
import { SimNode, SimulationRunResult } from "../../../types/simulator";
import RiskBadge from "../../../components/RiskBadge";
import { stateStyle } from "../../../utils/simulatorState";

interface Props {
  node: SimNode;
  result: SimulationRunResult;
  riskChain: number[];
  appliedDefenseLabels: string[];
  availableDefenses: { id: string; label: string; category: string }[];
  onApplyDefense: (defenseId: string) => void;
  applyingDefense: string | null;
}

export default function CompromiseDetailsPanel({
  node,
  result,
  riskChain,
  appliedDefenseLabels,
  availableDefenses,
  onApplyDefense,
  applyingDefense,
}: Props) {
  const style = stateStyle(node.state);
  const currentRisk = riskChain[riskChain.length - 1];

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-4">
      <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: style.text }}>
        {style.label} Asset
      </p>
      <p className="text-sm font-semibold text-text mb-3">{node.name}</p>

      <div className="grid grid-cols-2 gap-y-1.5 text-xs mb-3">
        <span className="text-subtext">Attack</span>
        <span className="text-text text-right">{result.scenario_name}</span>
        <span className="text-subtext">Entry Point</span>
        <span className="text-text text-right">{result.entry_point_id}</span>
      </div>

      <div className="mb-3">
        <p className="text-[11px] font-semibold text-subtext uppercase tracking-wide mb-1">Impact</p>
        <ul className="text-xs text-text list-disc list-inside space-y-0.5">
          {result.explanation.map((e, i) => <li key={i}>{e}</li>)}
        </ul>
      </div>

      <div className="flex items-center justify-between mb-4">
        <span className="text-xs text-subtext">Simulated Risk</span>
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-text">{currentRisk}/100</span>
          <RiskBadge level={currentRisk >= 75 ? "CRITICAL" : currentRisk >= 50 ? "HIGH" : currentRisk >= 25 ? "MEDIUM" : "LOW"} size="sm" />
        </div>
      </div>

      {riskChain.length > 1 && (
        <div className="mb-4 border border-border rounded-md p-2.5 bg-bg">
          <p className="text-[11px] font-semibold text-subtext uppercase tracking-wide mb-1.5">Simulated Risk Reduction</p>
          <div className="flex items-center gap-1.5 flex-wrap text-xs">
            {riskChain.map((r, i) => (
              <span key={i} className="flex items-center gap-1.5">
                <span className={i === riskChain.length - 1 ? "font-semibold text-text" : "text-subtext"}>{r}</span>
                {i < riskChain.length - 1 && <span className="text-subtext">→</span>}
              </span>
            ))}
          </div>
          {appliedDefenseLabels.length > 0 && (
            <p className="text-[11px] text-subtext mt-1.5">Applied: {appliedDefenseLabels.join(", ")}</p>
          )}
          <p className="text-[10px] text-subtext mt-1.5">
            Simulated project estimates — not a guarantee of real-world risk reduction.
          </p>
        </div>
      )}

      <p className="text-[11px] font-semibold text-subtext uppercase tracking-wide mb-1.5">Possible Preventions</p>
      <div className="space-y-1.5">
        {availableDefenses.map((d) => {
          const applied = appliedDefenseLabels.includes(d.label);
          return (
            <button
              key={d.id}
              onClick={() => onApplyDefense(d.id)}
              disabled={applied || applyingDefense === d.id}
              className={`w-full flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-md border transition-colors ${
                applied
                  ? "border-green-200 bg-green-50 text-success"
                  : "border-border text-text hover:bg-bg"
              } disabled:opacity-70`}
            >
              <ShieldCheck size={13} className={applied ? "text-success" : "text-subtext"} />
              {applyingDefense === d.id ? "Applying..." : d.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
