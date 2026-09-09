import { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  tone?: "default" | "danger" | "warning" | "success";
}

const TONE_TEXT: Record<string, string> = {
  default: "text-text",
  danger: "text-danger",
  warning: "text-warning",
  success: "text-success",
};

export default function MetricCard({ label, value, icon: Icon, tone = "default" }: Props) {
  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-5 flex items-start justify-between">
      <div>
        <p className="text-sm text-subtext font-medium">{label}</p>
        <p className={`mt-2 text-2xl font-semibold ${TONE_TEXT[tone]}`}>{value}</p>
      </div>
      {Icon && (
        <div className="rounded-md bg-bg border border-border p-2">
          <Icon size={18} className="text-subtext" />
        </div>
      )}
    </div>
  );
}
