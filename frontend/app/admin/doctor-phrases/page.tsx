"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, get, patch } from "@/lib/api";
import { Card, Empty, PageHeader, StatusPill, Toast, useToast } from "@/components/admin/ui";

interface PhraseRow {
  id: string;
  code: string;
  urdu_text: string;
  english_text: string;
  priority: string;
  verification_status: string;
  verified_by: string | null;
  is_enabled: boolean;
  is_demo_critical: boolean;
  category_code: string | null;
  category_name: string | null;
  video_path: string | null;
  permission_status: string | null;
  permitted_demo_playback: boolean | null;
}

export default function DoctorPhrasesPage() {
  const [phrases, setPhrases] = useState<PhraseRow[]>([]);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const load = useCallback(() => {
    get<{ phrases: PhraseRow[] }>("/api/admin/doctor-phrases")
      .then((data) => setPhrases(data.phrases))
      .catch(() => setPhrases([]));
  }, []);

  useEffect(load, [load]);

  const update = async (row: PhraseRow, body: Record<string, unknown>) => {
    setBusy(true);
    try {
      await patch(`/api/admin/doctor-phrases/${row.id}`, body);
      toast.ok(`${row.code} updated.`);
      load();
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  };

  /** Enabling needs BOTH conditions — show them as a checklist. */
  const gate = (row: PhraseRow) => {
    const verified = row.verification_status === "psl_verified";
    const permitted = row.permitted_demo_playback === true;
    const hasVideo = Boolean(row.video_path);
    return { verified, permitted, hasVideo, ok: verified && permitted && hasVideo };
  };

  return (
    <>
      <PageHeader
        title="Doctor phrases"
        description="Verified PSL and demo permission are both required before a phrase can be enabled"
      />

      <div className="p-6 max-w-[1400px]">
        <Card>
          {phrases.length === 0 ? (
            <Empty>No phrases defined.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1050px]">
                <thead>
                  <tr>
                    <th className="th">Phrase</th>
                    <th className="th">Urdu</th>
                    <th className="th">Category</th>
                    <th className="th">PSL verified</th>
                    <th className="th">Video rights</th>
                    <th className="th">Enabled</th>
                  </tr>
                </thead>
                <tbody>
                  {phrases.map((row) => {
                    const check = gate(row);
                    return (
                      <tr key={row.id} className="hover:bg-page/60">
                        <td className="td">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">{row.english_text}</span>
                            {row.is_demo_critical && (
                              <span className="pill-info text-[10px] py-0.5">demo</span>
                            )}
                          </div>
                          <div className="font-mono text-[10px] text-muted mt-0.5">{row.code}</div>
                        </td>
                        <td className="td">
                          <span className="urdu text-[17px]">{row.urdu_text}</span>
                        </td>
                        <td className="td text-muted text-xs">{row.category_name ?? "—"}</td>
                        <td className="td">
                          <button
                            onClick={() =>
                              update(row, {
                                verification_status:
                                  row.verification_status === "psl_verified"
                                    ? "draft"
                                    : "psl_verified",
                                verified_by:
                                  row.verification_status === "psl_verified"
                                    ? null
                                    : "Reviewed in admin console",
                              })
                            }
                            disabled={busy}
                          >
                            <StatusPill value={row.verification_status} />
                          </button>
                        </td>
                        <td className="td">
                          <StatusPill value={row.permission_status ?? "unknown"} />
                          {!check.permitted && (
                            <div className="text-[10px] text-amber-700 mt-1">
                              no demo playback
                            </div>
                          )}
                        </td>
                        <td className="td">
                          <button
                            onClick={() => update(row, { is_enabled: !row.is_enabled })}
                            disabled={busy || (!row.is_enabled && !check.ok)}
                            title={
                              check.ok
                                ? undefined
                                : [
                                    check.verified ? null : "PSL is not verified",
                                    check.hasVideo ? null : "No PSL video attached",
                                    check.permitted ? null : "Video has no demo-playback permission",
                                  ]
                                    .filter(Boolean)
                                    .join(" · ")
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
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <p className="text-xs text-muted mt-3">
          If a phrase cannot be verified, remove it. Never let an unqualified team member
          improvise medical PSL and present it as correct.
        </p>
      </div>

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}
