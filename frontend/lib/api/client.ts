export class ApiError extends Error {
  constructor(message: string, public readonly status: number, public readonly data: unknown) {
    super(message);
    this.name = "ApiError";
  }
}

export type ApiRequestOptions = Omit<RequestInit, "body" | "headers"> & {
  body?: unknown;
  headers?: HeadersInit;
  timeoutMs?: number;
  retries?: number;
  guestCart?: boolean;
};

function errorMessage(data: unknown) {
  if (data && typeof data === "object" && "detail" in data && typeof data.detail === "string") return data.detail;
  if (data && typeof data === "object") return Object.values(data).flat().filter((value) => typeof value === "string").join(" ") || "درخواست ناموفق بود.";
  return "درخواست ناموفق بود.";
}

function guestToken() {
  return typeof window === "undefined" ? null : window.localStorage.getItem("guestCartToken");
}

export function storeGuestCartToken(payload: unknown) {
  if (typeof window === "undefined" || !payload || typeof payload !== "object" || !("guest_token" in payload)) return;
  const token = payload.guest_token;
  if (typeof token === "string" && token) window.localStorage.setItem("guestCartToken", token);
  if (token === null) window.localStorage.removeItem("guestCartToken");
}

export async function apiRequest<T>(path: string, { body, headers, timeoutMs = 12_000, retries = 0, guestCart = false, signal, ...init }: ApiRequestOptions = {}): Promise<T> {
  let attempt = 0;
  while (true) {
    const controller = new AbortController();
    const timeout = globalThis.setTimeout(() => controller.abort(), timeoutMs);
    const abort = () => controller.abort();
    signal?.addEventListener("abort", abort, { once: true });
    const requestHeaders = new Headers(headers);
    if (body !== undefined) requestHeaders.set("Content-Type", "application/json");
    if (guestCart) { const token = guestToken(); if (token) requestHeaders.set("X-Guest-Token", token); }
    try {
      const response = await fetch(path, { ...init, headers: requestHeaders, body: body === undefined ? undefined : JSON.stringify(body), signal: controller.signal });
      const data: unknown = response.status === 204 ? null : await response.json().catch(() => null);
      if (!response.ok) throw new ApiError(errorMessage(data), response.status, data);
      storeGuestCartToken(data);
      return data as T;
    } catch (error) {
      if (attempt >= retries || (error instanceof ApiError && error.status < 500)) throw error;
      attempt += 1;
    } finally {
      globalThis.clearTimeout(timeout);
      signal?.removeEventListener("abort", abort);
    }
  }
}
