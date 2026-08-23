"use client";

import type { CameraState } from "@/lib/useRecognition";
import type { RecognitionEventType } from "@/lib/types";

interface Props {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  cameraState: CameraState;
  cameraError: string | null;
  status: RecognitionEventType;
  motion: number;
  connected: boolean;
  isStub: boolean;
  onStart: () => void;
}

/** Camera framing guidance, shown until the camera is live. */
function Placeholder({
  cameraState,
  cameraError,
  onStart,
}: Pick<Props, "cameraState" | "cameraError" | "onStart">) {
  const denied = cameraState === "denied" || cameraState === "unavailable";

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-8 gap-5">
      <div
        className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
          denied ? "bg-danger/15" : "bg-white/10"
        }`}
      >
        <svg viewBox="0 0 24 24" className={`w-8 h-8 ${denied ? "text-danger" : "text-white/70"}`}
             fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"
             strokeLinejoin="round" aria-hidden="true">
          <path d="M23 7l-7 5 7 5V7z" />
          <rect x="1" y="5" width="15" height="14" rx="2" />
          {denied && <path d="M2 2l20 20" strokeWidth="2.2" />}
        </svg>
      </div>

      {denied ? (
        <>
          <p className="text-white/90 max-w-sm text-[15px]">{cameraError}</p>
          <button onClick={onStart} className="btn-secondary h-11 px-5">
            Try again
          </button>
        </>
      ) : cameraState === "starting" ? (
        <p className="text-white/70 animate-pulse-soft">Starting camera…</p>
      ) : (
        <>
          <div className="space-y-1.5">
            <p className="text-white/90 text-[15px] font-medium">Camera is off</p>
            <p className="text-white/55 text-sm max-w-xs">
              Sit so your face, upper body and both hands are inside the frame.
            </p>
          </div>
          <button onClick={onStart} className="btn-primary h-12 px-6">
            Start camera
          </button>
        </>
      )}
    </div>
  );
}

export default function CameraPanel({
  videoRef,
  cameraState,
  cameraError,
  status,
  motion,
  connected,
  isStub,
  onStart,
}: Props) {
  const live = cameraState === "ready";
  const capturing = status === "capturing" || status === "analyzing";

  return (
    <div className="relative flex-1 min-h-0 rounded-card overflow-hidden bg-camera border border-line">
      <video
        ref={videoRef}
        playsInline
        muted
        // Mirrored so signing feels natural, like a mirror.
        className={`w-full h-full object-cover scale-x-[-1] transition-opacity duration-300 ${
          live ? "opacity-100" : "opacity-0"
        }`}
      />

      {!live && (
        <Placeholder cameraState={cameraState} cameraError={cameraError} onStart={onStart} />
      )}

      {/* A capture in progress gets a calm ring, never a pulsing spectacle. */}
      {live && capturing && (
        <div className="absolute inset-0 ring-[3px] ring-inset ring-brand/70 rounded-card pointer-events-none transition-opacity" />
      )}

      {live && (
        <>
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <div className="pill bg-black/55 text-white border-white/15 backdrop-blur-sm">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  connected ? "bg-ok" : "bg-warn"
                }`}
              />
              {connected ? "Live" : "Reconnecting"}
            </div>
            {isStub && (
              <div
                className="pill bg-warn/90 text-white border-white/20 backdrop-blur-sm"
                title="The recognition engine is a stub. Results are simulated and must not be presented as sign recognition."
              >
                Simulated engine
              </div>
            )}
          </div>

          {/* Motion meter — makes it obvious the system is watching movement,
              and helps the signer understand why a capture started. */}
          <div className="absolute bottom-3 left-3 right-3 flex items-center gap-2.5">
            <span className="text-[10px] uppercase tracking-wider text-white/50 font-medium">
              Motion
            </span>
            <div className="flex-1 h-1.5 rounded-full bg-white/15 overflow-hidden">
              <div
                className={`h-full rounded-full transition-[width] duration-100 ${
                  capturing ? "bg-brand" : "bg-white/45"
                }`}
                style={{ width: `${Math.min(100, motion * 1600)}%` }}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
