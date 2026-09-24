const BASE = "http://127.0.0.1:8317/api";

export async function uploadTrack(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${BASE}/upload`, { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json()).detail ?? "Error de subida");
  return r.json() as Promise<{ path: string }>;
}

export async function startSeparation(path: string, stages: number[]) {
  const r = await fetch(`${BASE}/separate`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, stages }),
  });
  if (!r.ok) throw new Error((await r.json()).detail);
  return r.json() as Promise<{ job_id: string }>;
}

export function openJobEvents(jobId: string, onEvent: (e: unknown) => void) {
  const es = new EventSource(`${BASE}/separate/${jobId}/events`);
  es.onmessage = (m) => onEvent(JSON.parse(m.data));
  es.onerror = () => es.close();
  return () => es.close();
}

export const stemUrl = (jobId: string, stem: string) => `${BASE}/stems/${jobId}/${encodeURIComponent(stem)}`;

export async function getModels() {
  const r = await fetch(`${BASE}/models`);
  return (await r.json()) as { models: unknown[] };
}
