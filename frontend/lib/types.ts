export type Role = "admin" | "doctor" | "staff";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  must_change_password: boolean;
}

export interface Sign {
  code: string;
  urdu_meaning: string;
  english_meaning: string;
  is_demo_critical: boolean;
}

export interface Message {
  code: string;
  urdu_text: string;
  english_text: string | null;
  priority: string;
  is_demo_critical: boolean;
  audio_path: string | null;
  audio_ok: boolean;
  concept_sequence: string | null;
}

export interface DoctorPhrase {
  code: string;
  urdu_text: string;
  english_text: string;
  priority: string;
  is_demo_critical: boolean;
  sort_order: number;
  category_code: string;
  video_path: string | null;
}

export interface PhraseCategory {
  code: string;
  name_en: string;
  name_ur: string;
  sort_order: number;
  phrases: DoctorPhrase[];
}

/** Mirrors the server event vocabulary in backend/app/services/recognition.py */
export type RecognitionEventType =
  | "ready"
  | "capturing"
  | "analyzing"
  | "recognized"
  | "unknown_ambiguous"
  | "unknown_no_match"
  | "aborted"
  | "discarded";

export interface RecognitionEvent {
  type: RecognitionEventType;
  engine: string;
  is_stub?: boolean;
  sign_code?: string;
  similarity?: number;
  d1?: number;
  d2_diff_label?: number;
  duration_ms?: number;
  reason?: string;
  notice?: string;
  vocabulary_size?: number;
  landmarks?: boolean;
  best_sign_code?: string;
  hand_visibility?: number;
  frames?: number;
  capture_path?: string;
  thresholds?: Record<string, number>;
}

export interface Health {
  status: string;
  database: { mode: "live" | "snapshot"; available: boolean; error: string | null };
  snapshot: { available: boolean; exported_at: string | null; counts: Record<string, number> };
  recognition: { engine: string; is_stub: boolean };
  speech: { primary: string; kokoro_installed: boolean };
  stt: { any_available: boolean; groq_configured: boolean; local_available: boolean };
  degradations: string[];
  internet_required: boolean;
}

export interface HistoryTurn {
  id: number;
  speaker: "patient" | "doctor";
  urdu: string;
  english?: string | null;
  at: number;
}
