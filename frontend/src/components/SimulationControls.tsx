import { useState } from "react";
import { Pause, Play, Zap, Crosshair, RotateCcw } from "lucide-react";
import { generateLiveEvent, pauseLive, resetLiveEnvironment, resumeLive, simulateLiveAttack } from "../services/api";

interface Props {
  paused: boolean;
  onStateChange?: () => void;
}

export default function SimulationControls({ paused, onStateChange }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function run(action: string, fn: () => Promise<any>) {
    setBusy(action);
    setMessage(null);
    try {
      await fn();
      onStateChange?.();
    } catch {
      setMessage("Action failed. Check that the backend is running.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-4">
      <p className="text-sm font-semibold text-text mb-3">Live Simulation</p>
      <div className="flex flex-wrap gap-2">
        {paused ? (
          <ControlButton icon={Play} label="Resume" busy={busy === "resume"} onClick={() => run("resume", resumeLive)} />
        ) : (
          <ControlButton icon={Pause} label="Pause" busy={busy === "pause"} onClick={() => run("pause", pauseLive)} />
        )}
        <ControlButton icon={Zap} label="Generate Event" busy={busy === "generate"} onClick={() => run("generate", generateLiveEvent)} />
        <ControlButton icon={Crosshair} label="Simulate Attack" busy={busy === "attack"} onClick={() => run("attack", () => simulateLiveAttack())} />
        <ControlButton icon={RotateCcw} label="Reset Environment" busy={busy === "reset"} onClick={() => run("reset", resetLiveEnvironment)} />
      </div>
      {message && <p className="text-xs text-danger mt-2">{message}</p>}
      <p className="text-[11px] text-subtext mt-3">
        SIMULATED ENVIRONMENT — all telemetry, events, and attacks here are synthetic.
      </p>
    </div>
  );
}

function ControlButton({
  icon: Icon,
  label,
  busy,
  onClick,
}: {
  icon: typeof Pause;
  label: string;
  busy: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={busy}
      className="flex items-center gap-1.5 text-xs font-medium text-text border border-border px-2.5 py-1.5 rounded-md hover:bg-bg transition-colors disabled:opacity-60"
    >
      <Icon size={13} />
      {busy ? "Working..." : label}
    </button>
  );
}
