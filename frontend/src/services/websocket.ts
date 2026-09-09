import { LiveMessage } from "../types/live";

type Listener = (message: LiveMessage) => void;
type StatusListener = (connected: boolean) => void;

/**
 * Thin wrapper around the browser WebSocket API with auto-reconnect.
 * One shared instance is used by useLiveFeed so multiple components can
 * subscribe to the same connection instead of opening one socket each.
 */
class LiveSocketService {
  private socket: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private statusListeners = new Set<StatusListener>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyClosed = false;
  private refCount = 0;

  connect() {
    this.refCount += 1;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }
    this.manuallyClosed = false;
    this.open();
  }

  private open() {
    const token = localStorage.getItem("cdt_token");
    if (!token) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Same-origin through the Vite dev proxy (see vite.config.ts), matching
    // the existing REST client's use of a relative /api base URL.
    const url = `${protocol}//${window.location.host}/api/live/ws?token=${encodeURIComponent(token)}`;

    try {
      this.socket = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      this.statusListeners.forEach((l) => l(true));
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as LiveMessage;
        this.listeners.forEach((l) => l(message));
      } catch {
        // Ignore malformed frames rather than crashing the UI.
      }
    };

    this.socket.onclose = () => {
      this.statusListeners.forEach((l) => l(false));
      if (!this.manuallyClosed) {
        this.scheduleReconnect();
      }
    };

    this.socket.onerror = () => {
      this.socket?.close();
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.manuallyClosed && this.refCount > 0) {
        this.open();
      }
    }, 3000);
  }

  disconnect() {
    this.refCount = Math.max(0, this.refCount - 1);
    if (this.refCount > 0) return; // other subscribers still active

    this.manuallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }

  onMessage(listener: Listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onStatusChange(listener: StatusListener) {
    this.statusListeners.add(listener);
    return () => this.statusListeners.delete(listener);
  }
}

export const liveSocket = new LiveSocketService();
