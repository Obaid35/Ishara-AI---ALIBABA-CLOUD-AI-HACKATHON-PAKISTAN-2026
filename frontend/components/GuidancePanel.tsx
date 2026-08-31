"use client";

/**
 * Guidance drawer — "what am I supposed to perform?"
 *
 * Nobody remembers ten movements exactly, and a half-remembered sign is worse
 * than no sign: it either lands as unknown or, if it drifts toward a different
 * reference, produces the wrong sentence. So the reference performance is put
 * one tap away, looping, next to the sentence that sign will produce.
 *
 * Only the live vocabulary is listed. Teaching a movement the recogniser cannot
 * match would waste the signer's time.
 *
 * The panel is admin-controlled (settings.guidance_panel_enabled) because it is
 * a rehearsal aid: useful for a team learning the vocabulary, out of place on a
 * screen facing a patient mid-consultation.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { get } from "@/lib/api";

export interface GuidanceSign {
  code: string;
  urdu_meaning: string;
  english_meaning: string;
  urdu_text: string | null;
  note: string | null;
  reference_count: number;
  video: string | null;
  start_s: number | null;
  end_s: number | null;
}

/** Plays only the slice of the source video that is the sign, on a loop. */
function SignClip({ sign }: { sign: GuidanceSign }) {
  const ref = useRef<HTMLVideoElement | null>(null);
  const [failed, setFailed] = useState(false);

  const start = sign.start_s ?? 0;
  const end = sign.end_s ?? null;

  // The media fragment gets the browser to the right place on load; keeping it
  // there needs a seek, because a fragment does not loop.
  const rewind = useCallback(() => {
    const video = ref.current;
    if (!video) return;
    if (end !== null && video.currentTime >= end) video.currentTime = start;
  }, [start, end]);

  useEffect(() => {
    const video = ref.current;
    if (!video) return;
    video.currentTime = start;
    void video.play().catch(() => undefined);
  }, [start, sign.code]);

  if (!sign.video || failed) {
    return (
      <div className="aspect-video rounded-lg bg-page border border-line grid place-items-center">
        <p className="text-xs text-muted px-4 text-center">
          No reference video on file for this sign.
        </p>
      </div>
    );
  }

  return (
    <video
      ref={ref}
      // eslint-disable-next-line jsx-a11y/media-has-caption -- silent reference clip
      src={end !== null ? `${sign.video}#t=${start},${end}` : sign.video}
      className="w-full aspect-video rounded-lg bg-camera object-contain"
      autoPlay
      muted
      playsInline
      loop
      onTimeUpdate={rewind}
      onError={() => setFailed(true)}
    />
  );
}

export default function GuidancePanel() {
  const [enabled, setEnabled] = useState(false);
  const [open, setOpen] = useState(false);
  const [signs, setSigns] = useState<GuidanceSign[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    get<{ settings: Record<string, unknown> }>("/api/settings", false)
      .then((data) => setEnabled(data.settings.guidance_panel_enabled === true))
      .catch(() => setEnabled(false));
  }, []);

  // Loaded on first open, not on mount: the patient screen should not pay for
  // a panel most sessions never use.
  useEffect(() => {
    if (!open || signs.length > 0) return;
    get<{ signs: GuidanceSign[] }>("/api/guidance", false)
      .then((data) => {
        setSigns(data.signs);
        setActive(data.signs[0]?.code ?? null);
        setError(data.signs.length === 0 ? "No signs are enabled yet." : null);
      })
      .catch(() => setError("Could not load the sign guide."));
  }, [open, signs.length]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!enabled) return null;

  return (
    <>
      {/* ------------------------------------------------ floating button

          Hidden while the drawer is open: the drawer sits over this corner, so
          a toggle here would be behind it and the panel would look unclosable.
          Closing belongs to the X in the drawer's own header. */}
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open the sign guide"
          className="fixed bottom-14 right-5 z-40 h-14 w-14 rounded-full bg-brand text-white
                     shadow-lift grid place-items-center hover:bg-brand-hover
                     focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2
                     transition-transform active:scale-95"
        >
          <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H10a2 2 0 0 1 2 2v13a1.5 1.5 0 0 0-1.5-1.5h-5A1.5 1.5 0 0 1 4 16V5.5Z" />
            <path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H14a2 2 0 0 0-2 2v13a1.5 1.5 0 0 1 1.5-1.5h5A1.5 1.5 0 0 0 20 16V5.5Z" />
          </svg>
        </button>
      )}

      {/* ------------------------------------------------ drawer */}
      {open && (
        <>
          <div
            className="fixed inset-0 z-30 bg-ink/20 lg:hidden"
            onClick={() => setOpen(false)}
            aria-hidden
          />
          <aside
            className="fixed top-0 right-0 z-40 h-full w-full sm:w-[420px] bg-surface
                       border-l border-line shadow-lift flex flex-col animate-fade-up"
            aria-label="Sign guide"
          >
            <header className="shrink-0 px-5 py-4 border-b border-line flex items-start gap-3">
              <div className="min-w-0 flex-1">
                <h2 className="text-base font-semibold text-ink">How to sign</h2>
                <p className="text-xs text-muted mt-0.5">
                  Copy the movement, then perform it to the camera.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close the sign guide"
                className="shrink-0 -mr-1.5 -mt-1 h-9 w-9 rounded-lg grid place-items-center
                           text-muted hover:text-ink hover:bg-page
                           focus-visible:ring-2 focus-visible:ring-brand"
              >
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </header>

            <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-2.5">
              {error && <p className="text-sm text-muted px-1">{error}</p>}

              {signs.map((sign) => {
                const isActive = active === sign.code;
                return (
                  <div
                    key={sign.code}
                    className={`rounded-card border transition-colors ${
                      isActive ? "border-brand/40 bg-brand-soft/40" : "border-line bg-surface"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => setActive(isActive ? null : sign.code)}
                      aria-expanded={isActive}
                      className="w-full px-4 py-3 flex items-center justify-between gap-3 text-left"
                    >
                      <span className="min-w-0">
                        <span className="block font-urdu text-lg text-ink leading-snug">
                          {sign.urdu_meaning}
                        </span>
                        <span className="block text-xs text-muted mt-0.5">
                          {sign.english_meaning || sign.code}
                        </span>
                      </span>
                      <svg
                        viewBox="0 0 24 24"
                        className={`h-4 w-4 shrink-0 text-muted transition-transform ${
                          isActive ? "rotate-180" : ""
                        }`}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                      >
                        <path d="M6 9l6 6 6-6" />
                      </svg>
                    </button>

                    {isActive && (
                      <div className="px-4 pb-4 space-y-3">
                        <SignClip sign={sign} />

                        {/* What the screen will actually say, so the signer can
                            check it is the sentence they meant before speaking. */}
                        {sign.urdu_text ? (
                          <div className="rounded-lg bg-surface border border-line px-3 py-2.5">
                            <p className="text-[11px] uppercase tracking-wide text-muted mb-1">
                              This sign says
                            </p>
                            <p className="font-urdu text-lg text-ink leading-relaxed">
                              {sign.urdu_text}
                            </p>
                          </div>
                        ) : (
                          <p className="text-xs text-muted">
                            Recognised, but no sentence is written for this sign yet.
                          </p>
                        )}

                        {sign.note && <p className="text-xs text-muted">{sign.note}</p>}

                        <p className="text-[11px] text-muted">
                          {sign.reference_count} reference
                          {sign.reference_count === 1 ? "" : "s"} on file
                        </p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <footer className="shrink-0 px-5 py-3 border-t border-line">
              <p className="text-[11px] text-muted">
                These are the only signs the system can recognise. Anything else is
                reported as unknown rather than guessed.
              </p>
            </footer>
          </aside>
        </>
      )}
    </>
  );
}
