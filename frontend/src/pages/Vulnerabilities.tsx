import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import PageHeader from "../components/PageHeader";
import RiskBadge from "../components/RiskBadge";
import { LoadingState, ErrorState, EmptyState } from "../components/StateViews";
import { fetchVulnerabilities } from "../services/api";

const SEVERITIES = ["", "LOW", "MEDIUM", "HIGH", "CRITICAL"];
const STATUSES = ["", "open", "patched", "accepted_risk"];

export default function Vulnerabilities() {
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [keOnly, setKeOnly] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["vulnerabilities", severity, status, keOnly],
    queryFn: () =>
      fetchVulnerabilities({
        ...(severity ? { severity } : {}),
        ...(status ? { status } : {}),
        ...(keOnly ? { known_exploited: "true" } : {}),
      }),
  });

  return (
    <div>
      <PageHeader title="Vulnerabilities" subtitle="Tracked findings across every asset in your environment." />

      <div className="p-6 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="rounded-md border border-border px-2.5 py-1.5 text-sm text-subtext">
            <option value="">All Severities</option>
            {SEVERITIES.filter(Boolean).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-md border border-border px-2.5 py-1.5 text-sm text-subtext">
            <option value="">All Statuses</option>
            {STATUSES.filter(Boolean).map((s) => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}
          </select>
          <label className="flex items-center gap-1.5 text-sm text-subtext">
            <input type="checkbox" checked={keOnly} onChange={(e) => setKeOnly(e.target.checked)} />
            Known Exploited only
          </label>
        </div>

        {isLoading ? (
          <LoadingState label="Loading vulnerabilities..." />
        ) : isError ? (
          <ErrorState message="Unable to load vulnerabilities." />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No vulnerabilities found" description="Try adjusting your filters." />
        ) : (
          <div className="overflow-x-auto border border-border rounded-lg bg-surface">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-bg text-left text-subtext">
                  <th className="px-4 py-2.5 font-medium">CVE</th>
                  <th className="px-4 py-2.5 font-medium">Title</th>
                  <th className="px-4 py-2.5 font-medium">Severity</th>
                  <th className="px-4 py-2.5 font-medium">CVSS</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="px-4 py-2.5 font-medium">Known Exploited</th>
                  <th className="px-4 py-2.5 font-medium">Recommended Action</th>
                </tr>
              </thead>
              <tbody>
                {data.map((v) => (
                  <tr key={v.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-2.5 text-text">{v.cve_id || "—"}</td>
                    <td className="px-4 py-2.5 text-text">{v.title}</td>
                    <td className="px-4 py-2.5"><RiskBadge level={v.severity} size="sm" /></td>
                    <td className="px-4 py-2.5 text-subtext">{v.cvss_score ?? "—"}</td>
                    <td className="px-4 py-2.5 text-subtext capitalize">{v.status.replaceAll("_", " ")}</td>
                    <td className="px-4 py-2.5">
                      {v.known_exploited ? <span className="text-danger font-medium">Yes</span> : <span className="text-subtext">No</span>}
                    </td>
                    <td className="px-4 py-2.5 text-subtext text-xs max-w-xs">{v.recommended_action || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
