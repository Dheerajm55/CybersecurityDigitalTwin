import { useEffect, useRef, useState } from "react";
import { liveSocket } from "../services/websocket";
import { LiveMessage, LiveSecurityEvent, RiskUpdateMessage } from "../types/live";

const MAX_EVENTS = 50;

interface LiveFeedState {
  connected: boolean;
  events: LiveSecurityEvent[];
  lastRiskUpdate: RiskUpdateMessage | null;
  paused: boolean;
}

/**
 * Subscribes to the shared live telemetry WebSocket for the lifetime of
 * the calling component. Multiple components can use this hook at once —
 * they share one underlying connection (see services/websocket.ts).
 */
export function useLiveFeed() {
  const [state, setState] = useState<LiveFeedState>({
    connected: false,
    events: [],
    lastRiskUpdate: null,
    paused: false,
  });
  const riskUpdateHandlers = useRef<Set<(msg: RiskUpdateMessage) => void>>(new Set());

  useEffect(() => {
    liveSocket.connect();

    const offStatus = liveSocket.onStatusChange((connected) => {
      setState((s) => ({ ...s, connected }));
    });

    const offMessage = liveSocket.onMessage((message: LiveMessage) => {
      if (message.type === "security_event") {
        setState((s) => ({ ...s, events: [message.event, ...s.events].slice(0, MAX_EVENTS) }));
      } else if (message.type === "risk_update") {
        setState((s) => ({ ...s, lastRiskUpdate: message }));
        riskUpdateHandlers.current.forEach((h) => h(message));
      } else if (message.type === "connected" || message.type === "simulation_status") {
        setState((s) => ({ ...s, paused: message.paused }));
      } else if (message.type === "environment_reset") {
        setState((s) => ({ ...s, events: [] }));
      }
    });

    return () => {
      offStatus();
      offMessage();
      liveSocket.disconnect();
    };
  }, []);

  function onRiskUpdate(handler: (msg: RiskUpdateMessage) => void) {
    riskUpdateHandlers.current.add(handler);
    return () => riskUpdateHandlers.current.delete(handler);
  }

  return { ...state, onRiskUpdate };
}
