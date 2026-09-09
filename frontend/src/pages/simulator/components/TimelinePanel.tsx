import { TimelineEvent } from "../../../types/simulator";

export default function TimelinePanel({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return <p className="text-xs text-subtext">Run a simulation to see the event timeline here.</p>;
  }
  return (
    <div className="flex gap-4 overflow-x-auto pb-1">
      {events.map((e, i) => (
        <div key={i} className="flex-shrink-0 min-w-[160px]">
          <p className="text-[11px] text-subtext font-mono">t+{e.offset_seconds}s</p>
          <p className="text-xs text-text">{e.message}</p>
        </div>
      ))}
    </div>
  );
}
