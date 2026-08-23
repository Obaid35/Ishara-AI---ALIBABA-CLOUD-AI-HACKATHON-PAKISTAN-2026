"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { get, patch } from "@/lib/api";
import { ApiError } from "@/lib/api";
import {
  Card,
  ConfirmPanel,
  Empty,
  PageHeader,
  StatusPill,
  Toast,
  useToast,
} from "@/components/admin/ui";

interface SignRow {
  id: string;
  code: string;
  urdu_meaning: string;
  english_meaning: string;
  verification_status: string;
  reliability_status: string;
  is_enabled: boolean;
  verified_by: string | null;
  is_demo_critical: boolean;
  notes: string;
  reference_count: number;
  used_by_messages: number;
}

interface Impact {
  messages: { code: string; is_enabled: boolean }[];
  enabled_count: number;
}

const RELIABILITY = ["candidate", "experimenting", "testing", "reliable", "weak", "dropped"];

export default function SignsPage() {
  const [signs, setSigns] = useState<SignRow[]>([]);
  const [filter, setFilter] = useState<"all" | "demo" | "reliable" | "blocked">("all");
  const [pending, setPending] = useState<{ sign: SignRow; status: string; impact: Impact } | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const load = useCallback(() => {
    get<{ signs: SignRow[] }>("/api/admin/signs")
      .then((data) => setSigns(data.signs))
      .catch(() => setSigns([]));
  }, []);

  useEffect(load, [load]);

  const visible = useMemo(
    () =>
      signs.filter((sign) => {
        if (filter === "demo") return sign.is_demo_critical;
        if (filter === "reliable") return sign.reliability_status === "reliable" && sign.is_enabled;
        if (filter === "blocked")
          return sign.is_demo_critical && !(sign.reliability_status === "reliable" && sign.is_enabled);
        return true;
      }),
    [signs, filter],
  );

  const apply = async (sign: SignRow, body: Record<string, unknown>) => {
    setBusy(true);
    try {
      await patch(`/api/admin/signs/${sign.id}`, body);
      toast.ok(`${sign.code} updated.`);
      load();
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Update failed.");
    } finally {
      setBusy(false);
      setPending(null);
    }
  };

  /** Demotion cascades — show exactly what breaks before it happens. */
  const changeReliability = async (sign: SignRow, status: string) => {
    const demoting = status !== "reliable" && sign.reliability_status === "reliable";
    if (demoting && sign.used_by_messages > 0) {
      try {
        const impact = await get<Impact>(`/api/admin/signs/${sign.id}/impact`);
        if (impact.enabled_count > 0) {
          setPending({ sign, status, impact });
          return;
        }
      } catch {
        /* fall through to the plain update */
      }
    }
    await apply(sign, {
      reliability_status: status,
      ...(status !== "reliable" ? { is_enabled: false } : {}),
    });
  };

  const blocked = signs.filter(
    (s) => s.is_demo_critical && !(s.reliability_status === "reliable" && s.is_enabled),
  ).length;

  return (
    <>
      <PageHeader
        title="Signs"
        description="Only Reliable + Enabled signs enter the production vocabulary"
        actions={
          <div className="flex gap-1.5">
            {(
              [
                ["all", `All ${signs.length}`],
                ["demo", "Demo-critical"],
                ["reliable", "Reliable"],
                ["blocked", `Blocking ${blocked}`],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                onClick={() => setFilter(value)}
                className={`px-3 h-9 rounded-lg text-xs font-medium border transition-colors ${
                  filter === value
                    ? "bg-brand text-white border-brand"
                    : "bg-surface text-muted border-line hover:bg-brand-soft"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        }
      />

      <div className="p-6 max-w-[1400px]">
        <Card>
          {visible.length === 0 ? (
            <Empty>No signs match this filter.</Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px]">
                <thead>
                  <tr>
                    <th className="th">Sign</th>
                    <th className="th">Urdu</th>
                    <th className="th">PSL verified</th>
                    <th className="th">Reliability</th>
                    <th className="th">Refs</th>
                    <th className="th">Messages</th>
                    <th className="th">Enabled</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((sign) => (
                    <tr key={sign.id} className="hover:bg-page/60">
                      <td className="td">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-medium">{sign.code}</span>
                          {sign.is_demo_critical && (
                            <span className="pill-info text-[10px] py-0.5">demo</span>
                          )}
                        </div>
                        <div className="text-[11px] text-muted mt-0.5">{sign.english_meaning}</div>
                      </td>
                      <td className="td">
                        <span className="urdu text-base">{sign.urdu_meaning}</span>
                      </td>
                      <td className="td">
                        <button
                          onClick={() =>
                            apply(sign, {
                              verification_status:
                                sign.verification_status === "psl_verified" ? "draft" : "psl_verified",
                              verified_by:
                                sign.verification_status === "psl_verified"
                                  ? null
                                  : "Reviewed in admin console",
                            })
                          }
                          disabled={busy}
                          title="Verification is by a Deaf signer, interpreter or trusted source"
                        >
                          <StatusPill value={sign.verification_status} />
                        </button>
                      </td>
                      <td className="td">
                        <select
                          value={sign.reliability_status}
                          onChange={(event) => void changeReliability(sign, event.target.value)}
                          disabled={busy}
                          className="h-8 px-2 rounded-lg border border-line bg-surface text-xs capitalize"
                        >
                          {RELIABILITY.map((status) => (
                            <option key={status} value={status}>
                              {status}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="td tabular-nums text-muted">{sign.reference_count}</td>
                      <td className="td tabular-nums text-muted">{sign.used_by_messages}</td>
                      <td className="td">
                        <button
                          onClick={() => apply(sign, { is_enabled: !sign.is_enabled })}
                          disabled={busy || sign.reliability_status !== "reliable"}
                          title={
                            sign.reliability_status !== "reliable"
                              ? "Only Reliable signs can be enabled"
                              : undefined
                          }
                          className={`relative w-11 h-6 rounded-full transition-colors disabled:opacity-30 ${
                            sign.is_enabled ? "bg-brand" : "bg-slate-300"
                          }`}
                        >
                          <span
                            className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${
                              sign.is_enabled ? "translate-x-[22px]" : "translate-x-0.5"
                            }`}
                          />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        <p className="text-xs text-muted mt-3">
          Demoting a sign automatically disables every message that depends on it. You will be
          shown exactly which messages before that happens.
        </p>
      </div>

      {pending && (
        <ConfirmPanel
          title={`Demote ${pending.sign.code} to "${pending.status}"?`}
          confirmLabel={`Demote and disable ${pending.impact.enabled_count} message${
            pending.impact.enabled_count === 1 ? "" : "s"
          }`}
          busy={busy}
          onCancel={() => setPending(null)}
          onConfirm={() =>
            void apply(pending.sign, {
              reliability_status: pending.status,
              is_enabled: false,
            })
          }
          body={
            <>
              <p>
                These enabled messages depend on this sign and will be disabled automatically:
              </p>
              <ul className="space-y-1">
                {pending.impact.messages
                  .filter((message) => message.is_enabled)
                  .map((message) => (
                    <li key={message.code} className="font-mono text-xs text-ink">
                      · {message.code}
                    </li>
                  ))}
              </ul>
            </>
          }
        />
      )}

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}
