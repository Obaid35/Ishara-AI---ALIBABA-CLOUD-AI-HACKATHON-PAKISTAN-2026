"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { get, post } from "@/lib/api";
import { Card, PageHeader, Toast, useToast } from "@/components/admin/ui";
import type { Sign } from "@/lib/types";

/**
 * Record your own reference samples.
 *
 * Boundaries are manual: you press Start, perform the sign, press Stop. When
 * recording a template the signer knows exactly where the sign begins and
 * ends, and a wrong boundary poisons every future match against it. The server
 * still trims leading and trailing stillness so the edges match what live
 * capture produces.
 */

const TAKES_TARGET = 4;
const SEND_HZ = 25;
const FRAME_W = 640;
const FRAME_H = 480;
const FRAME_QUALITY = 0.7;

interface ClipRange {
  video: string;
  start_s: number;
  end_s: number;
}

interface Captured {
  frames: number;
  duration_s: number;
  hand_visibility: number;
  problems: string[];
}

// "starting" and "processing" are brief, but without them the UI looked
// frozen: a control message queues behind every buffered frame, so the
// server can take a moment to acknowledge it.
type Phase = "idle" | "starting" | "recording" | "processing" | "review";

function Spinner() {
  return (
    <svg viewBox="0 0 24 24" className="w-4 h-4 animate-spin" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" opacity="0.25" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3"
            strokeLinecap="round" />
    </svg>
  );
}

export default function RecordPage() {
  const [signs, setSigns] = useState<string[]>([]);
  const [clips, setClips] = useState<Record<string, ClipRange>>({});
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [participant, setParticipant] = useState("P01");
  const [active, setActive] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [captured, setCaptured] = useState<Captured | null>(null);
  const [connected, setConnected] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const toast = useToast();

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const timerRef = useRef<number | null>(null);
  const startedRef = useRef(0);
  const inFlightRef = useRef(false);
  const phaseRef = useRef<Phase>("idle");
  // Frames are only streamed while a take is in progress. Streaming when
  // idle filled the server's receive queue, so Start and Stop appeared to
  // lag by however many frames were already buffered.
  const sendingRef = useRef(false);

  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  // ---------------------------------------------------------------- setup
  const loadCounts = useCallback(async () => {
    try {
      const data = await get<{ per_sign: Record<string, { recorded: number }> }>(
        "/api/admin/references",
      );
      const next: Record<string, number> = {};
      for (const [code, info] of Object.entries(data.per_sign ?? {})) {
        next[code] = info.recorded ?? 0;
      }
      setCounts(next);
    } catch {
      setCounts({});
    }
  }, []);

  useEffect(() => {
    get<{ signs: Sign[] }>("/api/signs", false)
      .then((d) => {
        const codes = d.signs.map((s) => s.code).sort();
        setSigns(codes);
        setActive((current) => current ?? codes[0] ?? null);
      })
      .catch(() => setSigns([]));
    get<{ clips: Record<string, ClipRange> }>("/api/reference-clips", false)
      .then((d) => setClips(d.clips))
      .catch(() => setClips({}));
    void loadCounts();
  }, [loadCounts]);

  // ---------------------------------------------------------------- socket
  useEffect(() => {
    const url = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.hostname}:8000/ws/record`;
    let socket: WebSocket;
    try {
      socket = new WebSocket(url);
    } catch {
      return;
    }
    socketRef.current = socket;
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (raw) => {
      let msg: Record<string, unknown>;
      try {
        msg = JSON.parse(raw.data as string);
      } catch {
        return;
      }
      switch (msg.type) {
        case "recording":
          setPhase("recording");
          startedRef.current = performance.now();
          break;
        case "ready":
          // Sent after a discard; nothing to do but return to idle.
          break;
        case "captured":
          setPhase("review");
          setCaptured(msg as unknown as Captured);
          break;
        case "saved":
          setPhase("idle");
          setCaptured(null);
          toast.ok(`Saved ${msg.name}. ${msg.takes_for_sign} take(s) for ${msg.sign_code}.`);
          void loadCounts();
          break;
        case "error":
          sendingRef.current = false;
          setPhase("idle");
          setCaptured(null);
          toast.fail(String(msg.reason ?? "Recording failed."));
          break;
        default:
          break;
      }
    };
    return () => {
      socket.close();
      socketRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------------------------------------------------------- camera
  const startCamera = useCallback(async () => {
    if (streamRef.current) return;
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => undefined);
      }
      setCameraOn(true);
    } catch (error) {
      const name = (error as DOMException)?.name;
      setCameraError(
        name === "NotAllowedError"
          ? "Camera permission was denied. Allow access and try again."
          : "The camera could not be started.",
      );
    }
  }, []);

  useEffect(
    () => () => {
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    },
    [],
  );

  // Frames stream continuously; the server only keeps them between start/stop.
  useEffect(() => {
    if (!cameraOn) return;
    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
      canvasRef.current.width = FRAME_W;
      canvasRef.current.height = FRAME_H;
    }
    const context = canvasRef.current.getContext("2d");
    if (!context) return;

    const tick = () => {
      const video = videoRef.current;
      const socket = socketRef.current;
      if (!video || video.readyState < 2) return;
      if (!socket || socket.readyState !== WebSocket.OPEN) return;
      if (!sendingRef.current) return;
      if (inFlightRef.current || socket.bufferedAmount > 512 * 1024) return;

      if (phaseRef.current === "recording") {
        setElapsed((performance.now() - startedRef.current) / 1000);
      }

      context.drawImage(video, 0, 0, FRAME_W, FRAME_H);
      const capturedAt = Math.round(performance.now());
      inFlightRef.current = true;
      canvasRef.current!.toBlob(
        (blob) => {
          inFlightRef.current = false;
          if (!blob) return;
          const live = socketRef.current;
          if (!live || live.readyState !== WebSocket.OPEN) return;
          blob.arrayBuffer().then((buffer) => {
            if (live.readyState !== WebSocket.OPEN) return;
            const framed = new Uint8Array(4 + buffer.byteLength);
            new DataView(framed.buffer).setUint32(0, capturedAt >>> 0, true);
            framed.set(new Uint8Array(buffer), 4);
            live.send(framed);
          });
        },
        "image/jpeg",
        FRAME_QUALITY,
      );
    };

    timerRef.current = window.setInterval(tick, 1000 / SEND_HZ);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [cameraOn]);

  // ---------------------------------------------------------------- actions
  const send = (payload: Record<string, unknown>) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  };

  const total = useMemo(
    () => signs.reduce((sum, code) => sum + (counts[code] ?? 0), 0),
    [signs, counts],
  );
  const activeCount = active ? counts[active] ?? 0 : 0;
  const clip = active ? clips[active] : undefined;

  return (
    <>
      <PageHeader
        title="Record reference samples"
        description={`${TAKES_TARGET} takes per sign · your own performances become references`}
        actions={
          <div className="flex items-center gap-2">
            <span className={connected ? "pill-ok" : "pill-warn"}>
              {connected ? "connected" : "connecting…"}
            </span>
            <input
              value={participant}
              onChange={(e) => setParticipant(e.target.value.toUpperCase())}
              disabled={phase !== "idle"}
              className="h-9 w-24 px-2 rounded-lg border border-line bg-surface text-sm disabled:opacity-50"
              title="Who is recording"
            />
          </div>
        }
      />

      <div className="p-6 max-w-[1500px] space-y-5">
        <div className="card border-brand/30 bg-brand-soft px-4 py-3 text-sm">
          Dictionary clips did not transfer to a new signer — only 2 of 8 live attempts
          had the correct sign nearest. Recording your own takes fixes that for the people
          who record them. Aim for <strong>{TAKES_TARGET} takes per sign</strong>, signing
          naturally rather than copying the video exactly.
        </div>

        {/* signs to record */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {signs.map((code) => {
            const n = counts[code] ?? 0;
            const isActive = code === active;
            return (
              <button
                key={code}
                onClick={() => phase === "idle" && setActive(code)}
                disabled={phase !== "idle"}
                className={`card px-4 py-3 text-left transition-colors disabled:opacity-60 ${
                  isActive ? "border-brand ring-1 ring-brand" : "hover:border-brand/40"
                }`}
              >
                <div className="font-mono text-xs font-medium">{code}</div>
                <div className="flex items-center justify-between mt-1.5">
                  <span
                    className={
                      n >= TAKES_TARGET ? "pill-ok" : n > 0 ? "pill-info" : "pill-neutral"
                    }
                  >
                    {n} / {TAKES_TARGET}
                  </span>
                  {n >= TAKES_TARGET && (
                    <span className="text-[11px] text-brand">done</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-5">
          {/* ------------------------------------------------ what to copy */}
          <Card title="The sign" right={<span className="font-mono text-xs">{active}</span>}>
            <div className="p-4">
              {clip ? (
                <video
                  key={active ?? ""}
                  src={`${clip.video}#t=${clip.start_s},${clip.end_s}`}
                  autoPlay
                  muted
                  playsInline
                  onTimeUpdate={(e) => {
                    const v = e.currentTarget;
                    if (v.currentTime >= clip.end_s || v.currentTime < clip.start_s - 0.2) {
                      v.currentTime = clip.start_s;
                      void v.play();
                    }
                  }}
                  onLoadedMetadata={(e) => {
                    e.currentTarget.currentTime = clip.start_s;
                  }}
                  className="w-full rounded-lg border border-line bg-camera"
                />
              ) : (
                <div className="aspect-video rounded-lg bg-camera grid place-items-center text-white/50 text-sm">
                  no reference clip for this sign
                </div>
              )}
              <p className="text-[12px] text-muted mt-3">
                Watch it a few times first. Then sign it <strong>your own way</strong> — the
                point is to capture how you perform it, not to imitate the video frame by
                frame.
              </p>
            </div>
          </Card>

          {/* ------------------------------------------------ your camera */}
          <Card
            title="Your camera"
            right={
              phase === "recording" ? (
                <span className="pill-danger animate-pulse-soft">
                  ● recording {elapsed.toFixed(1)}s
                </span>
              ) : phase === "starting" ? (
                <span className="pill-info">starting…</span>
              ) : phase === "processing" ? (
                <span className="pill-info">processing…</span>
              ) : phase === "review" ? (
                <span className="pill-info">review</span>
              ) : (
                <span className="pill-neutral">ready</span>
              )
            }
          >
            <div className="relative aspect-video bg-camera">
              <video
                ref={videoRef}
                playsInline
                muted
                className="w-full h-full object-cover scale-x-[-1]"
              />
              {!cameraOn && (
                <div className="absolute inset-0 grid place-items-center">
                  <div className="text-center">
                    <button onClick={() => void startCamera()} className="btn-primary h-12 px-6">
                      Start camera
                    </button>
                    {cameraError && (
                      <p className="text-[12px] text-white/80 mt-3 px-6">{cameraError}</p>
                    )}
                  </div>
                </div>
              )}
              {phase === "recording" && (
                <>
                  <div className="absolute inset-0 ring-4 ring-inset ring-danger pointer-events-none" />
                  <div className="absolute top-3 left-3 pill bg-danger text-white border-white/20">
                    <span className="w-2 h-2 rounded-full bg-white animate-pulse-soft" />
                    REC {elapsed.toFixed(1)}s
                  </div>
                </>
              )}

              {(phase === "starting" || phase === "processing") && (
                <div className="absolute inset-0 bg-black/45 grid place-items-center pointer-events-none">
                  <div className="flex items-center gap-2.5 text-white text-sm font-medium">
                    <Spinner />
                    {phase === "starting"
                      ? "Getting the camera ready…"
                      : "Processing your take…"}
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 space-y-3">
              {phase === "review" && captured ? (
                <>
                  <div className="rounded-card border border-line bg-page px-4 py-3">
                    <div className="text-[11px] uppercase tracking-wider text-muted">
                      Take {activeCount + 1} for {active}
                    </div>
                    <div className="text-sm mt-1">
                      {captured.duration_s}s · {captured.frames} frames · hands{" "}
                      {(captured.hand_visibility * 100).toFixed(0)}%
                    </div>
                    {captured.problems.length > 0 && (
                      <ul className="text-[12px] text-amber-700 mt-2 space-y-0.5">
                        {captured.problems.map((p) => (
                          <li key={p}>· {p}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        sendingRef.current = false;
                        send({
                          type: "keep",
                          sign_code: active,
                          participant_code: participant,
                        });
                      }}
                      className="btn-primary flex-1 h-12"
                    >
                      Keep this take
                    </button>
                    <button
                      onClick={() => {
                        sendingRef.current = false;
                        send({ type: "discard" });
                        setPhase("idle");
                        setCaptured(null);
                      }}
                      className="btn-secondary h-12 px-5"
                    >
                      Redo
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <button
                    onClick={() => {
                      if (phase === "recording") {
                        // Stop streaming immediately so the queue drains and the
                        // server sees "stop" at once.
                        sendingRef.current = false;
                        setPhase("processing");
                        send({ type: "stop" });
                      } else if (phase === "idle") {
                        setElapsed(0);
                        setPhase("starting");
                        sendingRef.current = true;
                        send({ type: "start" });
                      }
                    }}
                    disabled={
                      !cameraOn ||
                      !connected ||
                      !active ||
                      phase === "starting" ||
                      phase === "processing"
                    }
                    className={
                      phase === "recording"
                        ? "btn w-full h-14 bg-danger text-white hover:bg-red-700 text-base"
                        : "btn-primary w-full h-14"
                    }
                  >
                    {phase === "starting" ? (
                      <>
                        <Spinner /> Getting ready…
                      </>
                    ) : phase === "processing" ? (
                      <>
                        <Spinner /> Processing take…
                      </>
                    ) : phase === "recording" ? (
                      `Stop — take ${activeCount + 1} of ${TAKES_TARGET}`
                    ) : (
                      `Start take ${activeCount + 1} of ${TAKES_TARGET} for ${active ?? ""}`
                    )}
                  </button>
                  <p className="text-[12px] text-muted">
                    Press <strong>Start</strong>, perform the sign once, press{" "}
                    <strong>Stop</strong>. Still moments at each end are trimmed
                    automatically. Then press Start again for the next take.
                  </p>
                </>
              )}
            </div>
          </Card>
        </div>

        {/* ------------------------------------------------ finish */}
        <Card title="When you are done">
          <div className="p-4 flex items-center justify-between gap-4">
            <p className="text-sm text-muted">
              {total} take{total === 1 ? "" : "s"} recorded across {signs.length} signs.
              Reload the library to make them count immediately, then run the live test
              again.
            </p>
            <button
              onClick={async () => {
                try {
                  const res = await post<{ detail: string }>("/api/admin/references/reload");
                  toast.ok(`Library reloaded — ${res.detail}`);
                } catch {
                  toast.fail("Could not reload the library.");
                }
              }}
              disabled={total === 0}
              className="btn-sm h-10 px-4 border-brand text-brand shrink-0"
            >
              Reload library
            </button>
          </div>
        </Card>
      </div>

      <Toast message={toast.toast?.message ?? null} tone={toast.toast?.tone} onDone={toast.clear} />
    </>
  );
}
