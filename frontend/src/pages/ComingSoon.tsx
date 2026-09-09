import { LucideIcon } from "lucide-react";
import PageHeader from "../components/PageHeader";

interface Props {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  phaseNote: string;
}

export default function ComingSoon({ title, subtitle, icon: Icon, phaseNote }: Props) {
  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} />
      <div className="p-6">
        <div className="flex flex-col items-center justify-center text-center py-20 border border-dashed border-border rounded-lg bg-surface">
          <div className="rounded-full bg-bg border border-border p-3 mb-3">
            <Icon size={20} className="text-subtext" />
          </div>
          <p className="text-sm font-medium text-text">Not built yet in this version</p>
          <p className="text-sm text-subtext max-w-md mt-1">{phaseNote}</p>
        </div>
      </div>
    </div>
  );
}
