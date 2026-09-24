import { useRef, useState, useCallback } from "react";

/** Mezclador con Web Audio API: la mezcla final se renderiza en el navegador. */
export function useMixer() {
  const ctxRef = useRef<AudioContext | null>(null);
  const [sources, setSources] = useState<Record<string, { buffer: AudioBuffer; gain: GainNode; muted: boolean }>>({});

  const loadStem = useCallback(async (name: string, url: string) => {
    ctxRef.current ??= new AudioContext();
    const ctx = ctxRef.current;
    const audio = await (await fetch(url)).arrayBuffer();
    const buffer = await ctx.decodeAudioData(audio);
    const gain = ctx.createGain();
    gain.connect(ctx.destination);
    setSources((s) => ({ ...s, [name]: { buffer, gain, muted: false } }));
  }, []);

  const play = useCallback(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    Object.values(sources).forEach(({ buffer, gain, muted }) => {
      const src = ctx.createBufferSource();
      src.buffer = buffer; src.connect(gain); gain.gain.value = muted ? 0 : 1;
      src.start();
    });
  }, [sources]);

  return { sources, setSources, loadStem, play };
}
