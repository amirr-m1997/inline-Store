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

function errorMessage(data: unknown, locale?: string) {
  if (data && typeof data === "object" && "detail" in data && typeof data.detail === "string") return data.detail;
  const messages = (value: unknown): string[] => {
    if (typeof value === "string") return [value];
    if (Array.isArray(value)) return value.flatMap(messages);
    if (value && typeof value === "object") return Object.values(value).flatMap(messages);
    if (typeof value === "number" || typeof value === "boolean") return [String(value)];
    return [];
  };
  const fallback = typeof window !== "undefined" && window.location.pathname.startsWith("/en") ? "Request failed." : "درخواست ناموفق بود.";
  return messages(data).join(" ") || (locale === "en" ? "Request failed." : fallback);
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

export async function apiRequest<T>(path: string, { body, headers, timeoutMs = 12_000, retries = 0, guestCart = false, signal, method = "GET", ...init }: ApiRequestOptions & { method?: string } = {}): Promise<T> {
  const idempotent = method === "GET" || method === "HEAD" || method === "OPTIONS";
  const maxRetries = idempotent ? retries : 0;
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
      const response = await fetch(path, { ...init, method, headers: requestHeaders, body: body === undefined ? undefined : JSON.stringify(body), signal: controller.signal });
      if (response.status === 204) return null as T;
      const text = await response.text();
      const data: unknown = text ? JSON.parse(text) as unknown : null;
      if (!response.ok) throw new ApiError(errorMessage(data), response.status, data);
      storeGuestCartToken(data);
      return data as T;
    } catch (error) {
      if (attempt >= maxRetries || (error instanceof ApiError && error.status < 500)) throw error;
      attempt += 1;
      await new Promise((resolve) => setTimeout(resolve, Math.min(1000 * 2 ** attempt, 4000)));
    } finally {
      globalThis.clearTimeout(timeout);
      signal?.removeEventListener("abort", abort);
    }
  }
}
