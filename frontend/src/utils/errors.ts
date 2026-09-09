/**
 * Normalizes an Axios/API error into a safe, readable string.
 *
 * FastAPI returns two different `detail` shapes depending on the error:
 *   - Pydantic validation errors (HTTP 422):
 *       { "detail": [{ type, loc, msg, input, ctx }, ...] }
 *   - Our own HTTPException errors (e.g. 401, 404):
 *       { "detail": "Invalid email or password" }
 *
 * React cannot render either the array or its objects directly — passing
 * either into JSX throws "Objects are not valid as a React child." Every
 * place in the app that surfaces an API error to the user should go
 * through this function rather than reading `err.response.data.detail`
 * directly.
 */
export function extractErrorMessage(err: unknown, fallback = "Something went wrong. Please try again."): string {
  const detail = (err as any)?.response?.data?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (item && typeof item === "object" ? item.msg : item))
      .filter((msg) => typeof msg === "string" && msg.length > 0);
    if (messages.length > 0) {
      return messages.join(", ");
    }
  }

  return fallback;
}

/**
 * Classifies an Axios error from an auth request (login/register/me)
 * into one of a small set of specific, safe-to-display messages. Unlike
 * extractErrorMessage (which surfaces whatever the backend's `detail`
 * says, for general API errors), this function deliberately does NOT
 * trust the raw backend message for every case — a network failure or a
 * bare 500 never has a usable `detail`, so those get their own clear,
 * actionable copy instead of a generic fallback. Never includes a raw
 * stack trace or exception message in the returned string.
 */
export function classifyAuthError(err: unknown): string {
  const axiosErr = err as any;

  // No `response` at all means the request never completed — the
  // backend is unreachable, DNS failed, CORS blocked it, etc. (This is
  // what a statically-served frontend calling an absolute backend URL
  // sees when the backend is down.)
  if (!axiosErr?.response) {
    if (axiosErr?.code === "ECONNABORTED") {
      return "The request timed out. Please try again.";
    }
    return "Unable to connect to the CDT2 backend. Make sure the backend is running.";
  }

  const status = axiosErr.response.status;
  if (status === 401) {
    return "Invalid email or password.";
  }
  if (status === 403) {
    return "Your account does not have permission to sign in.";
  }
  if (status >= 500) {
    // In this project's dev setup (Vite's proxy in front of a separate
    // uvicorn process), a backend that's down doesn't produce a genuine
    // axios network error — Vite's dev server itself answers with a
    // bare 500 and no JSON body, since the proxy target refused the
    // connection. CDT2's own backend, by contrast, always returns a
    // real JSON body with a `detail` field, even for its own 500s (see
    // the global exception handler in app/main.py). So a 500 with no
    // `detail` field is the backend being unreachable, not a backend
    // error — and gets the same actionable message as a real network
    // error above, rather than a generic "try again".
    if (typeof axiosErr.response.data?.detail !== "string") {
      return "Unable to connect to the CDT2 backend. Make sure the backend is running.";
    }
    return "Unable to sign in. Please try again.";
  }

  // 4xx other than 401/403 (e.g. 422 validation) — the backend's own
  // detail is safe and specific enough to show directly here.
  return extractErrorMessage(err, "Unable to sign in. Please try again.");
}
