import { useParams, useNavigate } from "react-router-dom";
import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { ArrowLeft, Sparkles } from "lucide-react";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import { LoadingState, ErrorState } from "../components/StateViews";
import { fetchAsset, fetchAssetMLRisk, fetchAssetRisk } from "../services/api";
import type { AssetMLRiskPrediction } from "../types";

export default function AssetDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const asset = useQuery({ queryKey: ["asset", id], queryFn: () => fetchAsset(id!), enabled: !!id });
  const risk = useQuery({ queryKey: ["asset-risk", id], queryFn: () => fetchAssetRisk(id!), enabled: !!id });
  const mlRisk = useQuery({ queryKey: ["asset-ml-risk", id], queryFn: () => fetchAssetMLRisk(id!), enabled: !!id });

  if (asset.isLoading) return <LoadingState label="Loading asset..." />;
  if (asset.isError || !asset.data) return <ErrorState message="Unable to load this asset." />;

  const a = asset.data;

  return (
    <div>
      <PageHeader
        title={a.name}
        subtitle={a.asset_type.replaceAll("_", " ")}
        actions={
          <button
            onClick={() => navigate("/assets")}
            className="flex items-center gap-1.5 text-sm text-subtext hover:text-text"
          >
            <ArrowLeft size={15} /> Back to Assets
          </button>
        }
      />

      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-surface border border-border rounded-lg shadow-card p-5">
            <h2 className="text-sm font-semibold text-text mb-4">Asset Details</h2>
            <div className="grid grid-cols-2 gap-y-3 text-sm">
              <Field label="Owner" value={a.owner || "Unassigned"} />
              <Field label="Environment" value={a.environment} />
              <Field label="Criticality" value={a.criticality} />
              <Field label="Operating System" value={a.operating_system || "—"} />
              <Field label="Hostname" value={a.hostname || "—"} />
              <Field label="Authentication" value={a.authentication_type} />
              <Field label="MFA" value={a.mfa_enabled ? "Enabled" : "Disabled"} />
              <Field label="Internet Exposure" value={a.internet_exposed ? "Public" : "Internal"} />
              <Field label="Permission Level" value={a.permission_level} />
              <Field label="Permission Count" value={String(a.permission_count)} />
            </div>
            {a.description && (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-xs text-subtext mb-1">Description</p>
                <p className="text-sm text-text">{a.description}</p>
              </div>
            )}
            {a.tags && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {a.tags.split(",").map((t) => (
                  <span key={t} className="text-xs bg-bg border border-border rounded-md px-2 py-0.5 text-subtext">
                    {t.trim()}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-surface border border-border rounded-lg shadow-card p-5">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-sm font-semibold text-text">Risk Score</h2>
              <RiskBadge level={a.risk_class} size="sm" />
            </div>
            <p className="text-3xl font-semibold text-text mt-2">{a.risk_score}<span className="text-base text-subtext font-normal">/100</span></p>
            <p className="text-xs text-subtext mt-1">Project Risk Score — deterministic, explainable calculation.</p>

            {risk.data && (
              <div className="mt-4 pt-4 border-t border-border">
                <p className="text-xs font-semibold text-text mb-2">Why is this asset risky?</p>
                <ul className="space-y-2">
                  {risk.data.factors.map((f, i) => (
                    <li key={i} className="text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-text font-medium">{i + 1}. {f.factor}</span>
                        <span className="text-subtext">+{f.weight}</span>
                      </div>
                      <p className="text-subtext">{f.detail}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <AIRiskAnalysisCard query={mlRisk} />
        </div>
      </div>
    </div>
  );
}

function AIRiskAnalysisCard({ query }: { query: UseQueryResult<AssetMLRiskPrediction> }) {
  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-5">
      <div className="flex items-center gap-1.5 mb-1">
        <Sparkles size={14} className="text-accent" />
        <h2 className="text-sm font-semibold text-text">AI Risk Analysis</h2>
      </div>
      <p className="text-xs text-subtext mb-4">
        Independent ML predictions, shown alongside — never in place of — the deterministic Risk Score above.
      </p>

      {query.isLoading && <p className="text-xs text-subtext">Running ML models…</p>}

      {query.isError && (
        <p className="text-xs text-subtext">AI risk analysis is currently unavailable.</p>
      )}

      {query.data && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-subtext">Deterministic Risk</span>
            <span className="font-medium text-text">
              {query.data.deterministic_risk} <RiskBadge level={query.data.deterministic_risk_class} size="sm" />
            </span>
          </div>

          {query.data.ml_status === "unavailable" ? (
            <div className="text-xs text-subtext bg-bg border border-border rounded-md p-3">
              ML models are available but not trained yet. Run <code className="text-text">python -m app.ml.training</code> on the backend to enable AI risk predictions.
            </div>
          ) : (
            <>
              {Object.values(query.data.ml_predictions).map((pred) => (
                <div key={pred.model} className="flex items-center justify-between text-sm">
                  <span className="text-subtext capitalize">{pred.model.replace("_", " ")}</span>
                  {pred.error ? (
                    <span className="text-xs text-subtext">{pred.error}</span>
                  ) : (
                    <span className="font-medium text-text">
                      {Math.round((pred.risk_probability ?? 0) * 100)}%{" "}
                      {pred.risk_level && <RiskBadge level={pred.risk_level} size="sm" />}
                    </span>
                  )}
                </div>
              ))}

              {query.data.ensemble_probability !== null && (
                <div className="pt-3 border-t border-border flex items-center justify-between text-sm">
                  <span className="text-text font-semibold">Ensemble Risk</span>
                  <span className="font-semibold text-text">
                    {Math.round(query.data.ensemble_probability * 100)}%{" "}
                    {query.data.ensemble_risk_level && <RiskBadge level={query.data.ensemble_risk_level} size="sm" />}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-subtext pt-1">
                <span>Model Agreement</span>
                <span className="text-text font-medium">{query.data.model_agreement}</span>
              </div>
            </>
          )}

          {query.data.dataset_label && (
            <p className="text-[11px] text-subtext pt-2 border-t border-border">
              Dataset: <span className="text-text">{query.data.dataset_label}</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-subtext">{label}</p>
      <p className="text-text font-medium">{value}</p>
    </div>
  );
}
