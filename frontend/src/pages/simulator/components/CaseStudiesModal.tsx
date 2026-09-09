import { useState, ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { X, ExternalLink } from "lucide-react";
import { fetchCaseStudies } from "../../../services/simulatorApi";
import { LoadingState } from "../../../components/StateViews";
import { CaseStudy } from "../../../types/simulator";

interface Props {
  onClose: () => void;
  onRecreate: (caseStudy: CaseStudy) => void;
}

export default function CaseStudiesModal({ onClose, onRecreate }: Props) {
  const { data, isLoading } = useQuery({ queryKey: ["case-studies"], queryFn: fetchCaseStudies });
  const [open, setOpen] = useState<CaseStudy | null>(null);

  return (
    <div className="fixed inset-0 bg-black/30 z-30 flex items-center justify-center p-6" onClick={onClose}>
      <div
        className="bg-surface border border-border rounded-lg shadow-card w-full max-w-2xl max-h-[80vh] overflow-y-auto p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold text-text">Real-World Security Cases</h2>
          <button onClick={onClose} className="text-subtext hover:text-text"><X size={16} /></button>
        </div>
        <p className="text-xs text-subtext mb-4">
          Educational, high-level summaries only — no exploit detail. See sources for further reading.
        </p>

        {isLoading ? (
          <LoadingState />
        ) : open ? (
          <div>
            <button onClick={() => setOpen(null)} className="text-xs text-accent mb-3">← Back to list</button>
            <p className="text-sm font-semibold text-text">{open.title} · {open.year}</p>
            <p className="text-xs text-subtext mb-3">{open.attack_category} · {open.affected_sector}</p>

            <Section label="Attack Chain">
              <ol className="list-decimal list-inside text-xs text-text space-y-0.5">
                {open.attack_chain_summary.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
            </Section>
            <Section label="Impact"><p className="text-xs text-text">{open.impact}</p></Section>
            <Section label="Security Lesson"><p className="text-xs text-text">{open.security_lesson}</p></Section>
            <Section label="Preventive Controls">
              <ul className="list-disc list-inside text-xs text-text space-y-0.5">
                {open.preventive_controls.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </Section>
            <Section label="Sources">
              {open.sources.map((s, i) => (
                <p key={i} className="text-xs text-accent flex items-center gap-1">
                  <ExternalLink size={11} /> {s}
                </p>
              ))}
            </Section>

            <button
              onClick={() => onRecreate(open)}
              className="mt-3 w-full bg-accent text-white text-sm font-medium py-2 rounded-md hover:bg-blue-700"
            >
              Recreate as Safe Simulation
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {(data || []).map((c) => (
              <button
                key={c.id}
                onClick={() => setOpen(c)}
                className="w-full text-left border border-border rounded-lg p-3 hover:bg-bg transition-colors"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-text">{c.title}</p>
                  <span className="text-xs text-subtext">{c.year}</span>
                </div>
                <p className="text-xs text-subtext mt-1">{c.attack_category} · {c.affected_sector}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mb-3">
      <p className="text-[11px] font-semibold text-subtext uppercase tracking-wide mb-1">{label}</p>
      {children}
    </div>
  );
}
