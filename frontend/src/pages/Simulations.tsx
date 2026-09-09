import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import { LoadingState, ErrorState } from "../components/StateViews";
import { fetchAssets, runWhatIf } from "../services/api";
import { SimulationResult } from "../types";
import { classify } from "../utils/risk";
import { extractErrorMessage } from "../utils/errors";

const ACTIONS = [
  { value: "enable_mfa", label: "Enable MFA" },
  { value: "remove_excess_permissions", label: "Remove excessive permissions" },
  { value: "patch_vulnerability", label: "Patch open vulnerabilities" },
  { value: "disable_public_access", label: "Disable public access" },
];

export default function Simulations() {
  const assets = useQuery({ queryKey: ["assets", "sim"], queryFn: () => fetchAssets() });
  const [assetId, setAssetId] = useState("");
  const [history, setHistory] = useState<SimulationResult[]>([]);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleRun(action: string) {
    if (!assetId) {
      setError("Select an asset first.");
      return;
    }
    setError(null);
    setLoading(action);
    try {
      const result = await runWhatIf(assetId, action);
      setHistory((prev) => [...prev, result]);
    } catch (err) {
      setError(extractErrorMessage(err, "Unable to run simulation."));
    } finally {
      setLoading(null);
    }
  }

  const currentRisk = history.length > 0 ? history[history.length - 1].risk_after : null;

  return (
    <div>
      <PageHeader title="Simulations" subtitle="What-if analysis: estimate risk reduction from hypothetical control changes." />

      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-surface border border-border rounded-lg shadow-card p-5 h-fit">
          <h2 className="text-sm font-semibold text-text mb-3">Choose an asset</h2>
          {assets.isLoading ? (
            <LoadingState />
          ) : assets.isError ? (
            <ErrorState />
          ) : (
            <select
              value={assetId}
              onChange={(e) => {
                setAssetId(e.target.value);
                setHistory([]);
                setError(null);
              }}
              className="w-full rounded-md border border-border px-3 py-2 text-sm"
            >
              <option value="">Select an asset...</option>
              {(assets.data || []).map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} ({a.risk_class}, {a.risk_score}/100)
                </option>
              ))}
            </select>
          )}

          {assetId && (
            <div className="mt-4 space-y-2">
              <p className="text-xs font-medium text-subtext mb-1">Apply a hypothetical control</p>
              {ACTIONS.map((a) => (
                <button
                  key={a.value}
                  onClick={() => handleRun(a.value)}
                  disabled={loading === a.value}
                  className="w-full text-left text-sm border border-border rounded-md px-3 py-2 hover:bg-bg transition-colors disabled:opacity-60"
                >
                  {loading === a.value ? "Running..." : a.label}
                </button>
              ))}
            </div>
          )}

          {error && <p className="text-xs text-danger mt-3">{error}</p>}

          <p className="text-xs text-subtext mt-4">
            All results are simulated, in-memory estimates — the project risk score model,
            not a guarantee. Nothing is changed on the real asset.
          </p>
        </div>

        <div className="lg:col-span-2 bg-surface border border-border rounded-lg shadow-card p-5">
          <h2 className="text-sm font-semibold text-text mb-4">Simulation Results</h2>

          {history.length === 0 ? (
            <p className="text-sm text-subtext">Run a simulation to see before/after risk here.</p>
          ) : (
            <div className="space-y-3">
              {currentRisk !== null && (
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-sm text-subtext">Current simulated risk:</span>
                  <span className="text-lg font-semibold text-text">{currentRisk}/100</span>
                  <RiskBadge level={classify(currentRisk)} size="sm" />
                </div>
              )}
              {history.map((h, idx) => (
                <div key={idx} className="border border-border rounded-md p-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-text">{ACTIONS.find((a) => a.value === h.action)?.label || h.action}</p>
                    <p className="text-xs text-subtext">{h.explanation}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-text">
                      <span className="text-subtext">{h.risk_before}</span> → <span className="font-semibold">{h.risk_after}</span>
                    </p>
                    <p className="text-xs text-success">−{h.risk_reduction} risk</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
