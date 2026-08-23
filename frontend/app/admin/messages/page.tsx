"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, get, patch } from "@/lib/api";
import { Card, Empty, PageHeader, Toast, useToast } from "@/components/admin/ui";

interface MessageRow {
  id: string;
  code: string;
  urdu_text: string;
  english_text: string | null;
  kokoro_input: string;
  priority: string;
  is_demo_critical: boolean;
  is_enabled: boolean;
  audio_path: string | null;
  audio_ok: boolean;
  audio_stale: boolean;
  concept_sequence: string | null;
  blocking_signs: string | null;
}

export default function MessagesPage() {
  const [messages, setMessages] = useState<MessageRow[]>([]);
  const [editing, setEditing] = useState<MessageRow | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const load = useCallback(() => {
    get<{ messages: MessageRow[] }>("/api/admin/messages")
      .then((data) => setMessages(data.messages))
      .catch(() => setMessages([]));
  }, []);

  useEffect(load, [load]);

  const update = async (row: MessageRow, body: Record<string, unknown>) => {
    setBusy(true);
    try {
      const result = await patch<{ warning: string | null }>(
        `/api/admin/messages/${row.id}`,
        body,
      );
      if (result.warning) toast.warn(result.warning);
      else toast.ok(`${row.code} updated.`);
      setEditing(null);
      load();
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  };

  const stale = messages.filter((m) => m.audio_stale).length;

  return (
    <>
      <PageHeader
        title="Patient messages"
        description="Concept sequence → reviewed Urdu → pre-generated audio"
        actions={
          stale > 0 ? (
            <span className="pill-warn">{stale} with stale audio</span>
          ) : (
            <span className="pill-ok">Audio in sync</span>
          )
        }
      />

      <div className="p-6 max-w-[1400px] space-y-4">
        {stale > 0 && (
          <div className="card border-warn/40 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            <strong className="font-semibold">Stale audio detected.</strong> The text changed after
            the audio was generated, so the screen and the speaker would disagree. Playback is
            blocked until the audio is regenerated:{" "}
            <code className="font-mono text-xs">python scripts/generate_audio.py</code>
          </div>
        )}

        <Card>
          {messages.length === 0 ? (
            <Empty>No messages defined.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1000px]">
                <thead>
                  <tr>
                    <th className="th">Message</th>
                    <th className="th">Concepts</th>
                    <th className="th">Urdu</th>
                    <th className="th">Audio</th>
                    <th className="th">Enabled</th>
                    <th className="th"></th>
                  </tr>
                </thead>
                <tbody>
                  {messages.map((row) => (
                    <tr key={row.id} className="hover:bg-page/60">
                      <td className="td">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-medium">{row.code}</span>
                          <span className="pill-neutral text-[10px] py-0.5 uppercase">
                            {row.priority}
                          </span>
                          {row.is_demo_critical && (
                            <span className="pill-info text-[10px] py-0.5">demo</span>
                          )}
                        </div>
                      </td>
                      <td className="td">
                        <span className="font-mono text-[11px] text-muted">
                          {row.concept_sequence ?? "—"}
                        </span>
                      </td>
                      <td className="td max-w-[320px]">
                        <span className="urdu text-[17px] block truncate">{row.urdu_text}</span>
                      </td>
                      <td className="td">
                        {row.audio_stale ? (
                          <span className="pill-warn">stale</span>
                        ) : row.audio_ok ? (
                          <span className="pill-ok">ready</span>
                        ) : (
                          <span className="pill-neutral">none</span>
                        )}
                      </td>
                      <td className="td">
                        <button
                          onClick={() => update(row, { is_enabled: !row.is_enabled })}
                          disabled={busy || Boolean(row.blocking_signs)}
                          title={
                            row.blocking_signs
                              ? `Blocked — these signs are not Reliable + Enabled: ${row.blocking_signs}`
                              : undefined
                          }
                          className={`relative w-11 h-6 rounded-full transition-colors disabled:opacity-30 ${
                            row.is_enabled ? "bg-brand" : "bg-slate-300"
                          }`}
                        >
                          <span
                            className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                              row.is_enabled ? "translate-x-[22px]" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                        {row.blocking_signs && (
                          <div className="text-[10px] text-amber-700 mt-1 max-w-[160px]">
                            blocked by {row.blocking_signs}
                          </div>
                        )}
                      </td>
                      <td className="td text-right">
                        <button onClick={() => setEditing(row)} className="btn-sm">
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      {editing && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4">
          <div className="card w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
            <h3 className="font-semibold">{editing.code}</h3>
            <p className="text-xs text-muted mt-0.5 font-mono">{editing.concept_sequence}</p>

            <div className="space-y-4 mt-5">
              <div>
                <label className="label">Urdu text — shown on screen</label>
                <textarea
                  value={editing.urdu_text}
                  onChange={(event) =>
                    setEditing({ ...editing, urdu_text: event.target.value })
                  }
                  rows={2}
                  dir="rtl"
                  className="input h-auto py-2.5 urdu text-lg"
                />
              </div>

              <div>
                <label className="label">English text</label>
                <input
                  value={editing.english_text ?? ""}
                  onChange={(event) =>
                    setEditing({ ...editing, english_text: event.target.value })
                  }
                  className="input"
                />
              </div>

              <div>
                <label className="label">
                  Kokoro input — Devanagari pronunciation, never shown to a user
                </label>
                <textarea
                  value={editing.kokoro_input}
                  onChange={(event) =>
                    setEditing({ ...editing, kokoro_input: event.target.value })
                  }
                  rows={2}
                  className="input h-auto py-2.5 text-lg"
                />
                <p className="text-[11px] text-muted mt-1.5">
                  This is a pronunciation aid, not a translation. Verify it{" "}
                  <strong>by ear</strong> with an Urdu speaker — never by reading the Devanagari.
                </p>
              </div>

              <div className="rounded-lg bg-amber-50 border border-warn/25 px-3 py-2.5 text-[12px] text-amber-800">
                Changing either text field invalidates the generated audio. Regenerate before the
                demo, or the screen and the speaker will say different things.
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setEditing(null)} className="btn-sm h-10 px-4">
                Cancel
              </button>
              <button
                onClick={() =>
                  update(editing, {
                    urdu_text: editing.urdu_text,
                    english_text: editing.english_text,
                    kokoro_input: editing.kokoro_input,
                  })
                }
                disabled={busy}
                className="btn h-10 px-4 bg-brand text-white hover:bg-brand-hover text-sm"
              >
                {busy ? "Saving…" : "Save changes"}
              </button>
            </div>
          </div>
        </div>
      )}

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}
