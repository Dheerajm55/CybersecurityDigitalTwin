import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import PageHeader from "../components/PageHeader";
import AssetTable from "../components/AssetTable";
import { LoadingState, ErrorState, EmptyState } from "../components/StateViews";
import { fetchAssets } from "../services/api";

const CRITICALITY_OPTIONS = ["", "LOW", "MEDIUM", "HIGH", "CRITICAL"];
const RISK_OPTIONS = ["", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function Assets() {
  const [search, setSearch] = useState("");
  const [criticality, setCriticality] = useState("");
  const [riskClass, setRiskClass] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["assets", search, criticality, riskClass],
    queryFn: () =>
      fetchAssets({
        ...(search ? { search } : {}),
        ...(criticality ? { criticality } : {}),
        ...(riskClass ? { risk_class: riskClass } : {}),
      }),
  });

  return (
    <div>
      <PageHeader title="Assets" subtitle="Every device, account, and system in your digital environment." />

      <div className="p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-2.5 text-subtext" />
            <input
              placeholder="Search assets..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 rounded-md border border-border px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent"
            />
          </div>
          <select
            value={criticality}
            onChange={(e) => setCriticality(e.target.value)}
            className="rounded-md border border-border px-2.5 py-1.5 text-sm text-subtext focus:outline-none"
          >
            <option value="">All Criticality</option>
            {CRITICALITY_OPTIONS.filter(Boolean).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={riskClass}
            onChange={(e) => setRiskClass(e.target.value)}
            className="rounded-md border border-border px-2.5 py-1.5 text-sm text-subtext focus:outline-none"
          >
            <option value="">All Risk Levels</option>
            {RISK_OPTIONS.filter(Boolean).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {isLoading ? (
          <LoadingState label="Loading assets..." />
        ) : isError ? (
          <ErrorState message="Unable to load assets." />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No assets found" description="Try adjusting your filters, or add a new asset." />
        ) : (
          <AssetTable assets={data} />
        )}
      </div>
    </div>
  );
}
