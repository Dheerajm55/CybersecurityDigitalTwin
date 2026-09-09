import { useState } from "react";
import { ChevronDown, Plus, RotateCcw, Save, FolderOpen, Download, Upload, LayoutTemplate, BookOpen, Target, Sparkles } from "lucide-react";
import { ComponentTypeDef } from "../../../types/simulator";
import { iconFor } from "../../../utils/simulatorIcons";

const CATEGORY_ORDER = ["NETWORK", "APPLICATION", "CLOUD", "ENDPOINT", "SECURITY", "THREAT"];

interface Props {
  catalog: ComponentTypeDef[];
  onAddComponent: (type: ComponentTypeDef) => void;
  onReset: () => void;
  onSave: () => void;
  onLoad: () => void;
  onExport: () => void;
  onImport: () => void;
  onOpenTemplates: () => void;
  onOpenCaseStudies: () => void;
  onFindPaths: () => void;
  onOptimize: () => void;
}

export default function Toolbar({
  catalog,
  onAddComponent,
  onReset,
  onSave,
  onLoad,
  onExport,
  onImport,
  onOpenTemplates,
  onOpenCaseStudies,
  onFindPaths,
  onOptimize,
}: Props) {
  const [menuOpen, setMenuOpen] = useState(false);

  const byCategory = CATEGORY_ORDER.map((cat) => ({
    category: cat,
    items: catalog.filter((c) => c.category === cat),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="h-14 flex items-center justify-between px-4 border-b border-border bg-surface gap-2">
      <div className="flex items-center gap-2 relative">
        <button
          onClick={() => setMenuOpen((v) => !v)}
          className="flex items-center gap-1.5 text-sm font-medium bg-accent text-white px-3 py-1.5 rounded-md hover:bg-blue-700"
        >
          <Plus size={14} /> Add Component <ChevronDown size={13} />
        </button>

        {menuOpen && (
          <div className="absolute top-11 left-0 z-20 w-72 max-h-96 overflow-y-auto bg-surface border border-border rounded-lg shadow-card p-2">
            {byCategory.map((group) => (
              <div key={group.category} className="mb-2 last:mb-0">
                <p className="text-[11px] font-semibold text-subtext px-2 py-1 uppercase tracking-wide">{group.category}</p>
                {group.items.map((item) => {
                  const Icon = iconFor(item.icon);
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        onAddComponent(item);
                        setMenuOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-text rounded-md hover:bg-bg text-left"
                    >
                      <Icon size={14} className="text-subtext" />
                      {item.label}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        )}

        <ToolbarButton icon={LayoutTemplate} label="Templates" onClick={onOpenTemplates} />
        <ToolbarButton icon={BookOpen} label="Case Studies" onClick={onOpenCaseStudies} />
        <ToolbarButton icon={Target} label="Find Attack Paths" onClick={onFindPaths} />
        <ToolbarButton icon={Sparkles} label="Optimize Defense" onClick={onOptimize} />
      </div>

      <div className="flex items-center gap-2">
        <ToolbarButton icon={RotateCcw} label="Reset" onClick={onReset} />
        <ToolbarButton icon={Save} label="Save" onClick={onSave} />
        <ToolbarButton icon={FolderOpen} label="Load" onClick={onLoad} />
        <ToolbarButton icon={Download} label="Export" onClick={onExport} />
        <ToolbarButton icon={Upload} label="Import" onClick={onImport} />
      </div>
    </div>
  );
}

function ToolbarButton({ icon: Icon, label, onClick }: { icon: typeof Plus; label: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 text-xs font-medium text-subtext border border-border px-2.5 py-1.5 rounded-md hover:bg-bg hover:text-text transition-colors"
    >
      <Icon size={13} />
      {label}
    </button>
  );
}
