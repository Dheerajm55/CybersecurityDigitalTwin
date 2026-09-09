import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  AUTH_UNAUTHORIZED_EVENT,
  clearStoredAuth,
  fetchCurrentUser,
  getStoredToken,
  getStoredUser,
  login as apiLogin,
} from "../services/api";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  /** True only while session restoration (the startup /auth/me check) is
   * in flight. The app must not render protected routes or redirect to
   * /login until this settles, or a valid session briefly flashes the
   * login page. */
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Guards against a stale in-flight /auth/me response (e.g. from a slow
  // network) overwriting state after a logout() has already run.
  const sessionEpoch = useRef(0);

  const logout = useCallback(() => {
    sessionEpoch.current += 1;
    clearStoredAuth();
    setUser(null);
    setToken(null);
    // Wipes every cached query result. Without this, switching accounts
    // (or a fresh login after a previous session) could briefly render
    // stale data belonging to the previous user before fresh requests
    // resolve.
    queryClient.clear();
  }, [queryClient]);

  const login = useCallback(async (email: string, password: string) => {
    const loggedInUser = await apiLogin(email, password);
    sessionEpoch.current += 1;
    setUser(loggedInUser);
    setToken(getStoredToken());
    // A fresh login should never reuse another session's cached data.
    queryClient.clear();
  }, [queryClient]);

  // Session restoration on app load: never trust the locally-stored user
  // object on its own — always confirm the token against the backend's
  // /auth/me first. Runs once per mount.
  useEffect(() => {
    const epoch = ++sessionEpoch.current;
    const storedToken = getStoredToken();

    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    // Optimistically show the last-known user immediately (avoids a
    // blank flash) while the backend confirms the token is still valid.
    setUser(getStoredUser());
    setToken(storedToken);

    fetchCurrentUser()
      .then((confirmedUser) => {
        if (sessionEpoch.current !== epoch) return; // a logout/login happened meanwhile
        setUser(confirmedUser);
        localStorage.setItem("cdt_user", JSON.stringify(confirmedUser));
      })
      .catch(() => {
        if (sessionEpoch.current !== epoch) return;
        // Token missing/expired/invalid, or the user no longer exists —
        // never keep an unverified session around. A backend that is
        // merely unreachable also lands here (the request errors), which
        // is the conservative, correct choice: we do not treat the user
        // as authenticated forever just because we couldn't check.
        clearStoredAuth();
        setUser(null);
        setToken(null);
      })
      .finally(() => {
        if (sessionEpoch.current === epoch) setIsLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Centralized 401 handling: any API call anywhere in the app that
  // comes back 401 dispatches this event (see services/api.ts), and this
  // is the one place that reacts to it — clearing state/cache. Routing
  // (redirecting to /login) is left to RequireAuth reacting to
  // isAuthenticated becoming false, not handled here, so there is only
  // ever one place deciding to navigate.
  useEffect(() => {
    function handleUnauthorized() {
      if (token) {
        logout();
      }
    }
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
  }, [token, logout]);

  const value: AuthContextValue = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
