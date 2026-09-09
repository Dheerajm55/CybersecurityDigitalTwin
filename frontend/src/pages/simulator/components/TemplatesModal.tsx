import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { fetchTemplates } from "../../../services/simulatorApi";
import { LoadingState } from "../../../components/StateViews";
import { EnvironmentTemplate } from "../../../types/simulator";

interface Props {
  onClose: () => void;
  onSelect: (template: EnvironmentTemplate) => void;
}

export default function TemplatesModal({ onClose, onSelect }: Props) {
  const { data, isLoading } = useQuery({ queryKey: ["simulator-templates"], queryFn: fetchTemplates });

  return (
    <div className="fixed inset-0 bg-black/30 z-30 flex items-center justify-center p-6" onClick={onClose}>
      <div
        className="bg-surface border border-border rounded-lg shadow-card w-full max-w-2xl max-h-[80vh] overflow-y-auto p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-text">Environment Templates</h2>
          <button onClick={onClose} className="text-subtext hover:text-text"><X size={16} /></button>
        </div>

        {isLoading ? (
          <LoadingState />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {(data || []).map((t) => (
              <button
                key={t.id}
                onClick={() => onSelect(t)}
                className="text-left border border-border rounded-lg p-3 hover:bg-bg transition-colors"
              >
                <p className="text-sm font-medium text-text">{t.name}</p>
                <p className="text-xs text-subtext mt-1">{t.description}</p>
                <p className="text-[11px] text-subtext mt-2">{t.nodes.length} components</p>
              </button>
            ))}
          </div>
        )}
        <p className="text-[11px] text-subtext mt-4">
          Loading a template replaces the current workspace. Synthetic topologies only — not tied to any real environment.
        </p>
      </div>
    </div>
  );
}
