import { STEM_LABELS } from "../types";
import { useMixer } from "../hooks/useAudioContext";

/** Mezclador minimalista: una pista por stem, con volumen y mute. */
export function Mixer({ jobId, stems }: { jobId: string; stems: Record<string, string> }) {
  const { sources, loadStem, play } = useMixer();
  const BASE = "http://127.0.0.1:8317/api";

  return (
    <section className="mixer">
      <button onClick={play} disabled={Object.keys(sources).length === 0}>▶ Reproducir mezcla</button>
      {Object.entries(stems).map(([name, rel]) => (
        <div className="track" key={name}>
          <span className="label">{STEM_LABELS[name] ?? name}</span>
          <button onClick={() => loadStem(name, `${BASE}/stems/${jobId}/${name}`)}>Cargar</button>
        </div>
      ))}
    </section>
  );
}
