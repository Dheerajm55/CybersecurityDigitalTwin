export const STATE_COLORS: Record<string, { border: string; bg: string; text: string; label: string }> = {
  NORMAL: { border: "#E2E8F0", bg: "#FFFFFF", text: "#64748B", label: "Normal" },
  TARGETED: { border: "#D97706", bg: "#FFFBEB", text: "#D97706", label: "Targeted" },
  UNDER_ATTACK: { border: "#D97706", bg: "#FFFBEB", text: "#D97706", label: "Under Attack" },
  COMPROMISED: { border: "#DC2626", bg: "#FEF2F2", text: "#DC2626", label: "Compromised" },
  DETECTED: { border: "#EA580C", bg: "#FFF7ED", text: "#EA580C", label: "Detected" },
  BLOCKED: { border: "#16A34A", bg: "#F0FDF4", text: "#16A34A", label: "Blocked" },
  ISOLATED: { border: "#2563EB", bg: "#EFF6FF", text: "#2563EB", label: "Isolated" },
  RECOVERED: { border: "#2563EB", bg: "#EFF6FF", text: "#2563EB", label: "Recovered" },
};

export function stateStyle(state: string) {
  return STATE_COLORS[state] || STATE_COLORS.NORMAL;
}
