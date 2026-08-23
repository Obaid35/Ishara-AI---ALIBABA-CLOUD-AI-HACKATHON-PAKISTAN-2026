"use client";

import type { Message } from "@/lib/types";

interface Props {
  concepts: string[];
  message: Message | null;
  matched: "exact" | "base" | "none" | null;
  note: string | null;
  speaking: boolean;
  speechError: string | null;
  onSpeak: () => void;
  onUndo: () => void;
  onClear: () => void;
}

/**
 * The visual hero. Largest text on the screen, and it stays visible until the
 * user changes or clears it.
 *
 * Nothing here speaks automatically — speech requires the explicit press of
 * Speak, no matter how confident recognition was.
 */
export default function MessageCard({
  concepts,
  message,
  matched,
  note,
  speaking,
  speechError,
  onSpeak,
  onUndo,
  onClear,
}: Props) {
  const empty = concepts.length === 0;
  const canSpeak = Boolean(message) && !speaking;

  return (
    <section className="card p-5 flex flex-col gap-4 flex-1 min-h-0">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
          Current message
        </h2>
        {concepts.length > 0 && (
          <span className="text-[11px] text-muted tabular-nums">
            {concepts.length} sign{concepts.length === 1 ? "" : "s"}
          </span>
        )}
      </div>

      {/* Recognised concepts, in the order they were signed. */}
      {!empty && (
        <div className="flex flex-wrap gap-1.5">
          {concepts.map((code, index) => (
            <span
              key={`${code}-${index}`}
              className="font-mono text-[11px] px-2 py-1 rounded-md bg-brand-soft text-brand border border-brand/20"
            >
              {code}
            </span>
          ))}
        </div>
      )}

      <div className="flex-1 min-h-0 flex items-center justify-center">
        {empty ? (
          <p className="text-muted text-center text-[15px] max-w-xs">
            Sign in front of the camera. Recognised signs will build a message here.
          </p>
        ) : message ? (
          <div className="w-full text-center animate-fade-up">
            <p className="urdu text-hero font-semibold text-ink">{message.urdu_text}</p>
            {message.english_text && (
              <p className="text-muted text-sm mt-3">{message.english_text}</p>
            )}
          </div>
        ) : (
          <div className="w-full text-center">
            <p className="text-muted text-[15px]">
              No supported message for these signs yet.
            </p>
          </div>
        )}
      </div>

      {/* Never invent a sentence — say plainly what happened instead. */}
      {note && matched !== "exact" && (
        <p className="text-[13px] text-amber-700 bg-amber-50 border border-warn/25 rounded-lg px-3 py-2">
          {note}
        </p>
      )}

      {speechError && (
        <p className="text-[13px] text-danger bg-red-50 border border-danger/25 rounded-lg px-3 py-2">
          {speechError}
        </p>
      )}

      <div className="flex gap-2.5">
        <button onClick={onSpeak} disabled={!canSpeak} className="btn-primary flex-1">
          {speaking ? (
            <>
              <svg viewBox="0 0 24 24" className="w-5 h-5 animate-pulse-soft" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                <path d="M11 5 6 9H2v6h4l5 4V5z" />
                <path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a9 9 0 0 1 0 14" />
              </svg>
              Speaking…
            </>
          ) : (
            <>
              <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor"
                   strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M11 5 6 9H2v6h4l5 4V5z" />
                <path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a9 9 0 0 1 0 14" />
              </svg>
              Speak to Doctor
            </>
          )}
        </button>

        <button onClick={onUndo} disabled={empty} className="btn-secondary px-4" title="Undo last sign">
          <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M3 7v6h6" />
            <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" />
          </svg>
          <span className="hidden xl:inline">Undo</span>
        </button>

        <button onClick={onClear} disabled={empty} className="btn-quiet px-4" title="Clear message">
          <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor"
               strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
          </svg>
          <span className="hidden xl:inline">Clear</span>
        </button>
      </div>
    </section>
  );
}
