import { Handle, Position } from "reactflow";
import { iconFor } from "../../../utils/simulatorIcons";
import { stateStyle } from "../../../utils/simulatorState";

export interface SimNodeCardData {
  name: string;
  shortId: string;
  icon: string;
  state: string;
  side: "ATTACK" | "DEFENSE";
}

export default function SimNodeCard({ data }: { data: SimNodeCardData }) {
  const Icon = iconFor(data.icon);
  const style = stateStyle(data.state);
  const isNormal = data.state === "NORMAL";

  return (
    <div
      style={{
        borderColor: style.border,
        background: style.bg,
      }}
      className="rounded-lg border-[1.5px] shadow-card px-3 py-2 w-[180px]"
    >
      <Handle type="target" position={Position.Left} style={{ background: "#94A3B8", width: 6, height: 6 }} />
      <Handle type="source" position={Position.Right} style={{ background: "#94A3B8", width: 6, height: 6 }} />

      <div className="flex items-center gap-1.5">
        <Icon size={14} style={{ color: isNormal ? "#64748B" : style.text }} />
        <span className="text-xs font-medium text-text truncate">{data.name}</span>
      </div>
      <p className="text-[10px] text-subtext mt-0.5">{data.shortId}</p>
      {!isNormal && (
        <p className="text-[10px] font-semibold mt-0.5" style={{ color: style.text }}>
          {style.label.toUpperCase()}
        </p>
      )}
    </div>
  );
}
