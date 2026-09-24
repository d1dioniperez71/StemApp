import { useState } from "react";
import { uploadTrack, startSeparation, openJobEvents } from "./services/api";
import { Mixer } from "./components/Mixer";
import type { JobEvent } from "./types";

/**
 * Limbus Split Pro — UI mínima y honesta.
 * Los avisos del backend (etapas no disponibles) se muestran SIEMPRE al usuario.
 */
export default function App() {
  const [phase, setPhase] = useState<"idle" | "working" | "mixed">("idle");
  const [log, setLog] = useState<string[]>([]);
  const [jobId, setJobId] = useState("");
  const [stems, setStems] = useState<Record<string, string>>({});

  async function onFile(f: File) {
    setPhase("working"); setLog(["Subiendo pista…"]);
    try {
      const { path } = await uploadTrack(f);
      const { job_id } = await startSeparation(path, [1, 5]);
      setJobId(job_id);
      openJobEvents(job_id, (e) => {
        const ev = e as JobEvent;
        if (ev.type === "stage") setLog((l) => [...l, ev.label!]);
        if (ev.type === "warning") setLog((l) => [...l, `⚠ ${ev.message}`]);
        if (ev.type === "done") { setStems(ev.stems ?? {}); setPhase("mixed"); }
        if (ev.type === "error") setLog((l) => [...l, `✖ ${ev.message}`]);
      });
    } catch (err) {
      setLog((l) => [...l, `✖ ${(err as Error).message}`]); setPhase("idle");
    }
  }

  return (
    <main className="app">
      <h1>Limbus Split Pro</h1>
      <p className="tagline">Separación de stems con IA · 100% local · sin nube</p>
      <input type="file" accept=".wav,.mp3,.flac,.ogg,.m4a" disabled={phase === "working"}
             onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} />
      <ul className="log">{log.map((m, i) => <li key={i}>{m}</li>)}</ul>
      {phase === "mixed" && <Mixer jobId={jobId} stems={stems} />}
    </main>
  );
}
