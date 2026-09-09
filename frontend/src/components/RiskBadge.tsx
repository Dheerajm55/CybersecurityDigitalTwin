interface Props {
  level: string;
  size?: "sm" | "md";
}

const STYLES: Record<string, string> = {
  CRITICAL: "bg-red-50 text-danger border-red-200",
  HIGH: "bg-orange-50 text-warning border-orange-200",
  MEDIUM: "bg-blue-50 text-accent border-blue-200",
  LOW: "bg-green-50 text-success border-green-200",
};

export default function RiskBadge({ level, size = "md" }: Props) {
  const style = STYLES[level] || STYLES.MEDIUM;
  const padding = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs";
  return (
    <span className={`inline-flex items-center rounded-md border font-medium ${padding} ${style}`}>
      {level}
    </span>
  );
}
