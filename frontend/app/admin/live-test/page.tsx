"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, get, post } from "@/lib/api";
import { useRecognition } from "@/lib/useRecognition";
import { Card, PageHeader, Toast, useToast } from "@/components/admin/ui";
import type { RecognitionEvent, Sign } from "@/lib/types";

/**
 * Live recognition trial harness.
 *
 * The protocol is fixed before the test starts, so nobody decides after the
 * fact what counted: the expected sign is shown BEFORE the attempt, and the
 * outcome is recorded from what the recogniser returned, not from an opinion.
 *
 * Person A calibrates. Thresholds are then frozen. Person B runs untouched --
 * tuning during Person B's run would destroy the only real validation we have.
 */

// 10 for a full run; 2 or 5 for a quick diagnostic pass.
const ATTEMPT_OPTIONS = [2, 5, 10] as const;

// Settling pause when the prompt moves to a new sign.
//
// Without it the first attempt of every block was recorded against the wrong
// label: the previous attempt completes, the prompt switches, and the signer is
// still lowering their hand from the PREVIOUS sign. That residual movement
// starts a fresh capture, which the recogniser then reads correctly as the
// previous sign -- scored as "wrong" purely because the prompt had moved on.
// Every single wrong answer in the last run was exactly this.
const SETTLE_MS = 3000;

// Every attempt is written to PostgreSQL the moment it happens, into
// recognition_trials + recognition_tests. Nothing lives in browser memory that
// matters: close the tab, refresh, crash -- the session resumes from the
// database. Per-trial distances are also exactly what threshold calibration
// needs (docs/RECOGNITION_SPEC.md section 5).

type Outcome = "correct" | "wrong" | "unknown";

interface Trial {
  index: number;
  expected: string;
  got: string | null;
  outcome: Outcome;
  d1: number | null;
  d2: number | null;
  best: string | null;      // nearest reference, even when refused
  visibility: number | null; // fraction of the capture with a hand tracked
  at: number;
}

interface ServerTrial {
  expected: string;
  got: string | null;
  outcome: string;
  d1: number | string | null;
  d2: number | string | null;
  trial_index: number;
  test_level: string;
}

interface ClipRange {
  video: string;
  start_s: number;
  end_s: number;
  samples: number;
}

interface Thresholds {
  config: { tau_accept: number; delta_margin: number; frozen_on: string | null } | null;
}

export default function LiveTestPage() {
  const [signs, setSigns] = useState<string[]>([]);
  const [participant, setParticipant] = useState("P01");
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);
  const [trials, setTrials] = useState<Trial[]>([]);
  const [running, setRunning] = useState(false);
  const [cursor, setCursor] = useState(0);
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const [clips, setClips] = useState<Record<string, ClipRange>>({});
  const [restored, setRestored] = useState(false);
  const [attemptsPerSign, setAttemptsPerSign] = useState(10);
  const [settleUntil, setSettleUntil] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const settleUntilRef = useRef(0);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [pending, setPending] = useState(0);

  // P01 is the calibration run, anyone after is validation.
  const testLevel = participant === "P01" ? "t2_live_team" : "t3_second_person";
  const refVideoRef = useRef<HTMLVideoElement | null>(null);
  const expectedRef = useRef<string | null>(null);
  const participantRef = useRef("P01");
  const runningRef = useRef(false);

  // ---------------------------------------------------------------- setup
  useEffect(() => {
    get<{ signs: Sign[] }>("/api/signs", false)
      .then((d) => setSigns(d.signs.map((s) => s.code).sort()))
      .catch(() => setSigns([]));
    get<Thresholds>("/api/admin/thresholds").then(setThresholds).catch(() => undefined);
    get<{ clips: Record<string, ClipRange> }>("/api/reference-clips", false)
      .then((d) => setClips(d.clips))
      .catch(() => setClips({}));
  }, []);

  // Resume from the database. Switching participant loads that person's run.
  const loadSession = useCallback(async (code: string, level: string) => {
    setRestored(false);
    try {
      const data = await get<{ trials: ServerTrial[] }>(
        `/api/admin/testing/session?participant_code=${encodeURIComponent(code)}` +
          `&test_level=${encodeURIComponent(level)}`,
      );
      const restoredTrials: Trial[] = data.trials.map((row, index) => ({
        index,
        expected: row.expected,
        got: row.got,
        outcome:
          row.outcome === "correct"
            ? "correct"
            : row.outcome === "wrong"
              ? "wrong"
              : "unknown",
        d1: row.d1 === null ? null : Number(row.d1),
        d2: row.d2 === null ? null : Number(row.d2),
        best: row.got,
        visibility: null,
        at: 0,
      }));
      setTrials(restoredTrials);
      setCursor(restoredTrials.length);
    } catch {
      setTrials([]);
      setCursor(0);
    } finally {
      setRestored(true);
    }
  }, []);

  useEffect(() => {
    void loadSession(participant, testLevel);
  }, [participant, testLevel, loadSession]);

  // Per-sign counts drive everything. The next sign is simply the first one
  // that has not reached the target yet, so changing the target or clearing
  // part-way never leaves the prompt out of step with what is recorded.
  const counts = useMemo(() => {
    const map: Record<string, number> = {};
    for (const code of signs) map[code] = 0;
    for (const trial of trials) {
      if (trial.expected in map) map[trial.expected] += 1;
    }
    return map;
  }, [signs, trials]);

  const expected = useMemo(
    () => signs.find((code) => (counts[code] ?? 0) < attemptsPerSign) ?? null,
    [signs, counts, attemptsPerSign],
  );

  const previousExpected = useRef<string | null>(null);
  useEffect(() => {
    const before = previousExpected.current;
    previousExpected.current = expected;
    // Only settle on a genuine switch during a run, not on first load.
    if (before && expected && before !== expected && runningRef.current) {
      const until = Date.now() + SETTLE_MS;
      setSettleUntil(until);
      settleUntilRef.current = until;
      recognitionRef.current?.reset();
    }
  }, [expected]);

  // Drives the countdown display.
  useEffect(() => {
    if (settleUntil <= Date.now()) return;
    const id = window.setInterval(() => setNow(Date.now()), 100);
    return () => window.clearInterval(id);
  }, [settleUntil]);

  const settling = settleUntil > now;
  const settleLeft = Math.max(0, Math.ceil((settleUntil - now) / 1000));

  const planTotal = signs.length * attemptsPerSign;
  useEffect(() => {
    expectedRef.current = expected;
  }, [expected]);
  useEffect(() => {
    runningRef.current = running;
  }, [running]);
  useEffect(() => {
    participantRef.current = participant;
  }, [participant]);

  // ---------------------------------------------------------------- recording
  const handleResult = useCallback(
    (event: RecognitionEvent) => {
      if (!runningRef.current) return;
      const want = expectedRef.current;
      if (!want) return;

      // Discarded segments are incidental movement, not an attempt.
      if (event.type === "discarded") return;

      // Inside the settling window this is almost certainly the tail of the
      // PREVIOUS sign, not an attempt at the new one. Recording it would
      // mislabel a correct recognition as wrong.
      if (Date.now() < settleUntilRef.current) return;

      const correct = event.type === "recognized" && event.sign_code === want;
      const outcome: Outcome =
        event.type === "recognized" ? (correct ? "correct" : "wrong") : "unknown";

      // The precise stored outcome: an aborted capture is not the same thing
      // as "nothing matched", and calibration wants to tell them apart.
      const storedOutcome =
        event.type === "recognized"
          ? correct
            ? "recognized_correct"
            : "recognized_wrong"
          : event.type === "unknown_ambiguous"
            ? "unknown_ambiguous"
            : event.type === "aborted"
              ? "aborted"
              : "unknown_no_match";

      const d1 = event.d1 ?? null;
      const d2 = event.d2_diff_label ?? null;

      setTrials((current) => [
        ...current,
        { index: current.length, expected: want, got: event.sign_code ?? null,
          outcome, d1, d2,
          best: event.best_sign_code ?? null,
          visibility: event.hand_visibility ?? null,
          at: Date.now() },
      ]);
      setCursor((c) => c + 1);

      // Persist immediately. The optimistic row above keeps the UI instant;
      // a failure here is surfaced rather than silently losing the attempt.
      setPending((n) => n + 1);
      void post("/api/admin/testing/trial", {
        test_level: participantRef.current === "P01" ? "t2_live_team" : "t3_second_person",
        participant_code: participantRef.current,
        expected_sign_code: want,
        outcome: storedOutcome,
        top1_sign_code: event.best_sign_code ?? event.sign_code ?? null,
        d1,
        d2_diff_label: d2,
        accepted: event.type === "recognized",
        capture_frames: event.frames ?? null,
        capture_ms: event.duration_ms ?? null,
        hand_visibility: event.hand_visibility ?? null,
        capture_path: event.capture_path ?? null,
      })
        .then(() => setSaveError(null))
        .catch((error) =>
          setSaveError(
            error instanceof Error
              ? `Attempt not saved: ${error.message}`
              : "An attempt could not be saved to the database.",
          ),
        )
        .finally(() => setPending((n) => Math.max(0, n - 1)));
    },
    [],
  );

  const recognition = useRecognition(handleResult, true);
  const recognitionRef = useRef(recognition);
  useEffect(() => {
    recognitionRef.current = recognition;
  }, [recognition]);

  // ---------------------------------------------------------------- summary
  const summary = useMemo(() => {
    const rows = signs.map((code) => {
      const mine = trials.filter((t) => t.expected === code);
      return {
        code,
        attempts: mine.length,
        correct: mine.filter((t) => t.outcome === "correct").length,
        wrong: mine.filter((t) => t.outcome === "wrong").length,
        unknown: mine.filter((t) => t.outcome === "unknown").length,
      };
    });
    const total = {
      attempts: trials.length,
      correct: trials.filter((t) => t.outcome === "correct").length,
      wrong: trials.filter((t) => t.outcome === "wrong").length,
      unknown: trials.filter((t) => t.outcome === "unknown").length,
    };
    return { rows, total };
  }, [signs, trials]);

  const confusion = useMemo(() => {
    const map: Record<string, Record<string, number>> = {};
    for (const code of signs) {
      map[code] = {};
      for (const other of [...signs, "UNKNOWN"]) map[code][other] = 0;
    }
    for (const t of trials) {
      const key = t.outcome === "unknown" ? "UNKNOWN" : t.got ?? "UNKNOWN";
      if (map[t.expected] && key in map[t.expected]) map[t.expected][key] += 1;
    }
    return map;
  }, [signs, trials]);

  // ---------------------------------------------------------------- actions
  const clearSession = async () => {
    if (
      trials.length > 0 &&
      !window.confirm(
        `Delete all ${trials.length} recorded attempt(s) for ${participant} from the ` +
          `database? This cannot be undone.`,
      )
    ) {
      return;
    }
    setSaving(true);
    try {
      await api(
        `/api/admin/testing/session?participant_code=${encodeURIComponent(participant)}`,
        { method: "DELETE" },
      );
      setTrials([]);
      setCursor(0);
      setRunning(false);
      recognition.reset();
      toast.ok(`Cleared ${participant}'s attempts.`);
    } catch {
      toast.fail("Could not clear the session.");
    } finally {
      setSaving(false);
    }
  };

  const frozen = Boolean(thresholds?.config?.frozen_on);
  const done = expected === null && signs.length > 0;
  const perSignDone = expected ? counts[expected] ?? 0 : 0;

  const last = trials.length ? trials[trials.length - 1] : null;
  const tau = thresholds?.config?.tau_accept ?? null;

  // Why the gate refused, in plain words. Guessing from the numbers is the
  // whole point of showing them.
  const rejection = (() => {
    if (!last || last.outcome !== "unknown" || last.d1 === null) return null;
    if (tau !== null && last.d1 > tau) {
      return `no match was close enough — best distance ${last.d1.toFixed(3)} is above the accept threshold ${tau}`;
    }
    if (last.d1 !== null && last.d2 !== null) {
      const margin = ((last.d2 - last.d1) / last.d1) * 100;
      return `two signs looked too similar — only ${margin.toFixed(0)}% apart`;
    }
    return "the movement did not produce a usable sequence";
  })();

  return (
    <>
      <PageHeader
        title="Live recognition test"
        description={`${attemptsPerSign} attempts per sign · every attempt saved to the database`}
        actions={
          <div className="flex items-center gap-2">
            <span className={frozen ? "pill-ok" : "pill-warn"}>
              {frozen ? "thresholds frozen" : "thresholds NOT frozen"}
            </span>
            <select
              value={attemptsPerSign}
              onChange={(e) => setAttemptsPerSign(Number(e.target.value))}
              disabled={running}
              title="How many attempts per sign before moving on"
              className="h-9 px-2 rounded-lg border border-line bg-surface text-sm disabled:opacity-50"
            >
              {ATTEMPT_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n} per sign ({n * 4} total)
                </option>
              ))}
            </select>
            <select
              value={participant}
              onChange={(e) => setParticipant(e.target.value)}
              disabled={running || trials.length > 0}
              className="h-9 px-2 rounded-lg border border-line bg-surface text-sm disabled:opacity-50"
            >
              <option value="P01">Person A (P01) — calibration</option>
              <option value="P02">Person B (P02) — validation</option>
            </select>
          </div>
        }
      />

      <div className="p-6 max-w-[1500px] space-y-5">
        {saveError && (
          <div className="card border-danger/40 bg-red-50 px-4 py-3 text-sm text-danger">
            <strong>{saveError}</strong> The attempt is shown below but is NOT in the
            database. Check the API is running before continuing, or the run will be
            incomplete.
          </div>
        )}

        {participant === "P02" && !frozen && (
          <div className="card border-danger/40 bg-red-50 px-4 py-3 text-sm text-danger">
            <strong>Freeze the thresholds before testing Person B.</strong> Tuning on
            Person B&apos;s data destroys the only strong validation this project has.
            Go to <span className="font-mono">/admin/testing</span> and freeze first.
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(420px,1fr)] gap-5">
          {/* ------------------------------------------------ camera + prompt */}
          <Card>
            <div className="relative aspect-video bg-camera">
              <video
                ref={recognition.videoRef}
                playsInline
                muted
                className="w-full h-full object-cover scale-x-[-1]"
              />
              {recognition.cameraState !== "ready" && (
                <div className="absolute inset-0 grid place-items-center">
                  <button
                    onClick={() => void recognition.startCamera()}
                    className="btn-primary h-12 px-6"
                  >
                    Start camera
                  </button>
                </div>
              )}
              {recognition.cameraState === "ready" && (
                <>
                  <div className="absolute top-3 left-3 flex gap-2">
                    <span
                      className={`pill border-white/15 text-white ${
                        settling
                          ? "bg-amber-500"
                          : recognition.status === "capturing" ||
                              recognition.status === "analyzing"
                            ? "bg-brand"
                            : "bg-black/55"
                      }`}
                    >
                      {settling
                        ? `get ready — ${settleLeft}s`
                        : recognition.status === "capturing"
                          ? "reading your sign…"
                          : recognition.status === "analyzing"
                            ? "analyzing…"
                            : recognition.status.replace(/_/g, " ")}
                    </span>
                    <span className="pill bg-black/55 text-white border-white/15">
                      engine {recognition.lastEvent?.engine ?? "?"}
                    </span>
                  </div>

                  {(recognition.status === "capturing" ||
                    recognition.status === "analyzing") &&
                    !settling && (
                      <div className="absolute inset-0 ring-4 ring-inset ring-brand/70 pointer-events-none" />
                    )}

                  {settling && (
                    <div className="absolute inset-0 bg-black/60 grid place-items-center">
                      <div className="text-center px-6">
                        <div className="text-[11px] uppercase tracking-wider text-white/60">
                          Next sign
                        </div>
                        <div className="text-4xl font-bold text-white mt-1">{expected}</div>
                        <div className="text-white/80 text-sm mt-3">
                          Lower your hands and get ready — {settleLeft}s
                        </div>
                        <div className="text-white/50 text-[12px] mt-2 max-w-xs">
                          Nothing is recorded during this pause.
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Motion meter: if this never moves, the camera is not
                      seeing your hands and no attempt will ever register. */}
                  <div className="absolute bottom-3 left-3 right-3 flex items-center gap-2.5">
                    <span className="text-[10px] uppercase tracking-wider text-white/60 font-medium">
                      Motion
                    </span>
                    <div className="flex-1 h-2 rounded-full bg-white/20 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-[width] duration-100 ${
                          recognition.status === "capturing" ? "bg-brand" : "bg-white/60"
                        }`}
                        style={{ width: `${Math.min(100, recognition.motion * 1600)}%` }}
                      />
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="p-5 border-t border-line">
              {done ? (
                <div className="text-center py-3">
                  <div className="text-lg font-semibold text-brand">All attempts complete</div>
                  <div className="text-sm text-muted mt-1">
                    {summary.total.attempts} attempts recorded and saved to the database.
                  </div>
                </div>
              ) : expected ? (
                <>
                  <div className="flex items-start gap-4">
                    {/* Watch and copy. The reference is the exact clip the
                        matcher compares against. */}
                    <div className="shrink-0">
                      {clips[expected] ? (
                        <video
                          key={expected}
                          ref={refVideoRef}
                          src={`${clips[expected].video}#t=${clips[expected].start_s},${clips[expected].end_s}`}
                          autoPlay
                          muted
                          playsInline
                          // Loop only the sign's range, not the whole video.
                          onTimeUpdate={(e) => {
                            const v = e.currentTarget;
                            const { start_s, end_s } = clips[expected];
                            if (v.currentTime >= end_s || v.currentTime < start_s - 0.2) {
                              v.currentTime = start_s;
                              void v.play();
                            }
                          }}
                          onLoadedMetadata={(e) => {
                            e.currentTarget.currentTime = clips[expected].start_s;
                          }}
                          className="w-44 rounded-lg border border-line bg-camera"
                        />
                      ) : (
                        <div className="w-44 h-32 rounded-lg border border-line bg-camera grid place-items-center text-[11px] text-white/50 px-3 text-center">
                          reference clip unavailable
                        </div>
                      )}
                      <div className="text-[10px] text-center text-muted mt-1">
                        copy this movement
                      </div>
                    </div>

                    <div className="min-w-0">
                      <div className="text-[11px] uppercase tracking-wider text-muted">
                        Perform this sign
                      </div>
                      <div className="text-4xl font-bold tracking-tight mt-1">{expected}</div>
                      <div className="text-sm text-muted mt-2">
                        attempt {perSignDone + 1} of {attemptsPerSign} for this sign ·{" "}
                        {trials.length} of {planTotal} overall
                      </div>
                      <ol className="text-[12px] text-muted mt-2.5 space-y-0.5 list-decimal list-inside">
                        <li>Watch the clip on the left</li>
                        <li>Copy it in front of the camera</li>
                        <li>Stop and hold still — the pause ends the attempt</li>
                      </ol>
                    </div>
                  </div>
                  <div className="mt-3 h-1.5 rounded-full bg-page overflow-hidden">
                    <div
                      className="h-full bg-brand transition-[width]"
                      style={{ width: `${(trials.length / Math.max(1, planTotal)) * 100}%` }}
                    />
                  </div>
                </>
              ) : (
                <div className="text-sm text-muted">No enabled signs to test.</div>
              )}

              {/* ---------------------------------------- what it detected */}
              {last && (
                <div
                  key={last.index}
                  className={`mt-4 rounded-card border px-4 py-3 animate-fade-up ${
                    last.outcome === "correct"
                      ? "bg-brand-soft border-brand/30"
                      : last.outcome === "wrong"
                        ? "bg-red-50 border-danger/30"
                        : "bg-amber-50 border-warn/30"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-[11px] uppercase tracking-wider text-muted">
                      Attempt {last.index + 1} · you performed {last.expected}
                    </div>
                    <span
                      className={
                        last.outcome === "correct"
                          ? "pill-ok"
                          : last.outcome === "wrong"
                            ? "pill-danger"
                            : "pill-warn"
                      }
                    >
                      {last.outcome}
                    </span>
                  </div>

                  <div className="mt-1.5 flex items-baseline gap-2">
                    <span className="text-[13px] text-muted">detected:</span>
                    <span
                      className={`text-2xl font-bold tracking-tight ${
                        last.outcome === "correct"
                          ? "text-brand"
                          : last.outcome === "wrong"
                            ? "text-danger"
                            : "text-amber-700"
                      }`}
                    >
                      {last.got ?? "nothing — refused to guess"}
                    </span>
                  </div>

                  {rejection && (
                    <p className="text-[12px] text-amber-800 mt-1.5">{rejection}</p>
                  )}

                  {/* Even a refusal says which reference was nearest. That is
                      what tells you whether raising tau would help or would
                      start producing confident errors. */}
                  {last.outcome === "unknown" && last.best && (
                    <p className="text-[12px] mt-1">
                      nearest reference was{" "}
                      <strong
                        className={
                          last.best === last.expected ? "text-brand" : "text-danger"
                        }
                      >
                        {last.best}
                      </strong>
                      {last.best === last.expected
                        ? " — correct order, only the threshold rejected it"
                        : " — the wrong sign was closest"}
                    </p>
                  )}

                  {last.visibility !== null && last.visibility < 0.6 && (
                    <p className="text-[12px] text-danger mt-1">
                      hands tracked in only {(last.visibility * 100).toFixed(0)}% of the
                      capture — keep both hands in frame and improve the lighting
                    </p>
                  )}

                  {last.d1 !== null && (
                    <div className="text-[11px] text-muted mt-2 font-mono">
                      d1={last.d1.toFixed(3)}
                      {last.d2 !== null && ` · d2=${last.d2.toFixed(3)}`}
                      {last.d1 && last.d2 !== null &&
                        ` · margin=${(((last.d2 - last.d1) / last.d1) * 100).toFixed(0)}%`}
                      {tau !== null && ` · accept ≤ ${tau}`}
                      {last.visibility !== null &&
                        ` · hands ${(last.visibility * 100).toFixed(0)}%`}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => setRunning((r) => !r)}
                  disabled={recognition.cameraState !== "ready" || done}
                  className={running ? "btn-quiet flex-1 h-12" : "btn-primary flex-1 h-12"}
                >
                  {running ? "Pause recording" : "Start recording attempts"}
                </button>
                <button
                  onClick={() => void clearSession()}
                  disabled={saving}
                  className="btn-secondary h-12 px-4"
                >
                  Reset
                </button>
              </div>

              {running && (
                <p className="text-[12px] text-muted mt-3">
                  Sign naturally, then <strong>pause and hold still</strong> — the pause is
                  what ends the capture. Each completed movement is recorded as one attempt.
                  Incidental movement is discarded, not counted.
                  {trials.length === 0 && recognition.motion < 0.005 && (
                    <span className="block mt-1.5 text-amber-700">
                      The motion bar is not moving. Make sure both hands are inside the
                      frame and well lit — nothing is recorded until hands are tracked.
                    </span>
                  )}
                </p>
              )}
            </div>
          </Card>

          {/* ------------------------------------------------ results */}
          <div className="space-y-5">
            <Card title="Results" right={<span className="pill-neutral">{participant}</span>}>
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="th">Sign</th>
                    <th className="th text-right">n</th>
                    <th className="th text-right">Correct</th>
                    <th className="th text-right">Wrong</th>
                    <th className="th text-right">Unknown</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.rows.map((row) => (
                    <tr key={row.code}>
                      <td className="td font-mono text-xs">{row.code}</td>
                      <td className="td text-right tabular-nums">{row.attempts}</td>
                      <td className="td text-right tabular-nums text-brand font-medium">
                        {row.correct}
                      </td>
                      <td className="td text-right tabular-nums text-danger font-medium">
                        {row.wrong}
                      </td>
                      <td className="td text-right tabular-nums text-amber-600 font-medium">
                        {row.unknown}
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-page/60">
                    <td className="td font-semibold">Total</td>
                    <td className="td text-right tabular-nums font-semibold">
                      {summary.total.attempts}
                    </td>
                    <td className="td text-right tabular-nums font-semibold text-brand">
                      {summary.total.correct}
                    </td>
                    <td className="td text-right tabular-nums font-semibold text-danger">
                      {summary.total.wrong}
                    </td>
                    <td className="td text-right tabular-nums font-semibold text-amber-600">
                      {summary.total.unknown}
                    </td>
                  </tr>
                </tbody>
              </table>

              {summary.total.attempts > 0 && (
                <div className="px-4 py-3 border-t border-line text-sm">
                  <span className="text-muted">Correct: </span>
                  <span className="font-semibold">
                    {((summary.total.correct / summary.total.attempts) * 100).toFixed(1)}%
                  </span>
                  <span className="text-muted"> of {summary.total.attempts} </span>
                  <span className="text-muted">
                    · wrong {((summary.total.wrong / summary.total.attempts) * 100).toFixed(1)}%
                    · unknown{" "}
                    {((summary.total.unknown / summary.total.attempts) * 100).toFixed(1)}%
                  </span>
                </div>
              )}

              <div className="p-4 border-t border-line flex items-center justify-between gap-3">
                <div className="text-[12px] flex items-center gap-2">
                  {saveError ? (
                    <span className="pill-danger">not saved</span>
                  ) : pending > 0 ? (
                    <span className="pill-info">saving {pending}…</span>
                  ) : (
                    <span className="pill-ok">saved to database</span>
                  )}
                  <span className="text-muted">
                    {trials.length} attempt{trials.length === 1 ? "" : "s"} recorded
                  </span>
                </div>
                <button
                  onClick={() => void clearSession()}
                  disabled={saving || trials.length === 0}
                  className="btn-sm text-danger border-danger/30"
                >
                  Clear {participant}
                </button>
              </div>
            </Card>

            <Card title="Confusion matrix" right={<span className="text-[11px] text-muted">expected → got</span>}>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="th"></th>
                      {[...signs, "UNKNOWN"].map((c) => (
                        <th key={c} className="th text-center text-[10px]">
                          {c.slice(0, 8)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {signs.map((row) => (
                      <tr key={row}>
                        <td className="td font-mono text-[11px]">{row}</td>
                        {[...signs, "UNKNOWN"].map((col) => {
                          const v = confusion[row]?.[col] ?? 0;
                          const diagonal = row === col;
                          return (
                            <td
                              key={col}
                              className={`td text-center tabular-nums ${
                                v === 0
                                  ? "text-muted/40"
                                  : diagonal
                                    ? "text-brand font-semibold"
                                    : col === "UNKNOWN"
                                      ? "text-amber-600"
                                      : "text-danger font-semibold"
                              }`}
                            >
                              {v || "·"}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>

            <Card title="Recent attempts">
              <div className="scroll-area max-h-56">
                <table className="w-full">
                  <tbody>
                    {[...trials].reverse().slice(0, 20).map((t) => (
                      <tr key={t.index}>
                        <td className="td text-[11px] text-muted w-8">{t.index + 1}</td>
                        <td className="td font-mono text-[11px]">{t.expected}</td>
                        <td className="td text-[11px]">
                          <span
                            className={
                              t.outcome === "correct"
                                ? "pill-ok"
                                : t.outcome === "wrong"
                                  ? "pill-danger"
                                  : "pill-warn"
                            }
                          >
                            {t.outcome === "wrong" ? `wrong → ${t.got}` : t.outcome}
                          </span>
                        </td>
                        <td className="td text-[11px] text-muted tabular-nums">
                          {t.d1 !== null ? `d1=${t.d1.toFixed(3)}` : ""}
                          {t.d2 !== null ? `  d2=${t.d2.toFixed(3)}` : ""}
                        </td>
                      </tr>
                    ))}
                    {trials.length === 0 && (
                      <tr>
                        <td className="td text-sm text-muted text-center py-6">
                          No attempts yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      </div>

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}
