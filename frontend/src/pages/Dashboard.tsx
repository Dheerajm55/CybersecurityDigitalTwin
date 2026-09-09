import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Server, ShieldAlert, Bug, Route as RouteIcon, Gauge, Activity, Radio } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import MetricCard from "../components/MetricCard";
import RiskBadge from "../components/RiskBadge";
import LiveEventFeed from "../components/LiveEventFeed";
import SimulationControls from "../components/SimulationControls";
import { LoadingState, ErrorState, EmptyState } from "../components/StateViews";
import { fetchAssets, fetchCriticalAttackPaths, fetchDashboard } from "../services/api";
import { useLiveFeed } from "../hooks/useLiveFeed";

const PIE_COLORS: Record<string, string> = {
  CRITICAL: "#DC2626",
  HIGH: "#D97706",
  MEDIUM: "#2563EB",
  LOW: "#16A34A",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { connected, events, lastRiskUpdate, paused } = useLiveFeed();

  const summary = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
  const assets = useQuery({ queryKey: ["assets", "top-risk"], queryFn: () => fetchAssets() });
  const paths = useQuery({ queryKey: ["attack-paths", "critical"], queryFn: fetchCriticalAttackPaths });

  // The frontend never computes risk or security-score numbers itself —
  // whenever the live telemetry stream signals that backend state changed,
  // it simply asks React Query to refetch the real values from the API.
  useEffect(() => {
    if (events.length > 0 || lastRiskUpdate) {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["attack-paths"] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events.length, lastRiskUpdate]);

  if (summary.isLoading) return <LoadingState label="Loading dashboard..." />;
  if (summary.isError) return <ErrorState message="Unable to load the dashboard. Please try again." />;

  const s = summary.data!;
  const pieData = Object.entries(s.risk_distribution).map(([name, value]) => ({ name, value }));
  const topRisky = (assets.data || []).slice(0, 5);

  return (
    <div>
      <PageHeader
        title="CDT2"
        subtitle="Understand your digital environment, simulate threats, and reduce security risk."
        actions={
          <span className="flex items-center gap-1.5 text-[11px] font-semibold text-subtext border border-border rounded-md px-2 py-1">
            <Radio size={11} className={connected ? "text-success animate-pulse" : "text-subtext"} />
            SIMULATED ENVIRONMENT
          </span>
        }
      />

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
          <MetricCard label="Total Assets" value={s.total_assets} icon={Server} />
          <MetricCard label="High Risk Assets" value={s.high_risk_assets} icon={ShieldAlert} tone="danger" />
          <MetricCard label="Critical Vulnerabilities" value={s.critical_vulnerabilities} icon={Bug} tone="danger" />
          <MetricCard label="Attack Paths" value={s.attack_path_count} icon={RouteIcon} tone="warning" />
          <MetricCard label="Active Threats" value={s.active_threats} icon={Activity} tone={s.active_threats > 0 ? "danger" : "default"} />
          <MetricCard label="Events / Min" value={s.events_per_min} icon={Radio} />
          <MetricCard label="Security Score" value={`${s.security_score}/100`} icon={Gauge} tone="success" />
        </div>

        <SimulationControls
          paused={paused}
          onStateChange={() => {
            queryClient.invalidateQueries({ queryKey: ["dashboard"] });
            queryClient.invalidateQueries({ queryKey: ["assets"] });
            queryClient.invalidateQueries({ queryKey: ["attack-paths"] });
          }}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-surface border border-border rounded-lg shadow-card p-5">
            <h2 className="text-sm font-semibold text-text mb-3">Security Risk Overview</h2>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} paddingAngle={2}>
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={PIE_COLORS[entry.name] || "#94A3B8"} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend iconSize={8} wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="lg:col-span-2 bg-surface border border-border rounded-lg shadow-card p-5">
            <h2 className="text-sm font-semibold text-text mb-3">Top Risky Assets</h2>
            {topRisky.length === 0 ? (
              <EmptyState title="No assets yet" description="Add assets to see risk rankings here." />
            ) : (
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-subtext border-b border-border">
                    <th className="py-2 font-medium">Asset</th>
                    <th className="py-2 font-medium">Type</th>
                    <th className="py-2 font-medium">Risk</th>
                    <th className="py-2 font-medium">Reason</th>
                    <th className="py-2 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {topRisky.map((a) => (
                    <tr
                      key={a.id}
                      className="border-b border-border last:border-0 hover:bg-bg cursor-pointer"
                      onClick={() => navigate(`/assets/${a.id}`)}
                    >
                      <td className="py-2 font-medium text-text">{a.name}</td>
                      <td className="py-2 text-subtext">{a.asset_type.replaceAll("_", " ")}</td>
                      <td className="py-2"><RiskBadge level={a.risk_class} size="sm" /></td>
                      <td className="py-2 text-subtext text-xs">
                        {!a.mfa_enabled ? "MFA disabled" : a.internet_exposed ? "Internet exposed" : "High criticality"}
                      </td>
                      <td className="py-2 text-xs text-accent">Review controls</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-surface border border-border rounded-lg shadow-card p-5">
            <h2 className="text-sm font-semibold text-text mb-3">Critical Attack Paths</h2>
            {paths.isLoading ? (
              <LoadingState />
            ) : !paths.data || paths.data.length === 0 ? (
              <EmptyState title="No attack paths found" description="Connect assets in the Digital Twin to compute attack paths." />
            ) : (
              <div className="space-y-3">
                {paths.data.slice(0, 4).map((p, idx) => (
                  <div key={idx} className="border border-border rounded-md p-3">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-xs text-subtext">
                        {p.path.map((s) => s.name).join(" → ")}
                      </p>
                      <RiskBadge level={p.risk_class} size="sm" />
                    </div>
                    <p className="text-xs text-subtext">Risk score: {p.risk_score}/100</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-surface border border-border rounded-lg shadow-card p-5">
            <h2 className="text-sm font-semibold text-text mb-3">Live Security Events</h2>
            <LiveEventFeed events={events} connected={connected} />
          </div>
        </div>
      </div>
    </div>
  );
}
