export interface ModelInfo {
  id: string; stage: number; role: string; source: string;
  license: string; sha256: string | null; status: string; notes: string;
  installed: boolean; hash_match: boolean | null; actual_sha256?: string;
}
export interface JobEvent {
  type: "status" | "stage" | "progress" | "warning" | "done" | "error";
  status?: string; stage?: number; label?: string; value?: number;
  message?: string; stems?: Record<string, string>; warnings?: string[];
}
export const STEM_LABELS: Record<string, string> = {
  vocals: "Voces", drums: "Batería", bass: "Bajo", other: "Otros", no_vocals: "Instrumental",
};
