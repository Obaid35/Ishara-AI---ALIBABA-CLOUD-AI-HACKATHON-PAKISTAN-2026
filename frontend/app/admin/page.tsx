"use client";

import { useCallback, useEffect, useState } from "react";
import { get, post } from "@/lib/api";
import { Card, Empty, PageHeader, Stat, Toast, useToast } from "@/components/admin/ui";

interface Dashboard {
  counts: Record<string, number>;
  signs_by_status: Record<string, number>;
  demo_readiness: { item_type: string; code: string; blocker: string }[];
  permission_gaps: { path: string; permission_status: string; used_by: string }[];
  recognition_config: {
    tau_accept: number;
    delta_margin: number;
    frozen_on: string | null;
    notes: string;
  } | null;
  recent_tests: {
    run_on: string;
    test_level: string;
    sign_code: string;
    attempts: number;
    correct: number;
    wrong: number;
    unknown: number;
  }[];
  snapshot: { available: boolean; exported_at: string | null };
}

export default function AdminDashboard() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const load = useCallback(() => {
    get<Dashboard>("/api/admin/dashboard").then(setData).catch(() => setData(null));
  }, []);

  useEffect(load, [load]);

  const exportSnapshot = async () => {
    setBusy(true);
    try {
      const result = await post<{ counts: Record<string, number> }>("/api/admin/snapshot/export");
      toast.ok(
        `Snapshot exported — ${result.counts.signs} signs, ${result.counts.messages} messages, ` +
          `${result.counts.doctor_phrases} phrases.`,
      );
      load();
    } catch {
      toast.fail("Snapshot export failed.");
    } finally {
      setBusy(false);
    }
  };

  if (!data) {
    return (
      <>
        <PageHeader title="Dashboard" />
        <Empty>Loading…</Empty>
      </>
    );
  }

  const c = data.counts;
  const ready = data.demo_readiness.length === 0;
  const gapsClear = data.permission_gaps.length === 0;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Content status, demo readiness and permissions"
        actions={
          <button onClick={exportSnapshot} disabled={busy} className="btn-sm h-10 px-4">
            {busy ? "Exporting…" : "Export snapshot"}
          </button>
        }
      />

      <div className="p-6 space-y-5 max-w-[1400px]">
        {/* The two tiles that actually matter. */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Stat
            label="Reliable signs"
            value={c.reliable_signs}
            hint={`of ${c.total_signs} total — the only count quoted publicly`}
            tone="ok"
          />
          <Stat
            label="Demoable messages"
            value={c.demoable_messages}
            hint={`of ${c.total_messages} defined`}
          />
          <Stat
            label="Demoable phrases"
            value={c.demoable_phrases}
            hint={`of ${c.total_phrases} defined`}
          />
          <Stat
            label="Stale audio"
            value={c.stale_audio}
            hint={c.stale_audio ? "text and audio disagree" : "all audio matches its text"}
            tone={c.stale_audio ? "danger" : "ok"}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Card
            title="Demo readiness"
            right={
              <span className={ready ? "pill-ok" : "pill-warn"}>
                {ready ? "Ready" : `${data.demo_readiness.length} blocking`}
              </span>
            }
          >
            {ready ? (
              <Empty>
                Every demo-critical sign, message and phrase is ready.
              </Empty>
            ) : (
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="th">Type</th>
                    <th className="th">Item</th>
                    <th className="th">Blocker</th>
                  </tr>
                </thead>
                <tbody>
                  {data.demo_readiness.map((row, index) => (
                    <tr key={`${row.code}-${index}`}>
                      <td className="td text-muted">{row.item_type.replace("_", " ")}</td>
                      <td className="td font-mono text-xs">{row.code}</td>
                      <td className="td text-amber-700">{row.blocker}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          <Card
            title="Permission gaps"
            right={
              <span className={gapsClear ? "pill-ok" : "pill-danger"}>
                {gapsClear ? "Clear" : `${data.permission_gaps.length} unresolved`}
              </span>
            }
          >
            {gapsClear ? (
              <Empty>
                Every asset in use has a settled rights record.
              </Empty>
            ) : (
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="th">Asset</th>
                    <th className="th">Status</th>
                    <th className="th">Used by</th>
                  </tr>
                </thead>
                <tbody>
                  {data.permission_gaps.map((row, index) => (
                    <tr key={`${row.path}-${index}`}>
                      <td className="td font-mono text-[11px]">{row.path}</td>
                      <td className="td">
                        <span className="pill-warn">{row.permission_status ?? "unknown"}</span>
                      </td>
                      <td className="td text-muted text-xs">{row.used_by}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <Card title="Signs by status">
            <div className="p-4 space-y-2">
              {Object.entries(data.signs_by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-muted">{status.replace(/_/g, " ")}</span>
                  <span className="font-semibold tabular-nums">{count}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Recognition thresholds">
            <div className="p-4 space-y-2.5 text-sm">
              {data.recognition_config ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted">tau_accept</span>
                    <span className="font-mono">{data.recognition_config.tau_accept}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">delta_margin</span>
                    <span className="font-mono">{data.recognition_config.delta_margin}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted">Frozen</span>
                    {data.recognition_config.frozen_on ? (
                      <span className="pill-ok">
                        {new Date(data.recognition_config.frozen_on).toLocaleDateString()}
                      </span>
                    ) : (
                      <span className="pill-warn">Not frozen</span>
                    )}
                  </div>
                  <p className="text-[11px] text-muted pt-1 border-t border-line">
                    Freeze before the T4 unseen-person test. Changing them afterwards voids
                    that result.
                  </p>
                </>
              ) : (
                <p className="text-muted">No active configuration.</p>
              )}
            </div>
          </Card>

          <Card title="Snapshot">
            <div className="p-4 space-y-2.5 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-muted">Fallback file</span>
                <span className={data.snapshot.available ? "pill-ok" : "pill-warn"}>
                  {data.snapshot.available ? "Present" : "Missing"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Exported</span>
                <span className="text-xs">
                  {data.snapshot.exported_at
                    ? new Date(data.snapshot.exported_at).toLocaleString()
                    : "never"}
                </span>
              </div>
              <p className="text-[11px] text-muted pt-1 border-t border-line">
                Re-export after every content change. A stale snapshot can restore a sign you
                removed.
              </p>
            </div>
          </Card>
        </div>

        <Card title="Recent test results">
          {data.recent_tests.length === 0 ? (
            <Empty>No recognition tests recorded yet.</Empty>
          ) : (
            <table className="w-full">
              <thead>
                <tr>
                  <th className="th">Date</th>
                  <th className="th">Level</th>
                  <th className="th">Sign</th>
                  <th className="th">Attempts</th>
                  <th className="th">Correct</th>
                  <th className="th">Wrong</th>
                  <th className="th">Unknown</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_tests.map((row, index) => (
                  <tr key={index}>
                    <td className="td text-muted">{row.run_on}</td>
                    <td className="td font-mono text-[11px]">{row.test_level}</td>
                    <td className="td font-mono text-xs">{row.sign_code}</td>
                    <td className="td tabular-nums">{row.attempts}</td>
                    <td className="td tabular-nums text-brand">{row.correct}</td>
                    <td className="td tabular-nums text-danger">{row.wrong}</td>
                    <td className="td tabular-nums text-amber-600">{row.unknown}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}
