import { useState } from "react";
import { Trash2, X } from "lucide-react";
import { SimNode } from "../../../types/simulator";
import { stateStyle } from "../../../utils/simulatorState";

interface Props {
  node: SimNode;
  onClose: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, name: string) => void;
  onToggle: (id: string, field: "mfa_enabled" | "firewall_enabled" | "monitoring_enabled" | "segmented") => void;
}

export default function NodeDetailsPanel({ node, onClose, onDelete, onRename, onToggle }: Props) {
  const [editingName, setEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState(node.name);
  const style = stateStyle(node.state);

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-subtext">{node.type.replaceAll("_", " ")}</p>
          {editingName ? (
            <input
              autoFocus
              value={nameDraft}
              onChange={(e) => setNameDraft(e.target.value)}
              onBlur={() => {
                onRename(node.id, nameDraft.trim() || node.name);
                setEditingName(false);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") (e.target as HTMLInputElement).blur();
              }}
              className="text-sm font-semibold border-b border-accent outline-none w-full"
            />
          ) : (
            <p className="text-sm font-semibold text-text cursor-text" onClick={() => setEditingName(true)}>
              {node.name}
            </p>
          )}
        </div>
        <button onClick={onClose} className="text-subtext hover:text-text ml-2">
          <X size={16} />
        </button>
      </div>

      <div className="flex items-center justify-between text-xs mb-3">
        <span className="text-subtext">Status</span>
        <span className="font-semibold" style={{ color: style.text }}>{style.label}</span>
      </div>

      <div className="space-y-2 text-xs">
        <ToggleRow label="MFA enabled" checked={node.mfa_enabled} onChange={() => onToggle(node.id, "mfa_enabled")} />
        <ToggleRow label="Firewall enabled" checked={node.firewall_enabled} onChange={() => onToggle(node.id, "firewall_enabled")} />
        <ToggleRow label="Monitoring enabled" checked={node.monitoring_enabled} onChange={() => onToggle(node.id, "monitoring_enabled")} />
        <ToggleRow label="Network segmented" checked={node.segmented} onChange={() => onToggle(node.id, "segmented")} />
      </div>

      <button
        onClick={() => onDelete(node.id)}
        className="mt-4 w-full flex items-center justify-center gap-1.5 text-xs text-danger border border-red-200 bg-red-50 rounded-md py-1.5 hover:bg-red-100 transition-colors"
      >
        <Trash2 size={13} /> Delete component
      </button>
    </div>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) {
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <span className="text-subtext">{label}</span>
      <input type="checkbox" checked={checked} onChange={onChange} className="accent-accent" />
    </label>
  );
}
