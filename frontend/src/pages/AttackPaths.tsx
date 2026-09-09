import { useQuery } from "@tanstack/react-query";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import { LoadingState, ErrorState, EmptyState } from "../components/StateViews";
import { fetchCriticalAttackPaths } from "../services/api";

export default function AttackPaths() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["attack-paths"], queryFn: fetchCriticalAttackPaths });

  return (
    <div>
      <PageHeader title="Attack Paths" subtitle="Ranked, deterministic attack paths computed across your digital twin." />

      <div className="p-6">
        {isLoading ? (
          <LoadingState label="Computing attack paths..." />
        ) : isError ? (
          <ErrorState message="Unable to compute attack paths." />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No attack paths found" description="Add relationships between assets in the Digital Twin to compute paths." />
        ) : (
          <div className="space-y-3">
            {data.map((p, idx) => (
              <div key={idx} className="bg-surface border border-border rounded-lg shadow-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-text">
                    {p.path.map((s) => s.name).join(" → ")}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-text font-semibold">{p.risk_score}/100</span>
                    <RiskBadge level={p.risk_class} size="sm" />
                  </div>
                </div>
                <ul className="text-xs text-subtext list-disc list-inside space-y-0.5">
                  {p.explanation.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
