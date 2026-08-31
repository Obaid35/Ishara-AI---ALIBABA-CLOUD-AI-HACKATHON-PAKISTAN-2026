"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, get, put } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Card, PageHeader, Toast, useToast } from "@/components/admin/ui";
import type { Health } from "@/lib/types";

type SettingValue = string | boolean;

const TOGGLES: [string, string, string][] = [
  ["english_text_enabled", "English text", "Show an English line beneath the Urdu message."],
  ["english_speech_enabled", "English speech", "Use the same TTS system for English."],
  ["overlay_enabled", "Landmark overlay", "Draw tracking landmarks over the camera."],
  [
    "doctor_voice_input_enabled",
    "Doctor voice input",
    "Let the doctor speak instead of tapping. Speech only selects a verified phrase.",
  ],
  [
    "guidance_panel_enabled",
    "Sign guide",
    "Show a help button on the patient screen that plays the reference video for each supported sign. Useful while a team is learning the vocabulary.",
  ],
];

export default function SettingsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [settings, setSettings] = useState<Record<string, SettingValue>>({});
  const [health, setHealth] = useState<Health | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (!loading && (!user || user.role !== "admin")) router.replace("/login");
  }, [loading, user, router]);

  const load = useCallback(() => {
    get<{ settings: Record<string, SettingValue> }>("/api/admin/settings")
      .then((data) => setSettings(data.settings))
      .catch(() => setSettings({}));
    get<Health>("/api/health", false).then(setHealth).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (user?.role === "admin") load();
  }, [user, load]);

  const save = async (key: string, value: SettingValue) => {
    setBusy(true);
    setSettings((current) => ({ ...current, [key]: value }));
    try {
      const result = await put<{ warning: string | null }>(`/api/admin/settings/${key}`, { value });
      if (result.warning) toast.warn(result.warning);
      else toast.ok("Saved.");
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Could not save.");
      load();
    } finally {
      setBusy(false);
    }
  };

  if (loading || !user || user.role !== "admin") {
    return <div className="min-h-dvh grid place-items-center text-muted text-sm">Loading…</div>;
  }

  return (
    <div className="min-h-dvh bg-page">
      <PageHeader
        title="Settings"
        description="Application-wide preferences"
        actions={
          <Link href="/" className="btn-sm h-10 px-4">
            Communication screen
          </Link>
        }
      />

      <div className="p-6 max-w-3xl space-y-5">
        <Card title="Output">
          <div className="p-4 space-y-1">
            <div className="flex items-center justify-between py-2.5">
              <div>
                <div className="text-sm font-medium">Primary language</div>
                <div className="text-xs text-muted">Urdu text and Urdu speech.</div>
              </div>
              <span className="pill-ok">Urdu</span>
            </div>

            {TOGGLES.map(([key, label, hint]) => (
              <div key={key} className="flex items-center justify-between py-2.5 border-t border-line">
                <div className="pr-6">
                  <div className="text-sm font-medium">{label}</div>
                  <div className="text-xs text-muted">{hint}</div>
                </div>
                <button
                  onClick={() => save(key, !settings[key])}
                  disabled={busy}
                  className={`relative w-11 h-6 rounded-full transition-colors shrink-0 ${
                    settings[key] ? "bg-brand" : "bg-slate-300"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                      settings[key] ? "translate-x-[22px]" : "translate-x-0.5"
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Speech voice">
          <div className="p-4 space-y-3">
            <div>
              <label className="label">Kokoro Hindi voice</label>
              <select
                value={(settings.tts_voice as string) ?? ""}
                onChange={(event) => save("tts_voice", event.target.value)}
                disabled={busy}
                className="input"
              >
                <option value="">Not chosen yet</option>
                <option value="hf_alpha">hf_alpha (female)</option>
                <option value="hf_beta">hf_beta (female)</option>
                <option value="hm_omega">hm_omega (male)</option>
                <option value="hm_psi">hm_psi (male)</option>
              </select>
            </div>
            <p className="text-xs text-muted">
              Choose by a <strong>blind listening test</strong> with 2–3 Urdu speakers, not by
              name. Changing the voice makes every pre-generated audio file stale — all of them
              were produced by the previous voice.
            </p>
          </div>
        </Card>

        <Card title="System status">
          <div className="p-4 space-y-2.5 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-muted">Database</span>
              <span className={health?.database.available ? "pill-ok" : "pill-warn"}>
                {health?.database.mode ?? "unknown"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted">Recognition engine</span>
              <span className={health?.recognition.is_stub ? "pill-warn" : "pill-ok"}>
                {health?.recognition.is_stub ? "stub (simulated)" : "live"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted">Kokoro installed</span>
              <span className={health?.speech.kokoro_installed ? "pill-ok" : "pill-neutral"}>
                {health?.speech.kokoro_installed ? "yes" : "not installed"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted">Speech-to-text</span>
              <span className={health?.stt.any_available ? "pill-ok" : "pill-neutral"}>
                {health?.stt.any_available ? "available" : "unavailable"}
              </span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-line">
              <span className="text-muted">Internet required</span>
              <span className="pill-ok">No</span>
            </div>
          </div>
        </Card>
      </div>

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </div>
  );
}
