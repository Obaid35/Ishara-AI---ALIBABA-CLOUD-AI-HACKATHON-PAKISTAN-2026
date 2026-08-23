"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, get, patch, post } from "@/lib/api";
import { Card, Empty, PageHeader, Stat, Toast, useToast } from "@/components/admin/ui";

interface TestRow {
  id: string;
  run_on: string;
  test_level: string;
  sign_code: string;
  participant_code: string | null;
  is_unseen: boolean | null;
  attempts: number;
  correct: number;
  wrong: number;
  unknown: number;
  confusion_code: string | null;
  notes: string;
}

interface SignOption {
  code: string;
}

const LEVELS = [
  ["t1_source", "T1 — source clip (sanity only)"],
  ["t2_live_team", "T2 — live team member"],
  ["t3_second_person", "T3 — second person"],
  ["t4_unseen", "T4 — unseen person (strongest)"],
  ["t5_room_variation", "T5 — room variation"],
] as const;

export default function TestingPage() {
  const [tests, setTests] = useState<TestRow[]>([]);
  const [totals, setTotals] = useState({ attempts: 0, correct: 0, wrong: 0, unknown: 0 });
  const [signs, setSigns] = useState<SignOption[]>([]);
  const [thresholds, setThresholds] = useState<{
    config: { tau_accept: number; delta_margin: number; frozen_on: string | null } | null;
    last_t4_run: string | null;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  const [form, setForm] = useState({
    test_level: "t2_live_team",
    sign_code: "",
    participant_code: "P01",
    attempts: 10,
    correct: 0,
    wrong: 0,
    unknown: 0,
    top_confusion_sign_code: "",
    notes: "",
  });

  const load = useCallback(() => {
    get<{ tests: TestRow[]; totals: typeof totals }>("/api/admin/testing")
      .then((data) => {
        setTests(data.tests);
        setTotals(data.totals);
      })
      .catch(() => setTests([]));
    get<{ signs: SignOption[] }>("/api/admin/signs")
      .then((data) => {
        setSigns(data.signs);
        setForm((current) =>
          current.sign_code ? current : { ...current, sign_code: data.signs[0]?.code ?? "" },
        );
      })
      .catch(() => setSigns([]));
    get<typeof thresholds>("/api/admin/thresholds").then(setThresholds).catch(() => undefined);
  }, []);

  useEffect(load, [load]);

  const sum = form.correct + form.wrong + form.unknown;
  const balanced = sum === form.attempts;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      await post("/api/admin/testing", {
        ...form,
        top_confusion_sign_code: form.top_confusion_sign_code || null,
        participant_code: form.participant_code || null,
      });
      toast.ok("Result recorded.");
      setForm({ ...form, correct: 0, wrong: 0, unknown: 0, notes: "" });
      load();
    } catch (error) {
      toast.fail(error instanceof ApiError ? error.message : "Could not record the result.");
    } finally {
      setBusy(false);
    }
  };

  const freeze = async () => {
    setBusy(true);
    try {
      await post("/api/admin/thresholds/freeze");
      toast.ok("Thresholds frozen. Run the T4 unseen-person test now.");
      load();
    } catch {
      toast.fail("Could not freeze thresholds.");
    } finally {
      setBusy(false);
    }
  };

  const rate = (value: number) =>
    totals.attempts ? `${((value / totals.attempts) * 100).toFixed(1)}%` : "—";

  return (
    <>
      <PageHeader
        title="Testing"
        description="Unknown is tracked separately from wrong — they are different behaviours"
      />

      <div className="p-6 max-w-[1400px] space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Stat label="Attempts" value={totals.attempts} hint="the denominator" />
          <Stat label="Correct" value={totals.correct} hint={rate(totals.correct)} tone="ok" />
          <Stat
            label="Wrong"
            value={totals.wrong}
            hint={`${rate(totals.wrong)} — target ≤ 2%`}
            tone={totals.attempts && totals.wrong / totals.attempts > 0.02 ? "danger" : "ok"}
          />
          <Stat label="Unknown" value={totals.unknown} hint={`${rate(totals.unknown)} — by design`} tone="warn" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_360px] gap-5 items-start">
          <Card title="Recorded results">
            {tests.length === 0 ? (
              <Empty>No results yet. Record the Day-1 trials here.</Empty>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[820px]">
                  <thead>
                    <tr>
                      <th className="th">Date</th>
                      <th className="th">Level</th>
                      <th className="th">Sign</th>
                      <th className="th">Person</th>
                      <th className="th">n</th>
                      <th className="th">✓</th>
                      <th className="th">✗</th>
                      <th className="th">?</th>
                      <th className="th">Confusion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tests.map((row) => (
                      <tr key={row.id} className="hover:bg-page/60">
                        <td className="td text-muted text-xs">{row.run_on}</td>
                        <td className="td font-mono text-[11px]">{row.test_level}</td>
                        <td className="td font-mono text-xs">{row.sign_code}</td>
                        <td className="td text-xs">
                          {row.participant_code ?? "—"}
                          {row.is_unseen && <span className="pill-info ml-1.5 text-[10px] py-0">unseen</span>}
                        </td>
                        <td className="td tabular-nums">{row.attempts}</td>
                        <td className="td tabular-nums text-brand font-medium">{row.correct}</td>
                        <td className="td tabular-nums text-danger font-medium">{row.wrong}</td>
                        <td className="td tabular-nums text-amber-600 font-medium">{row.unknown}</td>
                        <td className="td font-mono text-[11px] text-muted">
                          {row.confusion_code ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          <div className="space-y-5">
            <Card title="Record a result">
              <form onSubmit={submit} className="p-4 space-y-3">
                <div>
                  <label className="label">Test level</label>
                  <select
                    value={form.test_level}
                    onChange={(event) => setForm({ ...form, test_level: event.target.value })}
                    className="input"
                  >
                    {LEVELS.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label">Sign</label>
                    <select
                      value={form.sign_code}
                      onChange={(event) => setForm({ ...form, sign_code: event.target.value })}
                      className="input"
                    >
                      {signs.map((sign) => (
                        <option key={sign.code} value={sign.code}>
                          {sign.code}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">Participant</label>
                    <input
                      value={form.participant_code}
                      onChange={(event) =>
                        setForm({ ...form, participant_code: event.target.value })
                      }
                      placeholder="P01"
                      className="input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-2">
                  {(["attempts", "correct", "wrong", "unknown"] as const).map((field) => (
                    <div key={field}>
                      <label className="label capitalize text-[11px]">{field}</label>
                      <input
                        type="number"
                        min={0}
                        value={form[field]}
                        onChange={(event) =>
                          setForm({ ...form, [field]: Number(event.target.value) })
                        }
                        className="input px-2 text-center tabular-nums"
                      />
                    </div>
                  ))}
                </div>

                <p className={`text-[11px] ${balanced ? "text-muted" : "text-danger"}`}>
                  correct + wrong + unknown = {sum}, attempts = {form.attempts}
                  {!balanced && " — these must match"}
                </p>

                <div>
                  <label className="label">Top confusion (optional)</label>
                  <select
                    value={form.top_confusion_sign_code}
                    onChange={(event) =>
                      setForm({ ...form, top_confusion_sign_code: event.target.value })
                    }
                    className="input"
                  >
                    <option value="">—</option>
                    {signs.map((sign) => (
                      <option key={sign.code} value={sign.code}>
                        {sign.code}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={busy || !balanced || !form.sign_code}
                  className="btn h-11 w-full bg-brand text-white hover:bg-brand-hover text-sm"
                >
                  {busy ? "Saving…" : "Record result"}
                </button>
              </form>
            </Card>

            <Card title="Thresholds">
              <div className="p-4 space-y-3 text-sm">
                {thresholds?.config ? (
                  <>
                    <div className="flex justify-between">
                      <span className="text-muted">tau_accept</span>
                      <span className="font-mono">{thresholds.config.tau_accept}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">delta_margin</span>
                      <span className="font-mono">{thresholds.config.delta_margin}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-muted">Status</span>
                      {thresholds.config.frozen_on ? (
                        <span className="pill-ok">frozen</span>
                      ) : (
                        <span className="pill-warn">not frozen</span>
                      )}
                    </div>
                    {!thresholds.config.frozen_on && (
                      <button
                        onClick={freeze}
                        disabled={busy}
                        className="btn-sm w-full h-10 border-brand text-brand"
                      >
                        Freeze thresholds
                      </button>
                    )}
                    <p className="text-[11px] text-muted pt-2 border-t border-line">
                      Freeze <strong>before</strong> the T4 unseen-person test. Tuning on that
                      person&apos;s data destroys the only strong validation the project has.
                    </p>
                  </>
                ) : (
                  <p className="text-muted">No active configuration.</p>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}
