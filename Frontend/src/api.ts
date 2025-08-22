import type { GroupedGraphJSON } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function fetchGraph(seed?: string): Promise<GroupedGraphJSON> {
  const url = seed ? `${API_BASE}/graph?seed=${encodeURIComponent(seed)}` : `${API_BASE}/graph`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}
