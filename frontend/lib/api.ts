import type { ApiResponse } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("econet_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  const raw = await res.text();
  let json: any = null;
  try {
    json = raw ? JSON.parse(raw) : {};
  } catch {
    // Response wasn't JSON — almost always an HTML error page (Vercel 502/504,
    // Next.js 404, or wrong NEXT_PUBLIC_API_URL pointing somewhere wrong).
    const preview = raw.slice(0, 120).replace(/\s+/g, " ");
    throw new Error(
      `Server returned non-JSON (${res.status}). URL: ${BASE}${path}. Body: ${preview}`
    );
  }

  if (!res.ok && !json.success) {
    const msg =
      json.detail ??
      json.error ??
      `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return json as ApiResponse<T>;
}

export const api = {
  post<T>(path: string, body: unknown) {
    return request<T>(path, { method: "POST", body: JSON.stringify(body) });
  },
  patch<T>(path: string, body: unknown = {}) {
    return request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
  },
  get<T>(path: string) {
    return request<T>(path, { method: "GET" });
  },
};
