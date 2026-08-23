"use client";

/** Thin API client. Requests go through the Next rewrite to FastAPI. */

const ACCESS_KEY = "psl.access";
const REFRESH_KEY = "psl.refresh";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function setTokens(access: string | null, refresh?: string | null) {
  if (typeof window === "undefined") return;
  if (access) window.localStorage.setItem(ACCESS_KEY, access);
  else window.localStorage.removeItem(ACCESS_KEY);
  if (refresh !== undefined) {
    if (refresh) window.localStorage.setItem(REFRESH_KEY, refresh);
    else window.localStorage.removeItem(REFRESH_KEY);
  }
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function extractDetail(payload: unknown, fallback: string): string {
  if (typeof payload === "string") return payload;
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
  }
  return fallback;
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...((headers as Record<string, string>) ?? {}),
  };

  const token = auth ? getAccessToken() : null;
  if (token) finalHeaders.Authorization = `Bearer ${token}`;

  const response = await fetch(path, { ...rest, headers: finalHeaders });

  if (response.status === 204) return undefined as T;

  let payload: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    throw new ApiError(
      extractDetail(payload, `Request failed (${response.status})`),
      response.status,
    );
  }
  return payload as T;
}

export const get = <T,>(path: string, auth = true) => api<T>(path, { method: "GET", auth });

export const post = <T,>(path: string, body?: unknown, auth = true) =>
  api<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined, auth });

export const patch = <T,>(path: string, body: unknown, auth = true) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body), auth });

export const put = <T,>(path: string, body: unknown, auth = true) =>
  api<T>(path, { method: "PUT", body: JSON.stringify(body), auth });
