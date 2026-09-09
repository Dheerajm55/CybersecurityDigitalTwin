import { useState } from "react";
import { Radio } from "lucide-react";
import { LiveSecurityEvent } from "../types/live";
import RiskBadge from "./RiskBadge";
import { EmptyState } from "./StateViews";

const FILTERS = ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"];

interface Props {
  events: LiveSecurityEvent[];
  connected: boolean;
}

export default function LiveEventFeed({ events, connected }: Props) {
  const [filter, setFilter] = useState("All");

  const filtered = filter === "All" ? events : events.filter((e) => e.severity === filter);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`flex items-center gap-1 text-xs font-semibold ${connected ? "text-success" : "text-subtext"}`}>
            <Radio size={12} className={connected ? "animate-pulse" : ""} />
            {connected ? "LIVE" : "Disconnected"}
          </span>
        </div>
        <div className="flex gap-1">
          {FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 rounded text-[11px] font-medium border transition-colors ${
                filter === f ? "bg-accent text-white border-accent" : "bg-surface text-subtext border-border hover:bg-bg"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title={connected ? "No live events yet" : "Not connected"}
          description={connected ? "Simulated telemetry will appear here as it's generated." : "Reconnecting to the live telemetry stream..."}
        />
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
          {filtered.map((e) => (
            <div key={e.event_id} className="flex items-start justify-between border-b border-border last:border-0 pb-2 last:pb-0">
              <div className="min-w-0">
                <p className="text-xs text-subtext font-mono">
                  {new Date(e.timestamp).toLocaleTimeString()}
                </p>
                <p className="text-sm text-text truncate">{e.description}</p>
                <p className="text-xs text-subtext">{e.asset_name}</p>
              </div>
              <RiskBadge level={e.severity} size="sm" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
