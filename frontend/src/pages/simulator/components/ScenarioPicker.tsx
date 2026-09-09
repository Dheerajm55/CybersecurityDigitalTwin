import { useState } from "react";
import { Zap } from "lucide-react";
import { ScenarioDef } from "../../../types/simulator";
import RiskBadge from "../../../components/RiskBadge";
import { LoadingState } from "../../../components/StateViews";

interface Props {
  entryNodeName: string;
  scenarios: ScenarioDef[] | undefined;
  loading: boolean;
  onSimulate: (scenarioId: string) => void;
  simulating: boolean;
}

export default function ScenarioPicker({ entryNodeName, scenarios, loading, onSimulate, simulating }: Props) {
  const [selected, setSelected] = useState<ScenarioDef | null>(null);

  if (loading) return <div className="bg-surface border border-border rounded-lg shadow-card p-4"><LoadingState label="Loading scenarios..." /></div>;

  if (!scenarios || scenarios.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg shadow-card p-4">
        <p className="text-sm font-semibold text-text mb-1">Possible Simulated Scenarios</p>
        <p className="text-xs text-subtext">No scenarios are defined for this component type yet.</p>
      </div>
    );
  }

  if (selected) {
    return (
      <div className="bg-surface border border-border rounded-lg shadow-card p-4">
        <div className="flex items-center justify-between mb-1">
          <p className="text-xs font-semibold text-accent uppercase tracking-wide">Simulated Attack</p>
          <RiskBadge level={selected.risk_level} size="sm" />
        </div>
        <p className="text-sm font-semibold text-text mb-2">{selected.name}</p>
        <p className="text-xs text-subtext mb-3">{selected.description}</p>

        <DetailList label="Entry Point" items={[entryNodeName]} />
        <DetailList label="Prerequisites" items={selected.prerequisites} />
        <DetailList label="Potential Impact" items={selected.impact} />
        <DetailList label="Detection" items={selected.detection} />
        <DetailList label="Prevention" items={selected.prevention} />

        <div className="flex gap-2 mt-4">
          <button
            onClick={() => onSimulate(selected.id)}
            disabled={simulating}
            className="flex-1 flex items-center justify-center gap-1.5 bg-accent text-white text-sm font-medium py-2 rounded-md hover:bg-blue-700 disabled:opacity-60"
          >
            <Zap size={14} /> {simulating ? "Simulating..." : "Simulate"}
          </button>
          <button
            onClick={() => setSelected(null)}
            className="px-3 text-sm text-subtext border border-border rounded-md hover:bg-bg"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-4">
      <p className="text-sm font-semibold text-text mb-1">{entryNodeName}</p>
      <p className="text-xs text-subtext mb-3">Possible simulated scenarios</p>
      <div className="space-y-1.5">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={() => setSelected(s)}
            className="w-full text-left border border-border rounded-md px-3 py-2 hover:bg-bg transition-colors"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm text-text">{s.name}</span>
              <RiskBadge level={s.risk_level} size="sm" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function DetailList({ label, items }: { label: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="mb-2.5">
      <p className="text-[11px] font-semibold text-subtext uppercase tracking-wide mb-0.5">{label}</p>
      <ul className="text-xs text-text list-disc list-inside space-y-0.5">
        {items.map((it, i) => (
          <li key={i}>{it}</li>
        ))}
      </ul>
    </div>
  );
}
