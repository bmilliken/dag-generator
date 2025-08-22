import type { GroupedGraphJSON } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function fetchProjects(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function fetchGraph(project: string, seed?: string): Promise<GroupedGraphJSON> {
  const params = new URLSearchParams({ project });
  if (seed) {
    params.set('seed', seed);
  }
  const url = `${API_BASE}/graph?${params}`;
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}
