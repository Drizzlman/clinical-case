const DEFAULT_BASE_URL = "http://localhost:8000";

export function resolveApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_BASE_URL;
  }
  return process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_BASE_URL;
}
