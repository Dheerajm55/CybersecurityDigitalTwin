import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export default function PageHeader({ title, subtitle, actions }: Props) {
  return (
    <div className="h-16 flex items-center justify-between px-6 border-b border-border bg-surface">
      <div>
        <h1 className="text-base font-semibold text-text">{title}</h1>
        {subtitle && <p className="text-xs text-subtext">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}
