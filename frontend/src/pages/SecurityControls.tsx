import { useQuery } from "@tanstack/react-query";
import PageHeader from "../components/PageHeader";
import { LoadingState, ErrorState, EmptyState } from "../components/StateViews";
import { fetchControls } from "../services/api";

const STATE_STYLE: Record<string, string> = {
  implemented: "text-success",
  partial: "text-warning",
  not_implemented: "text-danger",
};

export default function SecurityControls() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["controls"], queryFn: fetchControls });

  return (
    <div>
      <PageHeader title="Security Controls" subtitle="Recommended controls, ranked by estimated risk reduction." />

      <div className="p-6">
        {isLoading ? (
          <LoadingState label="Loading controls..." />
        ) : isError ? (
          <ErrorState message="Unable to load security controls." />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No controls tracked yet" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.map((c) => (
              <div key={c.id} className="bg-surface border border-border rounded-lg shadow-card p-4">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-medium text-text">{c.name}</p>
                  <span className={`text-xs font-medium capitalize ${STATE_STYLE[c.current_state] || "text-subtext"}`}>
                    {c.current_state.replaceAll("_", " ")}
                  </span>
                </div>
                <p className="text-xs text-subtext mb-3">{c.category} · Priority: {c.priority}</p>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-subtext">Est. risk reduction</span>
                  <span className="text-text font-medium">{Math.round(c.risk_reduction_estimate * 100)}%</span>
                </div>
                <div className="w-full h-1.5 bg-bg rounded-full mt-1 overflow-hidden">
                  <div className="h-full bg-accent" style={{ width: `${c.risk_reduction_estimate * 100}%` }} />
                </div>
                <p className="text-xs text-subtext mt-2">Affects {c.affected_asset_count} asset(s)</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
